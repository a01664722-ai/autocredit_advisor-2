"""Cierre del perfil Soporte y consistencia con el tablero de Mariana."""
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from src import store
from src.ops_monitor import create_incident, change_incident
from src.manager_overview import build_team_metrics
from src.support_views import REPOSITORY_URL, support_snapshot


def _fake_model():
    cols=["Modelo","ROC-AUC","KS","PR-AUC","Accuracy","Precision",
          "Recall","F1","Brier","FP","FN","TP","TN"]
    data=[
      ["XGBoost",.85,.61,.72,.91,.76,.81,.78,.07,32,19,143,310],
      ["Logit",.79,.51,.66,.88,.71,.74,.72,.10,44,26,136,297],
    ]
    return SimpleNamespace(metricas=pd.DataFrame(data,columns=cols))


@pytest.fixture()
def setup_support(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"support.sqlite")
    store.initialize(.159)
    return store


def test_manager_and_support_share_the_same_monthly_resolution(setup_support):
    model=_fake_model()
    empty=support_snapshot(model)
    assert empty["month"]["total"]==0
    assert empty["month"]["rate"] is None
    assert empty["goal"]==pytest.approx(.99)
    assert empty["pending"]==[]
    assert empty["high_priority"]==[]
    first=create_incident("A-017","Predicción o variables",
         "Probabilidad no aparece","La probabilidad de la solicitud no es visible.","Alta")
    second=create_incident("A-022","Gráficas / métricas",
         "Gráfica no se muestra","La comparación de resultados se encuentra cortada.")
    assert first!=second
    snap=support_snapshot(model)
    assert snap["month"]["total"]==2
    assert snap["month"]["rate"]==0
    assert len(snap["pending"])==2
    assert len(snap["high_priority"])==1
    assert snap["xgb"]["ROC-AUC"]==pytest.approx(.85)
    assert change_incident(first,"Resuelto",
                           "Se corrigió el componente de probabilidad en la ficha.")
    after=support_snapshot(model)
    assert after["month"]["rate"]==pytest.approx(.5)
    assert after["month"]["solved"]==1
    assert len(after["pending"])==1
    assert not after["high_priority"]
    assert setup_support.unread("gerente")>=3
    assert setup_support.unread("analista","A-017")>=1


def test_support_has_no_audit_screen_and_has_repository_link():
    app=(Path(__file__).resolve().parents[1]/"app_v3.py").read_text(encoding="utf-8")
    support=(Path(__file__).resolve().parents[1]/"src/support_views.py").read_text(encoding="utf-8")
    assert "pages=['Centro de soporte','Validación del modelo','Mensajes']" in app
    assert "pages=['Incidencias DTI'" not in app
    assert "if role!='gerente':" in app
    assert "render_support_home(M)" in app
    assert "render_support_validation(M)" in app
    assert "REPOSITORY_URL" in app
    assert "Especialista · Soporte" in app
    assert "Especialista · Validación DTI" not in app
    assert "render_dti_incidents(show_heading=False,show_kpis=False)" in support
    assert REPOSITORY_URL.endswith("/tree/v3-integracion-xgboost-12v")
    assert support.count("_plot(fig,")>=5
    assert "precision_recall_curve" in support
    assert "calibration_curve" in support


def test_incidence_labels_are_support_not_dti(setup_support):
    ticket=create_incident("A-017","Error en el dashboard",
          "No funciona el gráfico","El gráfico de la ficha no se carga.")
    messages=setup_support.messages("dti")
    assert len(messages)==1
    assert "Soporte" in messages[0]["title"]
    assert "DTI" not in messages[0]["title"]
    assert change_incident(ticket,"En revisión")
    messages=setup_support.messages("analista","A-017")
    assert len(messages)==1
    assert "Soporte" in messages[0]["body"]
