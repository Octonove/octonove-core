"""Localizacion de FFmpeg y probes comunes (duracion, filtro whisper) de la
suite Octonove. Solo stdlib. Las capacidades especificas de cada app (encoders,
dshow, filter_complex de escena) viven en la app, no aqui."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .procutil import _decode, subprocess_kwargs

logger = logging.getLogger(__name__)


def app_dir(package_file: str | None = None) -> Path:
    """Carpeta base de la app. Congelada (PyInstaller): junto al .exe. En
    desarrollo: la raiz del proyecto del paquete LLAMADOR — los shims deben
    pasar su propio __file__, si no la base seria la carpeta de octonove_core."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    base = Path(package_file) if package_file else Path(__file__)
    return base.resolve().parent.parent


def _candidate_paths(app: Path) -> list[Path]:
    cands: list[Path] = []
    for sub in ("", "ffmpeg", "_internal", "bin"):
        cands.append((app / sub / "ffmpeg.exe") if sub else (app / "ffmpeg.exe"))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cands.append(Path(meipass) / "ffmpeg.exe")
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget.is_dir():
            cands.extend(winget.glob("Gyan.FFmpeg*/**/bin/ffmpeg.exe"))
    return cands


def find_ffmpeg(override: str = "", *, package_file: str | None = None) -> str | None:
    if override and Path(override).is_file():
        return override
    for c in _candidate_paths(app_dir(package_file)):
        try:
            if c.is_file():
                return str(c)
        except OSError:
            continue
    return shutil.which("ffmpeg")


def ffprobe_from(ffmpeg_path: str) -> str | None:
    p = Path(ffmpeg_path).with_name("ffprobe.exe")
    return str(p) if p.is_file() else shutil.which("ffprobe")


def has_whisper(ffmpeg_path: str) -> bool:
    """True si el build de FFmpeg trae el filtro whisper (build full de Gyan)."""
    try:
        out = _decode(subprocess.run([ffmpeg_path, "-hide_banner", "-filters"],
                                     capture_output=True, timeout=20,
                                     **subprocess_kwargs()).stdout)
        return bool(re.search(r"\bwhisper\b", out))
    except (OSError, subprocess.SubprocessError):
        return False


def get_duration(ffmpeg_path: str, path: str) -> float:
    if not os.path.isfile(path):
        logger.warning("get_duration: el fichero no existe: %s", path)
        return 0.0
    probe = ffprobe_from(ffmpeg_path)
    if probe:
        try:
            out = _decode(subprocess.run(
                [probe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", path],
                capture_output=True, timeout=20, **subprocess_kwargs()).stdout).strip()
            return float(out)
        except (ValueError, OSError, subprocess.SubprocessError):
            pass
    # Fallback sin ffprobe (app empaquetada): parsear "Duration:" de FFmpeg.
    try:
        r = subprocess.run([ffmpeg_path, "-hide_banner", "-i", path],
                           capture_output=True, timeout=30, **subprocess_kwargs())
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", _decode(r.stderr))
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except (OSError, subprocess.SubprocessError):
        pass
    logger.debug("get_duration: no se pudo determinar la duracion de %s (la barra de "
                 "progreso no avanzara, pero la transcripcion funciona)", path)
    return 0.0
