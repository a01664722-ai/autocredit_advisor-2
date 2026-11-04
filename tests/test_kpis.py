"""Pruebas de KPI: no inventar cifras y mantener denominadores correctos."""
import math

import pandas as pd
import pytest

from src import datos
from src.kpis import calcular_kpis


def test_kpis_base_real():
    k = calcular_kpis(datos.leer_base())
    assert k["registros"] == 80000
    assert k["incumplimientos"] == 10783
    assert k["default_validos"] == 80000
    assert k["tasa_default"] == pytest.approx(10783 / 80000)
    assert k["dti_promedio"] == pytest.approx(0.296079927246875)


def test_kpis_con_nulos():
    df = pd.DataFrame({"DEFAULT": [0, 1, None, 1],
                       "DEBT_TO_INCOME": [0.1, 0.3, None, 0.5]})
    k = calcular_kpis(df)
    assert k["registros"] == 4
    assert k["incumplimientos"] == 2
    assert k["default_validos"] == 3
    assert k["dti_validos"] == 3
    assert k["tasa_default"] == pytest.approx(2 / 3)
    assert k["dti_promedio"] == pytest.approx(0.3)


def test_kpis_vacios_y_columnas_faltantes():
    vacio = calcular_kpis(pd.DataFrame(columns=["DEFAULT", "DEBT_TO_INCOME"]))
    assert vacio["registros"] == 0
    assert math.isnan(vacio["tasa_default"])
    with pytest.raises(ValueError, match="DEBT_TO_INCOME"):
        calcular_kpis(pd.DataFrame({"DEFAULT": [0]}))
