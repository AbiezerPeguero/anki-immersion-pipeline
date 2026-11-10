"""Diagnostico del entorno: ¿Python ve la GPU y funcionan las librerias clave?

Uso (desde la carpeta del proyecto):
    uv run python scripts/check_env.py          # rapido, no descarga modelos
    uv run python scripts/check_env.py --full   # descarga modelos pequenos y prueba Whisper + Kokoro en GPU
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

failures: list[str] = []


def ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    failures.append(msg)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def check_python() -> None:
    section("Python")
    v = sys.version_info
    if (v.major, v.minor) == (3, 12):
        ok(f"Python {v.major}.{v.minor}.{v.micro} (version objetivo del proyecto)")
    else:
        warn(f"Python {v.major}.{v.minor}.{v.micro}: el proyecto esta pensado para 3.12 (Kokoro exige <3.13)")
    ok(f"Interprete: {sys.executable}")


def check_torch() -> bool:
    section("PyTorch + GPU")
    try:
        import torch
    except Exception as e:  # noqa: BLE001
        fail(f"No se pudo importar torch: {e!r}")
        return False

    ok(f"torch {torch.__version__} (CUDA de la build: {torch.version.cuda})")
    if "+cu" not in torch.__version__:
        fail("Este torch NO es una build CUDA (falta el sufijo '+cu126'): se instalo la version CPU. "
             "Revisa [tool.uv.sources] en pyproject.toml y vuelve a correr 'uv sync'.")
    if not torch.cuda.is_available():
        fail("torch.cuda.is_available() = False. Revisa el driver NVIDIA (nvidia-smi) y que torch sea '+cu126'.")
        return False

    props = torch.cuda.get_device_properties(0)
    ok(f"GPU: {props.name} | VRAM total: {props.total_memory / 1024**3:.1f} GB | sm_{props.major}{props.minor}")
    free, total = torch.cuda.mem_get_info()
    ok(f"VRAM libre ahora: {free / 1024**3:.1f} GB de {total / 1024**3:.1f} GB")

    x = torch.randn(2048, 2048, device="cuda", dtype=torch.float16)
    t0 = time.perf_counter()
    (x @ x).float().sum().item()
    torch.cuda.synchronize()
    ok(f"Operacion real en la GPU OK (matmul fp16 2048x2048 en {time.perf_counter() - t0:.3f}s)")
    ok(f"cuDNN (el de torch): {torch.backends.cudnn.version()}")
    return True


def check_ctranslate2() -> None:
    section("CTranslate2 (motor de faster-whisper)")
    try:
        from anki_pipeline.cuda_setup import ensure_cuda_dlls

        ensure_cuda_dlls()
        import ctranslate2
    except Exception as e:  # noqa: BLE001
        fail(f"No se pudo importar ctranslate2: {e!r}")
        return
    n = ctranslate2.get_cuda_device_count()
    if n < 1:
        fail("ctranslate2 no ve ninguna GPU CUDA.")
        return
    types = sorted(ctranslate2.get_supported_compute_types("cuda"))
    ok(f"ctranslate2 {ctranslate2.__version__}: {n} GPU(s) visibles | compute types: {', '.join(types)}")
    if "float16" not in types:
        warn("float16 no esta soportado en esta GPU.")


def check_libs() -> None:
    section("Librerias del pipeline")
    for mod in ("faster_whisper", "kokoro", "soundfile", "genanki", "easyocr", "yt_dlp", "spacy", "espeakng_loader"):
        try:
            __import__(mod)
            ok(f"import {mod}")
        except Exception as e:  # noqa: BLE001
            fail(f"import {mod} fallo: {e!r}")
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        out = subprocess.run([exe, "-version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
        ok(f"ffmpeg empaquetado: {out}")
    except Exception as e:  # noqa: BLE001
        fail(f"ffmpeg (imageio-ffmpeg) fallo: {e!r}")


def full_whisper() -> None:
    section("PRUEBA REAL: faster-whisper en GPU (modelo 'tiny', ~75 MB)")
    try:
        import numpy as np
        from anki_pipeline.cuda_setup import ensure_cuda_dlls

        ensure_cuda_dlls()
        from faster_whisper import WhisperModel

        model = WhisperModel("tiny", device="cuda", compute_type="float16")
        # 5 s de silencio: obliga a correr el encoder en GPU (aqui es donde falla si faltan cuBLAS/cuDNN)
        segments, info = model.transcribe(np.zeros(16000 * 5, dtype=np.float32), language="en", beam_size=1)
        list(segments)
        ok("Whisper corrio en la GPU sin errores (cuBLAS/cuDNN OK)")
    except Exception as e:  # noqa: BLE001
        fail(f"faster-whisper en GPU fallo: {e!r}  -> ver 'Problemas conocidos' en el README")


def full_kokoro() -> None:
    section("PRUEBA REAL: Kokoro TTS (voz af_heart, ~330 MB la primera vez)")
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline

        from anki_pipeline.config import KOKORO_LANG, KOKORO_VOICE, TMP_DIR, ensure_dirs

        ensure_dirs()
        pipe = KPipeline(lang_code=KOKORO_LANG, repo_id="hexgrad/Kokoro-82M")
        ok(f"Kokoro cargado en: {getattr(getattr(pipe, 'model', None), 'device', 'desconocido')}")
        text = "Hello! This is a quick test of the Kokoro voice for my English flashcards."
        t0 = time.perf_counter()
        chunks = []
        for _, _, audio in pipe(text, voice=KOKORO_VOICE):
            chunks.append(audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio))
        wav = np.concatenate(chunks)
        out = TMP_DIR / "check_kokoro.wav"
        sf.write(out, wav, 24000)
        ok(f"Audio de {len(wav) / 24000:.1f}s generado en {time.perf_counter() - t0:.2f}s -> {out}")
        print("       Escuchalo para validar la voz.")
    except Exception as e:  # noqa: BLE001
        fail(f"Kokoro fallo: {e!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="incluye pruebas reales de Whisper y Kokoro (descarga modelos)")
    args = ap.parse_args()

    check_python()
    gpu_ok = check_torch()
    if gpu_ok:
        check_ctranslate2()
    check_libs()
    if args.full and gpu_ok:
        full_whisper()
        full_kokoro()

    section("RESUMEN")
    if failures:
        print(f"{len(failures)} problema(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("Todo en orden." + ("" if args.full else "  Siguiente: uv run python scripts/check_env.py --full"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
