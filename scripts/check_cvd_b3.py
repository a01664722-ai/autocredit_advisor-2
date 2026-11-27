"""Simulacion reproducible protanopia/deuteranopia de paletas V3.

Metodo: matrices de Machado, Oliveira & Fernandes (2009), severidad 1.0,
aplicadas a RGB linealizado. Cubre tokens principales de estados, no pixeles
del DOM ni una certificacion clinica de percepcion.
"""
from __future__ import annotations
from pathlib import Path
import sys

from src.accessibility_theme import CVD_DARK, CVD_LIGHT, SIGNS

MATRICES = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
}
SURFACES = {"Oscuro": "#0f1110", "Claro": "#ffffff"}
PALETTES = {"Oscuro": CVD_DARK, "Claro": CVD_LIGHT}
LABELS = ("Aceptar", "Condicionar", "Rechazar")
MINIMUM = 4.5


def rgb_linear(hex_color: str):
    if len(hex_color) != 7 or not hex_color.startswith("#"):
        raise ValueError("Se espera un color hexadecimal de seis digitos")
    try:
        channels = [int(hex_color[pos:pos+2],16)/255.0 for pos in (1,3,5)]
    except ValueError as exc:
        raise ValueError("Color RGB hexadecimal invalido") from exc
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in channels)


def gamma_encode(linear):
    out=[]
    for value in linear:
        value=max(0.0,min(1.0,value))
        out.append(value*12.92 if value<=.0031308 else 1.055*value**(1/2.4)-.055)
    return "#" + "".join(f"{round(c*255):02X}" for c in out)


def simulated(hex_color: str, matrix):
    channels=rgb_linear(hex_color)
    return gamma_encode([sum(row[k]*channels[k] for k in range(3)) for row in matrix])


def contrast(fg: str, bg: str) -> float:
    def luminance(color):
        return sum(c*w for c,w in zip(rgb_linear(color),(.2126,.7152,.0722)))
    a,b=sorted((luminance(fg),luminance(bg)),reverse=True)
    return (a+.05)/(b+.05)


def evaluate():
    """Filas con ratio de texto/estado para normal y dos simulaciones."""
    results=[]
    for theme,colors in PALETTES.items():
        background=SURFACES[theme]
        for label,color in zip(LABELS,colors):
            for scenario,matrix in [("normal",None),*MATRICES.items()]:
                visible=simulated(color,matrix) if matrix is not None else color
                results.append({
                    "tema":theme, "estado":label, "vista":scenario,
                    "original":color, "simulado":visible,
                    "contraste":round(contrast(visible,background),2),
                })
    return results


def check_palette():
    errors=[]
    for row in evaluate():
        if row["contraste"] < MINIMUM:
            errors.append(f'{row["tema"]} {row["estado"]} {row["vista"]}: '
                          f'{row["contraste"]:.2f}:1 < {MINIMUM}:1')
    if set(SIGNS)!=set(LABELS) or len(set(SIGNS.values()))!=3:
        errors.append("Faltan simbolos y etiquetas no cromaticas para tres decisiones")
    app=(Path(__file__).resolve().parents[1]/"app_v3.py").read_text(encoding="utf-8")
    for fragment in ('vista["SUGERENCIA"].map(decision_label)',
                     'decision_label(r.SUGERENCIA)',
                     'riesgo_visible', 'preference_controls("login")',
                     'preference_controls("sidebar")'):
        if fragment not in app:
            errors.append("Sin cobertura visible: "+fragment)
    return errors


def markdown_table():
    rows=["| Tema | Estado / símbolo | Escenario | Tono RGB simulado | Contraste |",
          "|---|---|---|---|---:|"]
    for r in evaluate():
        rows.append(f'| {r["tema"]} | {SIGNS[r["estado"]]} | {r["vista"]} | '
                    f'{r["simulado"]} | {r["contraste"]:.2f}:1 |')
    return "\n".join(rows)


if __name__=="__main__":
    problems=check_palette()
    print(markdown_table())
    if problems:
        for p in problems:print("FAIL:",p,file=sys.stderr)
        sys.exit(1)
    print(f"PASS: {len(evaluate())} pares verificables (2 temas x 3 estados x 3 escenarios) >=4.5:1")
    print("Las formas ✓, ◇, ✕ y etiquetas textuales evitan depender solo del color.")
