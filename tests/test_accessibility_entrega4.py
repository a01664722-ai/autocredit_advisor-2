"""Pruebas de accesibilidad de Entrega 4 sin alterar motor ni datos."""
from pathlib import Path
import re

import pytest
import plotly.graph_objects as go
from src import accessibility_theme as theme
from src import profile_state
from scripts.check_cvd_b3 import check_palette, evaluate, simulated, MATRICES


def test_cvd_six_palette_modes_all_pass_under_both_deficiencies():
    assert check_palette()==[]
    rows=evaluate()
    assert len(rows)==18
    assert {r["vista"] for r in rows}=={"normal","protanopia","deuteranopia"}
    assert min(r["contraste"] for r in rows)>=4.5
    for label,decorated in theme.SIGNS.items():
        assert decorated.endswith(label)
        assert decorated.split(" ",1)[0] in ("✓","◇","✕")


def test_theme_is_explicit_and_respects_mode_switch():
    assert theme.visual_preferences({})==("Oscuro",False)
    assert theme.visual_preferences({"ac_visual_theme":"Claro","ac_cvd_mode":True})==("Claro",True)
    assert theme.visual_preferences({"ac_visual_theme":"INVALIDO"})==("Oscuro",False)
    light=theme.theme_css("Claro",True)
    dark=theme.theme_css("Oscuro",True)
    assert "#f6f8f7" in light and "#15251e" in light
    assert "#0f1110" in dark
    assert "#005A8C" in light and "#74D5FF" in dark
    assert ".ac-p1-kpi" in light and ".ac-p2-card" in light
    assert ".ac-mgr-kpi" in light and ".ac-support-card" in light
    assert ".ac-mail-metric" in light and ".ac-audit-card" in light
    assert ".ac0-cardtitle" in light
    with pytest.raises(ValueError):
        theme.theme_css("sepia",False)


def test_options_keep_labels_while_profiles_change():
    state={"ac_visual_theme":"Claro","ac_cvd_mode":True,"_demo_login_profile":"A"}
    profile_state.demo_sign_out(state)
    assert "ac_visual_theme" in state and state["ac_cvd_mode"] is True
    assert "_demo_login_profile" not in state
    assert theme.decision_label("Rechazar")=="✕ Rechazar"
    assert theme.decision_label("Condicionar")=="◇ Condicionar"
    assert theme.decision_label("Aceptar")=="✓ Aceptar"
    assert theme.decision_label("Otro")=="Otro"


def test_plotly_visible_shapes_with_cvd(monkeypatch):
    monkeypatch.setattr(theme,"visual_preferences",lambda:("Claro",True))
    fig=go.Figure()
    fig.add_trace(go.Bar(x=["alto"],y=[10],name="Aceptar"))
    fig.add_trace(go.Bar(x=["alto"],y=[7],name="Condicionar"))
    fig.add_trace(go.Scatter(x=[1,2],y=[1,2],name="Rechazar",mode="lines+markers"))
    theme.accessible_plotly(fig)
    assert fig.layout.font.color=="#17291e"
    assert fig.data[1].marker.pattern.shape=="/"
    assert fig.data[2].marker.symbol=="diamond"
    assert fig.data[2].line.dash=="dot"
    assert fig.data[0].name=="Aceptar"


def test_dashboard_has_switch_before_login_and_sidebar():
    app=Path("app_v3.py").read_text(encoding="utf-8")
    assert 'preference_controls("login")' in app
    assert 'preference_controls("sidebar")' in app
    assert app.index('preference_controls("login")') < app.index('render_login(PERSONAS)')
    assert "show_theme()" in app
    assert "'Sugerencia': vista['SUGERENCIA'].map(decision_label).to_numpy()," in app
    assert "decision=str(fila['Sugerencia']).split(' ',1)[-1]" in app
    assert "if accion in ('Aceptar', 'Condicionar', 'Rechazar')" in app
    assert "filtrada = filtrada.iloc[0:0]" in app
    assert "st.stop()" in app
    for path in ("src/kpi_views.py","src/manager_overview.py","src/support_views.py"):
        code=Path(path).read_text(encoding="utf-8")
        assert "render_accessible_chart" in code


def test_main_workflow_never_checks_out_other_branch():
    workflow=Path(".github/workflows/check_dashboard.yml").read_text(encoding="utf-8")
    assert "branches:" in workflow
    assert "- main" in workflow
    assert "ref: v3-integracion-xgboost-12v" not in workflow
    assert "python -m scripts.check_cvd_b3" in workflow
