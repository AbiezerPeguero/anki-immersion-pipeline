"""Rutas y constantes del proyecto (un solo lugar para no repetir rutas en cada script)."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"              # videos / audios / fotos de entrada
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"  # .txt generados por Whisper / OCR
AUDIO_DIR = DATA_DIR / "audio"              # .mp3 de cada oracion (TTS)
DECKS_DIR = DATA_DIR / "decks"              # .apkg finales
TMP_DIR = DATA_DIR / "tmp"                  # pruebas y temporales

# Modelos por defecto (se pueden cambiar sin tocar el resto del codigo)
WHISPER_MODEL = "large-v3"
WHISPER_COMPUTE_TYPE = "float16"
# Medido en la RTX 4060 (13.8 min de audio): batch 4 -> pico 4.85 GB y 32.9x tiempo real.
# batch 1 -> pico 5.24 GB y 7.2x. Con ~6.9 GB libres, batch 4 deja ~2 GB de margen.
WHISPER_BATCH_SIZE = 4
WHISPER_BEAM_SIZE = 5
WHISPER_LANGUAGE = "en"      # None = autodetectar
# Mezcla de dos voces (Kokoro promedia sus tensores): determinista, suena igual en cada generacion.
KOKORO_VOICE = "af_heart,af_bella"   # elegida por el usuario tras comparar de oido
KOKORO_SPEED = 1.0
KOKORO_LANG = "a"           # 'a' = American English

# OCR: solo ingles (los libros del aula son en ingles)
OCR_LANGUAGES = ("en",)
# Ajustes de EasyOCR (se eligen con scripts/compare_ocr.py, midiendo contra un texto de referencia)
OCR_MAG_RATIO = 1.0        # >1 amplia la imagen antes de leer: ayuda con letra pequena
OCR_DECODER = "greedy"     # "beamsearch" suele ser mas preciso y algo mas lento


# --- Anki: identidad de los mazos. NO CAMBIAR los nombres despues de importar: ---
# el ID del mazo y de cada nota se derivan del NOMBRE, y de eso depende que cada importacion se
# SUME AL mazo existente en vez de crear uno nuevo o duplicar tarjetas.
#
# Registro de mazos:  alias corto (minusculas, sin espacios)  ->  nombre EXACTO del mazo en Anki.
# Cada archivo de oraciones declara su mazo con una linea '@deck: alias' (o con --deck alias).
DECKS: dict[str, str] = {
    "aula": "Inglés Inmersión",   # todo lo que ensenan en el aula
    "blogs": "Sergii Speaks",     # canal: videos viajando y hablando con varias personas en ingles
    "podcast": "TED",             # canal: TED
    # "alias": "Nombre del mazo",   <- para agregar otro: alias en minusculas, sin espacios; nombre = como se vera en Anki
}
DECK_NAME = DECKS["aula"]  # mazo por defecto para las funciones de bajo nivel
MODEL_NAME = "Inglés Inmersión (Audio)"
MODEL_VERSION = 1  # subir SOLO si cambian los campos o las plantillas de la tarjeta (ver README)


def ensure_dirs() -> None:
    for d in (INPUT_DIR, TRANSCRIPTS_DIR, AUDIO_DIR, DECKS_DIR, TMP_DIR):
        d.mkdir(parents=True, exist_ok=True)
