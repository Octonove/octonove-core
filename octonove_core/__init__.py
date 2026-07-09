"""octonove_core — nucleo compartido de la suite Octonove.

Codigo comun a las 5 apps (CapturaStudio, ActaLocal, PDFLocal, GuiaClick,
AutoEscritorio). Cada app mantiene un modulo del mismo nombre que re-exporta
de aqui (shim) y anade solo lo especifico de esa app, de modo que un bug se
arregla UNA vez y no cinco.

Se instala en el venv compartido via un .pth que apunta a la carpeta 'shared'
(PyInstaller lo empaqueta como cualquier modulo del sys.path).
"""

CORE_VERSION = "1.0.0"
