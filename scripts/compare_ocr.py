"""Compara configuraciones de OCR sobre UNA foto y mide cual se parece mas al texto correcto.

Uso:
    python scripts/compare_ocr.py data/input/fotos/foto_02.jpg --reference data/input/fotos/foto_02.reference.txt

El archivo de referencia es el texto correcto de esa foto (escrito o copiado a mano).
Prueba preprocesado (gray/none) x ampliacion (1.0/1.5/2.0) x decodificador (greedy/beamsearch)
y guarda cada resultado en data/tmp/ocr_variants/ para que puedas abrirlos y compararlos.
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline import config  # noqa: E402
from anki_pipeline.ocr import PREPROCESS_MODES, make_reader, ocr_one, text_similarity  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("--reference", type=Path, required=True)
    args = ap.parse_args()

    reference = args.reference.read_text(encoding="utf-8")
    out_dir = config.TMP_DIR / "ocr_variants"
    out_dir.mkdir(parents=True, exist_ok=True)

    reader = make_reader()
    rows = []
    combos = list(itertools.product(PREPROCESS_MODES, (1.0, 1.5, 2.0), ("greedy", "beamsearch")))
    for i, (mode, mag, decoder) in enumerate(combos, start=1):
        label = f"{mode}_mag{mag}_{decoder}"
        t0 = time.perf_counter()
        try:
            text = ocr_one(reader, args.image, mode, mag, decoder)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(combos)}] {label}: FALLO {e!r}", flush=True)
            continue
        dt = time.perf_counter() - t0
        words, chars = text_similarity(reference, text)
        (out_dir / f"{label}.txt").write_text(text + "\n", encoding="utf-8")
        rows.append((words, chars, dt, label))
        print(f"[{i}/{len(combos)}] {label:<28} palabras {words:.1%} | caracteres {chars:.1%} | {dt:.1f}s", flush=True)

    print("\n=== RANKING (mejor primero) ===")
    for words, chars, dt, label in sorted(rows, reverse=True):
        print(f"{label:<28} palabras {words:.1%} | caracteres {chars:.1%} | {dt:.1f}s")
    print(f"\nTextos de cada variante en: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
