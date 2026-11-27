"""Tema claro/oscuro y accesibilidad inclusiva para AutoCredit Advisor V3.

Solo cambia PRESENTACION. No modifica modelos, bitacora, umbrales, permisos
ni las etiquetas sin procesar usadas por los flujos crediticios.
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

THEMES = ("Oscuro", "Claro")
SIGNS = {"Aceptar": "✓ Aceptar", "Condicionar": "◇ Condicionar", "Rechazar": "✕ Rechazar"}
CVD_DARK = ("#74D5FF", "#FFD166", "#F7A3CF")
CVD_LIGHT = ("#005A8C", "#815000", "#8E285C")

# La paleta accesible es suplementaria. SIEMPRE hay etiquetas o simbolos.
def decision_label(value: str) -> str:
    return SIGNS.get(str(value), str(value))


def visual_preferences(session=None) -> tuple[str, bool]:
    session = st.session_state if session is None else session
    return (
        session.get("ac_visual_theme", "Oscuro")
        if session.get("ac_visual_theme", "Oscuro") in THEMES else "Oscuro",
        bool(session.get("ac_cvd_mode", False)),
    )


def preference_controls(location: str) -> None:
    """Siempre visible al entrar: antes del login y en el lateral de cada rol."""
    if location not in ("login", "sidebar"):
        raise ValueError("Ubicacion de controles invalida")
    st.markdown("**Apariencia y accesibilidad**")
    st.segmented_control(
        "Tema de la aplicación",
        list(THEMES),
        default="Oscuro",
        key="ac_visual_theme",
        selection_mode="single",
        help="Este selector controla también las tarjetas y las gráficas; no solo el fondo.",
    )
    st.toggle(
        "Modo daltónico · símbolos y paleta",
        value=False,
        key="ac_cvd_mode",
        help="Distingue categorías mediante ✓, ◇ y ✕, además de tonos azul, ámbar y rosa.",
    )


# Estilos explicitos de ambos modos; evitar depender del tema del navegador
# que Streamlit aplica a sus controles y NO al HTML personalizado.
_LIGHT_CSS = r"""
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"],[data-testid="stHeader"]{
    background:#f6f8f7!important;color:#15251e!important;color-scheme:light!important}
section[data-testid="stSidebar"],section[data-testid="stSidebar"]>div{
    background:#eff3ef!important;color:#15251e!important}
[data-testid="stAppViewContainer"] h1,[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] h5,[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] small,
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"]{
    color:#15251e!important}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:#20382a!important}
[data-testid="stWidgetLabel"]>div,[data-testid="stCaptionContainer"]{color:#334b3d!important}
[data-testid="stMetric"],.kpi,.ac-p1-kpi,.ac-p2-card,.ac-month-card,
.ac-mgr-kpi,.ac-support-card,.ac-mail-metric,.ac-audit-card,
.ac0-pill,.ac0-note,.ac-mail-empty,.ac-support-empty,.ac-p2-toolbar,
.ac-p1-legend,.ac-p2-banner,.hint{
    background:#ffffff!important;color:#15251e!important;
    border:1px solid #ccd9d0!important;
    box-shadow:0 3px 14px rgba(20,40,28,.06)!important}
.ac-p1-title,.ac-p2-title,.ac-p2-consulta-title,.ac-month-title,.ac-mgr-title,
.ac-mgr-section,.ac-support-title,.ac-support-section,.ac-mail-title,
.ac-mail-subject,.ac-audit-title,.ac-audit-name,.ac0-title,.ac0-cardtitle,
.ac-profile-name,.ac-mail-metric strong,.ac-mail-empty strong,
.ac0-title span,.ac-p2-card .label,.ac-p2-card .value,
.ac-p1-kpi .name,.ac-p1-kpi .number,.ac-month-card .label,
.ac-mgr-label,.ac-support-card .name,.ac-audit-content{
    color:#15251e!important}
.ac-p1-description,.ac-p1-inline,.ac-p1-kpi .detail,.ac-p2-sub,
.ac-p2-card .sub,.ac-month-sub,.ac-month-card .goal,.ac-month-card .detail,
.ac-mgr-sub,.ac-mgr-desc,.ac-mgr-smallnote,.ac-support-lead,
.ac-support-card .detail,.ac-support-note,.ac-mail-sub,.ac-mail-content,
.ac-mail-metric span,.ac-mail-metric small,.ac-mail-who,.ac-mail-when,
.ac-audit-sub,.ac-audit-role,.ac0-hero-sub,.ac0-cardsub,.ac0-footer,
.ac0-note,.ac-p1-legend,.ac-p2-toolbar,.helper,.kpi .label,.kpi .sub{
    color:#3a5545!important}
.ac-p1-kpi.low,.ac-p2-card.alert,.ac-p2-banner.danger,.ac-month-card[style*="106,48"],
.ac-mgr-kpi[style*="98,41"],.ac-mail-tag.important{
    background:#fff0f1!important;border-color:#c48a93!important}
.ac-p1-kpi.mid,.ac-p2-card.warn,.ac-p2-banner.warn{
    background:#fff7e7!important;border-color:#d2b374!important}
.ac-p1-kpi.met,.ac-p2-card.ok,.ac-p2-banner.ok{
    background:#effaf2!important;border-color:#7bb695!important}
.ac-p1-kpi.low .number,.ac-p2-card.alert .value,.ac-p2-banner.danger{
    color:#8b2537!important}
.ac-p1-kpi.mid .number,.ac-p2-card.warn .value,.ac-p2-banner.warn{
    color:#754a00!important}
.ac-p1-kpi.met .number,.ac-p2-card.ok .value,.ac-p2-banner.ok{
    color:#17613b!important}
.ac-month-card .reading,.ac-mgr-val,.ac-support-card .value{
    color:#124c37!important}
.ac0-label,.ac0-sideintro,.ac-month-tag,.ac-mgr-eyebrow,.ac-support-kicker,
.ac-mail-eyebrow,.ac-audit-eyebrow,.ac-audit-label,.ac-p1-eyebrow{
    color:#165f43!important}
.ac-p1-inline b,.ac-p1-legend strong,.ac0-pill{color:#165f43!important}
.ac-p2-chip.r-high,.chip.bad{background:#fff0f2!important;color:#8b2537!important}
.ac-p2-chip.r-mid,.chip.warn{background:#fff5dd!important;color:#754a00!important}
.ac-p2-chip.r-low,.chip.good{background:#effaf2!important;color:#17613b!important}
[data-testid="stMetricValue"],[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"]{color:#15251e!important}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{
    background:#ffffff!important;color:#15251e!important;border-color:#b7c9bd!important}
[data-testid="stDataFrame"] [role="columnheader"]{color:#15251e!important}
[data-testid="stDataFrame"] [aria-selected="true"]{background:#e2f1e8!important}
[data-testid="stDataFrame"] [role="gridcell"]:focus-within{
    background:#d6eee0!important;outline:2px solid #11643a!important}
[data-testid="stApp"] button,[data-testid="stSidebar"] button,
[data-testid="stApp"] input,[data-testid="stApp"] textarea,
[data-testid="stApp"] div[data-baseweb="select"]>div,
div[data-baseweb="popover"] [role="listbox"],div[data-baseweb="popover"] [role="option"]{
    color:#17291e!important;background-color:#ffffff!important}
[data-testid="stApp"] button{border-color:#a8bdb0!important}
[data-testid="stApp"] button[kind="primary"]{
    color:#ffffff!important;background:#17613b!important;border-color:#17613b!important}
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [role="option"][aria-selected="true"]{
    background:#e4f1e8!important;color:#10281b!important}
[data-testid="stApp"] button:focus-visible,[data-testid="stApp"] input:focus-visible{
    outline:3px solid #095c83!important;outline-offset:2px!important}
"""

_DARK_CSS = r"""
html,body,.stApp,[data-testid="stAppViewContainer"],
[data-testid="stMain"],[data-testid="stHeader"]{
    color-scheme:dark!important;background:#0f1110!important;color:#edf5ef!important}
section[data-testid="stSidebar"],section[data-testid="stSidebar"]>div{
    background:#161817!important;color:#edf5ef!important}
[data-testid="stMetric"]{background:#161b18!important;color:#edf5ef!important}
[data-testid="stApp"] button:focus-visible,[data-testid="stApp"] input:focus-visible{
    outline:3px solid #74d5ff!important;outline-offset:2px!important}
"""

# Daltonismo: azul, amarillo y rosa se mantienen distinguibles por simbolos,
# etiquetas y patrones, no solamente por su matiz.
_CVD_CSS = r"""
.ac-p1-kpi.low,.ac-month-card[style*="106,48"],.ac-mgr-kpi[style*="98,41"]{
    border-style:dashed!important}
.ac-p1-kpi.mid,.ac-p2-card.warn{border-style:double!important;border-width:3px!important}
.ac-p1-kpi.met,.ac-p2-card.ok{border-style:solid!important;border-width:2px!important}
.ac-p2-chip.r-high::before,.chip.bad::before{content:"✕ ";font-weight:900}
.ac-p2-chip.r-mid::before,.chip.warn::before{content:"◇ ";font-weight:900}
.ac-p2-chip.r-low::before,.chip.good::before{content:"✓ ";font-weight:900}
"""

_CVD_DARK = r"""
.ac-p1-kpi.met .number,.ac-p2-card.ok .value,.chip.good,.ac-p2-chip.r-low,.good{color:#74D5FF!important}
.ac-p1-kpi.mid .number,.ac-p2-card.warn .value,.chip.warn,.ac-p2-chip.r-mid,.warn{color:#FFD166!important}
.ac-p1-kpi.low .number,.ac-p2-card.alert .value,.chip.bad,.ac-p2-chip.r-high,.bad{color:#F7A3CF!important}
"""
_CVD_LIGHT = r"""
.ac-p1-kpi.met .number,.ac-p2-card.ok .value,.chip.good,.ac-p2-chip.r-low,.good{color:#005A8C!important}
.ac-p1-kpi.mid .number,.ac-p2-card.warn .value,.chip.warn,.ac-p2-chip.r-mid,.warn{color:#815000!important}
.ac-p1-kpi.low .number,.ac-p2-card.alert .value,.chip.bad,.ac-p2-chip.r-high,.bad{color:#8E285C!important}
"""


def theme_css(theme: str, cvd: bool) -> str:
    if theme not in THEMES:
        raise ValueError("Tema invalido")
    css = _LIGHT_CSS if theme == "Claro" else _DARK_CSS
    if cvd:
        css += _CVD_CSS + (_CVD_LIGHT if theme == "Claro" else _CVD_DARK)
    return "<style>\n" + css + "\n</style>"


def show_theme() -> None:
    theme, cvd = visual_preferences()
    st.markdown(theme_css(theme, cvd), unsafe_allow_html=True)


def accessible_plotly(fig: go.Figure) -> go.Figure:
    """Contraste del tema, sin cambiar valores/datos o etiquetas originales."""
    theme, cvd = visual_preferences()
    fg = "#17291e" if theme == "Claro" else "#e5eee8"
    grid = "#d0dcd3" if theme == "Claro" else "rgba(145,169,151,.18)"
    fig.update_layout(
        font=dict(color=fg), title_font=dict(color=fg),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickfont=dict(color=fg),title_font=dict(color=fg),
                     gridcolor=grid,automargin=True)
    fig.update_yaxes(tickfont=dict(color=fg),title_font=dict(color=fg),
                     gridcolor=grid,automargin=True)
    if cvd:
        colors=CVD_LIGHT if theme=="Claro" else CVD_DARK
        for idx, trace in enumerate(fig.data):
            color=colors[idx % len(colors)]
            if isinstance(trace, go.Bar):
                trace.marker.color=color
                trace.marker.pattern.shape=("", "/", "x")[idx % len(colors)]
                trace.marker.line.width=1.2
                trace.marker.line.color=fg
            elif isinstance(trace, go.Scatter):
                if trace.mode and "markers" in trace.mode:
                    trace.marker.color=color
                    trace.marker.symbol=("circle", "square", "diamond")[idx % len(colors)]
                if trace.mode is None or "lines" in trace.mode:
                    trace.line.color=color
                    trace.line.dash=("solid", "dash", "dot")[idx % len(colors)]
            elif isinstance(trace, go.Pie):
                trace.marker.colors=list(colors)
                trace.textinfo="label+percent"
    return fig


def render_accessible_chart(fig: go.Figure, *args, **kwargs):
    return st.plotly_chart(accessible_plotly(fig), *args, **kwargs)
