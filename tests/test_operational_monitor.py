"""Integración DTI y seguimiento de sesiones del nuevo panel gerencial."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from src import store
from src.monthly_kpis import local_now
from src.ops_monitor import (
    begin_session, touch_session, end_session, monthly_session_stats,
    create_incident, incidents, change_incident, incident_month_summary
)
from src.manager_overview import build_team_metrics


@pytest.fixture
def demo(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"operational.sqlite")
    store.initialize(.159)
    return store


def test_manager_monthly_team_target_is_sum_of_two_analysts(demo):
    demo.set_targets_batch({"Decisiones mensuales":50},"Mariana")
    demo.save_decision("credit-101","A-017","Aceptar","Aceptar",.08,.10,.159)
    demo.save_decision("credit-102","A-022","Rechazar","Rechazar",.91,.87,.159)
    demo.save_decision("credit-103","A-022","Aceptar","Rechazar",.40,.49,.159,
                       "Información verificada","Revisión documentada suficiente")
    metrics=build_team_metrics(demo.decisions(),demo.targets())
    assert metrics["decisions"]==3
    assert metrics["decision_goal"]==100
    assert metrics["completion"]==pytest.approx(.03)
    assert metrics["exceptions"]==1
    assert metrics["justified"]==1
    assert metrics["agreement"]==pytest.approx(2/3)
    assert metrics["individuals"]["A-017"]["count"]==1
    assert metrics["individuals"]["A-022"]["count"]==2


def test_tickets_go_to_dti_and_manager_and_month_cohort(demo):
    assert incident_month_summary()["rate"] is None
    t1=create_incident("A-017","Error en el dashboard",
      "La gráfica no carga","No aparece la distribución de probabilidades",
      "Alta","468086")
    t2=create_incident("A-022","Predicción o variables",
      "Variable sin valor","El detalle del préstamo no presenta la variable esperada")
    assert t2==t1+1
    assert demo.unread("dti")==2
    assert demo.unread("gerente")==2
    assert demo.unread("analista","A-017")==0
    assert demo.unread("analista","A-022")==0
    initial=incident_month_summary()
    assert (initial["total"],initial["open"],initial["solved"])==(2,2,0)
    assert initial["rate"]==0
    assert change_incident(t1,"En revisión")
    assert demo.unread("analista","A-017")==1
    assert demo.unread("gerente")==3
    with pytest.raises(ValueError):
        change_incident(t1,"Resuelto","Hecho")
    assert change_incident(t1,"Resuelto",
           "Se corrigió la presentación de la distribución.")
    result=incident_month_summary()
    assert result["rate"]==pytest.approx(.5)
    assert (result["review"],result["open"],result["solved"])==(0,1,1)
    assert incidents(analyst_id="A-017")[0]["status"]=="Resuelto"
    assert len(incidents(analyst_id="A-022"))==1
    assert demo.unread("analista","A-017")==2
    assert not change_incident(t1,"Resuelto",
           "Se corrigió la presentación de la distribución.")
    with pytest.raises(ValueError):
        create_incident("A-009","Otro","Error desconocido",
                        "Descripción de incidencia suficiente")


def test_tracked_sessions_only_count_when_closed(demo):
    token_a=begin_session("analista","A-017","Adrián",token="session-a")
    token_s=begin_session("analista","A-022","Sofía",token="session-s")
    token_d=begin_session("dti",None,"Especialista DTI",token="session-d")
    report=monthly_session_stats()
    assert report[("analista","A-017")]["minutes"] is None
    assert report[("analista","A-022")]["minutes"] is None
    assert report[("dti",None)]["minutes"] is None
    assert report[("analista","A-017")]["open_without_logout"]==1
    # Se controla una duración registrada, no se inventa tiempo de actividad.
    with demo.db() as c:
        c.execute("UPDATE profile_sessions SET started_at=? WHERE session_token=?",
            ((datetime.now(timezone.utc)-timedelta(minutes=12)).isoformat(),token_a))
    touch_session(token_a)
    assert end_session(token_a)
    assert not end_session(token_a)
    report=monthly_session_stats()
    assert report[("analista","A-017")]["closed"]==1
    assert report[("analista","A-017")]["minutes"]==pytest.approx(12,abs=.15)
    assert report[("analista","A-017")]["open_without_logout"]==0
    assert report[("dti",None)]["open_without_logout"]==1


def test_initialize_is_idempotent_and_keeps_records(demo):
    t=create_incident("A-017","Gráficas / métricas",
              "Panel incompleto","Una gráfica del dashboard está incompleta.")
    begin_session("gerente",None,"Mariana",token="manager-session")
    demo.initialize(.159)
    demo.initialize(.159)
    assert len(incidents())==1 and incidents()[0]["id"]==t
    assert demo.targets()["Resolución DTI mensual"]==pytest.approx(.99)
    assert monthly_session_stats()[("gerente",None)]["open_without_logout"]==1
