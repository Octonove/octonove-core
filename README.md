# octonove-core

Núcleo compartido de la **suite Octonove** de aplicaciones de escritorio Windows local-first ([CapturaStudio](https://github.com/Octonove/capturastudio), [ActaLocal](https://github.com/Octonove/actalocal), [PDFLocal](https://github.com/Octonove/pdflocal), [GuiaClick](https://github.com/Octonove/guiaclick), [AutoEscritorio](https://github.com/Octonove/autoescritorio)).

Cada app mantiene módulos *shim* del mismo nombre que re-exportan de aquí y añaden solo lo específico de esa app. Así, un bug del núcleo se arregla **una vez**, no cinco.

## Módulos

| Módulo | Contenido |
|---|---|
| `theme.py` | Sistema de diseño Tkinter navy/terracota: paleta, estilos ttk, `header()`, `status_bar()`, `center_window()` |
| `llm.py` | Capa Ollama local opcional: detección (127.0.0.1 + `OLLAMA_HOST`), `generate()` con reintento, embeddings, recomendación de modelo según el PC |
| `config.py` | Rutas de datos (`get_data_dir`, `work_dir`, `models_dir` con carpetas compartidas), carga/guardado genérico con hooks (`post_load`/`pre_save`), `RedactingFilter` y `setup_logging` |
| `procutil.py` | Subprocesos sin ventana de consola (`CREATE_NO_WINDOW` con guard de plataforma, `subprocess_kwargs`, `_decode`) |
| `ffmpeg.py` | Localización de FFmpeg (incl. winget), `ffprobe_from`, `get_duration`, `has_whisper` |
| `jsonutil.py` | `extract_json`: primer objeto `{...}` balanceado de una respuesta de LLM |

**Solo stdlib** — nada que empaquetar: PyInstaller lo incluye como cualquier módulo del `sys.path`.

## Instalación (desarrollo)

Clonar junto a las apps y añadir un `.pth` en el `site-packages` del venv apuntando a la carpeta que contiene `octonove_core/`:

```
# <venv>\Lib\site-packages\octonove_shared.pth
C:\ruta\a\esta\carpeta
```

Verificar: `python -c "import octonove_core; print(octonove_core.CORE_VERSION)"`.

## Reglas del núcleo

1. `octonove_core` **nunca importa nada de una app** (los datos por-app entran por parámetro o hook).
2. Los estilos/valores con métricas por-app viven en el shim de esa app, no aquí.
3. 100% stdlib.

## Licencia

[MIT](LICENSE) — © 2026 Octonove.
