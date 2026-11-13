"""Vista ejecutiva mensual de gerencia: área, analistas, DTI y sesiones.

Todas las cifras operativas proceden de decisiones e incidencias realmente
registradas en la instancia SQLite. Los perfiles y asignaciones son ficticios.
"""
from __future__ import annotations
import html
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import store
from src.kpi_views import ANALYSTS
from src.monthly_kpis import KPI_SPECS, KPI_MAP, local_now, monthly_summary, progress, fmt, level
from src.ops_monitor import (
    CATEGORIES, incident_month_summary, incidents, monthly_session_stats, STATES,
)

STYLES="""
<style>
.ac-mgr-top{height:24px}
.ac-mgr-eyebrow{font-size:.74rem;letter-spacing:.14em;color:#66e3a4;font-weight:780}
.ac-mgr-title{font-size:1.9rem;letter-spacing:-.04em;line-height:1.2;
 color:#eff8f1;font-weight:830;margin:5px 0 8px}
.ac-mgr-sub{font-size:.88rem;color:#aac1b3;line-height:1.5;margin-bottom:21px}
.ac-mgr-kpi{box-sizing:border-box;min-height:160px;border-radius:16px;padding:18px 18px 14px;
 border:1px solid rgba(123,169,143,.27);
 background:linear-gradient(125deg,var(--panel),rgba(16,23,20,.95) 82%);
 box-shadow:0 12px 24px rgba(0,0,0,.10);position:relative;margin-bottom:8px;overflow:hidden}
.ac-mgr-kpi:before{content:"";position:absolute;top:0;left:13px;right:13px;height:2px;
 background:linear-gradient(90deg,var(--tone),transparent)}
.ac-mgr-label{font-size:.82rem;color:#d7e6dc;font-weight:700;min-height:20px}
.ac-mgr-val{font-size:1.7rem;color:var(--tone);font-weight:840;
 line-height:1.18;letter-spacing:-.045em;margin:8px 0;overflow-wrap:anywhere}
.ac-mgr-desc{font-size:.75rem;color:#a7b9ad;line-height:1.4}
.ac-mgr-track{height:7px;background:#283930;border-radius:20px;overflow:hidden;margin-top:8px}
.ac-mgr-track>div{height:100%;background:var(--tone);border-radius:20px}
.ac-mgr-section{margin:24px 0 8px;color:#f2f8f3;font-size:1.15rem;font-weight:760}
.ac-mgr-smallnote{font-size:.78rem;color:#a1b9aa;line-height:1.5}
.ac-mgr-avatar{display:inline-flex;width:31px;height:31px;align-items:center;justify-content:center;
 border-radius:50%;background:#1c3628;color:#7ee6ac;border:1px solid #45795c;font-weight:800;margin-right:8px}
@media(max-width:800px){.ac-mgr-title{font-size:1.45rem}.ac-mgr-kpi{min-height:165px;padding:12px}
 .ac-mgr-val{font-size:1.45rem}}
</style>
"""
PALETTES={
    "green":("#68e9aa","rgba(40,91,61,.34)"),
    "amber":("#f2c66f","rgba(105,79,37,.24)"),
    "red":("#f29aa5","rgba(98,41,47,.29)"),
    "neutral":("#d3dfd6","rgba(53,65,56,.18)"),
}
ANALYST_IDS={aid:person for person,aid,_ in ANALYSTS}


def _kcard(label,value,detail,tone="green",p=None):
    fg,bg=PALETTES[tone]
    bar="" if p is None else f'<div class="ac-mgr-track"><div style="width:{min(max(p,0),1)*100:.1f}%"></div></div>'
    return (f'<div class="ac-mgr-kpi" style="--tone:{fg};--panel:{bg}">'
            f'<div class="ac-mgr-label">{html.escape(label)}</div>'
            f'<div class="ac-mgr-val">{html.escape(str(value))}</div>'
            f'<div class="ac-mgr-desc">{html.escape(detail)}</div>{bar}</div>')


def format_executive_chart(fig,height=380,horizontal=False):
    """Reserva una zona bajo el eje X para leyendas sin superposición."""
    is_pie=any(isinstance(trace,go.Pie) for trace in fig.data)
    show_legend=fig.layout.showlegend
    if show_legend is None:
        show_legend=(len(fig.data)>1 or is_pie)
    fig.update_layout(
        height=max(height,390) if show_legend else max(height,345),
        margin=dict(l=195 if horizontal else 35,r=35,t=64,
                    b=118 if show_legend else 65),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d8e7db",size=12),
        title_font=dict(size=16,color="#ecf7f0"),
        showlegend=show_legend,
        legend=dict(orientation="h",yanchor="top",y=-0.35,
                    xanchor="center",x=0.5,font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(151,172,155,.10)",zeroline=False,
                   automargin=True,title_standoff=12),
        yaxis=dict(gridcolor="rgba(151,172,155,.13)",zeroline=False,
                   automargin=True,title_standoff=10),
    )
    return fig


def _fig(fig,height=380,horizontal=False):
    format_executive_chart(fig,height=height,horizontal=horizontal)
    st.plotly_chart(fig,use_container_width=True,
                    config={"displayModeBar":False,"responsive":True})


def build_team_metrics(records, targets, reference=None):
    """Pure aggregation for tests; shared targets but per-analyst numerators."""
    reference=reference or local_now()
    individuals={aid:monthly_summary(records,aid,reference) for aid in ANALYST_IDS}
    n=sum(x["count"] for x in individuals.values())
    target=float(targets.get("Decisiones mensuales",50))*len(ANALYST_IDS)
    exc=sum(x["overrides"] for x in individuals.values())
    justified=sum(x["justified"] for x in individuals.values())
    agreement=(sum(x["matches"] for x in individuals.values())/n) if n else None
    return dict(individuals=individuals,decisions=n,decision_goal=target,
                completion=progress(n,target),exceptions=exc,justified=justified,
                agreement=agreement,
                justification_rate=justified/exc if exc else None,
                period=next(iter(individuals.values()))["period"])


def render_manager_overview(scores=None):
    st.markdown(STYLES,unsafe_allow_html=True)
    st.markdown('<div class="ac-mgr-top"></div>',unsafe_allow_html=True)
    targets=store.targets()
    team=build_team_metrics(store.decisions(),targets)
    sessions=monthly_session_stats()
    tickets=incidents(limit=100000)
    dti=incident_month_summary(tickets)
    dti_target=float(targets.get("Resolución DTI mensual",.99))
    reached=team["completion"]
    dti_reached=progress(dti["rate"],dti_target)
    total_closed_sessions=sum(x["closed"] for x in sessions.values())
    total_minutes=sum(x["minutes"] or 0 for x in sessions.values())
    month=team["period"].capitalize()

    st.markdown(
        f'<div class="ac-mgr-eyebrow">AUTOCREDIT / CONTROL DIRECTIVO MENSUAL</div>'
        f'<div class="ac-mgr-title">Métricas del área</div>'
        f'<div class="ac-mgr-sub">Mariana Torres · {html.escape(month)} · '
        'indicadores operativos consolidados de Adrián, Sofía y soporte DTI.</div>',
        unsafe_allow_html=True)

    cards=[
        ("Decisiones registradas",f'{team["decisions"]:,} / {team["decision_goal"]:,.0f}',
         "Suma de los dos objetivos mensuales fijados por gerencia*",
         "green" if reached>=1 else "amber" if reached>=.5 else "red",reached),
        ("Meta mensual del equipo",f'{reached:.1%}',
         "Avance en decisiones registradas por ambos analistas",
         "green" if reached>=1 else "amber" if reached>=.5 else "red",reached),
        ("Incidencias DTI resueltas",
         f'{dti["solved"]} / {dti["total"]}',
         "Incidencias abiertas este mes y resueltas",
         "green" if dti_reached is not None and dti_reached>=1 else "amber" if dti_reached is not None and dti_reached>=.5 else "neutral",dti_reached),
        ("Resolución mensual DTI",f'{dti["rate"]:.1%}' if dti["rate"] is not None else "—",
         f'Meta de referencia: {dti_target:.0%} · sin casos = no evaluable',
         "green" if dti_reached is not None and dti_reached>=1 else "amber" if dti_reached is not None and dti_reached>=.5 else "neutral",dti_reached),
        ("Excepciones de crédito",f'{team["exceptions"]:,}',
         f'Justificadas: {team["justified"]:,} · notificación a gerencia',
         "amber" if team["exceptions"] else "green",None),
        ("Tiempo de sesión registrado",f'{total_minutes/60:.1f} h' if total_closed_sessions else "—",
         f'{total_closed_sessions} sesiones cerradas este mes · todos los perfiles',
         "neutral",None),
    ]
    for start in (0,3):
        cols=st.columns(3,gap="small")
        for col,(label,val,desc,tone,p) in zip(cols,cards[start:start+3]):
            with col:
                st.markdown(_kcard(label,val,desc,tone,p),unsafe_allow_html=True)
    st.caption("* Las metas de los dos analistas provienen de la misma consola de gerencia; "
       "las cifras son decisiones registradas este mes en SQLite, no créditos futuros ni resultados de DEFAULT. "
       "El tiempo representa el intervalo inicio-cierre de sesiones finalizadas, no tiempo de trabajo activo.")

    st.markdown('<div class="ac-mgr-section">Comparación y seguimiento por perfil</div>',
                unsafe_allow_html=True)
    f1,f2,f3=st.columns([1.1,1.5,1.1],gap="medium")
    with f1:
        profile=st.selectbox("Perfil",["Todos los perfiles","Adrián · A-017",
                           "Sofía · A-022","Soporte DTI"],key="mgr_overview_filter")
    with f2:
        selected=st.selectbox("Indicador de analistas",[x[0] for x in KPI_SPECS],
           format_func=lambda x:KPI_MAP[x][1],key="mgr_overview_metric")
    with f3:
        order=st.selectbox("Ordenar",["Mayor avance","Menor avance"],
                           key="mgr_overview_sort")

    if profile=="Soporte DTI":
        st.info("Perfil DTI seleccionado: el panel siguiente muestra sus incidencias, "
                "resolución mensual y casos pendientes. DTI no toma decisiones crediticias.")
    else:
        chosen_ids=(
           ["A-017"] if profile.startswith("Adrián") else
           ["A-022"] if profile.startswith("Sofía") else ["A-017","A-022"])
        metric_type=KPI_MAP[selected][2]
        goal=float(targets.get(selected,KPI_MAP[selected][3]))
        ranking=[]
        for aid in chosen_ids:
            person=ANALYST_IDS[aid]
            stats=team["individuals"][aid]
            value=stats["metrics"][selected]
            pct=progress(value,goal)
            ranking.append({"Analista":person,"Identificador":aid,
                 "Registrado":fmt(selected,value),"Meta":fmt(selected,goal),
                 "Cumplimiento":f"{pct:.1%}" if pct is not None else "—",
                 "Estado":"No evaluable" if pct is None else
                          "Meta lograda" if pct>=1 else "En progreso",
                 "_pct":-1 if pct is None else pct})
        ranking.sort(key=lambda r:r["_pct"],reverse=order=="Mayor avance")
        st.dataframe(pd.DataFrame(ranking).drop(columns="_pct"),hide_index=True,
                     use_container_width=True)
        left,right=st.columns(2,gap="large")
        with left:
            fig=go.Figure()
            labels=[ANALYST_IDS[aid].split()[0] for aid in chosen_ids]
            vals=[team["individuals"][aid]["metrics"][selected] for aid in chosen_ids]
            mult=100 if metric_type=="rate" else 1
            fig.add_trace(go.Bar(x=labels,y=[v*mult if v is not None else None for v in vals],
                         name="Resultado",marker_color="#64dca6",text=[
                             f"{v*mult:.1f}" if v is not None else "—" for v in vals
                         ],textposition="outside"))
            fig.add_hline(y=goal*mult,line_dash="dash",line_color="#f6c76a",
                          annotation_text="Meta de gerencia")
            fig.update_layout(title="Resultado vs. meta individual",
                       showlegend=False,
                       yaxis_title="Porcentaje (%)" if metric_type=="rate" else "Casos")
            _fig(fig,365)
        with right:
            fig=go.Figure()
            colors={"A-017":"#5ed6a0","A-022":"#f4bf68"}
            for aid in chosen_ids:
                stats=team["individuals"][aid]
                days=np.arange(1,stats["month_days"]+1)
                curve=[v if idx<stats["day"] else None for idx,v in enumerate(stats["cumulative"])]
                fig.add_trace(go.Scatter(x=days,y=curve,mode="lines+markers",
                   name=ANALYST_IDS[aid].split()[0],
                   line=dict(color=colors[aid],width=3),marker=dict(size=4)))
            fig.add_trace(go.Scatter(x=[1,stats["month_days"]],
                      y=[goal/stats["month_days"],goal],
                      mode="lines",name="Meta del mes",
                      line=dict(color="#9cafa2",dash="dash")))
            fig.update_layout(title="Decisiones acumuladas del mes",
                               xaxis_title="Día del mes",yaxis_title="Decisiones")
            _fig(fig,410)

        st.markdown("**Indicadores de gestión por analista**")
        table=[]
        for aid in chosen_ids:
            stats=team["individuals"][aid]
            for key,short,kind,default,description in KPI_SPECS:
                value=stats["metrics"][key]
                target=float(targets.get(key,default))
                ratio=progress(value,target)
                table.append({"Analista":ANALYST_IDS[aid],
                  "KPI":short,"Registrado":fmt(key,value),
                  "Meta":fmt(key,target),
                  "Avance":f"{ratio:.0%}" if ratio is not None else "—",
                  "Semáforo":("Sin base" if ratio is None else
                              "Verde" if ratio>=1 else "Ámbar" if ratio>=.5 else "Rojo")})
        st.dataframe(pd.DataFrame(table),hide_index=True,use_container_width=True,height=310)
        st.caption("Los indicadores de atención cuentan el riesgo sugerido por XGBoost, "
                   "no obligan a aceptar o rechazar solicitudes. El ranking no representa "
                   "por sí solo calidad crediticia.")

    st.markdown('<div class="ac-mgr-section">Supervisión de incidencias · DTI</div>',
                unsafe_allow_html=True)
    a,b,c,d=st.columns(4,gap="small")
    a.metric("Reportadas este mes",dti["total"])
    b.metric("Sin resolver",dti["open"]+dti["review"])
    c.metric("En revisión",dti["review"])
    d.metric("Resueltas",dti["solved"])
    l,r=st.columns([1.2,1],gap="large")
    with l:
        categories=[x["category"] for x in dti["rows"]]
        values=[categories.count(x) for x in CATEGORIES]
        if dti["total"]:
            # Barras horizontales: etiquetas completas, sin diagonales.
            nonzero=[(cat,n) for cat,n in zip(CATEGORIES,values) if n>0]
            categories_show=[p[0] for p in nonzero][::-1]
            values_show=[p[1] for p in nonzero][::-1]
            fig=go.Figure(go.Bar(
                x=values_show,y=categories_show,orientation="h",
                marker_color="#54d9a1",text=values_show,
                textposition="outside",cliponaxis=False))
            fig.update_layout(
                title="Incidencias por categoría",
                xaxis_title="Número de reportes",showlegend=False,
                xaxis=dict(range=[0,max(values_show)*1.25+0.4],dtick=1),
                yaxis=dict(type="category",automargin=True),
            )
            _fig(fig,385,horizontal=True)
        else:
            st.info("Sin reportes de DTI este mes. La distribución por categoría aparecerá cuando existan incidencias.")
    with r:
        fig=go.Figure(go.Pie(
            labels=list(STATES),values=[dti["open"],dti["review"],dti["solved"]],
            hole=.67,marker=dict(colors=["#ee959d","#e9c068","#59d8a0"])))
        fig.update_layout(title="Estado de casos DTI",showlegend=True)
        _fig(fig,390) if dti["total"] else st.info(
            "Sin incidencias DTI durante este mes: la resolución no es evaluable.")
    with st.expander("Ver detalle de incidencias reportadas"):
        st.dataframe(pd.DataFrame([{
          "Ticket":f'#{t["id"]}',"Analista":ANALYST_IDS.get(t["analyst_id"],t["analyst_id"]),
          "Tipo":t["category"],"Prioridad":t["priority"],
          "Estado":t["status"],"Loan ID":t.get("loan_id") or "—",
          "Asunto":t["title"],"Resolución":t["resolution_note"] or "Pendiente"
        } for t in tickets]),hide_index=True,use_container_width=True)
        st.caption("Los mensajes de alerta llegan al buzón de DTI y de Mariana. "
                   "La resolución se registra desde el perfil Especialista DTI.")

    st.markdown('<div class="ac-mgr-section">Sesiones en plataforma · todos los perfiles</div>',
                unsafe_allow_html=True)
    session_rows=[]
    for (role,aid),record in sessions.items():
        session_rows.append({
            "Perfil":record["name"],"Rol":role.upper(),
            "Sesiones cerradas":record["closed"],
            "Tiempo inicio-cierre":f'{record["minutes"]:.1f} min' if record["minutes"] is not None else "—",
            "Sin cierre registrado":record["open_without_logout"],
        })
    st.dataframe(pd.DataFrame(session_rows),hide_index=True,use_container_width=True)
    st.caption("La duración se mide solo cuando el perfil pulsa Cerrar sesión. "
               "No mide conexión real continua ni actividad frente a la pantalla. "
               "Una pestaña cerrada sin logout queda pendiente de cierre; no se infieren horas.")

    st.markdown('<div class="ac-mgr-section">Metas y política</div>',unsafe_allow_html=True)
    st.info("Las metas mensuales operativas se editan en **Analistas y KPI**, "
            "con confirmación y avisos a ambos analistas. "
            "El objetivo de resolución DTI es 99% de las incidencias reportadas "
            "durante el mes; no implica que hayan existido incidencias.")
