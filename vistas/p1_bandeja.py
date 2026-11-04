"""P1 · Bandeja de solicitudes · Adrián (analista).
Decisión: ¿qué solicitud atiendo primero?"""
from datetime import date

import pandas as pd
import streamlit as st

from src import almacen, auth, config as C, servicios, ui
from src.simulacion import texto_hace

usuario = auth.exigir_acceso("P1")
ui.cabecera("P1", usuario, extra=f"Solo ves lo asignado a **{usuario.analista_id}**")

cola, _ = servicios.cola_analista(usuario)
hoy = date.today().isoformat()
decididas = almacen.decisiones(fecha=hoy, analista_id=usuario.analista_id)

# --- KPIs ----------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Pendientes", int((cola["ESTADO_SOLICITUD"] == "Pendiente").sum()), border=True,
              help="Solicitudes asignadas a tu ANALISTA_ID que esperan decisión. SIMULADO.")
with k2:
    st.metric("En espera de documento", int((cola["ESTADO_SOLICITUD"] == "En espera de documento").sum()),
              border=True, help="Pediste un documento porque faltaba un dato clave. SIMULADO.")
with k3:
    st.metric("Resueltas hoy", len(decididas), border=True,
              help="Decisiones que guardaste hoy en la ficha (REAL en bitácora).")
with k4:
    if len(decididas):
        minutos = decididas["duracion_seg"].median() / 60
        st.metric("Tiempo mediano por decisión", f"{minutos:.1f} min", border=True,
                  delta=f"meta < {C.META_MINUTOS_DECISION} min", delta_color="off",
                  help="Desde que abres la ficha hasta que guardas. REAL en bitácora.")
    else:
        st.metric("Tiempo mediano por decisión", "—", border=True,
                  help=f"Aparece al guardar tu primera decisión. Meta: menos de {C.META_MINUTOS_DECISION} min.")

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
vista = vista.sort_values(["PD", "RECIBIDA_MIN"], ascending=[False, False])
ui.corte_activo(f"Estado = {estado} · Riesgo = {', '.join(niveles) if niveles else 'ninguno'}",
                len(vista), len(cola), extra="solicitudes asignadas a ti (SIMULADO)",
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
    ui.titulo_grafica("¿Qué solicitud reviso primero?", "SIMULADO", "CALCULADO", "REAL", codigo="G4 · tabla con mini-barra")
    tabla = pd.DataFrame({
        "Folio": vista["FOLIO"],
        "Recibida": vista["RECIBIDA_MIN"].map(texto_hace),
        "PD": vista["PD"] * 100,
        "Nivel": vista["NIVEL"],
        "Datos": vista["CALIDAD"],
        "Sugerencia del modelo": vista["SUGERENCIA"],
        "DTI": vista["DEBT_TO_INCOME"].map(lambda v: "falta" if pd.isna(v) else f"{v:.0%}"),
        "LTV": vista["LOAN_TO_VALUE"].map(lambda v: "falta" if pd.isna(v) else f"{v:.0%}"),
    })
    seleccion = st.dataframe(
        tabla, hide_index=True, on_select="rerun", selection_mode="single-row", key="p1_tabla",
        column_config={
            "Folio": st.column_config.TextColumn("Folio (SIMULADO)", help="Completo porque es tu caso (matriz F)."),
            "Recibida": st.column_config.TextColumn("Recibida (SIMULADO)"),
            "PD": st.column_config.ProgressColumn("PD (CALCULADO)", format="%.1f%%", min_value=0,
                                                  max_value=C.ESCALA_PD_MAX * 100),
            "Datos": st.column_config.TextColumn("Calidad de datos", help="Incompleto o Fuera de rango abren un "
                                                 "estado de excepción en la ficha."),
            "DTI": st.column_config.TextColumn("DTI (REAL)"),
            "LTV": st.column_config.TextColumn("LTV (REAL)"),
        },
    )
    filas = seleccion.selection.rows if seleccion else []
    if filas:
        st.session_state["folio_actual"] = tabla.iloc[filas[0]]["Folio"]
        st.switch_page("vistas/p2_ficha.py")

    def _abrir_primera():
        st.session_state["folio_actual"] = tabla.iloc[0]["Folio"]

    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button(f"Abrir la de mayor prioridad ({tabla.iloc[0]['Folio']})", type="primary",
                     icon=":material/arrow_forward:", on_click=_abrir_primera):
            st.switch_page("vistas/p2_ficha.py")
        st.caption("o selecciona una fila para abrir su ficha.")

st.caption(
    f"Orden por defecto: PD de mayor a menor; en empate, la más antigua primero. Solo aparecen las solicitudes "
    f"asignadas a tu ANALISTA_ID (filtro en el servidor). Nivel de riesgo: Bajo < {C.LIMITE_RIESGO_BAJO:.0%} ≤ "
    f"Medio < {C.CORTE_PD:.0%} (corte) ≤ Alto. Barra = PD en escala 0–{C.ESCALA_PD_MAX:.0%}."
)
ui.pie_origen("Las variables de cada solicitud son filas REAL del 25% de la base que el modelo no vio al entrenar; "
              "folio, hora y los tres casos con dato faltante o fuera de rango son SIMULADOS.")
