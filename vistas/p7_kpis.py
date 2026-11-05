"""P7 · KPIs diferentes por rol, sin compartir datos individuales.

Analista: bandeja DEMO filtrada por ANALISTA_ID.
Gerente: agregados históricos de la base REAL.
Operación: calidad de la base REAL; no se mezclan con alertas SIMULADAS.
"""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from src import auth, config as C, servicios, ui

usuario = auth.exigir_acceso("P7")
ui.cabecera("P7", usuario, extra="KPI específicos de tu función; las fuentes aparecen en cada tarjeta")


def tarjetas(datos: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(datos), gap="medium")
    for col, (nombre, valor, explicacion) in zip(cols, datos):
        with col:
            st.metric(nombre, valor, help=explicacion, border=True)


if usuario.rol == "analista":
    # La función aplica el filtro de ANALISTA_ID antes de obtener la bandeja.
    indicadores = servicios.indicadores_bandeja(usuario)
    st.subheader(f"Mi bandeja · {usuario.nombre}")
    ui.origen("SIMULADO", "CALCULADO")
    tarjetas([
        ("Solicitudes asignadas", f"{indicadores['solicitudes']:,}",
         "SIMULADO · Solicitudes de la cola de demostración asignada exclusivamente a este analista."),
        ("Pendientes de atender", f"{indicadores['pendientes']:,}",
         "SIMULADO / BITÁCORA · Conteo de la bandeja con ESTADO_SOLICITUD = 'Pendiente'."),
        ("Casos con datos por revisar", f"{indicadores['revisar_datos']:,}",
         "CALCULADO / SIMULADO · Calidad distinta de 'Completo'; requiere verificar datos antes de decidir."),
    ])
    st.info(
        "Esta es una bandeja de demostración: los atributos financieros proceden de filas de la base, "
        "pero los folios, asignaciones, fechas y excepciones son **SIMULADOS**. "
        "Estos KPI no representan solicitudes reales recibidas por la institución."
    )
    st.caption(
        "**Decisión:** priorizar pendientes y revisar información incompleta antes de resolver. "
        "Los analistas no reciben DEFAULT histórico ni métricas agregadas de otros analistas."
    )
    metodologia = [
        {"KPI": "Solicitudes asignadas", "Fórmula": "Número de filas de MI bandeja", "Origen": "SIMULADO"},
        {"KPI": "Pendientes de atender", "Fórmula": "Conteo(ESTADO_SOLICITUD = Pendiente)", "Origen": "SIMULADO / BITÁCORA"},
        {"KPI": "Casos con datos por revisar", "Fórmula": "Conteo(CALIDAD != Completo)", "Origen": "CALCULADO / SIMULADO"},
    ]

elif usuario.rol == "gerente":
    indicadores = servicios.indicadores_base(usuario.rol)
    st.subheader("Panorama histórico del conjunto crediticio")
    ui.origen("REAL", "CALCULADO")
    tasa = indicadores["tasa_default"]
    dti = indicadores["dti_promedio"]
    # Juan: segmentación ya existente y autorizada para el rol gerente.
    tabla_dti = servicios.tasa_cruzada(usuario.rol, tuple(), "SEG_DTI", None)
    tabla_dti = tabla_dti.set_index("SEG_DTI").reindex(C.SEGMENTOS["SEG_DTI"]["orden"])
    tasa_dti_alto = float(tabla_dti.loc["Alto", "tasa"])
    tarjetas([
        ("Registros crediticios", f"{indicadores['registros']:,}",
         "REAL · Número de filas del CSV, no necesariamente créditos únicos."),
        ("Tasa histórica de incumplimiento", f"{tasa:.2%}" if math.isfinite(tasa) else "—",
         "CALCULADO / REAL · DEFAULT = 1 dividido entre DEFAULT con dato válido."),
        ("DTI promedio", f"{dti:.2%}" if math.isfinite(dti) else "—",
         "CALCULADO / REAL · Promedio de DEBT_TO_INCOME. Es una medida descriptiva de endeudamiento."),
        ("Default con DTI alto", f"{tasa_dti_alto:.2%}" if math.isfinite(tasa_dti_alto) else "—",
         "CALCULADO / REAL · Proporción de DEFAULT = 1 en el tercil más alto de DTI (n ≥ 30)."),
    ])
    st.caption(
        f"Fuente: Base_SAS_Equipo3.csv · {indicadores['incumplimientos']:,} resultados DEFAULT = 1 "
        f"de {indicadores['default_validos']:,} con resultado válido. "
        "Sin fecha ni identificador de solicitud no es posible interpretar estos datos como cartera vigente o tendencia."
    )
    st.caption("**Decisión:** dimensionar la exposición histórica y priorizar análisis de segmentos antes de modificar la política crediticia.")

    # Juan: cada pregunta tiene su KPI y una visualización específica (solo agregados).
    import plotly.graph_objects as go

    st.subheader("Cuatro preguntas de negocio")
    panel1, panel2 = st.columns(2, gap="medium")
    panel3, panel4 = st.columns(2, gap="medium")

    with panel1, st.container(border=True):
        st.markdown("**1. ¿Cómo se distribuye el endeudamiento histórico (DTI)?**")
        st.metric("KPI · Registros crediticios", f"{indicadores['registros']:,}")

        from src import datos
        import numpy as np

        dti_real = pd.to_numeric(
            datos.leer_base()["DEBT_TO_INCOME"], errors="coerce"
        ).dropna() * 100

        if not dti_real.empty:
            frecuencias, limites = np.histogram(dti_real, bins=20)

            fig_volumen = go.Figure(go.Bar(
                x=(limites[:-1] + limites[1:]) / 2,
                y=frecuencias,
                width=np.diff(limites)
            ))
            fig_volumen.update_layout(
                title="Distribución real del endeudamiento",
                xaxis_title="DTI (%)",
                yaxis_title="Número de registros",
                bargap=0, height=330,
                margin=dict(l=20, r=20, t=55, b=25)
            )
            st.plotly_chart(fig_volumen, use_container_width=True,
                            key="juan_volumen")
        else:
            st.info("No hay valores válidos de DTI.")

        st.caption(
            "Decisión: identificar en qué rangos se concentra el "
            "endeudamiento histórico. Fuente: CSV REAL."
        )

    with panel2, st.container(border=True):
        st.markdown("**2. ¿Qué proporción terminó en incumplimiento?**")
        st.metric("KPI · Tasa histórica de default", f"{tasa:.2%}" if math.isfinite(tasa) else "—")
        sin_default = indicadores["default_validos"] - indicadores["incumplimientos"]
        fig_default = go.Figure(go.Pie(
            labels=["Sin incumplimiento", "Incumplimiento"],
            values=[sin_default, indicadores["incumplimientos"]],
            hole=0.58, textinfo="label+percent"
        ))
        fig_default.update_layout(
            title="Distribución histórica de DEFAULT",
            height=330, margin=dict(l=20, r=20, t=55, b=25), showlegend=False
        )
        st.plotly_chart(fig_default, use_container_width=True, key="juan_default")
        st.caption("Decisión: dimensionar el riesgo observado. Se cuentan únicamente resultados DEFAULT válidos.")

    with panel3, st.container(border=True):
        st.markdown("**3. ¿Cuál es el endeudamiento promedio (DTI)?**")
        st.metric("KPI · DTI promedio", f"{dti:.2%}" if math.isfinite(dti) else "—")
        if math.isfinite(dti):
            corte_bajo, corte_alto = servicios.cortes_dti()
            fig_dti_prom = go.Figure(go.Indicator(
                mode="gauge+number", value=round(dti * 100, 2),
                number={"suffix": "%"},
                gauge={"axis": {"range": [0, max(100.0, dti * 120)]},
                       "threshold": {"line": {"width": 3}, "value": corte_alto * 100}}
            ))
            fig_dti_prom.update_layout(
                title="DTI medio (línea: inicio del tercil alto)",
                height=330, margin=dict(l=30, r=30, t=55, b=25)
            )
            st.plotly_chart(fig_dti_prom, use_container_width=True, key="juan_dti_prom")
        else:
            st.info("No hay DTI válido para calcular el promedio.")
        st.caption("Decisión: contextualizar el endeudamiento histórico; el tercil es descriptivo, no un límite de aprobación.")

    with panel4, st.container(border=True):
        st.markdown("**4. ¿Cuánto incumplen los perfiles con DTI alto?**")
        st.metric("KPI · Default con DTI alto", f"{tasa_dti_alto:.2%}" if math.isfinite(tasa_dti_alto) else "—")
        tasas_por_dti = tabla_dti["tasa"] * 100
        if tasas_por_dti.notna().any():
            fig_riesgo = go.Figure(go.Bar(
                x=tasas_por_dti.index.tolist(), y=tasas_por_dti.tolist(),
                text=[f"{v:.1f}%" if pd.notna(v) else "Sin muestra" for v in tasas_por_dti],
                textposition="auto"
            ))
            fig_riesgo.update_layout(
                title="Tasa de incumplimiento por nivel de DTI",
                xaxis_title="Endeudamiento", yaxis_title="Incumplimiento (%)",
                height=330, margin=dict(l=20, r=20, t=55, b=25), showlegend=False
            )
            st.plotly_chart(fig_riesgo, use_container_width=True, key="juan_riesgo_dti")
        else:
            st.info("No hay segmentos con suficientes registros para mostrar tasas.")
        st.caption(
            f"Decisión: priorizar revisión de segmentos. Tasas solo con n ≥ {C.N_MINIMO}; "
            "asociación descriptiva, no causalidad ni predicción."
        )

    metodologia = [
        {"KPI": "Registros crediticios", "Fórmula": "Número de filas del CSV", "Origen": "REAL"},
        {"KPI": "Tasa histórica de incumplimiento", "Fórmula": "Conteo(DEFAULT = 1) / Conteo(DEFAULT válido)", "Origen": "CALCULADO / REAL"},
        {"KPI": "DTI promedio", "Fórmula": "Promedio(DEBT_TO_INCOME) × 100 para expresarlo en %", "Origen": "CALCULADO / REAL"},
        {"KPI": "Default con DTI alto", "Fórmula": "Media(DEFAULT) en SEG_DTI = Alto, con n ≥ 30", "Origen": "CALCULADO / REAL"},
    ]

elif usuario.rol == "operacion":
    indicadores = servicios.indicadores_calidad(usuario.rol)
    st.subheader("Calidad de los datos de entrada")
    ui.origen("REAL", "CALCULADO")
    completos = indicadores["proporcion_completos"]
    tarjetas([
        ("Registros revisados", f"{indicadores['registros']:,}",
         "REAL · Número de filas del CSV fuente, no volumen de procesamiento en producción."),
        ("Campos críticos completos", f"{completos:.2%}" if math.isfinite(completos) else "—",
         "CALCULADO / REAL · Porcentaje de filas sin nulos en las variables críticas configuradas."),
        ("Registros fuera de límites", f"{indicadores['fuera_limite']:,}",
         "CALCULADO / REAL · Filas con al menos una variable de entrada fuera de los rangos válidos configurados."),
    ])
    st.caption(
        f"Fuente: Base_SAS_Equipo3.csv · {indicadores['completos']:,} filas con variables críticas completas; "
        f"{indicadores['fuera_limite']:,} filas fuera de límites. "
        "Los umbrales son los declarados en src/config.py."
    )
    st.caption(
        "**Decisión:** verificar si la base es apta para el procesamiento. "
        "Esto NO es un monitor en vivo ni valida AUC, KS, PSI o desempeño del modelo campeón."
    )
    metodologia = [
        {"KPI": "Registros revisados", "Fórmula": "Número de filas del CSV", "Origen": "REAL"},
        {"KPI": "Campos críticos completos", "Fórmula": "Filas sin nulos en VARIABLES_CLAVE / total de filas", "Origen": "CALCULADO / REAL"},
        {"KPI": "Registros fuera de límites", "Fórmula": "Conteo(filas con ≥1 valor fuera de LIMITES_VALIDOS)", "Origen": "CALCULADO / REAL"},
    ]

else:
    st.error("Rol no autorizado para esta pantalla.")
    st.stop()

with st.expander("Metodología y trazabilidad de estos indicadores"):
    st.dataframe(pd.DataFrame(metodologia), hide_index=True)
    st.caption(
        "Ninguna tarjeta utiliza resultados de un supuesto modelo campeón. "
        "Las métricas de predicción (TP/FP/FN/TN, matriz de confusión, ROC, AUC, KS) "
        "se incorporarán al módulo de validación cuando se cierre el experimento de modelos "
        "y se definan la muestra de prueba y el umbral de clasificación."
    )
