"""Configuracion compartida de la suite Octonove: rutas de datos, carga/guardado
generico de la config y logging.

Cada app conserva su <paquete>/config.py como shim: alli viven su AppConfig
COMPLETO (los campos son 100% especificos y renombrarlos romperia los
config.json ya guardados), las constantes CONFIG_PATH/LOG_PATH (evaluadas al
importar, como siempre) y los hooks propios (p.ej. el cifrado DPAPI de la
stream_key de CapturaStudio entra por post_load/pre_save — el core NUNCA
importa nada de una app).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------- rutas
def get_data_dir(app_name: str) -> Path:
    for base in (os.environ.get("APPDATA"), str(Path.home())):
        if not base:
            continue
        d = Path(base) / app_name
        try:
            d.mkdir(parents=True, exist_ok=True)
            return d
        except OSError:
            continue
    d = Path(tempfile.gettempdir()) / app_name
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def default_documents_dir(app_name: str) -> Path:
    return Path.home() / "Documents" / app_name


def default_videos_dir(app_name: str) -> Path:
    return Path.home() / "Videos" / app_name


def work_dir(app_name: str) -> Path:
    """Carpeta de trabajo temporal de la app."""
    d = get_data_dir(app_name) / "work"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def models_dir(app_name: str, shared_candidates: list[Path] | None = None) -> Path:
    """Modelos de IA (Whisper). Reutiliza una carpeta compartida de otra app de la
    suite SOLO si de verdad contiene modelos (ggml-*.bin): asi no se descargan dos
    veces, pero una carpeta vacia ajena no 'secuestra' las descargas propias."""
    for shared in (shared_candidates or []):
        try:
            if shared.is_dir() and any(shared.glob("ggml-*.bin")):
                return shared
        except OSError:
            continue
    d = get_data_dir(app_name) / "models"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


# --------------------------------------------------------------- carga/guardado
def load_config(config_path: Path, config_cls, post_load=None):
    """Carga generica: filtra claves desconocidas (compat con configs antiguas),
    tolera JSON corrupto y llama cfg.ensure_dirs() solo si existe. El hook
    post_load(data, cfg) corre ANTES de ensure_dirs y recibe el dict crudo
    (para claves fuera del dataclass, p.ej. stream_key_enc)."""
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            known = {f for f in config_cls().__dict__}
            cfg = config_cls(**{k: v for k, v in data.items() if k in known})
            if post_load:
                post_load(data, cfg)
            if hasattr(cfg, "ensure_dirs"):
                cfg.ensure_dirs()
            return cfg
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Config corrupta: %s", exc)
    cfg = config_cls()
    if hasattr(cfg, "ensure_dirs"):
        cfg.ensure_dirs()
    return cfg


def save_config(cfg, config_path: Path, pre_save=None) -> None:
    """Guardado generico. El hook pre_save(data) opera sobre la COPIA asdict y
    nunca muta cfg (p.ej. sustituir stream_key por su version cifrada)."""
    try:
        data = asdict(cfg)
        if pre_save:
            pre_save(data)
        config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                               encoding="utf-8")
    except OSError as exc:
        logger.error("No se pudo guardar la config: %s", exc)


# -------------------------------------------------------------------- logging
class RedactingFilter(logging.Filter):
    """Enmascara secretos en los logs (defensa en profundidad). Generica: la
    regex concreta la aporta cada app; el grupo 1 se conserva y el resto se
    sustituye por ***."""

    def __init__(self, pattern, repl: str = r"\1***"):
        super().__init__()
        self._rx = pattern
        self._repl = repl

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            red = self._rx.sub(self._repl, msg)
            if red != msg:
                record.msg = red
                record.args = ()
        except Exception:  # noqa: BLE001
            pass
        return True


def setup_logging(log_path: Path, filters: list[logging.Filter] | None = None) -> None:
    handlers: list[logging.Handler] = []
    try:
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except OSError:
        pass
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler(sys.stderr))
    if not handlers:
        handlers.append(logging.NullHandler())
    for f in (filters or []):
        for h in handlers:
            h.addFilter(f)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        handlers=handlers)
