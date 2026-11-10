"""Nucleo compartido: transcripcion, TTS, OCR y generacion de mazos Anki.

Los scripts de scripts/ (CLI) son una capa fina encima de este paquete: la logica vive aqui,
para poder reutilizarla desde otros programas o exponerla como servicio.
"""
import os

# Aviso inofensivo de Hugging Face en Windows (cache sin symlinks); lo silenciamos.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
