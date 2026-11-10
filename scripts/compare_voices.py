"""Genera la MISMA muestra con varias voces de Kokoro para compararlas de oido.

Uso:
    uv run python scripts/compare_voices.py                  # voces por defecto
    uv run python scripts/compare_voices.py --speed 0.9      # un poco mas lento (bueno para aprender)
    uv run python scripts/compare_voices.py --voices af_heart af_bella "af_heart,af_bella"

Una voz con coma ("af_heart,af_bella") es una MEZCLA de dos voces.
Resultado: un .wav por voz en data/tmp/voices/ (3 frases seguidas cada uno). Escuchalos en orden.
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline.config import KOKORO_LANG, TMP_DIR, ensure_dirs  # noqa: E402

SAMPLE_RATE = 24000
SENTENCES = [
    "I can't believe how fast time flies when you're having fun.",
    "Could you tell me where the nearest bank is? I need to withdraw some cash.",
    "She's been working here for ten years, and she still loves it.",
]
DEFAULT_VOICES = [
    "af_heart", "af_bella", "af_nicole", "af_sarah", "af_nova", "af_sky",
    "af_heart,af_bella", "af_bella,af_nicole",
]


def to_numpy(audio) -> np.ndarray:
    return audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", nargs="+", default=DEFAULT_VOICES)
    ap.add_argument("--speed", type=float, default=1.0)
    args = ap.parse_args()

    from kokoro import KPipeline

    ensure_dirs()
    out_dir = TMP_DIR / "voices"
    out_dir.mkdir(exist_ok=True)

    pipe = KPipeline(lang_code=KOKORO_LANG, repo_id="hexgrad/Kokoro-82M")
    pause = np.zeros(int(SAMPLE_RATE * 0.8), dtype=np.float32)

    for voice in args.voices:
        t0 = time.perf_counter()
        parts: list[np.ndarray] = []
        try:
            for sentence in SENTENCES:
                for _, _, audio in pipe(sentence, voice=voice, speed=args.speed):
                    parts.append(to_numpy(audio))
                parts.append(pause)
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {voice}: {e!r}")
            continue
        name = voice.replace(",", "+")
        path = out_dir / f"{name}_speed{args.speed}.wav"
        sf.write(path, np.concatenate(parts), SAMPLE_RATE)
        print(f"[ OK ] {voice:<20} -> {path.name}  ({time.perf_counter() - t0:.1f}s)")

    print(f"\nListo. Abre la carpeta: {out_dir}")


if __name__ == "__main__":
    main()
