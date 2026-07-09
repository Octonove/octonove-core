"""Dialogo UNIFICADO de configuracion de IA para toda la suite Octonove.

El usuario elige, una sola vez y para las 5 apps:
  - Gratis y en tu PC (Ollama, privacidad total), o
  - una API potente (OpenAI / Gemini / Anthropic) pegando su clave.

La clave se guarda cifrada con DPAPI (octonove_core.aiconfig). Solo tkinter +
stdlib. `show_ai_dialog(parent, on_saved)` abre el dialogo; `on_saved()` se llama
tras guardar para que la app refresque su etiqueta de estado."""

from __future__ import annotations

import threading
import webbrowser

import tkinter as tk
from tkinter import ttk

from . import aiconfig, llm, theme

_GET_KEY_URL = {
    "openai": "https://platform.openai.com/api-keys",
    "gemini": "https://aistudio.google.com/apikey",
    "anthropic": "https://console.anthropic.com/settings/keys",
}


def status_text() -> str:
    """Resumen del proveedor de IA activo, para la etiqueta de cada app."""
    cfg = aiconfig.load()
    prov = cfg.get("provider", "ollama")
    if prov in aiconfig.CLOUD_MODELS and cfg.get("api_key"):
        mdl = cfg.get("model") or aiconfig.CLOUD_MODELS[prov]["default"]
        return f"✓ IA en la nube: {aiconfig.PROVIDER_LABELS[prov]} ({mdl})"
    if llm.available(timeout=2.0):
        return f"✓ IA local (Ollama): {llm.default_model() or '?'}"
    return "Sin IA avanzada: se usan heuristicas locales (o configura una)."


def _safe_modal(win) -> None:
    def _release(_e=None, w=win):
        try:
            if w.grab_current():
                w.grab_release()
        except tk.TclError:
            pass
    win.bind("<Destroy>", _release)
    try:
        win.grab_set()
    except tk.TclError:
        pass


def show_ai_dialog(parent, on_saved=None) -> None:
    cfg = aiconfig.load()
    win = tk.Toplevel(parent)
    theme.center_window(win)
    win.title("Configurar IA")
    win.configure(bg=theme.BG)
    win.transient(parent)
    win.resizable(False, False)

    outer = ttk.Frame(win, padding=18)
    outer.pack(fill="both", expand=True)
    ttk.Label(outer, text="Elige tu IA", style="H.TLabel").pack(anchor="w")
    ttk.Label(outer, text="Gratis y privado en tu PC (Ollama), o una API mas potente\n"
              "pegando tu clave. Se guarda cifrada y vale para todas las apps.",
              style="Muted.TLabel", justify="left").pack(anchor="w", pady=(2, 10))

    var_prov = tk.StringVar(value=cfg.get("provider", "ollama"))
    var_key = tk.StringVar(value=cfg.get("api_key", ""))
    var_model = tk.StringVar(value=cfg.get("model", ""))
    var_show = tk.BooleanVar(value=False)

    prov_row = ttk.Frame(outer)
    prov_row.pack(fill="x")
    for p in aiconfig.PROVIDERS:
        ttk.Radiobutton(prov_row, text=aiconfig.PROVIDER_LABELS[p], value=p,
                        variable=var_prov, command=lambda: _render()).pack(anchor="w")

    body = ttk.LabelFrame(outer, text="Detalles", padding=12)
    body.pack(fill="x", pady=(10, 0))
    status = ttk.Label(outer, text="", style="Muted.TLabel", wraplength=420, justify="left")
    status.pack(anchor="w", pady=(8, 0))

    def _set_status(msg: str) -> None:
        try:
            status.config(text=msg)
        except tk.TclError:
            pass

    def _test() -> None:
        prov = var_prov.get()
        _set_status("Probando conexion…")
        key, mdl = var_key.get().strip(), var_model.get().strip()

        def work():
            ok, msg = llm.test_provider(prov, key, mdl)
            try:
                win.after(0, lambda: _set_status(("✓ " if ok else "✗ ") + msg))
            except (tk.TclError, RuntimeError):
                pass
        threading.Thread(target=work, daemon=True).start()

    def _render() -> None:
        for w in body.winfo_children():
            w.destroy()
        prov = var_prov.get()
        if prov == "ollama":
            ram, gpu = llm.system_ram_gb(), llm.has_gpu()
            rec, size, motivo = llm.recommend_model(ram, gpu)
            ttk.Label(body, text="Ollama corre modelos en tu propio PC: gratis y sin que\n"
                      "nada salga de tu ordenador.", style="CardMuted.TLabel",
                      justify="left").pack(anchor="w")
            mods = llm.list_models(timeout=4.0)
            if mods:
                chat = [m for m in mods if "embed" not in m.lower()] or mods
                ttk.Label(body, text="Modelo:", style="H.TLabel").pack(anchor="w", pady=(8, 2))
                if var_model.get() not in chat:
                    var_model.set(chat[0])
                ttk.Combobox(body, textvariable=var_model, values=chat, state="readonly",
                             width=34).pack(anchor="w")
            else:
                ttk.Label(body, text=f"No se detecta Ollama. Instalalo en ollama.com y ejecuta:\n"
                          f"    ollama run {rec}   ({size} — {motivo})",
                          style="CardMuted.TLabel", justify="left").pack(anchor="w", pady=(8, 0))
                ttk.Button(body, text="Abrir ollama.com",
                           command=lambda: webbrowser.open("https://ollama.com")).pack(
                    anchor="w", pady=(6, 0))
        else:
            info = aiconfig.CLOUD_MODELS[prov]
            ttk.Label(body, text="Pega tu API key. Se cifra en tu equipo (DPAPI) y no se\n"
                      "guarda en claro ni se registra en ningun log.",
                      style="CardMuted.TLabel", justify="left").pack(anchor="w")
            ttk.Label(body, text="API key:", style="H.TLabel").pack(anchor="w", pady=(8, 2))
            ent = ttk.Entry(body, textvariable=var_key, width=44, show="•")
            ent.pack(anchor="w")

            def _toggle():
                ent.config(show="" if var_show.get() else "•")
            ttk.Checkbutton(body, text="Mostrar", variable=var_show,
                            command=_toggle).pack(anchor="w", pady=(2, 0))
            ttk.Button(body, text="Conseguir una API key…",
                       command=lambda p=prov: webbrowser.open(_GET_KEY_URL[p])).pack(
                anchor="w", pady=(2, 0))
            ttk.Label(body, text="Modelo:", style="H.TLabel").pack(anchor="w", pady=(8, 2))
            if not var_model.get():
                var_model.set(info["default"])
            ttk.Combobox(body, textvariable=var_model, values=info["options"],
                         width=34).pack(anchor="w")
            ttk.Label(body, text=f"Recomendado (economico): {info['default']}",
                      style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

    def _save() -> None:
        prov = var_prov.get()
        aiconfig.save(prov, var_model.get().strip(), var_key.get().strip())
        llm.reset_cache()   # relee la config de IA y limpia el modelo cacheado
        if on_saved:
            try:
                on_saved()
            except Exception:  # noqa: BLE001
                pass
        win.destroy()

    btns = ttk.Frame(outer)
    btns.pack(fill="x", pady=(14, 0))
    ttk.Button(btns, text="Probar conexion", command=_test).pack(side="left")
    ttk.Button(btns, text="Guardar", style="Primary.TButton", command=_save).pack(side="right")

    _render()
    _safe_modal(win)
