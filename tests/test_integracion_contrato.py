"""El mismo contrato protege los archivos y las tablas de Streamlit."""
from __future__ import annotations

import ast
import csv
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src import config as C, datos


RAIZ = Path(__file__).resolve().parents[1]


def base_de_prueba(tmp_path, alteracion=None):
    ruta = tmp_path / "Base_SAS_Equipo3.csv"
    ejemplo = {col: "0" for col in C.COLUMNAS_ESPERADAS}
    ejemplo.update({"SAVINGS_BALANCE": "25000.50", "YEARS_CREDIT_HISTORY": "8.5"})
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=C.COLUMNAS_ESPERADAS)
        escritor.writeheader()
        for fila in range(C.N_MINIMO):
            registro = ejemplo.copy()
            registro["DEFAULT"] = str(fila % 2)
            if fila == 0 and alteracion:
                registro.update(alteracion)
            escritor.writerow(registro)
    return ruta


def test_base_real_cargada_solo_con_columnas_numericas():
    df = datos.leer_base()
    assert list(df.columns) == C.COLUMNAS_ESPERADAS
    assert all(pd.api.types.is_numeric_dtype(df[c]) for c in C.COLUMNAS_ESPERADAS)


def test_texto_numerico_detiene_carga_antes_de_la_interfaz(tmp_path):
    ruta = base_de_prueba(tmp_path, {"SAVINGS_BALANCE": "ERROR_TIPO"})
    with pytest.raises(datos.ErrorDeDatos, match="SAVINGS_BALANCE.*no numérico"):
        datos.leer_base(ruta)


def test_ausencia_no_critica_se_convierte_en_nan(tmp_path):
    ruta = base_de_prueba(tmp_path, {"FINANCIAL_LITERACY_SCORE": "S/D"})
    df = datos.leer_base(ruta)
    assert pd.isna(df.loc[0, "FINANCIAL_LITERACY_SCORE"])
    assert pd.api.types.is_numeric_dtype(df["FINANCIAL_LITERACY_SCORE"])


def test_sidebar_muestra_verificacion_de_tipos():
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=120)
    at.session_state["demo_email"] = "adrian.perez@autocredit.mx"
    at.run()
    assert not at.exception, at.exception
    assert any("Contrato de datos válido" in c.value and "12/12" in c.value
               for c in at.sidebar.caption)


def test_todas_las_tablas_interactivas_ordenadas_y_sin_indice():
    cantidad = 0
    for archivo in (RAIZ / "vistas").glob("p*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                    and isinstance(nodo.func.value, ast.Name)
                    and nodo.func.value.id == "st" and nodo.func.attr == "dataframe"):
                continue
            cantidad += 1
            argumentos = {a.arg: a.value for a in nodo.keywords}
            assert "column_order" in argumentos, f"Falta column_order en {archivo.name}:{nodo.lineno}"
            assert isinstance(argumentos.get("hide_index"), ast.Constant) and argumentos["hide_index"].value is True, (
                f"Falta hide_index=True en {archivo.name}:{nodo.lineno}"
            )
    assert cantidad >= 14


def test_columna_ahorro_se_publica_como_numero():
    codigo = (RAIZ / "vistas" / "p1_bandeja.py").read_text(encoding="utf-8")
    assert '"Ahorro": pd.to_numeric(' in codigo
    assert 'st.column_config.NumberColumn("Ahorro (REAL)"' in codigo
