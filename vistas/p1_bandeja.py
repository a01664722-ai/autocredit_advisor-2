"""P1 · Bandeja de solicitudes · Adrián (analista).
Decisión: ¿qué solicitud atiendo primero?"""
from datetime import date

import pandas as pd
import streamlit as st

from src import almacen, auth, config as C, servicios, ui
from src.simulacion import texto_hace

usuario = auth.exigir_acceso("P1")
from src.juan_dashboard import avisos_analista

# Primer vistazo: KPI antes del título. Ninguna meta ausente se presenta como cumplida.
cola, _ = servicios.cola_analista(usuario)
hoy = date.today().isoformat()
decididas = almacen.decisiones(fecha=hoy, analista_id=usuario.analista_id)

st.markdown("""
<style>
.block-container {padding-top: 1rem !important;}
div.st-key-p1_editor [data-testid="stDataFrame"] {font-size: .88rem;}
div.st-key-p1_editor {border-radius: 10px;}
[data-testid="stAlert"] {border-width: 2px !important;}
</style>""", unsafe_allow_html=True)

n_pendientes = int(cola["ESTADO_SOLICITUD"].eq("Pendiente").sum())
n_espera = int(cola["ESTADO_SOLICITUD"].eq("En espera de documento").sum())
n_resueltas = len(decididas)
minutos = float(decididas["duracion_seg"].median() / 60) if n_resueltas else None

st.caption("Resumen operativo · mi bandeja*")
k1, k2, k3, k4 = st.columns(4, gap="small")
k1.metric("Pendientes*", n_pendientes, border=True, help="Casos asignados y sin resolver; meta de volumen no definida.")
k2.metric("Documentos pendientes*", n_espera, border=True, help="Casos que requieren documentación adicional.")
k3.metric("Resueltas hoy", n_resueltas, border=True, help="Decisiones registradas en la bitácora de esta demostración.")
k4.metric("Tiempo mediano", f"{minutos:.1f} min" if minutos is not None else "—",
          delta=(f"{minutos - C.META_MINUTOS_DECISION:+.1f} min vs meta" if minutos is not None else None),
          delta_color="inverse", border=True,
          help=f"Meta operativa propuesta: {C.META_MINUTOS_DECISION} min. Sin registros se muestra —.")
if minutos is not None and minutos > C.META_MINUTOS_DECISION:
    st.error(f"Atención: tiempo mediano {minutos:.1f} min, por encima de la meta propuesta "
             f"de {C.META_MINUTOS_DECISION} min.", icon=":material/warning:")
elif n_espera:
    st.warning(f"{n_espera} solicitudes necesitan seguimiento documental.", icon=":material/report:")
st.title("Bandeja de solicitudes")
st.caption(f"Analista: {usuario.nombre} · Solo casos asignados a {usuario.analista_id} · "
           "Modelo de PD: regresión logística de demostración, no el campeón de SAS.")
avisos_analista(usuario)

# --- Filtros (cada uno amarrado a una decisión de Adrián) ----------------------
def _restablecer():
    st.session_state["p1_f1"] = C.FILTROS["F1"]["defecto"]
    st.session_state["p1_f2"] = list(C.FILTROS["F2"]["defecto"])


f1, f2 = st.columns([1.25, 1])
with f1:
    estado = ui.filtro("F1", "p1_f1", widget="segmented", required=True)
with f2:
    niveles = ui.filtro("F2", "p1_f2", widget="pills")

vista = cola[(cola["ESTADO_SOLICITUD"] == estado) & (cola["NIVEL"].isin(niveles or []))]
orden = st.selectbox("Orden de atención", ["Mayor riesgo primero", "Más antigua primero"],
                     label_visibility="collapsed", key="p1_orden",
                     help="El orden representa prioridades de revisión, no autorizaciones automáticas.")
if orden == "Más antigua primero":
    vista = vista.sort_values(["RECIBIDA_MIN", "PD"], ascending=[False, False], na_position="last")
else:
    vista = vista.sort_values(["PD", "RECIBIDA_MIN"], ascending=[False, False], na_position="last")
ui.corte_activo(f"Estado: {estado} · Riesgo: {', '.join(niveles) if niveles else 'ninguno'}",
                len(vista), len(cola), extra="casos asignados*",
                on_reset=_restablecer, key="p1_reset")

if not niveles:
    ui.estado_vacio("No elegiste ningún nivel de riesgo",
                    "Con el filtro F2 vacío no hay solicitudes que mostrar. Elige al menos un nivel o restablece.",
                    [("Restablecer filtros", _restablecer)], key="p1_sin_nivel")
elif vista.empty and estado == "Pendiente" and len(niveles) == 3:
    ui.estado_vacio("No tienes solicitudes pendientes",
                    "Todo lo asignado a tu ANALISTA_ID está resuelto o en espera de documento.",
                    [("Ver en espera de documento",
                      lambda: st.session_state.update(p1_f1="En espera de documento"))], key="p1_vacia")
elif vista.empty:
    ui.estado_vacio("Ninguna solicitud cumple los filtros",
                    f"No hay solicitudes «{estado}» con riesgo {', '.join(niveles)}.",
                    [("Restablecer filtros", _restablecer)], key="p1_sin_match")
else:
    st.markdown("**Solicitudes y decisión rápida**")
    st.caption("Selecciona una acción directamente en la fila. Se abrirá la ficha para validar "
               "la información y confirmar: seleccionar no registra una decisión.")

    def _semaforo(x):
        return {"Rechazar": "🔴 Rechazar", "Condicionar": "🟡 Condicionar",
                "Aprobar": "🟢 Aprobar", "Revisión manual": "⚠ Revisar"}.get(x, "—")

    tabla = pd.DataFrame({
        "Folio": vista["FOLIO"].astype(str).to_numpy(),
        "Recibida*": vista["RECIBIDA_MIN"].map(texto_hace).to_numpy(),
        "PD**": (vista["PD"] * 100).to_numpy(),
        "Riesgo": vista["NIVEL"].to_numpy(),
        "Calidad": vista["CALIDAD"].to_numpy(),
        "Sugerencia": vista["SUGERENCIA"].map(_semaforo).to_numpy(),
        "DTI": vista["DEBT_TO_INCOME"].map(lambda v: "—" if pd.isna(v) else f"{v:.0%}").to_numpy(),
        "LTV": vista["LOAN_TO_VALUE"].map(lambda v: "—" if pd.isna(v) else f"{v:.0%}").to_numpy(),
        "Acción": ["Seleccionar…"] * len(vista),
    })
    id_real = bool(vista["ID_REAL"].all()) if "ID_REAL" in vista else False
    tabla.rename(columns={"Folio": "Loan ID" if id_real else "Folio*"}, inplace=True)
    id_col = "Loan ID" if id_real else "Folio*"

    # La tabla es interactiva: cada fila ofrece una decisión independiente.
    # El selector es solo un borrador; la ficha exige validación y confirmación.
    editada = st.data_editor(
        tabla, hide_index=True, key="p1_editor", width="stretch",
        height=min(600, 42 * min(len(tabla), 11) + 40),
        disabled=[c for c in tabla.columns if c != "Acción"],
        column_config={
            id_col: st.column_config.TextColumn(id_col, width="medium"),
            "Recibida*": st.column_config.TextColumn("Recibida*", width="small"),
            "PD**": st.column_config.ProgressColumn("PD** · Logit", format="%.1f%%",
                                                     min_value=0, max_value=100, width="medium"),
            "Riesgo": st.column_config.TextColumn("Riesgo", width="small"),
            "Sugerencia": st.column_config.TextColumn("Sugerencia", width="medium"),
            "DTI": st.column_config.TextColumn("DTI", width="small"),
            "LTV": st.column_config.TextColumn("LTV", width="small"),
            "Acción": st.column_config.SelectboxColumn(
                "Decisión rápida", options=["Seleccionar…", "Aprobar", "Condicionar",
                                            "Rechazar", "Ver detalle"], required=True, width="medium"),
        },
    )
    for pos, fila_editada in editada.iterrows():
        accion = fila_editada["Acción"]
        if accion != "Seleccionar…":
            elegido = str(fila_editada[id_col])
            st.session_state["folio_actual"] = elegido
            if accion != "Ver detalle":
                st.session_state[f"dec_{elegido}"] = accion
            st.switch_page("vistas/p2_ficha.py")

    fuera = vista[(vista["NIVEL"] == "Alto") | (vista["CALIDAD"] != "Completo")]
    if len(fuera):
        with st.expander(f"Casos que requieren atención ({len(fuera)})"):
            st.warning("Se priorizan los casos de riesgo alto o datos incompletos. "
                       "Una recomendación del modelo nunca sustituye la verificación de documentos.",
                       icon=":material/warning:")
            st.dataframe(fuera[["FOLIO", "NIVEL", "CALIDAD", "SUGERENCIA"]]
                         .rename(columns={"FOLIO": id_col, "NIVEL": "Riesgo",
                                          "CALIDAD": "Calidad", "SUGERENCIA": "Sugerencia"}),
                         hide_index=True, width="stretch")

    st.caption("Fuente y notación: * dato operativo simulado (folio, fecha de recepción y asignación); "
               "** probabilidad calculada por la regresión logística demostrativa. "
               "Los valores DTI y LTV proceden de registros históricos; las excepciones se simulan. "
               "El identificador es real exclusivamente cuando figura como Loan ID en el CSV fuente.")

st.caption("Orden ajustable: riesgo mayor o recepción más antigua. "
           "Algunas solicitudes son demostrativas; ninguna aprobación se registra desde la tabla.")
