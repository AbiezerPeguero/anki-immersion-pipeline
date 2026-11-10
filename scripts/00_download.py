"""ETAPA 0 - Descargar el audio de un video (YouTube y otros sitios) como .mp3.

Uso:
    uv run python scripts/00_download.py "https://www.youtube.com/watch?v=XXXX"
    uv run python scripts/00_download.py "https://youtu.be/XXXX" --out-dir data/input/downloads

IMPORTANTE: pon el enlace entre comillas (en PowerShell el & y el ? del enlace dan problemas sin ellas).
Resultado: data/input/downloads/<titulo>_<id>.mp3  (despues: 01_transcribe.py sobre ese archivo)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline.download import download_audio  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    try:
        path = download_audio(args.url, args.out_dir)
    except (ValueError, RuntimeError) as e:
        print(f"[FAIL] {e}")
        return 1
    print(f"\n[ OK ] Audio guardado en: {path}")
    print(f'       Siguiente: uv run python scripts/01_transcribe.py "{path}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
