"""Sistema de diseno compartido de la suite Octonove (paleta navy + terracota
de SimplificaconIA): navy #1E3A5F + terracota #CE6E61.

Fuente unica del tema: cada app tiene un <paquete>/theme.py que re-exporta de
aqui (shim) y anade solo sus estilos propios (p.ej. Go/Stop.TButton en
AutoEscritorio o la variante compacta de Rec.TButton en CapturaStudio).
NO definir __all__: los shims hacen 'from octonove_core.theme import *' y
necesitan TODAS las constantes publicas.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def _unbind_one(widget, seq: str, funcid: str) -> None:
    """Elimina SOLO el handler `funcid` de `seq`. Misc.unbind(seq, funcid) borra
    TODOS los handlers de la secuencia (bug conocido de tkinter, bpo-31485);
    esto filtra el script Tcl y conserva los handlers ajenos."""
    try:
        script = widget.bind(seq)
        keep = "\n".join(ln for ln in str(script).splitlines() if funcid not in ln)
        widget.bind(seq, keep if keep.strip() else "")
        widget.deletecommand(funcid)
    except tk.TclError:
        pass


def center_window(win) -> None:
    """Centra una ventana en la pantalla en cuanto se muestra (evita que el gestor
    la suelte en una esquina). Se engancha a <Map> para conocer ya su tamano."""
    def _do(_e=None):
        try:
            win.update_idletasks()
            w, h = win.winfo_width(), win.winfo_height()
            if w <= 1:
                return
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2 - 30)   # ligeramente por encima del centro optico
            win.geometry(f"+{x}+{y}")
            _unbind_one(win, "<Map>", bid)
        except tk.TclError:
            pass
    bid = win.bind("<Map>", _do, add="+")


# --- Paleta de marca (igual que la web) ----------------------------------
PRIMARY = "#CE6E61"        # terracota: accion principal (grabar, CTA)
PRIMARY_DARK = "#B85A4D"   # hover
PRIMARY_PRESS = "#A24E42"  # pressed
PRIMARY_DIS = "#E6C2BB"
NAVY = "#1E3A5F"           # navy de marca (cabecera, titulares)
NAVY_DARK = "#15304D"
HEAD_SUB = "#B7C7DA"       # subtitulo sobre cabecera navy
ACCENT = "#6EC1E4"         # azul claro acento
TEXT = "#1E293B"           # texto principal
MUTED = "#64748B"          # texto secundario
BG = "#FFFFFF"
SURFACE = "#EEF3F8"        # fondos sutiles / pestanas inactivas
CARD = "#FAFCFF"           # tarjetas / labelframes (off-white azulado)
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"
DANGER = "#DC2626"
REC = "#EF4444"            # rojo de grabacion
WHITE = "#FFFFFF"

FONT = "Segoe UI"
F_TITLE = (FONT, 19, "bold")
F_SUB = (FONT, 10)
F_H = (FONT, 11, "bold")
F_BODY = (FONT, 10)
F_BTN = (FONT, 10, "bold")
F_SMALL = (FONT, 9)


def apply(root: tk.Misc) -> None:
    """Aplica el tema comun. Superconjunto de los estilos de las 5 apps: definir
    un estilo que una app no usa es inocuo en ttk. Los estilos con metricas
    propias de una app (p.ej. Rec.TButton compacto) se redefinen en su shim
    DESPUES de llamar aqui (la redefinicion es acumulativa y determinista)."""
    try:
        root.configure(bg=BG)
    except tk.TclError:
        pass
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass

    st.configure(".", background=BG, foreground=TEXT, font=F_BODY,
                 focuscolor=PRIMARY, bordercolor=BORDER)
    st.configure("TFrame", background=BG)
    st.configure("Card.TFrame", background=CARD)
    st.configure("Dark.TFrame", background=NAVY)
    st.configure("TLabel", background=BG, foreground=TEXT, font=F_BODY)
    st.configure("Muted.TLabel", background=BG, foreground=MUTED, font=F_SMALL)
    st.configure("H.TLabel", background=BG, foreground=NAVY, font=F_H)
    st.configure("Big.TLabel", background=BG, foreground=NAVY, font=(FONT, 14, "bold"))
    st.configure("CardMuted.TLabel", background=CARD, foreground=MUTED, font=F_SMALL)

    st.configure("TLabelframe", background=CARD, bordercolor=BORDER,
                 relief="solid", borderwidth=1)
    st.configure("TLabelframe.Label", background=CARD, foreground=NAVY, font=F_H)

    st.configure("TButton", font=F_BODY, padding=(12, 7), relief="flat",
                 background=SURFACE, foreground=TEXT, bordercolor=BORDER)
    st.map("TButton",
           background=[("active", "#E2E8F0"), ("pressed", "#CBD5E1"),
                       ("disabled", "#F1F5F9")],
           foreground=[("disabled", "#94A3B8")])
    st.configure("Tool.TButton", font=F_BODY, padding=(10, 10), relief="flat",
                 background=SURFACE, foreground=TEXT, anchor="w")
    st.map("Tool.TButton", background=[("active", "#E2E8F0"), ("pressed", "#CBD5E1")])
    st.configure("Primary.TButton", font=F_BTN, padding=(16, 9), relief="flat",
                 background=PRIMARY, foreground=WHITE, bordercolor=PRIMARY)
    st.map("Primary.TButton",
           background=[("active", PRIMARY_DARK), ("pressed", PRIMARY_PRESS),
                       ("disabled", PRIMARY_DIS)],
           foreground=[("disabled", "#FBEEEB")])
    st.configure("Rec.TButton", font=(FONT, 12, "bold"), padding=(22, 12), relief="flat",
                 background=REC, foreground=WHITE, bordercolor=REC)
    st.map("Rec.TButton", background=[("active", "#DC2626"), ("pressed", "#B91C1C")])

    for s in ("TRadiobutton", "TCheckbutton"):
        st.configure(s, background=CARD, foreground=TEXT, font=F_BODY)
        st.map(s, background=[("active", CARD)], indicatorcolor=[("selected", PRIMARY)])
    st.configure("TCombobox", padding=5, arrowsize=14)
    st.configure("TSpinbox", padding=4, arrowsize=12)
    st.configure("TEntry", padding=4)

    st.configure("TNotebook", background=BG, bordercolor=BORDER, tabmargins=(6, 6, 6, 0))
    st.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED,
                 padding=(18, 9), font=F_BODY)
    st.map("TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", NAVY)],
           expand=[("selected", [1, 1, 1, 0])])

    st.configure("TProgressbar", background=PRIMARY, troughcolor=SURFACE,
                 bordercolor=SURFACE, lightcolor=PRIMARY, darkcolor=PRIMARY)
    st.configure("Status.TLabel", background=SURFACE, foreground=MUTED,
                 font=F_SMALL, padding=(12, 6))


def header(parent: tk.Misc, title: str, subtitle: str = "") -> tk.Frame:
    bar = tk.Frame(parent, bg=NAVY)
    bar.pack(fill="x")
    inner = tk.Frame(bar, bg=NAVY)
    inner.pack(fill="x", padx=18, pady=(13, 13))
    tk.Label(inner, text=title, bg=NAVY, fg=WHITE, font=F_TITLE).pack(side="left")
    if subtitle:
        tk.Label(inner, text=subtitle, bg=NAVY, fg=HEAD_SUB,
                 font=F_SUB).pack(side="left", padx=(12, 0), pady=(6, 0))
    return bar


def status_bar(parent: tk.Misc, text: str = "") -> ttk.Label:
    lbl = ttk.Label(parent, text=text, style="Status.TLabel", anchor="w")
    lbl.pack(fill="x", side="bottom")
    return lbl


def scrollable(parent: tk.Misc, *, width: int | None = None):
    """Columna con scroll VERTICAL cuando su contenido no cabe en alto.

    Devuelve el frame INTERIOR: mete ahi tus widgets con pack/grid normalmente.
    El ancho se ajusta al contenido (no recorta en horizontal) y la barra solo
    aparece si hace falta. Evita que paneles altos queden 'cortados' por abajo
    en ventanas pequenas o con texto grande (escalado DPI alto).
    """
    holder = ttk.Frame(parent)
    canvas = tk.Canvas(holder, highlightthickness=0, borderwidth=0, bg=BG)
    vsb = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    inner = ttk.Frame(canvas)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _sync(_e=None):
        try:
            canvas.configure(scrollregion=canvas.bbox("all"))
            req_w = width or inner.winfo_reqwidth()
            canvas.configure(width=req_w)              # sin recorte horizontal
            need = inner.winfo_reqheight() > canvas.winfo_height() + 1
            if need and not vsb.winfo_ismapped():
                vsb.pack(side="right", fill="y")
            elif not need and vsb.winfo_ismapped():
                vsb.pack_forget()
        except tk.TclError:
            pass

    inner.bind("<Configure>", _sync)
    canvas.bind("<Configure>", _sync)

    def _wheel(ev):
        if inner.winfo_reqheight() > canvas.winfo_height() + 1:
            canvas.yview_scroll(-1 if ev.delta > 0 else 1, "units")
    # el binado se activa solo mientras el puntero esta sobre la columna
    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _wheel))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
    holder.inner = inner        # por si el llamador quiere el interior via .inner
    return holder, inner
