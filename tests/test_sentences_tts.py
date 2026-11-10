import pytest

from anki_pipeline.sentences import parse_sentences_file
from anki_pipeline.tts import audio_filename


def test_parse_ok_and_duplicates(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text("# comentario\n\nHello   there. | Hola.\nhello there. | Hola otra vez.\nHow are you? | ¿Cómo estás?\n", encoding="utf-8")
    pairs, warns = parse_sentences_file(f)
    assert [p.english for p in pairs] == ["Hello there.", "How are you?"]
    assert pairs[1].spanish == "¿Cómo estás?"
    assert len(warns) == 1


def test_parse_reports_all_errors(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text("sin separador\nok | bien\nvacia |  \n", encoding="utf-8")
    with pytest.raises(ValueError) as e:
        parse_sentences_file(f)
    assert "linea 1" in str(e.value) and "linea 3" in str(e.value)


def test_audio_filename_is_stable_and_voice_specific():
    a = audio_filename("Hello  world", "af_heart,af_bella", 1.0)
    assert a == audio_filename("Hello world", "af_heart,af_bella", 1.0)  # espacios normalizados
    assert a != audio_filename("Hello world", "af_heart", 1.0)
    assert a != audio_filename("Hello world", "af_heart,af_bella", 0.9)
    assert a.endswith(".mp3") and len(a) == 16


def test_prepare_for_tts_adds_final_period_only_when_missing():
    from anki_pipeline.tts import prepare_for_tts

    assert prepare_for_tts("I get lots of newspapers  delivered") == "I get lots of newspapers delivered."
    assert prepare_for_tts("Where is the bank?") == "Where is the bank?"
    assert prepare_for_tts("Wow!") == "Wow!"
