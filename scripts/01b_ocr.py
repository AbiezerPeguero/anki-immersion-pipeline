"""ETAPA 1b - Sacar el texto de fotos de un libro o material (OCR con EasyOCR en GPU).

Uso:
    uv run python scripts/01b_ocr.py data/input/fotos/pagina_01.jpg
    uv run python scripts/01b_ocr.py data/input/fotos/                     # todas las fotos de la carpeta, en orden
    uv run python scripts/01b_ocr.py foto1.jpg foto2.jpg --name unidad_3   # varias fotos -> un solo texto

Resultado: data/transcripts/<nombre>.txt  (despues: pegarlo en Claude con el mensaje de prompts/)
Consejo de foto: de frente (sin inclinar), buena luz, sin sombra de tu mano ni del celular.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline.ocr import PREPROCESS_MODES, collect_images, low_resolution_warning, ocr_images, write_ocr_text  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", type=Path, help="fotos y/o carpetas con fotos")
    ap.add_argument("--name", default=None, help="nombre del .txt de salida (por defecto, el de la primera foto)")
    ap.add_argument("--preprocess", choices=PREPROCESS_MODES, default="gray")
    ap.add_argument("--cpu", action="store_true", help="usar CPU en vez de GPU (mucho mas lento)")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    try:
        images = collect_images(args.images)
    except (ValueError, FileNotFoundError) as e:
        print(f"[FAIL] {e}")
        return 1
    name = args.name or images[0].stem
    for img in images:
        if (w := low_resolution_warning(img)):
            print(f"[WARN] {w}")
    print(f"{len(images)} imagen(es) | idioma: ingles | preprocesado: {args.preprocess} | {'CPU' if args.cpu else 'GPU'}", flush=True)

    t0 = time.perf_counter()
    try:
        pages = ocr_images(images, mode=args.preprocess, gpu=not args.cpu)
    except ValueError as e:
        print(f"[FAIL] {e}")
        return 1
    out = write_ocr_text(pages, name, args.out_dir)

    text = out.read_text(encoding="utf-8")
    print(f"\n[ OK ] {len(text.split())} palabras de {len(images)} imagen(es) en {time.perf_counter() - t0:.1f}s -> {out}")
    print("\n--- vista previa (primeras lineas) ---")
    print("\n".join(text.splitlines()[:6]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
