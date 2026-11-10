"""ETAPA 1 - Transcribir un audio/video a texto (Whisper large-v3 en GPU).

Uso:
    uv run python scripts/01_transcribe.py data/input/prueba_ingles.mp3
    uv run python scripts/01_transcribe.py data/input/clase.mp4 --language en
    uv run python scripts/01_transcribe.py data/input/otro.mp3 --batch-size 1   # modo mas lento y conservador

Resultado: data/transcripts/<nombre>.txt  y  <nombre>.timestamps.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline import config  # noqa: E402
from anki_pipeline.transcribe import fmt_timestamp, transcribe_file  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", type=Path, help="audio o video de entrada")
    ap.add_argument("--out-dir", type=Path, default=None, help=f"por defecto {config.TRANSCRIPTS_DIR}")
    ap.add_argument("--model", default=config.WHISPER_MODEL)
    ap.add_argument("--batch-size", type=int, default=config.WHISPER_BATCH_SIZE)
    ap.add_argument("--language", default=config.WHISPER_LANGUAGE, help="codigo ISO (en, es...) o 'auto'")
    args = ap.parse_args()

    language = None if args.language in (None, "auto") else args.language
    next_mark = [60.0]  # avisar cada ~60 s de audio procesado

    def progress(done_s: float, total_s: float) -> None:
        if done_s >= next_mark[0]:
            print(f"   ... {fmt_timestamp(done_s)} / {fmt_timestamp(total_s)}", flush=True)
            next_mark[0] = done_s + 60.0

    print(f"Transcribiendo {args.audio.name} con {args.model} (batch {args.batch_size}) ...", flush=True)
    try:
        r = transcribe_file(
            args.audio,
            args.out_dir,
            model_name=args.model,
            batch_size=args.batch_size,
            language=language,
            progress=progress,
        )
    except FileNotFoundError as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"\n[ OK ] {r.n_words} palabras en {r.n_segments} segmentos | idioma: {r.language}")
    print(f"       {fmt_timestamp(r.duration_s)} de audio en {r.elapsed_s:.0f}s ({r.duration_s / r.elapsed_s:.1f}x tiempo real)")
    print(f"       -> {r.text_path}")
    print(f"       -> {r.timestamps_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
