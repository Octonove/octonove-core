"""Utilidades JSON compartidas: extraer el primer objeto {...} balanceado de una
respuesta de LLM (que suele venir envuelta en texto)."""

from __future__ import annotations

import json


def extract_json(raw: str) -> dict | None:
    """Devuelve el primer bloque {...} balanceado parseado, o None."""
    if not raw:
        return None
    start = raw.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None
