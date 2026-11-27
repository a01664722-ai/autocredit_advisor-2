"""Pruebas binarias de B3: preguntas por gráfica, estado vacío, filtros y acceso de V3.

Son comprobaciones de presencia en código; no sustituyen una inspección en navegador.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUESTIONS = {
    "app_v3.py": (
        "¿La PD de este caso supera el corte de la política crediticia?",
        "¿Dónde se ubica la PD del caso frente a las solicitudes de TEST?",
        "¿Cómo se compara el endeudamiento del caso con los grupos de TRAIN?",
        "¿Qué indicadores superan la mediana de buenos pagadores?",
        "¿Qué percentil ocupa cada indicador del caso dentro de TRAIN?",
        "¿Cómo cambian los casos condicionados y rechazados al mover el corte?",
        "¿Qué incumplimiento se observó en la zona condicional de TEST?",
    ),
    "src/manager_overview.py": (
        "¿Qué tan cerca está cada analista de su meta individual?",
        "¿Cómo avanzan las decisiones de los analistas frente a la meta?",
        "¿Qué categorías concentran las incidencias de Soporte?",
        "¿Cuáles son los estados de los casos de Soporte?",
    ),
    "src/kpi_views.py": (
        "¿Cómo evolucionan las decisiones del mes frente a la meta?",
        "¿Qué proporción de decisiones fue aceptar, condicionar o rechazar?",
        "¿Cuántos casos se atendieron por nivel de riesgo frente a la meta?",
        "¿Qué tan cerca están los indicadores de procedimiento de sus metas?",
        "¿Qué nivel de riesgo o cumplimiento presenta cada analista?",
        "¿Cómo evoluciona el número de decisiones por analista durante el mes?",
        "¿Qué niveles de riesgo atiende cada analista?",
    ),
    "src/support_views.py": (
        "¿Qué tan bien distinguen los modelos el incumplimiento?",
        "¿Qué precisión obtiene cada modelo al aumentar la detección de incumplimientos?",
        "¿Cuántos casos clasifica correcta e incorrectamente XGBoost?",
        "¿Cómo se distribuye la PD entre créditos cumplidos e incumplidos?",
        "¿Qué variables tienen mayor importancia interna en XGBoost?",
        "¿Coinciden las probabilidades estimadas con el incumplimiento observado?",
    ),
}


def test_every_active_v3_chart_has_a_business_question():
    for path, questions in QUESTIONS.items():
        source = (ROOT / path).read_text(encoding="utf-8")
        for question in questions:
            assert question in source, f"Pregunta faltante en {path}: {question}"


def test_empty_state_stops_without_data():
    source = (ROOT / "app_v3.py").read_text(encoding="utf-8")
    assert "No hay solicitudes para esta combinación" in source
    assert "No hay coincidencias para ese Loan ID" in source
    assert source.count("st.stop()") >= 5


def test_two_filters_and_visible_count():
    source = (ROOT / "app_v3.py").read_text(encoding="utf-8")
    assert "st.segmented_control('Estado de la solicitud'" in source
    assert "st.pills('Recomendación XGBoost'" in source
    assert "resultados · datos de TEST" in source


def test_quick_decision_menu_has_visible_popup_and_preserved_choices():
    source = (ROOT / "app_v3.py").read_text(encoding="utf-8")
    assert 'div[data-baseweb="popover"]{z-index:100000!important}' in source
    assert "'Decisión rápida'" in source
    for choice in ("Seleccionar", "Aceptar", "Condicionar", "Rechazar", "Ver detalle"):
        assert choice in source


def test_streamlit_url_is_first_readme_line():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text.splitlines()[0] == "https://autocreditadvisor-2-f2ww6wn7nnrysa43edznfp.streamlit.app/"
