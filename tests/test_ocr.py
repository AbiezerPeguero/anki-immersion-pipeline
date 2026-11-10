import pytest

from anki_pipeline.ocr import collect_images, preprocess_image, write_ocr_text


def test_collect_images_from_dir_sorted_and_errors(tmp_path):
    for n in ("b.jpg", "a.png", "notas.txt"):
        (tmp_path / n).write_bytes(b"x")
    assert [p.name for p in collect_images([tmp_path])] == ["a.png", "b.jpg"]
    with pytest.raises(ValueError, match="Formato no soportado"):
        collect_images([tmp_path / "notas.txt"])
    with pytest.raises(FileNotFoundError):
        collect_images([tmp_path / "no_existe.jpg"])
    empty = tmp_path / "vacia"
    empty.mkdir()
    with pytest.raises(ValueError, match="ninguna imagen"):
        collect_images([empty])


def test_write_ocr_text_joins_pages(tmp_path):
    out = write_ocr_text(["page one", "page two"], "unidad", tmp_path)
    assert out.read_text(encoding="utf-8") == "page one\n\npage two\n"


def test_preprocess_modes():
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    img = np.full((400, 600, 3), 255, dtype=np.uint8)
    cv2.putText(img, "Hello world", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)
    gray = preprocess_image(img, "gray")
    assert gray.ndim == 2 and max(gray.shape) >= 1600  # se amplio
    assert preprocess_image(img, "none") is img
    with pytest.raises(ValueError, match="Modo desconocido"):
        preprocess_image(img, "magia")


def test_dehyphenate_joins_line_breaks_only():
    from anki_pipeline.ocr import dehyphenate

    assert dehyphenate("Es- tado y Ha- cienda") == "Estado y Hacienda"
    assert dehyphenate("conver- sation") == "conversation"
    assert dehyphenate("Artículo 18.- Se crea") == "Artículo 18.- Se crea"  # no es corte de linea
    assert dehyphenate("well- Known") == "well- Known"


def test_text_similarity():
    from anki_pipeline.ocr import text_similarity

    ref = "That's a situation where a mandamus petition might force action."
    assert text_similarity(ref, ref) == (1.0, 1.0)
    assert text_similarity(ref, "That's   a situation\nwhere a mandamus petition might force action.") == (1.0, 1.0)
    w, c = text_similarity(ref, "That $ a situation where a mandamus petition might forcc action.")
    assert 0.5 < w < 1.0 and 0.9 < c < 1.0


def test_low_resolution_warning(tmp_path):
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    from anki_pipeline.ocr import low_resolution_warning

    small, big = tmp_path / "small.jpg", tmp_path / "big.jpg"
    cv2.imwrite(str(small), np.full((673, 1107, 3), 255, dtype=np.uint8))
    cv2.imwrite(str(big), np.full((2400, 3200, 3), 255, dtype=np.uint8))
    assert "baja resolucion" in low_resolution_warning(small)
    assert low_resolution_warning(big) is None
