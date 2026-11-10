"""Mide en TU GPU cuanta VRAM y tiempo usa cada combinacion de modelo / precision / batch.

Uso:
    uv run python scripts/probe_whisper_vram.py data/input/mi_audio.mp3
    uv run python scripts/probe_whisper_vram.py data/input/mi_audio.mp3 --models large-v3 --compute float16 int8_float16 --batch 1 8

Usa un audio de 5-10 minutos en ingles. La primera vez descarga los modelos (large-v3 ~3 GB, turbo ~1.6 GB).
"""
from __future__ import annotations

import argparse
import gc
import sys
import threading
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from anki_pipeline.cuda_setup import ensure_cuda_dlls  # noqa: E402

ensure_cuda_dlls()

import torch  # noqa: E402
from faster_whisper import BatchedInferencePipeline, WhisperModel  # noqa: E402

GB = 1024**3


class VramSampler(threading.Thread):
    """Muestrea cada 0.1 s la VRAM usada en TODA la GPU y guarda el pico."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.peak_used = 0
        self._halt = threading.Event()

    def run(self) -> None:
        while not self._halt.is_set():
            free, total = torch.cuda.mem_get_info()
            self.peak_used = max(self.peak_used, total - free)
            time.sleep(0.1)

    def stop(self) -> None:
        self._halt.set()
        self.join()


def run_case(audio: Path, model_name: str, compute_type: str, batch_size: int) -> dict:
    gc.collect()
    torch.cuda.empty_cache()
    free, total = torch.cuda.mem_get_info()
    baseline = total - free  # lo que ya usan Windows / navegador / etc.

    sampler = VramSampler()
    sampler.start()
    try:
        t0 = time.perf_counter()
        model = WhisperModel(model_name, device="cuda", compute_type=compute_type)
        t_load = time.perf_counter() - t0
        after_load = total - torch.cuda.mem_get_info()[0]

        t0 = time.perf_counter()
        if batch_size > 1:
            segments, info = BatchedInferencePipeline(model).transcribe(
                str(audio), language="en", beam_size=5, batch_size=batch_size
            )
        else:
            segments, info = model.transcribe(str(audio), language="en", beam_size=5, vad_filter=True)
        words = sum(len(s.text.split()) for s in segments)
        t_run = time.perf_counter() - t0
    finally:
        sampler.stop()

    del model
    gc.collect()
    return {
        "model": model_name,
        "compute": compute_type,
        "batch": batch_size,
        "vram_load_gb": (after_load - baseline) / GB,
        "vram_peak_gb": (sampler.peak_used - baseline) / GB,
        "audio_s": info.duration,
        "run_s": t_run,
        "x_realtime": info.duration / t_run,
        "load_s": t_load,
        "words": words,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", type=Path)
    ap.add_argument("--models", nargs="+", default=["large-v3", "large-v3-turbo"])
    ap.add_argument("--compute", nargs="+", default=["float16"])
    ap.add_argument("--batch", nargs="+", type=int, default=[1, 8])
    args = ap.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("No hay GPU visible para torch. Corre primero scripts/check_env.py")

    total = torch.cuda.get_device_properties(0).total_memory / GB
    free = torch.cuda.mem_get_info()[0] / GB
    print(f"GPU: {torch.cuda.get_device_name(0)} | VRAM total {total:.1f} GB | libre antes de empezar {free:.1f} GB\n")

    rows = []
    for model_name in args.models:
        for compute in args.compute:
            for batch in args.batch:
                label = f"{model_name} / {compute} / batch={batch}"
                print(f"-> {label} ...", flush=True)
                try:
                    r = run_case(args.audio, model_name, compute, batch)
                    rows.append(r)
                    print(f"   VRAM pico {r['vram_peak_gb']:.2f} GB | {r['x_realtime']:.1f}x tiempo real "
                          f"({r['run_s']:.0f}s para {r['audio_s'] / 60:.1f} min) | {r['words']} palabras")
                except Exception as e:  # noqa: BLE001
                    print(f"   FALLO: {e!r}")

    print("\n=== RESUMEN ===")
    print(f"{'modelo':<18}{'precision':<14}{'batch':<7}{'VRAM carga':<12}{'VRAM pico':<11}{'x real-time':<12}{'1 h de audio ≈'}")
    for r in rows:
        mins_per_hour = 60 / r["x_realtime"]
        print(f"{r['model']:<18}{r['compute']:<14}{r['batch']:<7}{r['vram_load_gb']:<12.2f}{r['vram_peak_gb']:<11.2f}"
              f"{r['x_realtime']:<12.1f}{mins_per_hour:.1f} min")


if __name__ == "__main__":
    main()
