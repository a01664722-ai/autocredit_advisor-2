"""Regresión KPI mensual: conteos reales, objetivos gerenciales y buzones vinculados."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src import store
from src.monthly_kpis import KPI_SPECS, monthly_summary, level, progress

TZ=ZoneInfo("America/Mexico_City")


def _decision(loan_id,when,decision,suggested,motivo="",detail=""):
    override=int(decision!=suggested)
    return {"loan_id":loan_id, "analyst_id":"A-017", "decision":decision,
            "suggested":suggested, "override":override, "motivo":motivo,
            "text_detail":detail,"updated_at":when}


def test_mes_separado_y_sin_inventar_resultados():
    rows=[
        _decision("101","2026-11-11T23:30:00+00:00","Rechazar","Rechazar"),
        _decision("102","2026-11-12T15:00:00+00:00","Condicionar","Rechazar",
                  "Documento validado","Se revisaron ocho datos"),
        _decision("103","2026-10-04T15:00:00+00:00","Aceptar","Aceptar"),
        _decision("104","2026-11-12T15:00:00+00:00","Aceptar","Aceptar")
    ]
    nov=monthly_summary(rows,"A-017",datetime(2026,11,12,tzinfo=TZ))
    assert nov["count"]==3 and nov["overrides"]==1
    assert nov["metrics"]["Decisiones mensuales"]==3
    assert nov["metrics"]["Riesgo alto atendido"]==2
    assert nov["metrics"]["Riesgo bajo atendido"]==1
    assert nov["metrics"]["Riesgo medio atendido"]==0
    assert nov["metrics"]["Coincidencia con sugerencia"]==pytest.approx(2/3)
    assert nov["metrics"]["Con justificación"]==1
    assert nov["cumulative"][10]==1  # Nov 11 a las 17:30 CDMX
    assert nov["cumulative"][11]==3
    assert level(3,50)=="low"
    assert progress(3,50)==pytest.approx(.06)


def test_nulidad_sin_eventos():
    stats=monthly_summary([], "A-017",datetime(2026,11,12,tzinfo=TZ))
    assert stats["count"]==0
    assert stats["metrics"]["Coincidencia con sugerencia"] is None
    assert stats["metrics"]["Con justificación"] is None
    assert level(None,1)=="na"
    assert progress(None,1) is None


def test_metas_editables_mensuales_y_notificaciones(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"monthly.sqlite")
    store.initialize(.159)
    base=store.targets()
    assert all(key in base for key,*_ in KPI_SPECS)
    assert base["Decisiones mensuales"]==50
    assert store.set_targets_batch(
        {"Decisiones mensuales":100,"Riesgo alto atendido":25,
         "Coincidencia con sugerencia":.85},"Mariana")
    updated=store.targets()
    assert updated["Decisiones mensuales"]==100
    assert updated["Riesgo alto atendido"]==25
    assert updated["Coincidencia con sugerencia"]==pytest.approx(.85)
    assert store.unread("analista","A-017")==1
    assert store.unread("analista","A-022")==1
    assert "100" in store.messages("analista","A-017")[0]["body"]
    assert not store.set_targets_batch({"Decisiones mensuales":100},"Mariana")
    assert store.unread("analista","A-017")==1
    with pytest.raises(ValueError):
        store.set_targets_batch({"Con justificación":1.1},"Mariana")
    with pytest.raises(ValueError):
        store.set_targets_batch({"Decisiones mensuales":0},"Mariana")
    assert store.targets()["Con justificación"]==1.0
