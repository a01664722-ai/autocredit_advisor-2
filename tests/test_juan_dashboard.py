"""Regresión: cálculos agregados del proyecto y avisos de metas."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src import juan_politica as politica
from src.juan_dashboard import datos_agregados, calcular, estado


def test_train_verificado():
    df, meta = datos_agregados()
    total = calcular(df)
    assert meta["partition"] == "TRAIN"
    assert total["n"] == 80000
    assert total["bad"] == 10783
    assert total["tasa"] == pytest.approx(10783 / 80000)
    assert total["dti"] == pytest.approx(0.29607992724690124)
    assert total["monto"] == pytest.approx(20348.014475)
    assert len(meta["columns"]) == 14


def test_semaforo_sin_meta_no_fabrica_verde():
    assert estado(.1348, None) == "Sin meta aprobada"
    assert estado(.1348, .13) == "Fuera de meta"
    assert estado(.1348, .14) == "Dentro de meta"


def test_avisos_gerente_persisten_en_sqlite():
    with TemporaryDirectory() as tmp:
        db = Path(tmp) / "kpi.db"
        assert politica.leer_metas(db) == {}
        metas = {"incumplimiento": .13, "dti": .30, "dti_alto": .25}
        assert politica.guardar_metas(metas, "Mariana", db)
        assert politica.leer_metas(db)["dti"] == .30
        avisos = politica.avisos_no_leidos("analista@demo.mx", db)
        assert len(avisos) == 1
        assert not politica.guardar_metas(metas, "Mariana", db)
        politica.marcar_leidos("analista@demo.mx", db)
        assert politica.avisos_no_leidos("analista@demo.mx", db) == []
