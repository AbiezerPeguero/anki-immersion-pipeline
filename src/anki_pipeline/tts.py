"""Etapa 2 del pipeline: oraciones en ingles -> audio .mp3 con Kokoro (GPU).

Cada oracion produce data/audio/<hash>.mp3 donde <hash> depende de (texto + voz + velocidad):
  - mismo texto, misma voz  -> mismo archivo: no se regenera (cache) y el nombre es estable.
  - cambias la voz o la velocidad -> nombre nuevo: nunca se mezclan audios de voces distintas.

Esta etapa corre como su propio proceso: al terminar, Windows libera toda la VRAM.
"""
from __future__ import annotations

import hashlib
import subprocess
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from anki_pipeline import config
from anki_pipeline.sentences import SentencePair, normalize

SAMPLE_RATE = 24000
TAIL_SILENCE_S = 0.25  # evita que Anki corte la ultima silaba al reproducir


def audio_filename(english: str, voice: str, speed: float) -> str:
    key = f"{normalize(english)}|{voice}|{speed:.2f}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12] + ".mp3"


_END_PUNCT = (".", "!", "?", "…", '"', "'", ")", "”", "’")


def prepare_for_tts(text: str) -> str:
    """Anade un punto final si falta: la entonacion de cierre de Kokoro depende de la puntuacion.
    Solo afecta lo que se le dice a la voz; el texto de la tarjeta y el nombre del audio no cambian."""
    t = normalize(text)
    return t if t.endswith(_END_PUNCT) else t + "."


def pcm_to_mp3(samples, out_path: Path) -> None:
    """samples: array float32 mono a 24 kHz. Escribe de forma atomica (.part -> .mp3)."""
    import imageio_ffmpeg
    import numpy as np

    padded = np.concatenate([samples, np.zeros(int(SAMPLE_RATE * TAIL_SILENCE_S), dtype=np.float32)])
    pcm16 = (np.clip(padded, -1.0, 1.0) * 32767).astype("<i2").tobytes()
    part = out_path.with_name(out_path.name + ".part")
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "pipe:0",
        "-codec:a", "libmp3lame", "-q:a", "4", "-f", "mp3", str(part),
    ]
    proc = subprocess.run(cmd, input=pcm16, capture_output=True)
    if proc.returncode != 0:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg fallo: {proc.stderr.decode(errors='replace')[:300]}")
    part.replace(out_path)


class KokoroSynth:
    def __init__(self, voice: str = config.KOKORO_VOICE, speed: float = config.KOKORO_SPEED,
                 lang: str = config.KOKORO_LANG) -> None:
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*dropout option adds dropout.*")
        from kokoro import KPipeline

        self.voice = voice
        self.speed = speed
        self.pipe = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")

    def synth(self, text: str):
        import numpy as np

        chunks = []
        for _, _, audio in self.pipe(prepare_for_tts(text), voice=self.voice, speed=self.speed):
            chunks.append(audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio))
        if not chunks:
            raise RuntimeError(f"Kokoro no genero audio para: {text[:60]!r}")
        return np.concatenate(chunks).astype(np.float32)


@dataclass
class TtsStats:
    generated: int = 0
    cached: int = 0
    failed: int = 0
    elapsed_s: float = 0.0
    load_s: float = 0.0  # tiempo de cargar el modelo (incluido en elapsed_s)


def synthesize_all(
    pairs: Sequence[SentencePair],
    audio_dir: str | Path | None = None,
    *,
    voice: str = config.KOKORO_VOICE,
    speed: float = config.KOKORO_SPEED,
    force: bool = False,
    progress: Callable[[int, int, SentencePair, str], None] | None = None,
) -> TtsStats:
    """progress(i, total, pair, estado) con estado en {'generada', 'cache', 'FALLO: ...'}."""
    audio_dir = Path(audio_dir) if audio_dir else config.AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)
    stats = TtsStats()
    t0 = time.perf_counter()

    todo = [p for p in pairs if force or not (audio_dir / audio_filename(p.english, voice, speed)).exists()]
    t_load = time.perf_counter()
    synth = KokoroSynth(voice, speed) if todo else None  # si todo esta en cache, ni se carga el modelo
    stats.load_s = time.perf_counter() - t_load

    for i, pair in enumerate(pairs, start=1):
        out = audio_dir / audio_filename(pair.english, voice, speed)
        if not force and out.exists():
            stats.cached += 1
            status = "cache"
        else:
            try:
                pcm_to_mp3(synth.synth(pair.english), out)  # type: ignore[union-attr]
                stats.generated += 1
                status = "generada"
            except Exception as e:  # noqa: BLE001
                stats.failed += 1
                status = f"FALLO: {e}"
        if progress:
            progress(i, len(pairs), pair, status)

    stats.elapsed_s = time.perf_counter() - t0
    return stats
