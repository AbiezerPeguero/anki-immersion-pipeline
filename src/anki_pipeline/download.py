"""Etapa 0 del pipeline: enlace de YouTube (u otro sitio) -> audio .mp3 local, con yt-dlp.

yt-dlp corre como PROCESO APARTE (python -m yt_dlp): sus errores no tumban el pipeline, se ve su
progreso en pantalla, y puede ser orquestado desde otro programa. ffmpeg y Deno (el runtime JS que
YouTube exige hoy) vienen empaquetados en el entorno, no hay que instalar nada en Windows.

Uso permitido: material que tu puedes ver legalmente, para tu estudio personal. Descargar de YouTube
va contra sus condiciones de servicio; para otros usos (por ejemplo comerciales) revisa esto aparte.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from anki_pipeline import config

OUTPUT_TEMPLATE = "%(title).80s_%(id)s.%(ext)s"


def build_ytdlp_command(
    url: str,
    out_dir: Path,
    ffmpeg_exe: str,
    filepath_log: Path,
    python_exe: str = sys.executable,
) -> list[str]:
    return [
        python_exe, "-m", "yt_dlp",
        "--no-playlist",                       # un enlace con lista de reproduccion baja SOLO ese video
        "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "--ffmpeg-location", ffmpeg_exe,
        "--restrict-filenames",                # nombres sin espacios ni caracteres raros (seguros en Windows)
        "-o", str(out_dir / OUTPUT_TEMPLATE),
        "--print-to-file", "after_move:filepath", str(filepath_log),  # donde quedo el .mp3 final
        url,
    ]


def download_audio(url: str, out_dir: str | Path | None = None) -> Path:
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError(f"Eso no parece un enlace: {url!r} (debe empezar con http:// o https://)")
    if url.lower().count("http") > 1:
        raise ValueError(
            f"El enlace parece tener otro enlace pegado dentro: {url!r}. "
            "Usa UN solo enlace completo, por ejemplo: https://youtu.be/XXXXXXXXXXX"
        )
    out_dir = Path(out_dir) if out_dir else config.INPUT_DIR / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    config.TMP_DIR.mkdir(parents=True, exist_ok=True)

    import imageio_ffmpeg

    log = config.TMP_DIR / "last_download_path.txt"
    log.unlink(missing_ok=True)
    cmd = build_ytdlp_command(url, out_dir, imageio_ffmpeg.get_ffmpeg_exe(), log)

    # El Deno empaquetado vive junto al python del entorno: asegurar que yt-dlp lo encuentre aunque
    # el entorno no este "activado".
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")

    proc = subprocess.run(cmd, env=env)
    if proc.returncode != 0 or not log.exists():
        raise RuntimeError(
            f"yt-dlp termino con error (codigo {proc.returncode}). Lee el mensaje de arriba. "
            "Causas comunes: enlace privado/borrado, restriccion de pais o edad, o yt-dlp desactualizado "
            "(YouTube cambia seguido: prueba 'uv lock --upgrade-package yt-dlp' y luego 'uv sync')."
        )
    path = Path(log.read_text(encoding="utf-8").strip().splitlines()[-1])
    if not path.is_file():
        raise RuntimeError(f"yt-dlp dijo que guardo {path}, pero el archivo no existe.")
    return path
