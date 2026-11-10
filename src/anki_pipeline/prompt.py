"""Arma el mensaje para el chat (Claude/DeepSeek) a partir de la plantilla y la transcripcion."""
from __future__ import annotations

from pathlib import Path

from anki_pipeline import config

TEMPLATE_PATH = config.PROJECT_ROOT / "prompts" / "plantilla_prompt.txt"
PLACEHOLDERS = ("{{DECK}}", "{{N}}", "{{TEXT}}")


def build_prompt(deck_key: str, n: int, text: str, template: str | None = None) -> str:
    if n < 1:
        raise ValueError("La cantidad de oraciones debe ser al menos 1.")
    template = template if template is not None else TEMPLATE_PATH.read_text(encoding="utf-8")
    missing = [p for p in PLACEHOLDERS if p not in template]
    if missing:
        raise ValueError(f"La plantilla no tiene estos marcadores: {', '.join(missing)}")
    # El texto va al final y se inserta de ULTIMO: asi nada dentro de la transcripcion se confunde con un marcador.
    body = template.replace("{{DECK}}", deck_key).replace("{{N}}", str(n))
    return body.replace("{{TEXT}}", text.strip())
