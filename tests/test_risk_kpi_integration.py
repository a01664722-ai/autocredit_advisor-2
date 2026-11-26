"""Pruebas integradas: riesgo de crédito en P1, analistas y gerencia.

No usa DEFAULT real para evaluar a los analistas; el importe es exposición
revisada, no pérdidas realizadas ni créditos incumplidos.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import pandas as pd
import pytest

from src import store
from src.monthly_kpis import RISK_HEADLINES, monthly_summary, fmt_risk
from src.manager_overview import build_team_metrics

TZ = ZoneInfo("America/Mexico_City")
REF = datetime(2026, 11, 25, 20, 0, tzinfo=TZ)


def decision(loan_id, analyst, suggested, decision_final, pd_value, date="2026-11-25T15:00:00+00:00"):
    override = suggested != decision_final
    return {
        "loan_id": loan_id, "analyst_id": analyst,
        "suggested": suggested, "decision": decision_final,
        "pd_xgb": pd_value, "override": int(override),
        "motivo": "Validación documental" if override else "",
        "text_detail": "Evidencia documentada" if override else "",
        "updated_at": date,
    }


@pytest.fixture
def scored():
    return pd.DataFrame([
        {"LOAN_ID": "101", "ANALISTA_ID": "A-017", "LOAN_AMOUNT": 20000.0, "DEFAULT": 1},
        {"LOAN_ID": "102", "ANALISTA_ID": "A-017", "LOAN_AMOUNT": 30000.0, "DEFAULT": 0},
        {"LOAN_ID": "103", "ANALISTA_ID": "A-017", "LOAN_AMOUNT": 80000.0, "DEFAULT": 1},
        {"LOAN_ID": "201", "ANALISTA_ID": "A-022", "LOAN_AMOUNT": 40000.0, "DEFAULT": 0},
        {"LOAN_ID": "202", "ANALISTA_ID": "A-022", "LOAN_AMOUNT": 9000.0, "DEFAULT": 1},
        {"LOAN_ID": "104", "ANALISTA_ID": "A-017", "LOAN_AMOUNT": 999000.0, "DEFAULT": 1},
    ])


@pytest.fixture
def rows():
    return [
        decision("101", "A-017", "Rechazar", "Rechazar", .51),
        decision("102", "A-017", "Rechazar", "Aceptar", .20),
        decision("103", "A-017", "Aceptar", "Aceptar", .03),
        decision("201", "A-022", "Rechazar", "Condicionar", .60),
        decision("202", "A-022", "Condicionar", "Condicionar", .14),
        decision("104", "A-017", "Rechazar", "Rechazar", .90,
                 date="2026-10-24T15:00:00+00:00"),
    ]


def test_risk_kpi_are_three_risk_and_one_productivity(rows, scored):
    names = [item[0] for item in RISK_HEADLINES]
    assert names == [
        "Exposición alto riesgo evaluada",
        "Riesgo alto atendido",
        "PD promedio evaluada",
        "Decisiones mensuales",
    ]
    stat = monthly_summary(rows, "A-017", REF, scored)
    assert stat["metrics"]["Exposición alto riesgo evaluada"] == pytest.approx(50000.0)
    assert stat["metrics"]["Riesgo alto atendido"] == 2
    assert stat["metrics"]["PD promedio evaluada"] == pytest.approx((.51 + .20 + .03) / 3)
    assert stat["metrics"]["Decisiones mensuales"] == 3
    # La aprobación excepcional no borra la sugerencia de alto riesgo.
    assert stat["overrides"] == 1
    assert fmt_risk("Exposición alto riesgo evaluada", 50000) == "50,000 u.m."
    assert fmt_risk("PD promedio evaluada", .2466666) == "24.7%"


def test_manager_and_analysts_share_exact_same_source(rows, scored):
    targets = {"Decisiones mensuales": 50, "Riesgo alto atendido": 15}
    team = build_team_metrics(rows, targets, REF, scores=scored)
    a = team["individuals"]["A-017"]
    b = team["individuals"]["A-022"]
    assert team["risk_high"] == 3
    assert team["risk_high"] == (a["metrics"]["Riesgo alto atendido"] +
                                  b["metrics"]["Riesgo alto atendido"])
    assert team["risk_exposure"] == pytest.approx(90000.)
    assert team["risk_exposure"] == (
        a["metrics"]["Exposición alto riesgo evaluada"] +
        b["metrics"]["Exposición alto riesgo evaluada"])
    assert team["risk_pd"] == pytest.approx((.51 + .20 + .03 + .60 + .14) / 5)
    assert team["decisions"] == 5
    assert a["count"] == 3 and b["count"] == 2


def test_risk_not_measured_from_realized_default(rows, scored):
    first = build_team_metrics(rows, {"Decisiones mensuales": 50}, REF, scores=scored)
    inverted = scored.copy()
    inverted["DEFAULT"] = 1 - inverted["DEFAULT"]
    second = build_team_metrics(rows, {"Decisiones mensuales": 50}, REF, scores=inverted)
    assert first["risk_exposure"] == second["risk_exposure"]
    assert first["risk_high"] == second["risk_high"]
    assert first["risk_pd"] == second["risk_pd"]


def test_missing_or_foreign_amount_never_counted_as_zero(rows, scored):
    missing = scored.loc[scored.LOAN_ID != "102"]
    s = monthly_summary(rows, "A-017", REF, scored=missing)
    assert s["metrics"]["Exposición alto riesgo evaluada"] is None
    changed = scored.copy()
    changed.loc[changed.LOAN_ID == "102", "ANALISTA_ID"] = "A-022"
    assert monthly_summary(rows, "A-017", REF, changed)["metrics"]["Exposición alto riesgo evaluada"] is None
    assert monthly_summary([], "A-017", REF, scored)["metrics"]["Exposición alto riesgo evaluada"] == 0.0
    assert monthly_summary([], "A-017", REF, scored)["metrics"]["PD promedio evaluada"] is None


def test_updated_decisions_not_double_counted_and_manager_targets_notify(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB", tmp_path / "risk_kpis.sqlite")
    store.initialize(.159)
    assert store.save_decision("101", "A-017", "Rechazar", "Rechazar", .51, .40, .159) is False
    assert store.save_decision("101", "A-017", "Rechazar", "Rechazar", .51, .40, .159) is False
    s = pd.DataFrame([{"LOAN_ID": "101", "ANALISTA_ID": "A-017",
                       "LOAN_AMOUNT": 20000., "DEFAULT": 1}])
    a = monthly_summary(store.decisions_map("A-017"), "A-017", scored=s)
    assert a["count"] == 1
    assert a["metrics"]["Exposición alto riesgo evaluada"] == 20000.0
    assert a["metrics"]["PD promedio evaluada"] == pytest.approx(.51)
    assert store.set_targets_batch({"Riesgo alto atendido": 21, "Decisiones mensuales": 60},
                                   "Mariana")
    assert store.targets()["Riesgo alto atendido"] == 21
    assert store.unread("analista", "A-017") == 1
    assert store.unread("analista", "A-022") == 1
    assert "21" in store.messages("analista", "A-017")[0]["body"]
    assert store.decisions()[0]["pd_xgb"] == pytest.approx(.51)


def test_actual_ui_calls_share_same_scored_and_neon_border():
    root = Path(__file__).resolve().parents[1]
    app = (root / "app_v3.py").read_text(encoding="utf-8")
    analyst = (root / "src/kpi_views.py").read_text(encoding="utf-8")
    manager = (root / "src/manager_overview.py").read_text(encoding="utf-8")
    assert "mensual = monthly_summary(decisiones, analyst_id, scored=M.scores)" in app
    assert "stats=monthly_summary(records,analyst_id,scored=score_df)" in analyst
    assert "summaries={aid:monthly_summary(records,aid,scored=score_df)" in analyst
    assert "render_manager_month(name, M.scores)" in app
    assert "render_manager_overview(M.scores)" in app
    assert "team=build_team_metrics(store.decisions(),targets,scores=scores)" in manager
    assert "outline:2px solid #52dc9a!important" in app
    assert "Exposición de alto riesgo · u.m." in app
