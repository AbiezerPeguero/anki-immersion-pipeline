"""A que mazo pertenece cada archivo de oraciones (y donde viven sus audios).

Un archivo declara su mazo con una linea   @deck: alias   (o se pasa --deck alias en la linea de comandos).
Los alias validos viven en config.DECKS. Un alias desconocido es un ERROR a proposito: evita que un
error de tipeo cree un mazo nuevo sin que te des cuenta.
"""
from __future__ import annotations

import re
from pathlib import Path

from anki_pipeline import config

_DIRECTIVE = re.compile(r"^@deck\s*:\s*(.+?)\s*$", re.IGNORECASE)


def read_deck_directive(path: str | Path) -> str | None:
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        m = _DIRECTIVE.match(raw.strip())
        if m:
            return m.group(1).strip().lower()
    return None


def resolve_deck(key: str | None) -> tuple[str, str]:
    """(alias, nombre_del_mazo). Lanza ValueError con la lista de alias validos si no hay/no existe."""
    valid = ", ".join(sorted(config.DECKS))
    if not key:
        raise ValueError(
            "No se indico a que mazo pertenece este archivo. Agrega una linea '@deck: alias' "
            f"al inicio del archivo o usa --deck. Mazos validos: {valid}"
        )
    key = key.strip().lower()
    if key not in config.DECKS:
        raise ValueError(f"Mazo desconocido '{key}'. Validos: {valid}. (Se agregan en config.DECKS)")
    return key, config.DECKS[key]


def deck_audio_dir(key: str) -> Path:
    return config.AUDIO_DIR / key
