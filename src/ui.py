"""Componentes de interfaz compartidos: rótulos de origen, filtros amarrados a una
decisión, corte activo, estados vacíos y tarjetas de semáforo."""
from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from src import config as C
from src.seguridad import PANTALLAS

COLOR_ORIGEN = {
    "REAL": "green",
    "REAL en bitácora": "green",
    "CALCULADO": "blue",
    "SIMULADO": "orange",
    "POLÍTICA": "violet",
    "NO PRESENTE": "gray",
}
AYUDA_ORIGEN = {
    "REAL": "Columna tal cual de Base_SAS_Equipo3.csv (80,000 créditos × 12 columnas).",
    "REAL en bitácora": "Decisión registrada por una persona en este tablero.",
    "CALCULADO": "Derivado de columnas REAL o del modelo de PD.",
    "SIMULADO": "Dato propuesto que la base aún no trae; se construye para demostrar la pantalla.",
    "POLÍTICA": "Umbral definido por el equipo; se calibra con datos reales.",
    "NO PRESENTE": "Columna del dataset completo que no viene en esta base.",
}


def estilos() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px;}
        [data-testid="stMetricValue"] {font-size: 1.9rem;}
        [data-testid="stCaptionContainer"] p {line-height: 1.35;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def origen(*etiquetas: str) -> None:
    with st.container(horizontal=True, gap="small"):
        for e in etiquetas:
            st.badge(e, color=COLOR_ORIGEN.get(e, "gray"), help=AYUDA_ORIGEN.get(e))


def cabecera(pantalla: str, usuario, extra: str | None = None) -> None:
    p = PANTALLAS[pantalla]
    st.title(f"{pantalla} · {p['titulo']}")
    persona = f"{usuario.persona} ({usuario.nombre_corto})" if usuario else ""
    linea = f"**Sirve a:** {persona} · **Decisión que habilita:** {p['decision']}"
    if extra:
        linea += f" · {extra}"
    st.caption(linea)


def titulo_grafica(pregunta: str, *origenes: str, codigo: str | None = None) -> None:
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.markdown(f"**{pregunta}**" + (f"  \n:gray[{codigo}]" if codigo else ""))
        st.space("stretch")
        for e in origenes:
            st.badge(e, color=COLOR_ORIGEN.get(e, "gray"), help=AYUDA_ORIGEN.get(e))


def amarre(fid_o_cid: str) -> str:
    reg = C.FILTROS.get(fid_o_cid) or C.CONTROLES[fid_o_cid]
    persona = reg["persona"].split(" (")[0]
    return f"↳ {persona} decide: {reg['decision']}"


def filtro(fid: str, key: str, widget: str = "selectbox", on_change: Callable | None = None, **kw):
    """Dibuja un filtro desde el registro, siempre con su decisión visible."""
    reg = C.FILTROS[fid]
    etiqueta = f"{fid} · {reg['nombre']}"
    ayuda = f"Persona: {reg['persona']}. Decisión: {reg['decision']} Por defecto: {reg['defecto']}."
    if key not in st.session_state:
        st.session_state[key] = reg["defecto"]
    if widget == "selectbox":
        valor = st.selectbox(etiqueta, reg["opciones"], key=key, help=ayuda, on_change=on_change, **kw)
    elif widget == "segmented":
        valor = st.segmented_control(etiqueta, reg["opciones"], key=key, help=ayuda, on_change=on_change, **kw)
    elif widget == "pills":
        valor = st.pills(etiqueta, reg["opciones"], selection_mode="multi", key=key, help=ayuda,
                         on_change=on_change, **kw)
    else:
        raise ValueError(widget)
    st.caption(amarre(fid))
    return valor


def corte_activo(descripcion: str, n: int, total: int, extra: str = "",
                 on_reset: Callable | None = None, key: str = "reset") -> None:
    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        pct = n / total * 100 if total else 0
        st.markdown(
            f":blue[**Corte activo:**] {descripcion} → **{n:,} de {total:,}** ({pct:.1f}%)"
            + (f" · {extra}" if extra else "")
        )
        st.space("stretch")
        if on_reset:
            st.button("Restablecer", key=key, on_click=on_reset, icon=":material/restart_alt:")


def estado_vacio(titulo: str, causa: str, acciones: list[tuple[str, Callable]] | None = None,
                 icono: str = ":material/block:", key: str = "vacio") -> None:
    with st.container(border=True):
        st.markdown(f"### {titulo}")
        st.markdown(causa)
        if acciones:
            with st.container(horizontal=True):
                for i, (texto, cb) in enumerate(acciones):
                    st.button(texto, key=f"{key}_{i}", on_click=cb, type="primary" if i == 0 else "secondary")


ESTADOS_SEMAFORO = {
    "ok": ("En banda", "green", ":material/check_circle:"),
    "vigilar": ("Vigilar", "orange", ":material/visibility:"),
    "alerta": ("Fuera de banda", "red", ":material/warning:"),
    "sin_datos": ("Sin datos frescos", "gray", ":material/hourglass_empty:"),
}


def semaforo(nombre: str, valor: str, estado: str, detalle: str, delta: str | None = None,
             delta_color: str = "off", origen_tag: str = "SIMULADO") -> None:
    texto, color, icono = ESTADOS_SEMAFORO[estado]
    with st.container(border=True):
        with st.container(horizontal=True, gap="small"):
            st.badge(texto, color=color, icon=icono)
            st.space("stretch")
            st.badge(origen_tag, color=COLOR_ORIGEN.get(origen_tag, "gray"))
        st.metric(nombre, valor if estado != "sin_datos" else f"{valor}", delta=delta,
                  delta_color=delta_color if estado != "sin_datos" else "off")
        st.caption(detalle)


def ver_tabla(df: pd.DataFrame, etiqueta: str = "Ver como tabla", **kw) -> None:
    with st.expander(etiqueta):
        st.dataframe(df, hide_index=True, **kw)


def pie_origen(texto_extra: str = "") -> None:
    st.caption(
        "Rótulos de origen → **REAL**: columna de la base · **CALCULADO**: derivado de la base o del modelo · "
        "**SIMULADO**: dato propuesto que aún no existe · **POLÍTICA**: umbral del equipo. " + texto_extra
    )


def pct(x: float | None, dec: int = 1) -> str:
    if x is None or pd.isna(x):
        return "—"
    return f"{x * 100:.{dec}f}%"
