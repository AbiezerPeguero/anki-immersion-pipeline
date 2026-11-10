"""Etapa 1 del pipeline: audio/video -> texto, con faster-whisper en GPU.

Entrada : cualquier audio o video que ffmpeg/PyAV pueda leer (mp3, mp4, wav, m4a...).
Salida  : dos archivos en data/transcripts/
            <nombre>.txt             texto limpio, una frase/segmento por linea (para pegar en Claude)
            <nombre>.timestamps.txt  igual, con [MM:SS] al inicio de cada linea (para ubicar momentos)

Esta etapa corre como su propio proceso: al terminar, Windows libera toda la VRAM.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from anki_pipeline import config

Row = tuple[float, float, str]  # (inicio_s, fin_s, texto)


@dataclass
class TranscriptResult:
    text_path: Path
    timestamps_path: Path
    language: str
    duration_s: float
    elapsed_s: float
    n_segments: int
    n_words: int


def fmt_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def render_transcripts(rows: Sequence[Row]) -> tuple[str, str]:
    """Devuelve (texto_limpio, texto_con_timestamps)."""
    clean = "\n".join(text for _, _, text in rows) + "\n"
    stamped = "\n".join(f"[{fmt_timestamp(start)}] {text}" for start, _, text in rows) + "\n"
    return clean, stamped


def transcribe_file(
    audio_path: str | Path,
    out_dir: str | Path | None = None,
    *,
    model_name: str = config.WHISPER_MODEL,
    compute_type: str = config.WHISPER_COMPUTE_TYPE,
    batch_size: int = config.WHISPER_BATCH_SIZE,
    beam_size: int = config.WHISPER_BEAM_SIZE,
    language: str | None = config.WHISPER_LANGUAGE,
    progress: Callable[[float, float], None] | None = None,
) -> TranscriptResult:
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise FileNotFoundError(f"No existe el archivo de entrada: {audio_path}")
    out_dir = Path(out_dir) if out_dir else config.TRANSCRIPTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # Imports pesados aqui adentro: importar este modulo (y sus tests) no exige GPU.
    from anki_pipeline.cuda_setup import ensure_cuda_dlls

    ensure_cuda_dlls()
    from faster_whisper import BatchedInferencePipeline, WhisperModel

    model = WhisperModel(model_name, device="cuda", compute_type=compute_type)

    t0 = time.perf_counter()
    if batch_size > 1:
        segments, info = BatchedInferencePipeline(model).transcribe(
            str(audio_path), language=language, beam_size=beam_size, batch_size=batch_size
        )
    else:
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=beam_size,
            vad_filter=True,
            condition_on_previous_text=False,  # evita bucles de repeticion en audios largos
        )

    rows: list[Row] = []
    for seg in segments:  # el generador es el que realmente transcribe
        text = seg.text.strip()
        if text:
            rows.append((seg.start, seg.end, text))
        if progress:
            progress(seg.end, info.duration)
    elapsed = time.perf_counter() - t0

    clean, stamped = render_transcripts(rows)
    text_path = out_dir / f"{audio_path.stem}.txt"
    stamps_path = out_dir / f"{audio_path.stem}.timestamps.txt"
    text_path.write_text(clean, encoding="utf-8")
    stamps_path.write_text(stamped, encoding="utf-8")

    return TranscriptResult(
        text_path=text_path,
        timestamps_path=stamps_path,
        language=info.language,
        duration_s=info.duration,
        elapsed_s=elapsed,
        n_segments=len(rows),
        n_words=sum(len(t.split()) for _, _, t in rows),
    )
