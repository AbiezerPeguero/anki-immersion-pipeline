"""Etapa 1b del pipeline: foto(s) de un libro o material -> texto, con OpenCV + EasyOCR (GPU).

Es la alternativa a la transcripcion (etapa 1) cuando el material es una foto en vez de un audio:
la salida es el mismo tipo de archivo .txt en data/transcripts/, listo para pasarlo a Claude.

Esta etapa corre como su propio proceso: al terminar, Windows libera toda la VRAM.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Sequence

from anki_pipeline import config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
PREPROCESS_MODES = ("gray", "none")  # "binarize" se probo y destruye el texto (2% de palabras correctas): eliminado
MIN_SIDE_PX = 1600  # las letras de fotos chicas se leen mal; se amplia hasta este lado largo


def collect_images(paths: Sequence[str | Path]) -> list[Path]:
    """Acepta archivos y/o carpetas. Las carpetas aportan sus imagenes en orden alfabetico (pagina_01, pagina_02...)."""
    found: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            found.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS))
        elif p.is_file():
            if p.suffix.lower() not in IMAGE_EXTS:
                raise ValueError(f"Formato no soportado: {p.name} (usa {', '.join(sorted(IMAGE_EXTS))})")
            found.append(p)
        else:
            raise FileNotFoundError(f"No existe: {p}")
    if not found:
        raise ValueError("No se encontro ninguna imagen.")
    return found


def preprocess_image(img, mode: str = "gray"):
    """img: array BGR de OpenCV.
    gray -> escala de grises + realce de contraste local (CLAHE). Ganador en las pruebas (compare_ocr.py).
    none -> sin tocar la imagen (casi empata con gray)."""
    import cv2

    if mode not in PREPROCESS_MODES:
        raise ValueError(f"Modo desconocido {mode!r}; validos: {', '.join(PREPROCESS_MODES)}")
    if mode == "none":
        return img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    longest = max(gray.shape[:2])
    if longest < MIN_SIDE_PX:
        scale = MIN_SIDE_PX / longest
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


_HYPHEN_BREAK = re.compile(r"(?<=\w)- (?=[a-záéíóúüñ])")


def dehyphenate(text: str) -> str:
    """Une palabras partidas por guion al final de linea: 'conver- sation' -> 'conversation'.
    Solo si lo que sigue empieza en minuscula, asi '18.- Se crea' o 'well- Known' no se tocan."""
    return _HYPHEN_BREAK.sub("", text)


def read_image(path: Path):
    """Lee la imagen por bytes: cv2.imread falla con rutas con acentos o espacios raros en Windows."""
    import cv2
    import numpy as np

    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"No pude abrir la imagen: {path}")
    return img


def low_resolution_warning(path: Path) -> str | None:
    """Las fotos comprimidas por Telegram/WhatsApp (~1280 px) hacen que el OCR confunda letras (e<->c)."""
    h, w = read_image(path).shape[:2]
    if max(h, w) < MIN_SIDE_PX:
        return (f"{path.name} es de baja resolucion ({w}x{h}). Para mejor lectura usa la foto ORIGINAL de la camara "
                "(no la comprimida por WhatsApp/Telegram; en Telegram, enviala como 'Archivo').")
    return None


def ocr_one(reader, path: Path, mode: str, mag_ratio: float, decoder: str) -> str:
    processed = preprocess_image(read_image(path), mode)
    lines = reader.readtext(processed, detail=0, paragraph=True, mag_ratio=mag_ratio, decoder=decoder)
    return dehyphenate("\n".join(t.strip() for t in lines if t.strip()))


def make_reader(gpu: bool = True, languages=config.OCR_LANGUAGES):
    import easyocr

    return easyocr.Reader(list(languages), gpu=gpu)


def ocr_images(
    paths: Sequence[Path],
    mode: str = "gray",
    gpu: bool = True,
    languages=config.OCR_LANGUAGES,
    mag_ratio: float = config.OCR_MAG_RATIO,
    decoder: str = config.OCR_DECODER,
) -> list[str]:
    """Devuelve el texto de cada imagen (una cadena por imagen, parrafos separados por salto de linea)."""
    reader = make_reader(gpu, languages)
    return [ocr_one(reader, p, mode, mag_ratio, decoder) for p in paths]


def text_similarity(reference: str, hypothesis: str) -> tuple[float, float]:
    """(similitud por palabras, similitud por caracteres), de 0 a 1, ignorando saltos de linea y espacios repetidos."""
    ref, hyp = " ".join(reference.split()), " ".join(hypothesis.split())
    words = difflib.SequenceMatcher(None, ref.split(), hyp.split(), autojunk=False).ratio()
    chars = difflib.SequenceMatcher(None, ref, hyp, autojunk=False).ratio()
    return words, chars


def write_ocr_text(pages: Sequence[str], name: str, out_dir: str | Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else config.TRANSCRIPTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.txt"
    out.write_text("\n\n".join(pages).strip() + "\n", encoding="utf-8")
    return out
