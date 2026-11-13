"""Pruebas del aislamiento entre Adrián A-017 y Sofía A-022."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src import store
from src.monthly_kpis import monthly_summary
from src.profile_state import reset_profile_navigation


def test_navigation_does_not_leak_between_analysts():
    state={"perfil":"Sofía · Analista A-022",
           "_active_profile_identity":"analista:A-017",
           "page":"Ficha de solicitud","nav_analista":"Ficha de solicitud",
           "page_to":"Ficha de solicitud",
           "loan_actual":"277432","pending_choice":{"loan_id":"277432","choice":"Rechazar"},
           "p2_buscar_loan":"277432","p2_selector_loan":"277432",
           "p1_estado_v3":"Resuelta","p1_pagina_v3":14,"p1_editor_v3_A-017":"contenido",
           "internal_mail_analista_A-017_subject":"Borrador",
           "override_motive":"Otro","override_note":"Motivo antiguo",
           "table_rev":4,"meta_no_personal":"se conserva"}
    assert reset_profile_navigation(state,"analista","A-022")
    assert state["_active_profile_identity"]=="analista:A-022"
    assert state["perfil"]=="Sofía · Analista A-022"
    assert state["meta_no_personal"]=="se conserva"
    assert "loan_actual" not in state
    assert "pending_choice" not in state
    assert "nav_analista" not in state
    assert "p2_buscar_loan" not in state
    assert "p1_estado_v3" not in state
    assert "internal_mail_analista_A-017_subject" not in state
    state["page"]="Mis indicadores"
    assert not reset_profile_navigation(state,"analista","A-022")
    assert state["page"]=="Mis indicadores"
    assert reset_profile_navigation(state,"analista","A-017")
    assert state["_active_profile_identity"]=="analista:A-017"
    assert "page" not in state


def test_independent_decisions_and_monthly_kpis(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"analyst-bridge.sqlite")
    store.initialize(.159)
    assert not store.save_decision("loan-adrian-1","A-017","Aceptar","Aceptar",
                                   .05,.07,.159)
    assert store.save_decision("loan-sofia-1","A-022","Rechazar","Aceptar",
                               .75,.70,.159,"Documento verificado",
                               "La revisión encontró diferencias sustanciales.")
    assert not store.save_decision("loan-sofia-2","A-022","Rechazar","Rechazar",
                                   .95,.90,.159)
    adrian=store.decisions_map("A-017")
    sofia=store.decisions_map("A-022")
    assert set(adrian)=={"loan-adrian-1"}
    assert set(sofia)=={"loan-sofia-1","loan-sofia-2"}
    assert set(adrian).isdisjoint(sofia)
    reference=datetime.now(ZoneInfo("America/Mexico_City"))
    ma=monthly_summary(adrian,"A-017",reference)
    ms=monthly_summary(sofia,"A-022",reference)
    assert ma["count"]==1 and ms["count"]==2
    assert ma["metrics"]["Riesgo bajo atendido"]==1
    assert ms["metrics"]["Riesgo bajo atendido"]==1
    assert ms["metrics"]["Riesgo alto atendido"]==1
    assert ma["metrics"]["Coincidencia con sugerencia"]==1
    assert ms["metrics"]["Coincidencia con sugerencia"]==pytest.approx(.5)
    assert ma["metrics"]["Con justificación"] is None
    assert ms["metrics"]["Con justificación"]==1
    assert store.unread("gerente")==1
    assert store.unread("analista","A-017")==0
    assert store.unread("analista","A-022")==0
    assert store.set_targets_batch({"Decisiones mensuales":70},"Mariana")
    assert store.targets()["Decisiones mensuales"]==70
    assert store.unread("analista","A-017")==1
    assert store.unread("analista","A-022")==1
    assert store.messages("analista","A-017")[0]["kind"]=="KPI"
    assert store.messages("analista","A-022")[0]["kind"]=="KPI"
    with pytest.raises(PermissionError):
        store.save_decision("loan-sofia-1","A-017","Aceptar","Aceptar",
                            .04,.05,.159)


def test_mail_for_sofia_is_private_to_her_demo_profile(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"mail.sqlite")
    store.initialize(.159)
    store.send_internal_message("gerente",None,"Mariana",
        "analista","A-022","Meta de Sofía","Revisa tus indicadores mensuales.")
    assert store.inbox_counts("analista","A-022")["total"]==1
    assert store.inbox_counts("analista","A-017")["total"]==0
    assert store.sent_messages("gerente")[0]["analyst_id"]=="A-022"
