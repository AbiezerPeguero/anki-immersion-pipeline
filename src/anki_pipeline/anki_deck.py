"""Etapa 3 del pipeline: oraciones + audios -> mazo Anki (.apkg) con IDs ESTABLES.

Como se evita duplicar al importar (la razon de este modulo):
  * ID del mazo  = derivado del NOMBRE del mazo  -> mismo nombre => mismo ID, siempre.
  * ID del modelo = derivado del nombre + version -> Anki reconoce el mismo tipo de tarjeta.
  * GUID de cada nota = derivado del MAZO + el texto en ingles (normalizado, sin mayusculas):
        - importar de nuevo la misma oracion ACTUALIZA la nota existente, no la duplica;
        - corregir la traduccion o cambiar la voz tambien actualiza, no duplica;
        - la misma oracion en dos mazos distintos SI son dos notas (cada mazo es independiente).
  * Cada .apkg trae solo el lote nuevo: al importarlo, Anki suma esas notas al mazo
    existente y no toca ni borra las demas.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from anki_pipeline import config
from anki_pipeline.sentences import SentencePair, normalize
from anki_pipeline.tts import audio_filename


def stable_id(label: str) -> int:
    """Entero reproducible en [2**30, 2**31): el rango que genanki recomienda para IDs de Anki."""
    n = int(hashlib.sha1(label.encode("utf-8")).hexdigest()[:8], 16)
    return (1 << 30) + (n % (1 << 30))


def deck_id(deck_name: str = config.DECK_NAME) -> int:
    return stable_id(f"deck::{deck_name}")


def model_id(model_name: str = config.MODEL_NAME, version: int = config.MODEL_VERSION) -> int:
    return stable_id(f"model::{model_name}::v{version}")


def note_guid_key(english: str) -> str:
    return normalize(english).casefold()


CSS = """
/* Sin colores fijos: Anki usa los de tu tema (claro u oscuro) y todo se lee bien. */
.card { font-family: Arial, sans-serif; font-size: 24px; text-align: center; }
.en { font-size: 28px; font-weight: 600; margin-bottom: 12px; }
.es { font-size: 24px; margin-top: 8px; }
"""


@dataclass
class DeckBuildResult:
    apkg_path: Path
    deck_name: str
    deck_id: int
    n_notes: int


def build_deck(
    pairs: Sequence[SentencePair],
    out_path: str | Path,
    *,
    audio_dir: str | Path | None = None,
    voice: str = config.KOKORO_VOICE,
    speed: float = config.KOKORO_SPEED,
    deck_name: str = config.DECK_NAME,
) -> DeckBuildResult:
    import genanki

    audio_dir = Path(audio_dir) if audio_dir else config.AUDIO_DIR
    out_path = Path(out_path)

    media: list[str] = []
    missing: list[str] = []
    for p in pairs:
        f = audio_dir / audio_filename(p.english, voice, speed)
        (media if f.is_file() else missing).append(str(f) if f.is_file() else p.english)
    if missing:
        raise FileNotFoundError(
            f"Faltan {len(missing)} audio(s). Corre primero la etapa 2 (02_tts.py) con la misma voz/velocidad.\n  "
            + "\n  ".join(m[:70] for m in missing[:10])
        )

    model = genanki.Model(
        model_id(config.MODEL_NAME, config.MODEL_VERSION),
        config.MODEL_NAME,
        fields=[{"name": "English"}, {"name": "Spanish"}, {"name": "Audio"}],
        templates=[{
            "name": "Escuchar y recordar",
            "qfmt": '<div class="en">{{English}}</div>{{Audio}}',
            "afmt": '{{FrontSide}}<hr id="answer"><div class="es">{{Spanish}}</div>',
        }],
        css=CSS,
    )

    class StableNote(genanki.Note):
        @property
        def guid(self):  # identidad = (mazo, oracion en ingles); la traduccion y la voz NO cuentan
            return genanki.guid_for(deck_name, note_guid_key(self.fields[0]))

    deck = genanki.Deck(deck_id(deck_name), deck_name)
    for p in pairs:
        sound = f"[sound:{audio_filename(p.english, voice, speed)}]"
        deck.add_note(StableNote(model=model, fields=[p.english, p.spanish, sound]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = media
    package.write_to_file(str(out_path))
    return DeckBuildResult(out_path, deck_name, deck_id(deck_name), len(pairs))
