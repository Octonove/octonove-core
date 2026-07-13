"""Captura de audio por DirectShow (via FFmpeg) como RESPALDO de soundcard/WASAPI.

Algunos microfonos (tipicos 'USB PnP Audio Device' baratos) reportan un formato
de mezcla que NO es WAVEFORMATEXTENSIBLE; soundcard hace un assert sobre ese
formato y aborta, asi que no se pueden abrir por su via. FFmpeg -f dshow si los
abre. Este modulo emite PCM crudo (s16le) por una tuberia, para que el que lo
consuma calcule el nivel (VU) y/o escriba el WAV exactamente igual que con la
via nativa.
"""

from __future__ import annotations

import difflib
import logging
import re
import subprocess

from .procutil import subprocess_kwargs

logger = logging.getLogger(__name__)


def list_audio_devices(ffmpeg: str) -> list[str]:
    """Nombres de dispositivos de ENTRADA de audio segun DirectShow."""
    if not ffmpeg:
        return []
    try:
        p = subprocess.run(
            [ffmpeg, "-hide_banner", "-list_devices", "true", "-f", "dshow",
             "-i", "dummy"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10, **subprocess_kwargs())
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("dshow list_devices fallo: %s", exc)
        return []
    devs = []
    for ln in (p.stderr or "").splitlines():
        m = re.search(r'"([^"]+)"\s*\(audio', ln)
        if m:
            devs.append(m.group(1))
    return devs


def match_device(wanted: str, devs: list[str]) -> str | None:
    """El nombre dshow puede diferir del de WASAPI: exacto -> subcadena -> el
    mas parecido (difflib)."""
    if not devs:
        return None
    if wanted in devs:
        return wanted
    for d in devs:
        if wanted and (wanted in d or d in wanted):
            return d
    close = difflib.get_close_matches(wanted or "", devs, n=1, cutoff=0.5)
    return close[0] if close else None


def open_pcm(ffmpeg: str, device: str, samplerate: int, channels: int):
    """Popen que emite PCM s16le por stdout. Detener con stop_pcm()."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "dshow",
           "-i", f"audio={device}", "-ar", str(samplerate), "-ac", str(channels),
           "-f", "s16le", "pipe:1"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, **subprocess_kwargs())


def stop_pcm(proc) -> None:
    """Cierra el proceso de captura con suavidad (q -> terminate -> kill)."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if proc.stdin:
            proc.stdin.write(b"q")
            proc.stdin.flush()
            proc.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except (subprocess.TimeoutExpired, OSError):
            try:
                proc.kill()
            except OSError:
                pass
