from pathlib import Path

import pytest

from anki_pipeline.download import build_ytdlp_command, download_audio


def test_command_has_the_flags_we_depend_on():
    cmd = build_ytdlp_command("https://youtu.be/abc", Path("out"), "ffmpeg.exe", Path("log.txt"), python_exe="py")
    assert cmd[:3] == ["py", "-m", "yt_dlp"]
    for flag in ("--no-playlist", "-x", "--restrict-filenames", "--ffmpeg-location", "--print-to-file"):
        assert flag in cmd
    assert cmd[cmd.index("--audio-format") + 1] == "mp3"
    assert cmd[-1] == "https://youtu.be/abc"


def test_rejects_non_urls():
    with pytest.raises(ValueError, match="no parece un enlace"):
        download_audio("no es un enlace")


def test_rejects_url_pasted_inside_another_url():
    with pytest.raises(ValueError, match="otro enlace pegado"):
        download_audio("https://www.youtube.com/watch?v=https://youtu.be/sLaoFiVnJJc")
