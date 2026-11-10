"""LANZADOR - Un solo comando por camino. Cada etapa corre como proceso aparte (la VRAM se libera entre etapas).

CAMINO A (video o audio -> mensaje listo para el chat):
    python scripts/run.py transcribir "https://youtu.be/XXXX" --deck blogs
    python scripts/run.py transcribir data/input/clase.mp4 --deck aula --n 15
      -> descarga (si es enlace), transcribe, y deja el mensaje completo en el portapapeles (solo pegar en el chat)

     ...tu pasas el mensaje por el chat y guardas el bloque que te devuelva en data/input/<algo>.txt ...

CAMINO B (oraciones -> mazo de Anki):
    python scripts/run.py armar data/input/<algo>.txt
      -> genera los audios y arma el .apkg (el mazo sale de la linea '@deck:' del archivo)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline import config  # noqa: E402
from anki_pipeline.decks import resolve_deck  # noqa: E402
from anki_pipeline.prompt import build_prompt  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent


def run_stage(script: str, *args: str) -> int:
    """Corre una etapa como PROCESO APARTE: al terminar, Windows libera toda su VRAM."""
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd).returncode


def copy_to_clipboard(path: Path) -> bool:
    if sys.platform != "win32":
        return False
    env = dict(os.environ, ANKI_CLIP_FILE=str(path))
    ps = "Get-Content -Raw -Encoding UTF8 -LiteralPath $env:ANKI_CLIP_FILE | Set-Clipboard"
    return subprocess.run(["powershell", "-NoProfile", "-Command", ps], env=env).returncode == 0


def cmd_transcribir(args: argparse.Namespace) -> int:
    try:
        deck_key, deck_name = resolve_deck(args.deck)
    except ValueError as e:
        print(f"[FAIL] {e}")
        return 1

    source = args.source
    if source.lower().startswith(("http://", "https://")):
        print("== 1/3 Descargando audio ==", flush=True)
        from anki_pipeline.download import download_audio

        try:
            audio = download_audio(source)
        except (ValueError, RuntimeError) as e:
            print(f"[FAIL] {e}")
            return 1
    else:
        audio = Path(source)
        if not audio.is_file():
            print(f"[FAIL] No existe el archivo: {audio}")
            return 1

    print(f"\n== 2/3 Transcribiendo con Whisper ({audio.name}) ==", flush=True)
    if run_stage("01_transcribe.py", str(audio)) != 0:
        print("[FAIL] La transcripcion fallo; mira el mensaje de arriba.")
        return 1

    print("\n== 3/3 Armando el mensaje para el chat ==", flush=True)
    transcript = (config.TRANSCRIPTS_DIR / f"{audio.stem}.txt").read_text(encoding="utf-8")
    prompt = build_prompt(deck_key, args.n, transcript)
    prompt_path = config.TRANSCRIPTS_DIR / f"{audio.stem}.prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    copied = (not args.no_copiar) and copy_to_clipboard(prompt_path)
    print(f"[ OK ] Mensaje para el mazo '{deck_name}' ({args.n} oraciones) -> {prompt_path}")
    print("       " + ("COPIADO al portapapeles: pegalo en el chat con Ctrl+V." if copied
                        else "Abre ese archivo, copia todo y pegalo en el chat."))
    print("\nSiguiente: guarda el bloque que te devuelva el chat en data/input/<nombre>.txt y corre:")
    print("    python scripts/run.py armar data/input/<nombre>.txt")
    return 0


def cmd_armar(args: argparse.Namespace) -> int:
    if not args.sentences.is_file():
        print(f"[FAIL] No existe el archivo: {args.sentences}")
        return 1
    print("== 1/2 Generando audios (Kokoro) ==", flush=True)
    if run_stage("02_tts.py", str(args.sentences)) != 0:
        print("[FAIL] La generacion de audios fallo; mira el mensaje de arriba.")
        return 1
    print("\n== 2/2 Armando el mazo de Anki ==", flush=True)
    if run_stage("03_build_deck.py", str(args.sentences)) != 0:
        print("[FAIL] El armado del mazo fallo; mira el mensaje de arriba.")
        return 1
    print("\nListo: abre la carpeta data\\decks y haz doble clic en el .apkg para importarlo en Anki.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("transcribir", help="enlace/archivo -> transcripcion -> mensaje listo para el chat")
    t.add_argument("source", help="enlace (entre comillas) o ruta a un audio/video")
    t.add_argument("--deck", required=True, help="alias del mazo (ver config.DECKS)")
    t.add_argument("--n", type=int, default=10, help="cuantas oraciones pedir al chat (por defecto 10)")
    t.add_argument("--no-copiar", action="store_true", help="no copiar el mensaje al portapapeles")
    t.set_defaults(func=cmd_transcribir)

    a = sub.add_parser("armar", help="archivo de oraciones -> audios -> mazo .apkg")
    a.add_argument("sentences", type=Path)
    a.set_defaults(func=cmd_armar)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
