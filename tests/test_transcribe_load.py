from huggingface_hub.errors import LocalEntryNotFoundError

from anki_pipeline.transcribe import load_whisper_model


class FakeModel:
    """Sustituto de WhisperModel: registra cada llamada y falla si se le indica."""

    calls: list[dict] = []
    fail_offline = False

    def __init__(self, name, **kwargs):
        FakeModel.calls.append({"name": name, **kwargs})
        if kwargs.get("local_files_only") and FakeModel.fail_offline:
            raise LocalEntryNotFoundError("modelo no esta en cache")


def setup_function():
    FakeModel.calls = []
    FakeModel.fail_offline = False


def test_usa_solo_disco_si_el_modelo_esta_en_cache():
    load_whisper_model(FakeModel, "large-v3", "float16")
    assert len(FakeModel.calls) == 1
    assert FakeModel.calls[0]["local_files_only"] is True


def test_reintenta_con_red_si_falta_el_modelo():
    FakeModel.fail_offline = True
    load_whisper_model(FakeModel, "large-v3", "float16")
    assert len(FakeModel.calls) == 2
    assert FakeModel.calls[0]["local_files_only"] is True
    assert "local_files_only" not in FakeModel.calls[1]
