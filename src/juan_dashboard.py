"""Vista de gerencia: KPIs reales agregados de TRAIN 12V, con referencias y metas explícitas."""
from __future__ import annotations
import base64
import gzip
import json
import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src import config as C, juan_politica as politica

RUTA = Path(__file__).resolve().parents[1] / "data" / "juan_agregados_12v.b64"
DTI = ["Bajo", "Medio", "Alto"]
MONTOS = ["Hasta 10 mil", "10–20 mil", "20–35 mil", "Más de 35 mil"]

@st.cache_data(show_spinner=False)
def datos_agregados():
    obj = json.loads(gzip.decompress(base64.b64decode(RUTA.read_text().strip())))
    df = pd.DataFrame(obj["data"], columns=obj["fields"])
    if obj["partition"] != "TRAIN" or obj["rows"] != 80000 or int(df.n.sum()) != 80000 or int(df.defaults.sum()) != 10783:
        raise ValueError("El agregado no coincide con TRAIN")
    return df, obj

def calcular(df):
    n = int(df.n.sum())
    bad = int(df.defaults.sum())
    return dict(n=n, bad=bad,
                tasa=bad/n if n else math.nan,
                dti=float(df.dti_sum.sum())/n if n else math.nan,
                monto=float(df.amount_sum.sum())/n if n else math.nan)

def porcentaje(x):
    return f"{x:.2%}" if math.isfinite(x) else "—"

def estado(valor, meta):
    if meta is None or not math.isfinite(valor):
        return "Sin meta aprobada"
    return "Dentro de meta" if valor <= meta else "Fuera de meta"

def kpi(pregunta, valor, explicacion, referencia, semaforo="Referencia descriptiva", diferencia=None):
    with st.container(border=True):
        st.caption(pregunta)
        st.metric("Indicador", valor, delta=diferencia,
                  delta_color="off", label_visibility="collapsed")
        if semaforo == "Dentro de meta":
            st.badge(semaforo, color="green")
        elif semaforo == "Fuera de meta":
            st.badge(semaforo, color="red")
        elif semaforo == "Muestra insuficiente":
            st.badge(semaforo, color="orange")
        else:
            st.badge(semaforo, color="gray")
        st.caption(explicacion)
        st.caption("Referencia: " + referencia)

def configurar_metas(usuario):
    try:
        metas = politica.leer_metas()
    except Exception as exc:
        st.error(f"No se pudieron leer las metas del tablero ({type(exc).__name__}).")
        return {}
    with st.popover("Metas de gerencia", icon=":material/tune:", use_container_width=True):
        st.markdown("**Control de metas de seguimiento**")
        st.caption("Son propuestas, no límites regulatorios ni reglas de aprobación. "
                   "Si una meta está desactivada, el KPI no se pinta rojo o verde.")
        with st.form("juan_metas_form"):
            nuevas = {}
            for clave, etiqueta in [
                ("incumplimiento","Máximo incumplimiento (%)"),
                ("dti","Máximo DTI medio (%)"),
                ("dti_alto","Máximo incumplimiento DTI alto (%)"),
            ]:
                usar = st.checkbox("Activar: " + etiqueta, value=clave in metas, key=f"juan_use_{clave}")
                v = st.number_input(etiqueta, min_value=0.0, max_value=100.0,
                                    value=round(metas[clave]*100, 2) if clave in metas else 0.0,
                                    step=0.25, format="%.2f", disabled=not usar, key=f"juan_meta_{clave}")
                nuevas[clave] = v / 100 if usar else None
            if st.form_submit_button("Guardar y avisar", type="primary"):
                try:
                    if politica.guardar_metas(nuevas, usuario.nombre):
                        st.success("Metas actualizadas; aviso emitido para los analistas.")
                    else:
                        st.info("Sin cambios.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"No se pudo guardar: {type(exc).__name__}.")
    return metas

def avisos_analista(usuario):
    try:
        avisos = politica.avisos_no_leidos(usuario.email)
    except Exception:
        st.warning("El sistema de avisos gerenciales no está disponible.")
        return
    if not avisos:
        return
    st.error(f"Hay {len(avisos)} cambio(s) gerenciales sin leer.", icon=":material/notification_important:")
    with st.expander("Cambios de metas (requieren lectura)", expanded=True):
        for a in avisos:
            st.markdown(f"**{a['fecha']} · {a['autor']}** — {a['texto']}")
        if st.button("Confirmar lectura", key="juan_confirmar_aviso"):
            politica.marcar_leidos(usuario.email)
            st.rerun()
        st.caption("Notificación de una meta de seguimiento; no implica modificar un expediente.")

def mostrar_gerente(usuario):
    try:
        df, metadatos = datos_agregados()
    except Exception as exc:
        st.error(f"Agregados de TRAIN no disponibles ({type(exc).__name__}). No se mostrarán cifras estimadas.")
        return

    base = calcular(df)
    st.subheader("Cartera histórica · decisiones de negocio")
    st.caption("TRAIN: 80,000 registros ya imputados · 12 predictoras incluida LOAN_AMOUNT. "
               "Valores históricos, no cartera en tiempo real.")
    c1,c2,c3,c4,c5 = st.columns([1.05,1.05,1.05,0.9,1.20], gap="small")
    with c1:
        monto = st.selectbox("Monto de crédito", ["Todos"]+MONTOS, key="juan_monto")
    with c2:
        pagos = st.selectbox("Pagos atrasados",["Todos","0","1","2 o más"], key="juan_pagos")
    with c3:
        banc = st.selectbox("Bancarrota",["Todos","Sin antecedente","Con antecedente"],key="juan_banc")
    with c4:
        grupo = st.selectbox("DTI",["Todos"]+DTI,key="juan_dti")
    with c5:
        st.caption("Configuración")
        metas = configurar_metas(usuario)

    f = df.copy()
    for clave, valor in [("amount_band",monto),("missed_group",pagos),("bankruptcy",banc),("dti_seg",grupo)]:
        if valor != "Todos":
            f = f.loc[f[clave] == valor]
    v = calcular(f)
    st.caption(f"Selección: **{v['n']:,} de {base['n']:,} registros** ({v['n']/base['n']:.1%}). "
               "La referencia histórica corresponde siempre a TRAIN completo.")
    if v["n"] < C.N_MINIMO:
        st.error(f"Muestra insuficiente (n={v['n']}). Amplía filtros: no se publican tasas con menos de {C.N_MINIMO} registros.",
                 icon=":material/warning:")
        return

    alto = calcular(f[f.dti_seg == "Alto"])
    alto_base = calcular(df[df.dti_seg == "Alto"])
    if len(metas) < 3:
        st.warning("No hay meta aprobada para todos los KPI. Gerencia puede definir metas arriba; "
                   "hasta entonces se muestra el benchmark sin semáforo de cumplimiento.",
                   icon=":material/notification_important:")

    cols = st.columns(4, gap="small")
    with cols[0]:
        kpi("1. ¿Cuánto volumen crediticio analizamos?", f"{v['n']:,}",
            f"{v['n']/base['n']:.1%} de la muestra histórica.",
            f"{base['n']:,} registros de TRAIN")
    with cols[1]:
        kpi("2. ¿Cuál fue la tasa de incumplimiento?", porcentaje(v['tasa']),
            f"{v['bad']:,} incumplimientos / {v['n']:,} registros.",
            f"TRAIN {porcentaje(base['tasa'])}; meta: {porcentaje(metas['incumplimiento']) if 'incumplimiento' in metas else 'no definida'}",
            estado(v['tasa'],metas.get("incumplimiento")),
            f"{(v['tasa']-base['tasa'])*100:+.2f} pp vs. TRAIN")
    with cols[2]:
        kpi("3. ¿Cuál es el endeudamiento DTI?", porcentaje(v['dti']),
            "Media de la razón deuda/ingreso del corte.",
            f"TRAIN {porcentaje(base['dti'])}; meta: {porcentaje(metas['dti']) if 'dti' in metas else 'no definida'}",
            estado(v['dti'],metas.get("dti")),
            f"{(v['dti']-base['dti'])*100:+.2f} pp vs. TRAIN")
    with cols[3]:
        ok_alto = alto["n"] >= C.N_MINIMO
        kpi("4. ¿Qué incumplimiento tiene DTI alto?",
            porcentaje(alto["tasa"]) if ok_alto else "—",
            f"{alto['bad']:,} incumplimientos / {alto['n']:,} registros DTI alto.",
            f"DTI alto TRAIN: {porcentaje(alto_base['tasa'])}; meta: {porcentaje(metas['dti_alto']) if 'dti_alto' in metas else 'no definida'}",
            estado(alto['tasa'],metas.get("dti_alto")) if ok_alto else "Muestra insuficiente")

    alertas = []
    for titulo, val, meta in [
        ("Incumplimiento", v["tasa"], metas.get("incumplimiento")),
        ("DTI promedio", v["dti"], metas.get("dti")),
        ("Incumplimiento DTI alto", alto["tasa"] if alto["n"]>=C.N_MINIMO else math.nan, metas.get("dti_alto")),
    ]:
        if estado(val,meta) == "Fuera de meta":
            alertas.append(f"{titulo}: {porcentaje(val)} frente a meta {porcentaje(meta)}.")
    if alertas:
        st.error("**Atención: se superan los límites de seguimiento.** " + " ".join(alertas)
                 + " La gerente debe revisar el segmento antes de proponer cambios.",icon=":material/warning:")

    st.caption(f"**Monto medio solicitado:** {v['monto']:,.0f} unidades monetarias del archivo; "
               f"TRAIN completo: {base['monto']:,.0f}. "
               "No se atribuye una moneda porque no figura explícita en el CSV.")

    t1,t2,t3,t4 = st.tabs(["Monto de crédito","Resultado histórico","DTI frente a media","Riesgo por segmento"])
    with t1:
        g=f.groupby("amount_band")[["n","defaults"]].sum().reindex(MONTOS,fill_value=0)
        fig=go.Figure(go.Bar(x=g.index.tolist(),y=g.n.tolist(),
              text=[f"{int(x):,}" for x in g.n],textposition="auto",marker_color="#6FAFE0"))
        fig.update_layout(title="Registros por monto de crédito",yaxis_title="Registros",height=320)
        st.plotly_chart(fig,use_container_width=True,key="juan_amount")
        st.caption("Bandas descriptivas, no umbrales de autorización de préstamos.")
    with t2:
        fig=go.Figure(go.Pie(labels=["Sin incumplimiento","Incumplimiento"],
              values=[v['n']-v['bad'],v['bad']],hole=.60,textinfo="label+percent"))
        fig.update_layout(title="Resultado del corte seleccionado",height=320,showlegend=False)
        st.plotly_chart(fig,use_container_width=True,key="juan_default")
    with t3:
        g=f.groupby("dti_seg")[["n","dti_sum"]].sum().reindex(DTI,fill_value=0)
        y=[g.loc[x,"dti_sum"]/g.loc[x,"n"]*100 if g.loc[x,"n"]>=C.N_MINIMO else None for x in DTI]
        fig=go.Figure(go.Bar(x=DTI,y=y,marker_color="#74C3B3"))
        fig.add_hline(y=base["dti"]*100,line_dash="dash",
                      annotation_text="Media TRAIN")
        fig.update_layout(title="DTI promedio por tercil",yaxis_title="DTI (%)",height=320)
        st.plotly_chart(fig,use_container_width=True,key="juan_dtiseg")
    with t4:
        g=f.groupby("dti_seg")[["n","defaults"]].sum().reindex(DTI,fill_value=0)
        y=[g.loc[x,"defaults"]/g.loc[x,"n"]*100 if g.loc[x,"n"]>=C.N_MINIMO else None for x in DTI]
        fig=go.Figure(go.Bar(x=DTI,y=y,marker_color="#E5AA76",
              text=[f"{x:.1f}%" if x is not None else "n < 30" for x in y],textposition="auto"))
        fig.add_hline(y=base["tasa"]*100,line_dash="dash",annotation_text="Media TRAIN")
        fig.update_layout(title="Incumplimiento histórico por DTI",yaxis_title="Tasa (%)",height=320)
        st.plotly_chart(fig,use_container_width=True,key="juan_risk")
    with st.expander("Metodología y trazabilidad"):
        st.dataframe(pd.DataFrame([
            ["Registros","Suma de registros del corte","TRAIN real"],
            ["Incumplimiento","Suma(DEFAULT=1) / total de registros","Histórico, no una PD"],
            ["DTI medio","Suma(DEBT_TO_INCOME) / total de registros","Histórico"],
            ["DTI alto","Incumplimientos en tercil alto / registros en tercil alto","n ≥ 30"],
            ["Monto","Suma(LOAN_AMOUNT) / registros","Variable incorporada, 12V"],
        ],columns=["Indicador","Cálculo","Interpretación"]),hide_index=True)
        st.caption(f"Cortes de DTI: {metadatos['dti_cuts'][0]:.2%}, {metadatos['dti_cuts'][1]:.2%}. "
                   f"SHA256 del CSV: {metadatos['sha256']}. "
                   "No hay fechas para inferir tendencias. Metas propuestas: no son decisiones reales de crédito. "
                   "Los avisos se guardan en SQLite local de demostración y podrían perderse si Streamlit Cloud reinicia. "
                   "Las tasas por grupos menores de n=30 se ocultan.")
