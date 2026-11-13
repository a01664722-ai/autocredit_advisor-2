"""Paleta de identificación de personas (sin interpretación de riesgo).

Se utiliza de forma única en todas las comparaciones entre analistas.
Azul y morado codifican únicamente el nombre, no calidad, meta ni riesgo.
"""
from __future__ import annotations

ANALYST_COLORS = {
    "A-017": "#6EA8FE",  # Adrián: azul
    "A-022": "#B58BFA",  # Sofía: morado
}
ANALYST_NAMES = {"A-017": "Adrián", "A-022": "Sofía"}
GOAL_COLOR = "#AAB5AF"  # referencia gris neutro, nunca color de persona


def analyst_color(analyst_id: str) -> str:
    """Devuelve un color estable para cada analista conocido."""
    if analyst_id not in ANALYST_COLORS:
        raise ValueError("Analista no registrado en la paleta")
    return ANALYST_COLORS[analyst_id]
