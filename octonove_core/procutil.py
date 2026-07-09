"""Utilidades de subprocess compartidas (Windows): lanzar procesos hijos sin que
aparezca una ventana de consola. Solo stdlib."""

from __future__ import annotations

import os
import subprocess

# Guard de plataforma: creationflags != 0 en no-Windows lanza ValueError en Popen.
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def subprocess_kwargs() -> dict:
    """kwargs para subprocess.run/Popen que ocultan la consola en Windows.
    OJO: NO usar en llamadas que necesiten mostrar avisos interactivos del
    sistema (p.ej. la exportacion de certificados con contrasena de PDFLocal)."""
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = CREATE_NO_WINDOW
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kw["startupinfo"] = si
    return kw


def _decode(raw) -> str:
    """bytes -> str tolerante: utf-8, luego mbcs (ANSI de Windows), luego replace."""
    if not raw:
        return ""
    if isinstance(raw, str):
        return raw
    for enc in ("utf-8", "mbcs"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")
