"""Hace visibles a CTranslate2 (faster-whisper) las DLL de CUDA 12 en Windows.

Problema tipico: "Library cublas64_12.dll is not found or cannot be loaded".
Solucion: torch (build cu126) ya trae cuBLAS 12 y cuDNN 9 dentro de torch/lib; solo hay
que ponerlas en el camino de busqueda de DLL ANTES de cargar ctranslate2.
Llamar ensure_cuda_dlls() antes de importar faster_whisper.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_done = False


def ensure_cuda_dlls() -> None:
    global _done
    if _done or sys.platform != "win32":
        return
    spec = importlib.util.find_spec("torch")
    if spec is not None and spec.origin:
        lib = Path(spec.origin).parent / "lib"
        if lib.is_dir():
            os.add_dll_directory(str(lib))
            os.environ["PATH"] = str(lib) + os.pathsep + os.environ.get("PATH", "")
    import torch  # noqa: F401  (cargarlo primero deja cuBLAS/cuDNN ya residentes en el proceso)

    _done = True
