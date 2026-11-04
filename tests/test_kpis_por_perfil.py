"""Pruebas puras de tarjetas por perfil (sin valores inventados)."""
import pandas as pd
import pytest

from src import config as C, datos, seguridad as S
from src.kpis import calcular_kpis_bandeja, calcular_kpis_calidad


def test_todos_los_perfiles_pueden_abrir_p7():
    assert all(S.puede_ver(rol, "P7") for rol in S.ROLES)
    assert not S.puede_ver(None, "P7")


def test_calidad_de_la_base_real():
    r = calcular_kpis_calidad(datos.leer_base(), C.VARIABLES_CLAVE, C.LIMITES_VALIDOS)
    assert r["registros"] == 80_000
    assert r["completos"] == 80_000
    assert r["proporcion_completos"] == 1.0
    assert r["fuera_limite"] == 0


def test_calidad_detecta_valores_fuera_de_limite_y_faltantes():
    columnas = list(C.LIMITES_VALIDOS)
    df = pd.DataFrame([{c: 0.1 for c in columnas} for _ in range(3)])
    df.loc[0, "DEBT_TO_INCOME"] = None
    df.loc[1, "BANKRUPTCY_FLAG"] = 3
    r = calcular_kpis_calidad(df, C.VARIABLES_CLAVE, C.LIMITES_VALIDOS)
    assert r["completos"] == 2
    assert r["fuera_limite"] == 1


def test_bandeja_cuenta_pendientes_y_datos_incompletos():
    cola = pd.DataFrame({
        "FOLIO": ["A", "B", "C"],
        "ESTADO_SOLICITUD": ["Pendiente", "Resuelta hoy", "Pendiente"],
        "CALIDAD": ["Completo", "Incompleto", "Fuera de rango"],
    })
    r = calcular_kpis_bandeja(cola)
    assert r == {"solicitudes": 3, "pendientes": 2, "revisar_datos": 2}


def test_no_fabricar_si_faltan_columnas():
    with pytest.raises(ValueError, match="Faltan columnas"):
        calcular_kpis_bandeja(pd.DataFrame({"FOLIO": ["A"]}))
