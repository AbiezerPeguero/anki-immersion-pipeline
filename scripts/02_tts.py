"""ETAPA 2 - Convertir las oraciones en audios .mp3 (Kokoro en GPU, voz af_heart+af_bella).

Uso:
    uv run python scripts/02_tts.py data/input/oraciones_prueba.txt
    uv run python scripts/02_tts.py data/input/oraciones.txt --deck aula
    uv run python scripts/02_tts.py data/input/oraciones.txt --force      # regenerar aunque ya existan
    uv run python scripts/02_tts.py data/input/oraciones.txt --speed 0.9  # un poco mas lento

Formato del archivo: primera linea  @deck: alias   y luego una oracion por linea ->  ingles | espanol
Resultado: data/audio/<alias-del-mazo>/<hash>.mp3 (uno por oracion)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline import config  # noqa: E402
from anki_pipeline.decks import deck_audio_dir, read_deck_directive, resolve_deck  # noqa: E402
from anki_pipeline.sentences import parse_sentences_file  # noqa: E402
from anki_pipeline.tts import audio_filename, synthesize_all  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sentences", type=Path, help="archivo de oraciones (ingles | espanol)")
    ap.add_argument("--deck", default=None, help="alias del mazo (si no, se lee '@deck:' del archivo)")
    ap.add_argument("--voice", default=config.KOKORO_VOICE)
    ap.add_argument("--speed", type=float, default=config.KOKORO_SPEED)
    ap.add_argument("--force", action="store_true", help="regenerar aunque el audio ya exista")
    args = ap.parse_args()

    try:
        pairs, warns = parse_sentences_file(args.sentences)
        deck_key, deck_name = resolve_deck(args.deck or read_deck_directive(args.sentences))
    except (FileNotFoundError, ValueError) as e:
        print(f"[FAIL] {e}")
        return 1
    for w in warns:
        print(f"[WARN] {w}")
    audio_dir = deck_audio_dir(deck_key)
    print(f"Mazo: '{deck_name}' ({deck_key}) | {len(pairs)} oraciones | voz {args.voice} | velocidad {args.speed}\n", flush=True)

    def progress(i: int, total: int, pair, status: str) -> None:
        print(f"[{i}/{total}] {status:<9} {audio_filename(pair.english, args.voice, args.speed)}  {pair.english}", flush=True)

    stats = synthesize_all(pairs, audio_dir, voice=args.voice, speed=args.speed, force=args.force, progress=progress)

    print(f"\n{stats.generated} generadas | {stats.cached} ya existian | {stats.failed} fallidas | "
          f"{stats.elapsed_s:.1f}s en total (carga del modelo: {stats.load_s:.1f}s)")
    print(f"Audios en: {audio_dir}")
    return 1 if stats.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
