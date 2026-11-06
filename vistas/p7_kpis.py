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
    # Cambios de metas gerenciales: aviso visible, no altera expedientes.
    from src.juan_dashboard import avisos_analista
    avisos_analista(usuario)
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
    # Juan: solo métricas agregadas y filtros de la muestra de entrenamiento.
    from src.juan_dashboard import mostrar_gerente
    mostrar_gerente(usuario)
    metodologia = [
        {"KPI": "Volumen", "Fórmula": "Registros del corte", "Origen": "REAL / TRAIN 12V"},
        {"KPI": "Incumplimiento", "Fórmula": "DEFAULT=1 / registros", "Origen": "REAL / TRAIN 12V"},
        {"KPI": "DTI promedio", "Fórmula": "Media de DEBT_TO_INCOME", "Origen": "REAL / TRAIN 12V"},
        {"KPI": "Riesgo DTI alto", "Fórmula": "DEFAULT=1 entre DTI alto", "Origen": "REAL / TRAIN 12V"},
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
