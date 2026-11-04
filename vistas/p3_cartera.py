"""P3 · Cartera por segmento · Mariana (gerente de riesgo).
Decisión: endurecer o relajar la política de un segmento. Solo recibe agregados."""
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from src import config as C, datos, graficas as G, servicios, ui
from src import auth
from src.ui import pct

usuario = auth.exigir_acceso("P3")
ui.cabecera("P3", usuario, extra="Solo agregados con n ≥ 30; ningún crédito individual")

FIDS = ["F3", "F4", "F5", "F6"]
CLAVES = {f: f"p3_{f}" for f in FIDS}


def _registrar_cambio(fid: str) -> None:
    orden = st.session_state.setdefault("p3_orden", [])
    if fid in orden:
        orden.remove(fid)
    if st.session_state[CLAVES[fid]] != C.TODOS:
        orden.append(fid)


def _restablecer() -> None:
    for f in FIDS:
        st.session_state[CLAVES[f]] = C.TODOS
    st.session_state["p3_orden"] = []


def _quitar_ultimo() -> None:
    orden = st.session_state.get("p3_orden", [])
    if orden:
        st.session_state[CLAVES[orden.pop()]] = C.TODOS


# --- Filtros: uno por regla de política que Mariana puede mover ----------------
columnas = st.columns(4)
for col, fid in zip(columnas, FIDS):
    with col:
        ui.filtro(fid, CLAVES[fid], on_change=_registrar_cambio, args=(fid,))

filtros = tuple((f, st.session_state[CLAVES[f]]) for f in FIDS)
resumen = servicios.resumen_corte(usuario.rol, filtros)
ui.corte_activo(datos.describir_filtros(dict(filtros)), resumen["n"], resumen["total"],
                extra=f"default {pct(resumen['tasa'])} (CALCULADO sobre REAL)", on_reset=_restablecer, key="p3_reset")

# --- Recorrido de error: corte vacío o con muestra insuficiente ----------------
if resumen["n"] < C.N_MINIMO:
    orden = st.session_state.get("p3_orden", [])
    culpable = f"{C.FILTROS[orden[-1]]['nombre']}: {st.session_state[CLAVES[orden[-1]]]}" if orden else "—"
    k1, k2 = st.columns(2)
    k1.metric("Créditos en el corte · REAL", f"{resumen['n']:,}", border=True)
    k2.metric("Tasa de default", "—", border=True,
              help="Se muestra «—» y no 0%: sin registros suficientes no hay tasa, y un 0% se leería como riesgo nulo.")
    if resumen["n"] == 0:
        ui.estado_vacio("Ningún crédito cumple los filtros",
                        f"El último que aplicaste (**{culpable}**) dejó la selección en 0.",
                        [("Quitar último filtro", _quitar_ultimo), ("Restablecer filtros", _restablecer)], key="p3_vacio")
    else:
        ui.estado_vacio(f"Muestra insuficiente (n = {resumen['n']})",
                        f"Con menos de {C.N_MINIMO} créditos la tasa no tiene sustento y no se muestra. "
                        f"El último filtro aplicado fue **{culpable}**. Ejemplo real: solo 469 créditos tienen "
                        "antecedente de bancarrota; al cruzarlos con más filtros caen fácilmente bajo 30.",
                        [("Quitar último filtro", _quitar_ultimo), ("Restablecer filtros", _restablecer)], key="p3_chica")
    st.stop()

# --- Cruce elegido, KPIs, mapa de calor (G5) y barras (G6) --------------------
CRUCE = {"Bancarrota": ("SEG_BANCARROTA", "F6"), "Enganche": ("SEG_ENGANCHE", "F4"),
         "Pagos fallidos": ("SEG_PAGOS", "F5"), "LTV": ("SEG_LTV", None)}
seleccion = dict(filtros)
filas_dti = C.SEGMENTOS["SEG_DTI"]["orden"] if seleccion["F3"] == C.TODOS else [seleccion["F3"]]

if "p3_c1" not in st.session_state:
    st.session_state["p3_c1"] = C.CONTROLES["C1"]["defecto"]
seg_col, fid_col = CRUCE[st.session_state["p3_c1"]]
cols_orden = C.SEGMENTOS[seg_col]["orden"]
if fid_col and seleccion[fid_col] != C.TODOS:
    cols_orden = [seleccion[fid_col]]
tabla = servicios.tasa_cruzada(usuario.rol, filtros, "SEG_DTI", seg_col)
fuera = tabla[tabla["tasa"] > C.TOLERANCIA_SEGMENTO]
cortes_dti = servicios.cortes_dti()

# --- KPIs del corte -------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
dif_cartera = (resumen["tasa"] - servicios.modelo().tasa_base) * 100
k1.metric("Créditos en el corte", f"{resumen['n']:,}", border=True, help="n REAL de Base_SAS_Equipo3.csv.")
k2.metric("Tasa de default", pct(resumen["tasa"]), border=True,
          delta=f"{dif_cartera:+.1f} pp vs. cartera" if abs(dif_cartera) >= 0.05 else "igual a la cartera",
          delta_color="inverse" if abs(dif_cartera) >= 0.05 else "off",
          delta_arrow="auto" if abs(dif_cartera) >= 0.05 else "off",
          help="CALCULADO: proporción de DEFAULT = 1 (REAL) dentro del corte.")
k3.metric("Tolerancia de la política", f"{C.TOLERANCIA_SEGMENTO:.0%}", border=True,
          help=f"POLÍTICA del equipo. Regla de muestra mínima: n ≥ {C.N_MINIMO} por celda.")
k4.metric("Celdas sobre la tolerancia", f"{len(fuera)} de {int(tabla['suficiente'].sum())}", border=True,
          help="CALCULADO: celdas del mapa de calor con n ≥ 30 y default mayor a la tolerancia.")


izq, der = st.columns([1.3, 1], gap="medium")
with izq, st.container(border=True):
    ui.titulo_grafica("¿Qué combinación supera la tolerancia?", "CALCULADO", "REAL", codigo="G5 · mapa de calor")
    cruce = st.segmented_control(f"C1 · {C.CONTROLES['C1']['nombre']}", C.CONTROLES["C1"]["opciones"],
                                 key="p3_c1", required=True)
    st.caption(ui.amarre("C1"))
    G.mostrar(G.g5_mapa_calor(tabla, filas_dti, cols_orden, "SEG_DTI", seg_col, C.TOLERANCIA_SEGMENTO), key="g5")
    st.caption(f"Filas = terciles de DTI (CALCULADO: cortes {cortes_dti[0]:.1%} y {cortes_dti[1]:.1%}). Borde rojo = supera la "
               f"tolerancia de {C.TOLERANCIA_SEGMENTO:.0%}. Más oscuro = más default. Gris = n < {C.N_MINIMO}.")
    ui.ver_tabla(tabla.assign(tasa=tabla["tasa"].map(pct)).rename(
        columns={"SEG_DTI": "DTI", seg_col: cruce, "tasa": "Default", "n": "n (REAL)", "suficiente": "n ≥ 30"}))

with der, st.container(border=True):
    ui.titulo_grafica("¿Qué historial de pagos concentra más default?", "CALCULADO", "REAL", codigo="G6 · barras ordenadas")
    barras = servicios.tasa_cruzada(usuario.rol, filtros, "SEG_PAGOS", None)
    orden_pagos = C.SEGMENTOS["SEG_PAGOS"]["orden"] if seleccion["F5"] == C.TODOS else [seleccion["F5"]]
    G.mostrar(G.g6_barras_grupo(barras, "SEG_PAGOS", orden_pagos, C.TOLERANCIA_SEGMENTO), key="g6")
    st.caption("Pagos fallidos en los últimos 12 meses (MISSED_PAYMENTS_12M, REAL). " + ui.amarre("F5"))
    ui.ver_tabla(barras.assign(tasa=barras["tasa"].map(pct)).rename(
        columns={"SEG_PAGOS": "Pagos fallidos", "tasa": "Default", "n": "n (REAL)", "suficiente": "n ≥ 30"}))

# --- Curva del corte (G7) ------------------------------------------------------
with st.container(border=True):
    ui.titulo_grafica("Si muevo el corte, ¿cuánta aprobación pierdo y cuánto default evito?", "CALCULADO",
                      codigo="G7 · líneas de trade-off")
    curva, n_hold = servicios.curva_politica(usuario.rol, filtros)
    if curva.empty:
        ui.estado_vacio(f"El segmento tiene solo {n_hold} solicitudes en el holdout",
                        f"La curva se calcula con el 25% de la base que el modelo no vio. Con menos de {C.N_MINIMO} "
                        "casos no es confiable. Quita un filtro para ampliar el segmento.",
                        [("Quitar último filtro", _quitar_ultimo)], key="p3_curva")
    else:
        if "p3_c2" not in st.session_state:
            st.session_state["p3_c2"] = C.CORTE_PD * 100
        corte_pct = st.slider(f"C2 · {C.CONTROLES['C2']['nombre']} para este segmento", 5.0, 30.0, step=0.5,
                              format="%.1f%%", key="p3_c2")
        st.caption(ui.amarre("C2"))
        corte = corte_pct / 100
        g, m = st.columns([1.7, 1], gap="medium")
        with g:
            G.mostrar(G.g7_tradeoff(curva, C.CORTE_PD, corte), key="g7")

        def _en(c):
            return curva.iloc[(curva["corte"] - c).abs().argmin()]

        actual, propuesto = _en(C.CORTE_PD), _en(corte)
        with m:
            st.markdown(f"**Impacto en este segmento** (holdout, n = {n_hold:,})")
            d_ap = (propuesto["aprobacion"] - actual["aprobacion"]) * 100
            d_def = (propuesto["default_aprobados"] - actual["default_aprobados"]) * 100
            igual = abs(corte - C.CORTE_PD) < 0.004
            st.metric("Aprobación", pct(propuesto["aprobacion"]),
                      delta="igual al corte actual" if igual else f"{d_ap:+.1f} pp vs. corte actual",
                      delta_color="off" if igual else "normal", delta_arrow="off" if igual else "auto")
            st.metric("Default entre aprobados", pct(propuesto["default_aprobados"]),
                      delta="igual al corte actual" if igual else f"{d_def:+.1f} pp vs. corte actual",
                      delta_color="off" if igual else "inverse", delta_arrow="off" if igual else "auto")
            evitados = propuesto["defaults_evitados_1000"] - actual["defaults_evitados_1000"]
            perdidos = propuesto["buenos_rechazados_1000"] - actual["buenos_rechazados_1000"]
            st.markdown(f"Por cada 1,000 solicitudes: **{evitados:+.0f}** defaults evitados y **{perdidos:+.0f}** "
                        "buenos clientes rechazados frente al corte actual.")
        st.caption("La PD es del modelo entrenado con el 75% de la base; la curva se mide sobre el 25% restante "
                   "(REAL, nunca visto por el modelo). Dos paneles con el mismo eje X para no usar doble eje Y.")

        # --- Exportar propuesta: solo agregados --------------------------------
        propuesta = pd.DataFrame([{
            "fecha": date.today().isoformat(), "autor": usuario.nombre_corto,
            "segmento": datos.describir_filtros(dict(filtros)), "n_base": resumen["n"],
            "default_observado": round(resumen["tasa"], 4), "n_holdout": n_hold,
            "corte_actual": C.CORTE_PD, "corte_propuesto": round(corte, 3),
            "aprobacion_actual": round(actual["aprobacion"], 4), "aprobacion_propuesta": round(propuesto["aprobacion"], 4),
            "default_aprobados_actual": round(actual["default_aprobados"], 4),
            "default_aprobados_propuesto": round(propuesto["default_aprobados"], 4),
            "defaults_evitados_por_1000": round(evitados, 1), "buenos_rechazados_por_1000": round(perdidos, 1),
            "celdas_fuera_de_tolerancia": "; ".join(f"DTI {r['SEG_DTI']} × {r[seg_col]} ({r['tasa']:.1%}, n={r['n']})"
                                                    for _, r in fuera.iterrows()) or "ninguna",
        }])
        st.download_button("Exportar propuesta para el comité (solo agregados)", propuesta.to_csv(index=False).encode("utf-8"),
                           file_name=f"propuesta_politica_{date.today():%Y%m%d}.csv", mime="text/csv",
                           type="primary", icon=":material/download:")

st.caption("Los filtros activos aplican a las tres gráficas y cada una recalcula su n. Una celda o barra con "
           f"n < {C.N_MINIMO} se pinta gris con «muestra insuficiente».")
ui.pie_origen("Mapa de calor y barras: tasas reales de las 80,000 filas.")
