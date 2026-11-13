"""Consistencia visual de personas y eliminación del usuario Operación en V3."""
from pathlib import Path

import pytest

from src.analyst_palette import analyst_color, ANALYST_COLORS, GOAL_COLOR
from src.access_audit import ACCESS
from src.ops_monitor import ROLES, PROFILE_KEYS, begin_session, monthly_session_stats
from src import store


def test_neutral_analyst_palette_is_fixed():
    assert analyst_color("A-017") == "#6EA8FE"
    assert analyst_color("A-022") == "#B58BFA"
    assert analyst_color("A-017") != analyst_color("A-022")
    assert GOAL_COLOR not in ANALYST_COLORS.values()
    with pytest.raises(ValueError):
        analyst_color("operacion")


def test_both_manager_screens_use_single_shared_palette():
    base = Path(__file__).resolve().parents[1]
    main = (base/"src/manager_overview.py").read_text(encoding="utf-8")
    goals = (base/"src/kpi_views.py").read_text(encoding="utf-8")
    for content in (main, goals):
        assert "from src.analyst_palette import analyst_color, GOAL_COLOR" in content
        assert content.count("marker_color=analyst_color(aid)") >= 1
        assert "line=dict(color=analyst_color(aid)" in content
        assert "colors={\"A-017\"" not in content
    assert "line_color=GOAL_COLOR" in main
    assert "line_color=GOAL_COLOR" in goals


def test_operator_not_visible_in_active_v3():
    base=Path(__file__).resolve().parents[1]
    app=(base/"app_v3.py").read_text(encoding="utf-8")
    audit=(base/"src/access_audit.py").read_text(encoding="utf-8")
    assert "Luis · Operación" not in app
    assert "('operacion',None,'Luis" not in app
    assert "elif page=='Operación':" not in app
    assert "pages=['Operación'" not in app
    assert "Luis Ramírez" not in audit
    assert "operacion" not in ROLES
    assert len(PROFILE_KEYS)==4
    assert len(ACCESS)==4


def test_removed_role_cannot_start_new_sessions(tmp_path,monkeypatch):
    monkeypatch.setattr(store, "DB", tmp_path/"palette.sqlite")
    store.initialize(.159)
    with pytest.raises(ValueError):
        begin_session("operacion", None, "Luis")
    assert ("operacion", None) not in monthly_session_stats()
