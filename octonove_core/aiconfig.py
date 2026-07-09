"""Configuracion de IA COMPARTIDA por toda la suite Octonove.

Se guarda UNA sola vez en APPDATA/Octonove/ai.json y vale para las 5 apps: el
usuario elige proveedor (Ollama local gratis, o una API potente de OpenAI /
Gemini / Anthropic) y su API key. La key se cifra con DPAPI (ligada al usuario
de Windows); nunca se guarda en claro ni se registra en logs.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Proveedores soportados. "ollama" = local y gratis (por defecto).
PROVIDERS = ("ollama", "openai", "gemini", "anthropic")

PROVIDER_LABELS = {
    "ollama": "Gratis · en tu PC (Ollama)",
    "openai": "OpenAI (ChatGPT)",
    "gemini": "Google Gemini",
    "anthropic": "Anthropic (Claude)",
}

# Modelo economico recomendado y lista sugerida por proveedor (editable por el
# usuario). Los IDs pueden cambiar; se ofrecen como punto de partida.
CLOUD_MODELS = {
    "openai": {
        "default": "gpt-4o-mini",
        "options": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o4-mini"],
    },
    "gemini": {
        "default": "gemini-2.5-flash",
        "options": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    },
    "anthropic": {
        "default": "claude-haiku-4-5",
        "options": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"],
    },
}

_APP = "Octonove"   # carpeta compartida (no la de cada app): la config es de la suite


def _dir() -> Path:
    for base in (os.environ.get("APPDATA"), str(Path.home())):
        if not base:
            continue
        d = Path(base) / _APP
        try:
            d.mkdir(parents=True, exist_ok=True)
            return d
        except OSError:
            continue
    d = Path(tempfile.gettempdir()) / _APP
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def _path() -> Path:
    return _dir() / "ai.json"


def load() -> dict:
    """Devuelve {provider, model, api_key} con la key YA descifrada en memoria.
    Si no hay configuracion, provider='ollama' y api_key=''."""
    cfg = {"provider": "ollama", "model": "", "api_key": ""}
    p = _path()
    if not p.exists():
        return cfg
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        logger.warning("ai.json corrupto: %s", exc)
        return cfg
    prov = str(data.get("provider", "ollama"))
    cfg["provider"] = prov if prov in PROVIDERS else "ollama"
    cfg["model"] = str(data.get("model", ""))
    enc = data.get("api_key_enc") or ""
    if enc:
        try:
            from .dpapi import dpapi_decrypt
            cfg["api_key"] = dpapi_decrypt(enc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo descifrar la API key de IA: %s", exc)
    return cfg


def save(provider: str, model: str = "", api_key: str = "") -> None:
    """Guarda la configuracion. La API key se cifra con DPAPI (nunca en claro)."""
    data = {"provider": provider if provider in PROVIDERS else "ollama",
            "model": model or "", "api_key_enc": ""}
    if api_key:
        try:
            from .dpapi import dpapi_encrypt
            data["api_key_enc"] = dpapi_encrypt(api_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo cifrar la API key de IA: %s", exc)
    try:
        _path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        logger.error("No se pudo guardar ai.json: %s", exc)
