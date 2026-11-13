"""Vistas Streamlit de productividad mensual de la demo: analista y consola gerente."""
from __future__ import annotations
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.monthly_kpis import KPI_SPECS, KPI_MAP, monthly_summary, level, progress, fmt
from src import store
from src.analyst_palette import analyst_color, GOAL_COLOR

ANALYSTS=(("Adrián Pérez","A-017","AP"),("Sofía Reyes","A-022","SR"))
COLOR={"met":"#56dca0","mid":"#f2c46e","low":"#ee9ba5","na":"#b0bdb5"}
BG={"met":"rgba(47,108,74,.25)","mid":"rgba(103,76,32,.20)",
    "low":"rgba(106,48,54,.23)","na":"rgba(38,49,43,.2)"}

STYLE="""
<style>
.ac-month-head {margin:.15rem 0 1.1rem}
.ac-month-tag {font-size:.78rem;font-weight:750;color:#69e0aa;letter-spacing:.12em}
.ac-month-title {font-size:1.8rem;font-weight:790;line-height:1.25;color:#f3faf5;letter-spacing:-.035em}
.ac-month-sub {font-size:.87rem;color:#a9bcb0;line-height:1.5;margin-top:.35rem}
.ac-month-card {height:172px;min-height:172px;overflow:hidden;box-sizing:border-box;
  border-radius:15px;padding:15px 16px 13px;border:1px solid rgba(132,166,148,.24);
  background:linear-gradient(125deg,var(--ac-bg),rgba(15,24,20,.82) 77%);
  box-shadow:0 7px 22px rgba(0,0,0,.13);position:relative;margin-bottom:12px}
.ac-month-card::before {content:"";position:absolute;top:0;left:14px;right:14px;
  height:2px;background:linear-gradient(90deg,var(--ac-color),transparent)}
.ac-month-card .label {font-weight:670;color:#d9e5dc;font-size:.85rem;line-height:1.25;
  white-space:normal;overflow-wrap:break-word;min-height:34px}
.ac-month-card .reading {color:var(--ac-color);font-size:1.64rem;font-weight:820;
  letter-spacing:-.045em;margin-top:4px;line-height:1.18;overflow-wrap:break-word}
.ac-month-card .goal {color:#b4c6ba;font-size:.77rem;margin-top:3px;min-height:22px}
.ac-month-card .track {height:8px;border-radius:20px;background:#29342e;overflow:hidden;margin-top:7px}
.ac-month-card .fill {height:8px;border-radius:20px;background:var(--ac-color)}
.ac-month-card .detail {font-size:.72rem;color:#a4b5ac;margin-top:5px;line-height:1.35}
.ac-profile {display:flex;align-items:center;gap:12px;padding:.6rem 0}
.ac-avatar {width:45px;height:45px;flex:none;border-radius:50%;display:grid;
  place-items:center;border:1px solid #477f60;color:#91f2bf;background:#1c3126;font-weight:800}
.ac-profile-name {font-weight:710;font-size:1rem;color:#eff6ef}
.ac-profile-sub {font-size:.8rem;color:#afc4b4}
@media(max-width:900px){.ac-month-title{font-size:1.4rem}.ac-month-card{padding:12px;
  height:180px;min-height:180px}.ac-month-card .reading{font-size:1.35rem}}
</style>
"""


def _head(title, subtitle, tag):
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown(
        f'<div class="ac-month-head"><div class="ac-month-tag">{html.escape(tag)}</div>'
        f'<div class="ac-month-title">{html.escape(title)}</div>'
        f'<div class="ac-month-sub">{html.escape(subtitle)}</div></div>',
        unsafe_allow_html=True)


def _metric_card(spec, value, goal, note=""):
    key,title,kind,default,desc=spec
    status=level(value,goal)
    advance=progress(value,goal)
    progress_text="Sin base para calcular" if advance is None else f"{advance:.0%} de la meta"
    reached=0 if advance is None else min(advance,1.0)*100
    color=COLOR[status]
    bg=BG[status]
    return (
        f'<div class="ac-month-card" style="--ac-color:{color};--ac-bg:{bg}">'
        f'<div class="label">{html.escape(title)}</div>'
        f'<div class="reading">{html.escape(fmt(key,value))}</div>'
        f'<div class="goal">Meta gerencial*: {html.escape(fmt(key,goal))}</div>'
        f'<div class="track"><div class="fill" style="width:{reached:.2f}%"></div></div>'
        f'<div class="detail">{html.escape(progress_text if not note else note+" · "+progress_text)}</div>'
        '</div>'
    )


def format_kpi_chart(fig,height=340):
    """Leyenda bajo los ejes, nunca superpuesta al título ni a los datos."""
    import plotly.graph_objects as go
    has_pie=any(isinstance(trace,go.Pie) for trace in fig.data)
    legend=fig.layout.showlegend
    if legend is None:
        legend=len(fig.data)>1 or has_pie
    fig.update_layout(
        height=max(height,390) if legend else max(height,345),
        margin=dict(l=35,r=25,t=65,b=115 if legend else 60),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dceae1",size=12),
        title_font=dict(size=16,color="#eff8f2"),
        showlegend=legend,
        legend=dict(orientation="h",yanchor="top",y=-0.36,
                    xanchor="center",x=0.5,font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(145,169,151,.10)",zeroline=False,
                   automargin=True,title_standoff=10),
        yaxis=dict(gridcolor="rgba(145,169,151,.10)",zeroline=False,
                   automargin=True,title_standoff=10)
    )
    return fig


def _chart(fig,height=340):
    format_kpi_chart(fig,height)
    st.plotly_chart(fig,use_container_width=True,
                    config={"displayModeBar":False,"responsive":True})


def _goal_value(targets,key):
    return float(targets.get(key,KPI_MAP[key][3]))


def render_analyst_month(name,analyst_id,score_df):
    targets=store.targets()
    records=store.decisions_map(analyst_id)
    stats=monthly_summary(records,analyst_id)
    count_all=len(records)
    total_assigned=int(score_df["ANALISTA_ID"].eq(analyst_id).sum())
    pending=max(0,total_assigned-count_all)
    _head("Mis indicadores · Analista",
          f"{name} · {stats['period'].capitalize()} · avances contra las metas mensuales fijadas por gerencia*",
          "AUTOCREDIT / SEGUIMIENTO MENSUAL")

    info1,info2,info3=st.columns(3,gap="small")
    info1.metric("Cartera TEST asignada*",f"{total_assigned:,}")
    info2.metric("Pendientes en la bandeja*",f"{pending:,}")
    info3.metric("Decisiones registradas este mes",f"{stats['count']:,}")
    st.caption("* Las metas son definidas por gerencia y se comparten entre perfiles. "
               "Las solicitudes de TEST se asignan de forma demostrativa. "
               "Solo cuentan préstamos distintos con última decisión registrada en el mes local.")

    for start in (0,3):
        cols=st.columns(3,gap="small")
        for col,spec in zip(cols,KPI_SPECS[start:start+3]):
            key=spec[0];v=stats["metrics"][key];goal=_goal_value(targets,key)
            with col:
                st.markdown(_metric_card(spec,v,goal),unsafe_allow_html=True)

    st.caption("Semáforos: rojo <50% de la meta; ámbar 50–99%; verde ≥100%. "
               "Una tasa sin casos suficientes se presenta como «—». "
               "El cumplimiento de metas no mide por sí solo la calidad de la decisión.")

    left,right=st.columns([1.18,1],gap="large")
    with left:
        st.markdown("#### Evolución de decisiones este mes")
        day=np.arange(1,stats["month_days"]+1)
        real=[v if i<stats["day"] else None for i,v in enumerate(stats["cumulative"])]
        goal=_goal_value(targets,"Decisiones mensuales")
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=day,y=day*goal/stats["month_days"],mode="lines",
                  name="Ritmo de meta (referencia)",line=dict(color="#e9ba66",dash="dash",width=2)))
        fig.add_trace(go.Scatter(x=day,y=real,mode="lines+markers",
                  name="Registradas",line=dict(color="#5de3aa",width=3),marker=dict(size=5)))
        fig.update_xaxes(title="Día del mes",dtick=max(1,stats["month_days"]//6))
        fig.update_yaxes(title="Casos distintos")
        _chart(fig,315)
    with right:
        st.markdown("#### Decisiones registradas por tipo")
        composition=stats["decisions"]
        if sum(composition.values()):
            fig=go.Figure(go.Pie(
                labels=list(composition),values=list(composition.values()),hole=.64,
                marker=dict(colors=["#5add9f","#eec36d","#e98793"]),
                textinfo="percent+label",textposition="outside"))
            fig.update_layout(showlegend=False)
            _chart(fig,315)
        else:
            st.info("Sin decisiones este mes. La distribución aparecerá después de registrar solicitudes.")

    left,right=st.columns([1.15,.85],gap="large")
    with left:
        st.markdown("#### Casos atendidos por nivel de riesgo")
        cats=["Riesgo alto atendido","Riesgo medio atendido","Riesgo bajo atendido"]
        short=["Alto","Medio","Bajo"]
        fig=go.Figure()
        fig.add_trace(go.Bar(x=short,y=[stats["metrics"][k] for k in cats],
                    name="Registrados",marker_color="#5bd8a6"))
        fig.add_trace(go.Bar(x=short,y=[_goal_value(targets,k) for k in cats],
                    name="Meta gerencial",marker_color="#6b8878"))
        fig.update_layout(barmode="group",yaxis_title="Solicitudes del mes")
        _chart(fig,325)
    with right:
        st.markdown("#### Indicadores de procedimiento")
        rate_keys=["Coincidencia con sugerencia","Con justificación"]
        labels=["Coincidencia XGBoost","Excepciones justificadas"]
        fig=go.Figure()
        fig.add_trace(go.Bar(x=labels,y=[100*_goal_value(targets,k) for k in rate_keys],
                             name="Meta",marker_color="#6b8878"))
        fig.add_trace(go.Bar(x=labels,
               y=[100*stats["metrics"][k] if stats["metrics"][k] is not None else None for k in rate_keys],
               name="Actual",marker_color="#5bd8a6"))
        fig.update_layout(barmode="group",yaxis_title="Porcentaje (%)",
                          yaxis_range=[0,110])
        _chart(fig,325)
        st.caption("La coincidencia no sustituye la revisión humana. "
                   "Sin excepciones, la tasa de justificación no es evaluable.")

    with st.expander("Ver decisiones que sustentan los KPI de este mes"):
        if stats["rows"]:
            table=pd.DataFrame(stats["rows"])
            table["Registrada (CDMX)"]=table["_local_dt"].map(
                lambda d:d.strftime("%d/%m/%Y %H:%M"))
            st.dataframe(table[["loan_id","decision","suggested","override","motivo",
                    "Registrada (CDMX)"]].rename(columns={
                        "loan_id":"Loan ID","decision":"Decisión",
                        "suggested":"XGBoost recomendó","override":"Excepción",
                        "motivo":"Motivo"}),hide_index=True,use_container_width=True)
        else:
            st.info("Aún no se registran decisiones de este analista en el mes actual.")

    st.caption("Fuente: decisiones de SQLite de esta instancia. No hay fechas reales de "
               "recepción ni un registro histórico inmutable de cada modificación. "
               "No se estiman tiempos de respuesta ni calidad crediticia futura.")


@st.dialog("Confirmar actualización de metas mensuales")
def _confirm_targets(changes,manager):
    from src.monthly_kpis import fmt
    current=store.targets()
    st.warning("Los cambios se aplicarán a ambos analistas y generarán un aviso en sus bandejas.",
               icon=":material/notification_important:")
    for key,value in changes.items():
        st.write(f"**{KPI_MAP[key][1]}:** {fmt(key,current.get(key,KPI_MAP[key][3]))} → **{fmt(key,value)}**")
    col1,col2=st.columns(2)
    if col1.button("Cancelar",use_container_width=True):
        st.rerun()
    if col2.button("Confirmar y notificar",type="primary",use_container_width=True):
        if store.set_targets_batch(changes,manager):
            st.session_state["target_save_notice"]=True
        st.rerun()


def render_manager_month(manager):
    targets=store.targets()
    records=store.decisions()
    summaries={aid:monthly_summary(records,aid) for _,aid,_ in ANALYSTS}
    period=next(iter(summaries.values()))["period"]
    _head("Consola de metas e indicadores",
          f"Control mensual de {period} · Metas comunes y ranking operativo de analistas",
          "GERENCIA / KPI MENSUALES")

    if st.session_state.pop("target_save_notice",False):
        st.success("Metas guardadas. Se enviaron notificaciones a los analistas.")
    st.caption("Los KPI de la bandeja y de Mis indicadores consultan estas mismas metas*. "
               "Los valores reflejan decisiones guardadas, no productividad simulada.")

    cols=st.columns(2,gap="medium")
    for column,(person,aid,initials) in zip(cols,ANALYSTS):
        stats=summaries[aid]
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<div class="ac-profile"><div class="ac-avatar">{initials}</div>'
                    f'<div><div class="ac-profile-name">{html.escape(person)}</div>'
                    f'<div class="ac-profile-sub">Analista {aid} · perfil de prueba*</div></div></div>',
                    unsafe_allow_html=True)
                c1,c2,c3=st.columns(3)
                c1.metric("Decisiones mes",str(stats["count"]))
                c2.metric("Avance meta",f'{progress(stats["count"],_goal_value(targets,"Decisiones mensuales")):.0%}')
                c3.metric("Excepciones",str(stats["overrides"]))
                st.progress(min(1.0,stats["count"]/_goal_value(targets,"Decisiones mensuales")))
                st.caption(f'Meta mensual: {fmt("Decisiones mensuales",_goal_value(targets,"Decisiones mensuales"))} decisiones')

    st.markdown("### Comparar desempeño por indicador")
    selected=st.selectbox("Selecciona el KPI del ranking", [x[0] for x in KPI_SPECS],
                          format_func=lambda k: KPI_MAP[k][1],key="manager_kpi_selected")
    goal=_goal_value(targets,selected)
    ranks=[]
    for person,aid,_initials in ANALYSTS:
        value=summaries[aid]["metrics"][selected]
        advancement=progress(value,goal)
        ranks.append({"Analista":person,"ID":aid,
                      "Resultado":fmt(selected,value),
                      "Meta":fmt(selected,goal),
                      "Avance":f'{advancement:.0%}' if advancement is not None else "—",
                      "Estado":"Sin base" if advancement is None else
                              "Meta lograda" if advancement >= 1 else "En progreso",
                      "_sort":-1 if advancement is None else advancement})
    ranked=pd.DataFrame(ranks).sort_values("_sort",ascending=False)
    st.dataframe(ranked.drop(columns="_sort"),hide_index=True,use_container_width=True)
    fig=go.Figure()
    mult=100 if KPI_MAP[selected][2]=="rate" else 1
    for person,aid,_ in ANALYSTS:
        value=summaries[aid]["metrics"][selected]
        fig.add_trace(go.Bar(
            x=[person.split()[0]],y=[value*mult if value is not None else None],
            name=person.split()[0],marker_color=analyst_color(aid),
            text=[f"{value*mult:.1f}" if value is not None else "—"],
            textposition="outside"))
    reference=goal*mult
    fig.add_hline(y=reference,line_dash="dash",line_color=GOAL_COLOR,
                  annotation_text="Meta gerencial")
    fig.update_layout(yaxis_title="Porcentaje (%)" if KPI_MAP[selected][2]=="rate" else "Solicitudes",
                      showlegend=True)
    _chart(fig,390)

    st.markdown("### Metas que controla gerencia")
    st.caption("Todas son mensuales y aplican a cada analista. Los tres KPI de riesgo "
               "cuentan solicitudes evaluadas según la recomendación XGBoost; "
               "no establecen cuotas para aprobar o rechazar créditos.")

    changes={}
    with st.form("monthly_goals_form"):
        grid=st.columns(3,gap="medium")
        for index,spec in enumerate(KPI_SPECS):
            key,label,kind,default,desc=spec
            value=_goal_value(targets,key)
            with grid[index%3]:
                if kind=="rate":
                    entered=st.number_input(label+" · meta (%)",
                           min_value=1.0,max_value=100.0,step=1.0,value=float(round(value*100,2)),
                           key=f"goal_rate_{index}_{value}")
                    changes[key]=entered/100
                else:
                    entered=st.number_input(label+" · meta (casos)",
                           min_value=1,max_value=100000,step=1,value=int(value),
                           key=f"goal_count_{index}_{value}")
                    changes[key]=float(entered)
                st.caption(desc)
        submitted=st.form_submit_button("Revisar cambios de metas",type="primary",
                  use_container_width=True,icon=":material/tune:")
    if submitted:
        changed={key:value for key,value in changes.items()
                 if abs(_goal_value(targets,key)-value)>1e-9}
        if changed:
            _confirm_targets(changed,manager)
        else:
            st.info("No hiciste cambios respecto de las metas guardadas.")

    st.markdown("### Visión de equipo")
    team_cols=st.columns(2,gap="large")
    with team_cols[0]:
        fig=go.Figure()
        days=np.arange(1,next(iter(summaries.values()))["month_days"]+1)
        for person,aid,_ in ANALYSTS:
            d=summaries[aid]
            fig.add_trace(go.Scatter(x=days,
                y=[v if i<d["day"] else None for i,v in enumerate(d["cumulative"])],
                mode="lines+markers",name=person,marker=dict(size=5),
                line=dict(color=analyst_color(aid),width=3)))
        fig.update_layout(title="Decisiones acumuladas del mes",xaxis_title="Día",
                          yaxis_title="Solicitudes distintas")
        _chart(fig,320)
    with team_cols[1]:
        report=[]
        for person,aid,_ in ANALYSTS:
            m=summaries[aid]["metrics"]
            for key in ("Riesgo alto atendido","Riesgo medio atendido","Riesgo bajo atendido"):
                report.append((person,key,m[key]))
        fig=go.Figure()
        for person,aid,_ in ANALYSTS:
            subset=[x for x in report if x[0]==person]
            fig.add_trace(go.Bar(x=["Alto","Medio","Bajo"],y=[x[2] for x in subset],
                                 name=person,marker_color=analyst_color(aid)))
        fig.update_layout(title="Casos atendidos por nivel XGBoost",barmode="group",
                          yaxis_title="Solicitudes del mes")
        _chart(fig,320)

    st.caption("* Asignaciones de TEST, perfiles y metas son parte de la simulación académica. "
               "No se asigna una calificación laboral por volumen ni se incentiva la aprobación o el rechazo. "
               "Los KPI cambian inmediatamente tras guardar y confirmar en esta instancia SQLite.")
