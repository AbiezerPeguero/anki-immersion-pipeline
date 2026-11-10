import pytest

from anki_pipeline import config
from anki_pipeline.decks import deck_audio_dir, read_deck_directive, resolve_deck
from anki_pipeline.sentences import parse_sentences_file


def test_directive_and_parse(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text("# x\n@deck: Aula\nHello. | Hola.\n", encoding="utf-8")
    assert read_deck_directive(f) == "aula"
    pairs, _ = parse_sentences_file(f)  # la directiva NO cuenta como oracion ni como error
    assert len(pairs) == 1


def test_resolve_deck_ok_and_errors():
    assert resolve_deck("AULA") == ("aula", config.DECKS["aula"])
    with pytest.raises(ValueError, match="Mazos validos"):
        resolve_deck(None)
    with pytest.raises(ValueError, match="desconocido"):
        resolve_deck("auls")  # error de tipeo: no debe crear un mazo nuevo en silencio


def test_audio_dir_per_deck():
    assert deck_audio_dir("aula").name == "aula"


def test_registry_is_valid():
    """Red de seguridad para cuando agregues mazos a mano en config.DECKS."""
    import re

    assert "aula" in config.DECKS
    for key, name in config.DECKS.items():
        assert re.fullmatch(r"[a-z0-9][a-z0-9_-]*", key), f"alias invalido: {key!r} (minusculas, sin espacios)"
        assert name.strip() == name and name, f"nombre de mazo invalido para {key!r}"
    names = list(config.DECKS.values())
    assert len(names) == len(set(names)), "hay dos alias apuntando al mismo nombre de mazo"
