"""Capa de servicio con caché. Cada función que entrega datos recibe el rol, de modo
que la caché queda separada por rol y nunca se mezclan resultados (Bloque F)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src import almacen, config as C, datos, seguridad, simulacion
from src.modelo import ModeloPD, entrenar


@st.cache_data(show_spinner=False)
def _base_cruda() -> pd.DataFrame:
    return datos.leer_base()


@st.cache_resource(show_spinner="Entrenando el modelo de PD con la base REAL…")
def modelo() -> ModeloPD:
    return entrenar(_base_cruda())


@st.cache_resource(show_spinner=False)
def auc_con_variable_excluida() -> float:
    variables = C.VARIABLES_MODELO + list(C.EXCLUIDAS_DEL_MODELO)
    return entrenar(_base_cruda(), variables=variables).metricas["auc"]


def estado_datos() -> tuple[bool, str]:
    try:
        _base_cruda()
        return True, ""
    except datos.ErrorDeDatos as e:
        return False, str(e)


# --- Indicadores agregados de la base (gerencia y operación) -----------------
@st.cache_data(show_spinner=False)
def indicadores_base(rol: str) -> dict:
    """Nunca devuelve registros individuales; aplica la política por columna."""
    _exigir(rol, "DEFAULT")
    _exigir(rol, "DEBT_TO_INCOME")
    from src.kpis import calcular_kpis
    return calcular_kpis(_base_cruda())




@st.cache_data(show_spinner=False)
def indicadores_calidad(rol: str) -> dict:
    """Solo operación: indicadores de calidad calculados sobre la base REAL.

    No incluye muestras individuales ni métricas de simulaciones de producción.
    """
    if rol != "operacion":
        raise PermissionError("Solo operación consulta los KPI de calidad de datos.")
    from src.kpis import calcular_kpis_calidad
    return calcular_kpis_calidad(_base_cruda(), C.VARIABLES_CLAVE, C.LIMITES_VALIDOS)


def indicadores_bandeja(usuario: seguridad.Usuario) -> dict:
    """Solo el analista autenticado: conteos de SU cola operativa simulada."""
    if usuario.rol != "analista" or not usuario.analista_id:
        raise PermissionError("Los KPI de bandeja son exclusivos de analistas asignados.")
    from src.kpis import calcular_kpis_bandeja
    cola, _ = cola_analista(usuario)
    return calcular_kpis_bandeja(cola)


# --- Mariana: solo agregados -------------------------------------------------
@st.cache_data(show_spinner=False)
def _base_segmentada() -> pd.DataFrame:
    return datos.segmentar(_base_cruda())


@st.cache_data(show_spinner=False)
def cortes_dti() -> tuple[float, float]:
    return datos.cortes_terciles(_base_cruda()["DEBT_TO_INCOME"])


def _exigir(rol: str, dato: str) -> None:
    if not seguridad.puede_agregado(rol, dato):
        raise PermissionError(f"El rol {rol} no puede recibir {dato}.")


@st.cache_data(show_spinner=False)
def resumen_corte(rol: str, filtros: tuple) -> dict:
    _exigir(rol, "DEFAULT")
    df = datos.aplicar_filtros(_base_segmentada(), dict(filtros))
    return {"n": int(len(df)), "total": int(len(_base_segmentada())),
            "tasa": float(df[C.OBJETIVO].mean()) if len(df) else float("nan")}


@st.cache_data(show_spinner=False)
def tasa_cruzada(rol: str, filtros: tuple, filas: str, columnas: str | None) -> pd.DataFrame:
    _exigir(rol, "SEGMENTOS (DTI, enganche, pagos, LTV)")
    df = datos.aplicar_filtros(_base_segmentada(), dict(filtros))
    return datos.tasa_por_grupo(df, filas, columnas)


@st.cache_data(show_spinner=False)
def curva_politica(rol: str, filtros: tuple) -> tuple[pd.DataFrame, int]:
    """Curva corte vs aprobación sobre el holdout del segmento (PD CALCULADO)."""
    _exigir(rol, "PD_MODELO")
    from src.modelo import curva_corte
    m = modelo()
    hold = datos.segmentar(m.holdout, cortes_dti())
    sub = datos.aplicar_filtros(hold, dict(filtros))
    if len(sub) < C.N_MINIMO:
        return pd.DataFrame(), int(len(sub))
    return curva_corte(sub["PD"].to_numpy(), sub[C.OBJETIVO].to_numpy()), int(len(sub))


# --- Adrián: solo sus casos ---------------------------------------------------
@st.cache_data(show_spinner=False)
def _cola_evaluada(analista_id: str) -> tuple[pd.DataFrame, dict]:
    m = modelo()
    cola, originales = simulacion.cola_base(m, analista_id)
    return cola, originales


def cola_analista(usuario: seguridad.Usuario) -> tuple[pd.DataFrame, dict]:
    """Cola del analista con estados y documentos al día. Filtra por ANALISTA_ID."""
    if usuario.rol != "analista" or not usuario.analista_id:
        raise PermissionError("Solo un analista con ANALISTA_ID recibe solicitudes.")
    cola, originales = _cola_evaluada(usuario.analista_id)
    cola = cola.copy()
    for folio in almacen.documentos_recibidos() & set(originales):
        for var, valor in originales[folio].items():
            cola.loc[cola["FOLIO"] == folio, var] = valor
    cola = simulacion.evaluar_cola(modelo(), cola)
    est = almacen.estados(usuario.analista_id)
    cola["ESTADO_SOLICITUD"] = cola["FOLIO"].map(est).fillna("Pendiente")
    cola = cola[cola["ANALISTA_ID"] == usuario.analista_id]
    columnas = ["FOLIO", "RECIBIDA_MIN", "PD", "NIVEL", "CALIDAD", "SUGERENCIA", "ESTADO_SOLICITUD"] + \
        seguridad.columnas_individuales(usuario.rol, C.VARIABLES_MODELO)
    return cola[columnas], originales


# --- Luis: métricas y distribuciones agregadas --------------------------------
@st.cache_data(show_spinner=False)
def flujo_monitor(rol: str, escenario: str, reloj_iso: str) -> pd.DataFrame:
    _exigir(rol, "PSI y calibración")
    from datetime import datetime
    return simulacion.flujo(modelo(), escenario, datetime.fromisoformat(reloj_iso))


def distribucion_entrenamiento(rol: str, variable: str):
    _exigir(rol, variable)
    return modelo().entrenamiento[variable].to_numpy()
