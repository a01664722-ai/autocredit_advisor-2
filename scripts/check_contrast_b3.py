"""Puerta B3 de contraste de paleta WCAG 2.2 AA: solo lee código; nunca cambia colores.

Exige >=4.5:1 para etiquetas de texto normal y >=3:1 para series informativas.
Valida colores CSS declarados en las pantallas V3 y los de las series sobre fondo oscuro.
La auditoría visual en navegador sigue siendo necesaria para cobertura total de WCAG.
"""
from __future__ import annotations
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DARK_SURFACE = "#161b18"
DARK_PAGE = "#0f1110"
FILES = (
    "app_v3.py",
    "src/login_view.py",
    "src/manager_overview.py",
    "src/kpi_views.py",
    "src/support_views.py",
    "src/access_audit.py",
)
CHART_FILES = ("app_v3.py", "src/manager_overview.py", "src/kpi_views.py", "src/support_views.py")


def relative_luminance(hex_color: str) -> float:
    color = hex_color.lstrip("#")
    if len(color) != 6 or not all(c in "0123456789abcdefABCDEF" for c in color):
        raise ValueError(f"Color hexadecimal invalido: {hex_color}")
    channels = [int(color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(fg: str, bg: str) -> float:
    higher, lower = sorted((relative_luminance(fg), relative_luminance(bg)), reverse=True)
    return (higher + 0.05) / (lower + 0.05)


def css_text_colors(path: str) -> list[tuple[str, str]]:
    text = (ROOT / path).read_text(encoding="utf-8")
    selectors = re.findall(r"(\.[\w-]+(?:\s+\.[\w-]+)?)\s*\{([^{}]+)\}", text)
    found = []
    for selector, rules in selectors:
        match = re.search(r"(?:^|[;\n])\s*color\s*:\s*(#[0-9a-fA-F]{6})\b", rules)
        if match:
            found.append((selector, match.group(1)))
    if not found:
        raise AssertionError(f"No se detectaron reglas de color de texto en {path}")
    return found


def used_chart_colors(path: str) -> list[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    # Traza los colores literales de líneas/barras, no los fondos decorativos.
    patterns = (
        r"(?:marker_color|line_color)\s*=\s*['\\"](#[0-9a-fA-F]{6})",
        r"line\s*=\s*dict\(color\s*=\s*['\\"](#[0-9a-fA-F]{6})",
    )
    colors = []
    for pattern in patterns:
        colors.extend(re.findall(pattern, text))
    return colors


def check_palette() -> list[str]:
    errors = []
    total_text = 0
    total_chart = 0
    for path in FILES:
        for selector, fg in css_text_colors(path):
            total_text += 1
            for bg in (DARK_SURFACE, DARK_PAGE):
                value = contrast_ratio(fg, bg)
                if value < 4.5:
                    errors.append(
                        f"{path}: {selector} texto {fg} vs {bg} = {value:.2f}:1 (mín. 4.5:1)"
                    )
    for path in CHART_FILES:
        for color in used_chart_colors(path):
            total_chart += 1
            value = contrast_ratio(color, DARK_SURFACE)
            if value < 3.0:
                errors.append(f"{path}: grafica {color} vs {DARK_SURFACE} = {value:.2f}:1 (mín. 3:1)")
    if total_text < 55 or total_chart < 12:
        errors.append(
            f"Cobertura inesperadamente baja: {total_text} declaraciones de texto y {total_chart} series."
        )
    # Daltonismo: son categorías etiquetadas y no únicamente tonos.
    app = (ROOT / "app_v3.py").read_text(encoding="utf-8")
    for literal in ("Aceptar", "Condicionar", "Rechazar", "Seleccionar", "Ver detalle"):
        if literal not in app:
            errors.append(f"Falta la categoría textual {literal!r} junto al color.")
    if errors:
        return errors
    print(
        f"WCAG 2.2 AA B3: {total_text} estilos de texto >=4.5:1 "
        f"y {total_chart} colores de series >=3:1, en fondo oscuro de V3."
    )
    return []


if __name__ == "__main__":
    problems = check_palette()
    if problems:
        for problem in problems:
            print("FAIL:", problem, file=sys.stderr)
        sys.exit(1)
    print("PASS: contraste verificado (paleta V3; no sustituye auditoría de navegador).")
