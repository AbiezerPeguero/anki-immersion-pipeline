"""ETAPA 3 - Armar el mazo de Anki (.apkg) con las oraciones y sus audios.

Uso:
    uv run python scripts/03_build_deck.py data/input/oraciones_prueba.txt
    uv run python scripts/03_build_deck.py data/input/oraciones.txt --deck aula --out data/decks/lote_01.apkg

Requiere haber corrido antes la etapa 2 con el mismo mazo, voz y velocidad.
Resultado: data/decks/<alias>__<nombre-del-archivo>.apkg  -> doble clic para importarlo en Anki.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline import config  # noqa: E402
from anki_pipeline.anki_deck import build_deck  # noqa: E402
from anki_pipeline.decks import deck_audio_dir, read_deck_directive, resolve_deck  # noqa: E402
from anki_pipeline.sentences import parse_sentences_file  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sentences", type=Path)
    ap.add_argument("--deck", default=None, help="alias del mazo (si no, se lee '@deck:' del archivo)")
    ap.add_argument("--out", type=Path, default=None, help="por defecto data/decks/<alias>__<nombre>.apkg")
    ap.add_argument("--voice", default=config.KOKORO_VOICE)
    ap.add_argument("--speed", type=float, default=config.KOKORO_SPEED)
    args = ap.parse_args()

    try:
        pairs, warns = parse_sentences_file(args.sentences)
        deck_key, deck_name = resolve_deck(args.deck or read_deck_directive(args.sentences))
        out = args.out or (config.DECKS_DIR / f"{deck_key}__{args.sentences.stem}.apkg")
        r = build_deck(pairs, out, audio_dir=deck_audio_dir(deck_key), voice=args.voice, speed=args.speed, deck_name=deck_name)
    except (FileNotFoundError, ValueError) as e:
        print(f"[FAIL] {e}")
        return 1
    for w in warns:
        print(f"[WARN] {w}")

    print(f"[ OK ] {r.n_notes} tarjetas -> {r.apkg_path}  ({r.apkg_path.stat().st_size / 1024:.0f} KB)")
    print(f"       Mazo: '{r.deck_name}' (ID {r.deck_id})  | se suma al mazo existente con ese nombre")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
