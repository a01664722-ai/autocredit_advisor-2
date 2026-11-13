"""Regresiones visuales del panel gerencial: leyendas, barras horizontales y auditoría."""
from pathlib import Path

import plotly.graph_objects as go

from src.manager_overview import format_executive_chart
from src.kpi_views import format_kpi_chart
from src.access_audit import ACCESS


def test_manager_legend_is_below_x_axis_and_title_clear():
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=[1,2],y=[0,1],name="Adrián"))
    fig.add_trace(go.Scatter(x=[1,2],y=[0,0],name="Sofía"))
    fig.add_trace(go.Scatter(x=[1,2],y=[0,2],name="Meta del mes"))
    fig.update_layout(title="Decisiones acumuladas")
    styled=format_executive_chart(fig,height=320)
    assert styled.layout.showlegend is True
    assert styled.layout.legend.orientation=="h"
    assert styled.layout.legend.y<0
    assert styled.layout.legend.yanchor=="top"
    assert styled.layout.margin.b>=105
    assert styled.layout.margin.t>=55
    assert styled.layout.height>=390


def test_manager_single_bar_avoids_unnecessary_legend():
    fig=go.Figure(go.Bar(x=["Adrián","Sofía"],y=[3,0]))
    styled=format_executive_chart(fig,height=300)
    assert styled.layout.showlegend is False
    assert styled.layout.margin.b>=50


def test_dti_horizontal_bars_leave_room_for_long_labels():
    fig=go.Figure(go.Bar(
        x=[2,1],y=["Predicción o variables","Acceso / rendimiento"],
        orientation="h",text=[2,1]))
    styled=format_executive_chart(fig,height=350,horizontal=True)
    assert styled.data[0].orientation=="h"
    assert styled.layout.margin.l>=175
    assert styled.layout.showlegend is False
    assert styled.layout.yaxis.automargin


def test_kpi_second_screen_legend_outside_plot():
    fig=go.Figure()
    fig.add_trace(go.Bar(x=["Alto","Medio","Bajo"],y=[3,2,0],name="Adrián"))
    fig.add_trace(go.Bar(x=["Alto","Medio","Bajo"],y=[0,1,1],name="Sofía"))
    styled=format_kpi_chart(fig,320)
    assert styled.layout.legend.y<0
    assert styled.layout.margin.b>=105
    assert styled.layout.height>=390


def test_manager_navigation_and_access_audit():
    root=Path(__file__).resolve().parents[1]
    app=(root/"app_v3.py").read_text(encoding="utf-8")
    mgr=(root/"src/manager_overview.py").read_text(encoding="utf-8")
    assert "pages=['Métricas del área','Analistas y KPI','Mensajes','Auditoría de accesos']" in app
    assert "elif page=='Métricas del área':" in app
    assert "elif page=='Auditoría de accesos':" in app
    assert "render_access_audit()" in app
    assert "Recorridos, controles y gobierno" not in app
    assert "orientation=\"h\"" in mgr
    assert "xaxis_tickangle=-20" not in mgr
    assert len(ACCESS)==5
    assert {x[0] for x in ACCESS}=={
        "Mariana Torres","Adrián Pérez","Sofía Reyes",
        "Especialista DTI","Luis Ramírez"
    }
