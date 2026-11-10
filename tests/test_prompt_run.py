import subprocess
import sys
from pathlib import Path

import pytest

from anki_pipeline.prompt import TEMPLATE_PATH, build_prompt

RUN = Path(__file__).resolve().parents[1] / "scripts" / "run.py"


def test_build_prompt_fills_every_placeholder():
    p = build_prompt("blogs", 12, "Hello {{DECK}} world.\nSecond line.")
    assert "Mazo: blogs" in p and "@deck: blogs" in p and "12 oraciones" in p
    assert p.rstrip().endswith("Hello {{DECK}} world.\nSecond line.")  # el texto del usuario no se toca
    assert "{{N}}" not in p


def test_template_file_has_all_placeholders():
    t = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert all(m in t for m in ("{{DECK}}", "{{N}}", "{{TEXT}}"))


def test_build_prompt_validations():
    with pytest.raises(ValueError, match="al menos 1"):
        build_prompt("aula", 0, "x")
    with pytest.raises(ValueError, match="marcadores"):
        build_prompt("aula", 3, "x", template="sin marcadores")


def test_run_rejects_unknown_deck_and_missing_file(tmp_path):
    r = subprocess.run([sys.executable, str(RUN), "transcribir", "x.mp3", "--deck", "auls"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1 and "desconocido" in r.stdout
    r = subprocess.run([sys.executable, str(RUN), "armar", str(tmp_path / "nada.txt")], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 1 and "No existe" in r.stdout
