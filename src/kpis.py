"""Indicadores descriptivos de la base crediticia REAL.

No se utilizan pronósticos ni datos simulados. Cada resultado se calcula
nuevamente si cambia la base de origen.
"""
from __future__ import annotations

import pandas as pd


def calcular_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Calcula tres KPI a partir de DEFAULT y DEBT_TO_INCOME.

    Cada fila del CSV cuenta como un *registro*; el archivo no tiene identificador
    de solicitud ni variable de fechas, por lo que no inferimos créditos únicos
    ni tendencia temporal. La tasa usa únicamente DEFAULT no nulos.
    """
    faltantes = {"DEFAULT", "DEBT_TO_INCOME"} - set(df.columns)
    if faltantes:
        raise ValueError("Faltan columnas para calcular KPI: " + ", ".join(sorted(faltantes)))

    default = df["DEFAULT"]
    n_validos = int(default.notna().sum())
    n_default = int(default.eq(1).sum())
    dti = pd.to_numeric(df["DEBT_TO_INCOME"], errors="coerce")

    return {
        "registros": int(len(df)),
        "incumplimientos": n_default,
        "tasa_default": n_default / n_validos if n_validos else float("nan"),
        "dti_promedio": float(dti.mean()),
        "default_validos": n_validos,
        "dti_validos": int(dti.notna().sum()),
    }



def calcular_kpis_calidad(df: pd.DataFrame, variables_clave: list[str],
                          limites_validos: dict[str, tuple[float, float]]) -> dict[str, float | int]:
    """Métricas descriptivas de calidad de los registros de origen.

    No interpreta el dataset como datos de producción ni compara predicciones.
    """
    necesarias = set(variables_clave) | set(limites_validos)
    faltantes = necesarias - set(df.columns)
    if faltantes:
        raise ValueError("Faltan columnas para calidad: " + ", ".join(sorted(faltantes)))

    n = len(df)
    completos = int(df[variables_clave].notna().all(axis=1).sum())
    fuera_de_limite = pd.Series(False, index=df.index, dtype=bool)
    for columna, (minimo, maximo) in limites_validos.items():
        valores = pd.to_numeric(df[columna], errors="coerce")
        fuera_de_limite |= valores.notna() & ~valores.between(minimo, maximo)

    invalidos = int(fuera_de_limite.sum())
    return {
        "registros": n,
        "completos": completos,
        "proporcion_completos": completos / n if n else float("nan"),
        "fuera_limite": invalidos,
        "proporcion_fuera_limite": invalidos / n if n else float("nan"),
    }


def calcular_kpis_bandeja(cola: pd.DataFrame) -> dict[str, int]:
    """Conteos operativos de la bandeja filtrada de UN analista.

    Solo se llama DESPUÉS de aplicar el filtro de ANALISTA_ID en el servidor.
    Los folios/estados de esta aplicación son de demostración (SIMULADOS).
    """
    necesarias = {"FOLIO", "ESTADO_SOLICITUD", "CALIDAD"}
    faltantes = necesarias - set(cola.columns)
    if faltantes:
        raise ValueError("Faltan columnas para bandeja: " + ", ".join(sorted(faltantes)))
    return {
        "solicitudes": int(len(cola)),
        "pendientes": int(cola["ESTADO_SOLICITUD"].eq("Pendiente").sum()),
        "revisar_datos": int(cola["CALIDAD"].ne("Completo").sum()),
    }
