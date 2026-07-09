"""Capa de IA local OPCIONAL via Ollama, compartida por la suite Octonove.

Filosofia: NUNCA es una dependencia dura. Si el usuario tiene Ollama corriendo,
las apps desbloquean funciones de calidad; si no, todo cae a heuristicas locales.
Solo usa urllib (stdlib): nada que empaquetar y la privacidad intacta (el modelo
corre en el propio PC del usuario).

Cada app tiene un <paquete>/llm.py que re-exporta de aqui (shim) y define su
wrapper de generate() con SUS defaults de timeout/temperature (comportamiento,
no estilo: p.ej. AutoEscritorio necesita temperatura 0.1 para JSON determinista).
El estado (_cache) es UNICO y vive aqui: los shims lo importan, no lo redefinen.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def _resolve_ollama_url() -> str:
    """URL base de Ollama. Usa 127.0.0.1 (no 'localhost') a proposito: en Windows
    'localhost' resuelve primero a IPv6 ::1, donde Ollama no escucha, y el reintento
    a IPv4 anade ~2 s que agotan el timeout de deteccion. Respeta OLLAMA_HOST
    (formato 'host', 'host:port', 'http://host' o 'http://host:port')."""
    import re as _re
    import urllib.parse as _up
    host = (os.environ.get("OLLAMA_HOST") or "").strip()
    if not host:
        return "http://127.0.0.1:11434"
    if not _re.match(r"^https?://", host):
        host = "http://" + host
    try:
        parts = _up.urlsplit(host)
        scheme = parts.scheme or "http"
        hostname = parts.hostname or "127.0.0.1"
        port = parts.port or 11434           # puerto por defecto si falta (clave!)
    except ValueError:
        return "http://127.0.0.1:11434"
    if hostname == "localhost":
        hostname = "127.0.0.1"
    netloc = f"[{hostname}]:{port}" if ":" in hostname else f"{hostname}:{port}"  # IPv6 con corchetes
    return f"{scheme}://{netloc}"


OLLAMA_URL = _resolve_ollama_url()
_cache: dict = {}


def _get(path: str, timeout: float):
    with urllib.request.urlopen(OLLAMA_URL + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def list_models(timeout: float = 3.0) -> list[str]:
    try:
        data = _get("/api/tags", timeout)
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except (urllib.error.URLError, OSError, ValueError, TimeoutError, AttributeError, TypeError):
        return []


def available(timeout: float = 3.0) -> bool:
    """True si Ollama responde y tiene al menos un modelo instalado."""
    return bool(list_models(timeout))


def default_model() -> str | None:
    if "model" not in _cache:
        # el filtro 'embed' evita elegir un modelo de embeddings como modelo de chat
        models = [m for m in list_models() if "embed" not in m.lower()]
        pref = next((m for m in models if any(k in m.lower()
                     for k in ("llama3.2", "qwen2.5", "phi", "mistral", "gemma", "llama3.1"))), None)
        _cache["model"] = pref or (models[0] if models else None)
    return _cache["model"]


def default_embed_model() -> str | None:
    if "embed" not in _cache:
        models = list_models()
        pref = next((m for m in models if "embed" in m.lower()), None)
        _cache["embed"] = pref
    return _cache["embed"]


def generate(prompt: str, *, system: str | None = None, model: str | None = None,
             timeout: float = 120.0, temperature: float = 0.3) -> str | None:
    """Devuelve la respuesta del modelo, o None si Ollama no esta o falla."""
    model = model or default_model()
    if not model:
        return None
    body = {"model": model, "prompt": prompt, "stream": False,
            "options": {"temperature": temperature}}
    if system:
        body["system"] = system
    data = json.dumps(body).encode("utf-8")
    # 2 intentos: Ollama puede dar timeouts transitorios al cargar un modelo grande.
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                OLLAMA_URL + "/api/generate", data=data,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace")).get("response", "").strip()
        except (urllib.error.URLError, OSError, ValueError, TimeoutError, AttributeError,
                TypeError) as exc:
            logger.warning("Ollama generate fallo (intento %d/2): %s", attempt + 1, exc)
    return None


def embed(texts: list[str], model: str | None = None,
          timeout: float = 120.0) -> list[list[float]] | None:
    """Devuelve un vector por texto, o None si no hay embeddings disponibles."""
    model = model or default_embed_model()
    if not model:
        return None
    out: list[list[float] | None] = []
    for t in texts:
        body = {"model": model, "prompt": t}
        try:
            req = urllib.request.Request(
                OLLAMA_URL + "/api/embeddings", data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                vec = json.loads(r.read().decode("utf-8", "replace")).get("embedding")
            # Un fallo puntual no descarta todo el lote: marca esa entrada como None
            # y deja que el llamador decida (degradar a busqueda por palabras).
            out.append([float(x) for x in vec] if vec else None)
        except (urllib.error.URLError, OSError, ValueError, TimeoutError, AttributeError,
                TypeError) as exc:
            logger.warning("Ollama embeddings fallo: %s", exc)
            out.append(None)
    return out


def system_ram_gb() -> float:
    """RAM fisica total en GB (Windows, via ctypes). 0.0 si no se puede leer."""
    try:
        import ctypes

        class _MEM(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = _MEM()
        m.dwLength = ctypes.sizeof(_MEM)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return round(m.ullTotalPhys / (1024 ** 3), 1)
    except Exception:  # noqa: BLE001
        return 0.0


def has_gpu() -> bool:
    """Heuristica simple: si nvidia-smi existe, hay GPU NVIDIA utilizable."""
    return shutil.which("nvidia-smi") is not None


def recommend_model(ram_gb: float, has_gpu_: bool) -> tuple[str, str, str]:
    """Recomienda (modelo, tamano_aprox, motivo) segun el PC. Pensado para que un
    usuario sin conocimientos no tenga que elegir."""
    if has_gpu_ and ram_gb >= 16:
        return ("llama3.1:8b", "~4.7 GB",
                "tu PC va sobrado (buena RAM y tarjeta grafica): el modelo de mas calidad")
    if ram_gb >= 16:
        return ("qwen2.5:7b", "~4.7 GB",
                "tienes RAM de sobra: un modelo grande y de buena calidad")
    if ram_gb >= 8:
        return ("llama3.2", "~2 GB",
                "el equilibrio ideal para tu PC: rapido y con buena calidad")
    if ram_gb > 0:
        return ("qwen2.5:1.5b", "~1 GB",
                "ligero, para que vaya fluido en un PC con poca memoria")
    return ("llama3.2", "~2 GB", "una opcion equilibrada y segura para la mayoria de PCs")


def set_model(name: str | None) -> None:
    """Fija el modelo preferido (o None para volver a auto-deteccion)."""
    if name:
        _cache["model"] = name
    else:
        _cache.pop("model", None)


def reset_cache() -> None:
    _cache.clear()
