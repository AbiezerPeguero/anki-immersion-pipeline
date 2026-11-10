import json
import sqlite3
import zipfile

from anki_pipeline import config
from anki_pipeline.anki_deck import build_deck, deck_id, model_id, stable_id
from anki_pipeline.sentences import SentencePair
from anki_pipeline.tts import audio_filename

V, S = "af_heart,af_bella", 1.0


def _fake_audio(tmp_path, pairs):
    for p in pairs:
        (tmp_path / audio_filename(p.english, V, S)).write_bytes(b"ID3fake")


def _read_apkg(path, tmp_path):
    with zipfile.ZipFile(path) as z:
        z.extract("collection.anki2", tmp_path / "x")
        media = json.loads(z.read("media"))
    con = sqlite3.connect(tmp_path / "x" / "collection.anki2")
    notes = con.execute("select guid, flds from notes order by id").fetchall()
    decks = json.loads(con.execute("select decks from col").fetchone()[0])
    con.close()
    return notes, decks, media


def test_ids_are_deterministic_and_in_range():
    assert deck_id("A") == deck_id("A") != deck_id("B")
    assert model_id(version=1) != model_id(version=2)
    assert all((1 << 30) <= stable_id(x) < (1 << 31) for x in ("a", "b", "Inglés Inmersión"))


def test_rebuild_keeps_guids_and_deck_identity(tmp_path):
    pairs = [SentencePair("Hello there.", "Hola.", 1), SentencePair("How are you?", "¿Cómo estás?", 2)]
    # lote posterior: traduccion corregida + mayusculas/espacios distintos => MISMA identidad
    pairs2 = [SentencePair("hello   there.", "Hola, ¿qué tal?", 1), SentencePair("How are you?", "¿Cómo estás?", 2)]
    _fake_audio(tmp_path, pairs + pairs2)  # la etapa 2 generaria tambien el audio de la variante
    a = build_deck(pairs, tmp_path / "a.apkg", audio_dir=tmp_path, voice=V, speed=S)
    b = build_deck(pairs2, tmp_path / "b.apkg", audio_dir=tmp_path, voice=V, speed=S)
    notes_a, decks_a, media_a = _read_apkg(a.apkg_path, tmp_path / "a")
    notes_b, decks_b, _ = _read_apkg(b.apkg_path, tmp_path / "b")
    assert [n[0] for n in notes_a] == [n[0] for n in notes_b]  # mismos GUID => Anki actualiza, no duplica
    assert notes_a[0][1] != notes_b[0][1]                      # pero el contenido si cambio
    assert str(deck_id()) in decks_a and decks_a[str(deck_id())]["name"] == config.DECK_NAME
    assert set(decks_a) == set(decks_b)
    assert len(media_a) == 2


def test_missing_audio_is_reported(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError, match="Faltan 1 audio"):
        build_deck([SentencePair("No audio yet.", "Aun sin audio.", 1)], tmp_path / "c.apkg", audio_dir=tmp_path, voice=V, speed=S)


def test_same_sentence_in_two_decks_are_two_notes(tmp_path):
    pairs = [SentencePair("Hello there.", "Hola.", 1)]
    _fake_audio(tmp_path, pairs)
    a = build_deck(pairs, tmp_path / "a.apkg", audio_dir=tmp_path, voice=V, speed=S, deck_name="Inglés Inmersión")
    b = build_deck(pairs, tmp_path / "b.apkg", audio_dir=tmp_path, voice=V, speed=S, deck_name="Canal Ejemplo")
    na, da, _ = _read_apkg(a.apkg_path, tmp_path / "a")
    nb, db, _ = _read_apkg(b.apkg_path, tmp_path / "b")
    assert na[0][0] != nb[0][0]
    assert a.deck_id != b.deck_id and str(b.deck_id) in db and db[str(b.deck_id)]["name"] == "Canal Ejemplo"
