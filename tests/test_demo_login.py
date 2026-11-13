"""Pantalla 0 y cierre de sesión: aislación de controles por navegador."""
from pathlib import Path

import pytest

from src import store
from src.profile_state import (
    LOGIN_KEY, demo_current_profile, demo_sign_in, demo_sign_out
)

PERSONAS = {
    "Adrián · Analista A-017": ("analista", "A-017", "Adrián Pérez"),
    "Sofía · Analista A-022": ("analista", "A-022", "Sofía Reyes"),
    "Mariana · Gerente": ("gerente", None, "Mariana Torres"),
    "Especialista · Validación DTI": ("dti", None, "Especialista DTI"),
}


def test_access_is_initially_closed_and_checks_profile_catalog():
    state = {}
    assert demo_current_profile(state, PERSONAS) is None
    with pytest.raises(ValueError):
        demo_sign_in(state, "Perfil desconocido", PERSONAS)
    assert state == {}
    state[LOGIN_KEY] = "Perfil desconocido"
    assert demo_current_profile(state, PERSONAS) is None


@pytest.mark.parametrize("label,expected_role,expected_id", [
    ("Adrián · Analista A-017", "analista", "A-017"),
    ("Sofía · Analista A-022", "analista", "A-022"),
    ("Mariana · Gerente", "gerente", None),
    ("Especialista · Validación DTI", "dti", None),
])
def test_all_profiles_can_enter_and_sign_out(label,expected_role,expected_id):
    state={"loan_actual":"277432","pending_choice":{"loan_id":"277432"},
           "p1_pagina_v3":4,"internal_mail_analista_A-017_subject":"Borrador"}
    role,analyst_id,name=demo_sign_in(state,label,PERSONAS)
    assert (role,analyst_id)==(expected_role,expected_id)
    assert name
    assert demo_current_profile(state,PERSONAS)==label
    assert "loan_actual" not in state
    assert "pending_choice" not in state
    assert "internal_mail_analista_A-017_subject" not in state
    state.update({"page":"Mensajes","loan_actual":"999999",
                  "p1_pagina_v3":4,"unsubmitted_reason":"Temporal"})
    demo_sign_out(state)
    assert state=={}
    assert demo_current_profile(state,PERSONAS) is None


def test_logout_preserves_shared_sqlite(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"sessions.sqlite")
    store.initialize(.159)
    state={}
    demo_sign_in(state,"Sofía · Analista A-022",PERSONAS)
    store.save_decision("loan-demo-s","A-022","Aceptar","Aceptar",
                        .07,.08,.159)
    store.send_internal_message("gerente",None,"Mariana Torres",
        "analista","A-022","Aviso de meta","Consulta la nueva meta mensual.")
    demo_sign_out(state)
    assert "loan-demo-s" in store.decisions_map("A-022")
    assert store.unread("analista","A-022")==1
    demo_sign_in(state,"Adrián · Analista A-017",PERSONAS)
    assert store.decisions_map("A-017")=={}
    assert store.unread("analista","A-017")==0
    assert store.unread("analista","A-022")==1


def test_app_gates_navigation_before_model_training():
    # Verifica que el flujo de pantalla 0 detenga la ejecución sin perfil.
    app=(Path(__file__).resolve().parents[1]/"app_v3.py").read_text(encoding="utf-8")
    assert app.index("if selected_profile is None:") < app.index("@st.cache_resource")
    assert app.index("render_login(PERSONAS)") < app.index("@st.cache_resource")
    assert "demo_sign_out(st.session_state)" in app
    assert "selected=st.selectbox('Perfil de demostración*'" not in app
