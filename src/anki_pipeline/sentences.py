"""Lectura y validacion del archivo de oraciones (la entrada de las etapas 2 y 3).

Formato: una oracion por linea ->  oracion en ingles | traduccion al espanol
  - Lineas vacias y lineas que empiezan con '#' se ignoran.
  - Una linea '@deck: alias' indica a que mazo pertenece el archivo (la lee anki_pipeline.decks).
  - Se separa por el PRIMER '|'.
  - Si el mismo texto en ingles aparece dos veces, se conserva la primera (ver warnings).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SentencePair:
    english: str
    spanish: str
    line_no: int


def normalize(text: str) -> str:
    """Colapsa espacios repetidos/saltos: 'Hello   world ' -> 'Hello world'."""
    return " ".join(text.split())


def parse_sentences_file(path: str | Path) -> tuple[list[SentencePair], list[str]]:
    """Devuelve (oraciones, avisos). Lanza ValueError con TODOS los errores si el archivo es invalido."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de oraciones: {path}")

    pairs: list[SentencePair] = []
    warnings: list[str] = []
    errors: list[str] = []
    seen: dict[str, int] = {}

    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.lower().startswith("@deck"):
            continue
        if "|" not in line:
            errors.append(f"linea {line_no}: falta el separador '|'  ->  {line[:60]}")
            continue
        english, spanish = (normalize(p) for p in line.split("|", 1))
        if not english or not spanish:
            errors.append(f"linea {line_no}: el ingles o la traduccion estan vacios")
            continue
        key = english.casefold()
        if key in seen:
            warnings.append(f"linea {line_no}: repetida (ya estaba en la linea {seen[key]}), se omite -> {english[:50]}")
            continue
        seen[key] = line_no
        pairs.append(SentencePair(english, spanish, line_no))

    if errors:
        raise ValueError("Archivo de oraciones invalido:\n  " + "\n  ".join(errors))
    if not pairs:
        raise ValueError("El archivo no contiene ninguna oracion.")
    return pairs, warnings
