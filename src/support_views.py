"""Centro de Soporte: incidentes mensuales y métricas XGBoost calculadas sobre TEST.

'Soporte' es la etiqueta visible. El rol SQLite 'dti' y la tabla
'dti_incidents' se conservan para no romper mensajes ni históricos.
"""
from __future__ import annotations

import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve

from src import store
from src.engine import COLS, LABELS
from src.monthly_kpis import local_now
from src.ops_monitor import incident_month_summary, incidents
from src.dti_views import render_dti_incidents

REPOSITORY_URL = "https://github.com/a01664722-ai/autocredit_advisor-2/tree/v3-integracion-xgboost-12v"
MODEL_COLOR = "#65D8A6"
SECONDARY_COLOR = "#A4AEB0"
PRIORITY_COLOR = "#E4AC7A"

STYLE = """
<style>
.ac-support-spacer{height:18px}
.ac-support-kicker{font-size:.75rem;font-weight:800;letter-spacing:.13em;color:#67e5a7}
.ac-support-title{font-size:clamp(1.45rem,2.2vw,1.95rem);line-height:1.23;
 font-weight:840;letter-spacing:-.035em;color:#f3faf5;margin:4px 0 8px}
.ac-support-lead{color:#b0c6b8;font-size:.88rem;line-height:1.55;margin-bottom:18px}
.ac-support-card{box-sizing:border-box;min-height:163px;height:163px;
 background:linear-gradient(135deg,rgba(32,57,42,.52),rgba(14,24,20,.91) 85%);
 border:1px solid rgba(106,168,128,.28);border-radius:15px;
 padding:16px;position:relative;overflow:hidden;margin-bottom:7px}
.ac-support-card:before{content:"";position:absolute;left:14px;right:14px;top:0;
 height:2px;background:linear-gradient(90deg,var(--tone),transparent)}
.ac-support-card .name{font-size:.82rem;color:#c8d9ce;font-weight:680;min-height:23px}
.ac-support-card .value{font-size:clamp(1.35rem,2vw,1.9rem);line-height:1.18;
 color:var(--tone);font-weight:830;margin:9px 0;overflow-wrap:anywhere}
.ac-support-card .detail{font-size:.75rem;color:#afc4b4;line-height:1.5}
.ac-support-track{height:7px;background:#2b3b32;border-radius:100px;
 margin-top:11px;overflow:hidden}
.ac-support-track span{display:block;height:100%;background:var(--tone);border-radius:100px}
.ac-support-section{font-size:1.15rem;color:#f2f9f3;font-weight:770;margin:26px 0 8px}
.ac-support-note{font-size:.83rem;color:#b5c6ba;line-height:1.5}
.ac-support-empty{border:1px solid rgba(109,167,135,.25);border-radius:14px;
 background:linear-gradient(110deg,rgba(32,57,42,.25),rgba(12,22,18,.85));
 padding:20px;font-size:.86rem;color:#abc4b4;line-height:1.5}
@media(max-width:850px){.ac-support-card{height:175px;min-height:175px;padding:12px}}
</style>
"""


def _card(label,value,detail,tone="default",progress=None):
    colors={"default":"#DDE7DF","good":"#6BE0A9",
            "attention":"#F2C675","critical":"#F49CAA"}
    fg=colors.get(tone,colors["default"])
    bar="" if progress is None else (
        '<div class="ac-support-track"><span style="width:'
        + f'{max(0,min(1,progress))*100:.1f}%"></span></div>')
    return (
        f'<div class="ac-support-card" style="--tone:{fg}">'
        f'<div class="name">{html.escape(str(label))}</div>'
        f'<div class="value">{html.escape(str(value))}</div>'
        f'<div class="detail">{html.escape(str(detail))}</div>'
        f'{bar}</div>'
    )


def _header(title,subtitle,eyebrow):
    st.markdown(STYLE,unsafe_allow_html=True)
    st.markdown(
        f'<div class="ac-support-spacer"></div>'
        f'<div class="ac-support-kicker">{html.escape(eyebrow)}</div>'
        f'<div class="ac-support-title">{html.escape(title)}</div>'
        f'<div class="ac-support-lead">{html.escape(subtitle)}</div>',
        unsafe_allow_html=True)


def _cards(values,columns=3):
    for start in range(0,len(values),columns):
        cols=st.columns(columns,gap="small")
        for col,config in zip(cols,values[start:start+columns]):
            with col:
                st.markdown(_card(**config),unsafe_allow_html=True)


def _section(title):
    st.markdown(f'<div class="ac-support-section">{html.escape(title)}</div>',
                unsafe_allow_html=True)


def _plot(fig,height=380,legend=False,wide_left=False):
    fig.update_layout(
        height=height,
        margin=dict(t=42,l=145 if wide_left else 45,r=25,b=115 if legend else 65),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#DFEAE1",size=12),
        showlegend=legend,
        legend=dict(orientation="h",yanchor="top",y=-.33,xanchor="center",x=.5,
                    font=dict(size=11),bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(155,177,158,.12)",automargin=True,
                   title_standoff=12,zeroline=False),
        yaxis=dict(gridcolor="rgba(155,177,158,.12)",automargin=True,
                   title_standoff=12,zeroline=False),
    )
    st.plotly_chart(fig,use_container_width=True,
                    config={"displayModeBar":False,"responsive":True})


def support_snapshot(model, rows=None, targets=None, reference=None):
    """Cálculos verificables compartidos con el KPI de resolución gerencial."""
    tickets = rows if rows is not None else incidents(limit=100000)
    targets = targets if targets is not None else store.targets()
    month = incident_month_summary(tickets,reference=reference)
    pending = [r for r in tickets if r["status"]!="Resuelto"]
    priority = [r for r in pending if r["priority"]=="Alta"]
    mx = model.metricas.loc[model.metricas["Modelo"]=="XGBoost"].iloc[0]
    lg = model.metricas.loc[model.metricas["Modelo"]=="Logit"].iloc[0]
    return {
        "month":month,"pending":pending,"high_priority":priority,
        "goal":float(targets.get("Resolución DTI mensual",.99)),
        "xgb":mx,"logit":lg,"tickets":tickets,
    }


def render_support_home(model):
    snapshot=support_snapshot(model)
    month=snapshot["month"]
    goal=snapshot["goal"]
    mx=snapshot["xgb"]
    ratio=month["rate"]
    progress=None if ratio is None or goal<=0 else ratio/goal

    _header("Centro de soporte",
        f"Modelo XGBoost · 12 variables · {local_now().strftime('%m/%Y')} · "
        "alertas y métricas que también supervisa gerencia",
        "AUTOCREDIT / SOPORTE Y SEGUIMIENTO")
    _cards([
       {"label":"Resolución mensual*",
        "value":f"{ratio:.1%}" if ratio is not None else "—",
        "detail":f"Meta de gerencia: {goal:.0%} · reportes de este mes",
        "tone":"good" if progress is not None and progress>=1
               else "attention" if progress is not None else "default",
        "progress":progress},
       {"label":"Casos resueltos este mes",
        "value":f"{month['solved']:,} / {month['total']:,}",
        "detail":"Incidencias abiertas en el mes que ya fueron resueltas"},
       {"label":"Pendientes de soporte",
        "value":f"{len(snapshot['pending']):,}",
        "detail":"Abiertos o en revisión, incluidos meses anteriores",
        "tone":"attention" if snapshot["pending"] else "good"},
       {"label":"Alertas de prioridad alta",
        "value":f"{len(snapshot['high_priority']):,}",
        "detail":"Incidencias urgentes todavía sin resolver",
        "tone":"critical" if snapshot["high_priority"] else "good"},
       {"label":"ROC-AUC · XGBoost",
        "value":f'{mx["ROC-AUC"]:.3f}',
        "detail":"Discriminación estimada en TEST externo"},
       {"label":"KS · XGBoost",
        "value":f"{mx['KS']:.3f}",
        "detail":"Separación ROC observada en TEST"},
    ])
    st.caption("* Esta misma tasa de resolución (meta 99% inicial) se muestra en "
               "Métricas del área de Mariana. Sin reportes durante el mes, "
               "la tasa es «—», no 100%. El conjunto de datos crediticios es sintético.")

    _section("Alertas y salud del modelo")
    left,right=st.columns([1.1,1],gap="large")
    with left:
        if snapshot["high_priority"]:
            st.error(f"{len(snapshot['high_priority'])} incidencias de prioridad alta sin resolver.")
            table=pd.DataFrame([{
              "Ticket":f'#{r["id"]}',
              "Analista":r["analyst_id"],
              "Incidencia":r["title"],
              "Estado":r["status"]
            } for r in snapshot["high_priority"][:8]])
            st.dataframe(table,hide_index=True,use_container_width=True)
        elif snapshot["pending"]:
            st.warning(f"{len(snapshot['pending'])} incidencias pendientes. "
                       "No hay tickets de prioridad alta abiertos.")
        else:
            st.success("No hay incidencias operativas pendientes en esta instancia.")
        st.caption("Los tickets provienen de los reportes que registran los analistas. "
                   "No se generan alertas de producción ni se atribuyen fallas a préstamos reales.")
    with right:
        if month["total"]:
            fig=go.Figure(go.Pie(
                labels=["Abiertas","En revisión","Resueltas"],
                values=[month["open"],month["review"],month["solved"]],
                hole=.67,
                marker=dict(colors=["#F49CAA","#F2C675","#6BE0A9"]),
                textinfo="value+label"))
            _plot(fig,height=355)
        else:
            st.markdown(
                '<div class="ac-support-empty"><strong>Sin incidencias registradas este mes.</strong>'
                '<p>Al recibir un reporte, aquí aparecerá la distribución de '
                'casos abiertos, en revisión y resueltos.</p></div>',
                unsafe_allow_html=True)

    _section("Indicadores técnicos · XGBoost en TEST")
    _cards([
       {"label":"Recall · incumplimiento","value":f"{mx['Recall']:.1%}",
        "detail":"Proporción de incumplidores identificados"},
       {"label":"Precision · incumplimiento","value":f"{mx['Precision']:.1%}",
        "detail":"Proporción de aciertos en predicciones de incumplimiento"},
       {"label":"F1 · incumplimiento","value":f"{mx['F1']:.3f}",
        "detail":"Equilibrio entre precision y recall"},
       {"label":"Accuracy","value":f"{mx['Accuracy']:.1%}",
        "detail":"Clasificaciones correctas en TEST"},
       {"label":"Falsos negativos","value":f"{int(mx['FN']):,}",
        "detail":"Incumplidores no detectados al corte F2","tone":"attention"},
       {"label":"Falsos positivos","value":f"{int(mx['FP']):,}",
        "detail":"Cumplidores clasificados como incumplidores","tone":"attention"},
    ])

    b1,b2=st.columns(2,gap="large")
    with b1:
        st.markdown("**Desempeño comparativo en TEST**")
        frame=pd.DataFrame([
            {"Modelo":model_name,
             "ROC-AUC":float(row["ROC-AUC"]),
             "KS":float(row["KS"]),
             "F1":float(row["F1"]),
             "PR-AUC":float(row["PR-AUC"])}
            for model_name,row in (("XGBoost",mx),("Logit",snapshot["logit"]))
        ])
        st.dataframe(frame,hide_index=True,use_container_width=True)
        st.caption("La comparación se informa, no se utiliza para reajustar "
                   "el modelo ni los umbrales después de observar TEST.")
    with b2:
        st.markdown("**Validación e integridad del conjunto**")
        st.write(f"**TRAIN:** {len(model.train):,} solicitudes")
        st.write(f"**TEST:** {len(model.test):,} solicitudes")
        st.write(f"**Identificadores únicos TEST:** {model.test['LOAN_ID'].nunique():,}")
        st.write(f"**Predictores del modelo:** {len(COLS)}")
        st.caption("La carga verifica Loan ID únicos, datos completos y ausencia "
                   "de identificadores compartidos entre TRAIN y TEST.")

    _section("Bandeja de incidencias y resolución")
    render_dti_incidents(show_heading=False,show_kpis=False)
    st.caption("El seguimiento se registra en SQLite de esta instancia. "
               "Los cambios de estado notifican a la persona que reportó la incidencia "
               "y a Mariana.")

    _section("Herramientas")
    st.link_button("Ver código de la versión V3 en GitHub",REPOSITORY_URL,
                   icon=":material/code:",use_container_width=False)
    st.caption("Prototipo académico sin integración de monitoreo productivo, "
               "autenticación institucional ni base de datos persistente.")


def render_support_validation(model):
    mx=model.metricas.loc[model.metricas.Modelo=="XGBoost"].iloc[0]
    lg=model.metricas.loc[model.metricas.Modelo=="Logit"].iloc[0]
    _header("Validación técnica del modelo",
            "Comparación de modelos, matriz de confusión, distribuciones, importancia "
            "y calibración sobre el conjunto TEST externo.",
            "AUTOCREDIT / VALIDACIÓN TÉCNICA")
    _cards([
        {"label":"ROC-AUC","value":f'{mx["ROC-AUC"]:.3f}',
         "detail":"Capacidad discriminante · TEST"},
        {"label":"KS","value":f'{mx["KS"]:.3f}',
         "detail":"Máxima diferencia TPR - FPR · TEST"},
        {"label":"PR-AUC","value":f'{mx["PR-AUC"]:.3f}',
         "detail":"Precisión-recall en muestra desbalanceada"},
        {"label":"Recall default=1","value":f'{mx["Recall"]:.1%}',
         "detail":"Incumplidores detectados al corte F2"},
        {"label":"F1","value":f'{mx["F1"]:.3f}',
         "detail":"Balance precision/recall"},
        {"label":"Brier","value":f'{mx["Brier"]:.3f}',
         "detail":"Error cuadrático de probabilidad · menor es mejor"},
    ])
    st.info(f"Umbrales seleccionados en VALIDACIÓN de TRAIN: aceptar si PD XGBoost es menor que "
            f"{model.corte_base:.2%}, condicionar entre cortes y rechazar desde "
            f"{model.corte_rechazo:.2%} (política base). "
            "La matriz de confusión evalúa clasificación binaria al corte inferior F2.")
    _section("Comparación del desempeño en TEST")
    cols=["Modelo","ROC-AUC","KS","PR-AUC","Accuracy","Precision","Recall","F1","Brier"]
    st.dataframe(model.metricas[cols].round(3),hide_index=True,use_container_width=True)
    with st.expander("Detalle de conteos por modelo y criterio de evaluación"):
        detail=model.metricas[["Modelo","Umbral","TN","FP","FN","TP"]].copy()
        st.dataframe(detail,hide_index=True,use_container_width=True)
        st.caption("TP: incumplidores identificados; FN: incumplidores no detectados; "
                   "FP: cumplidores marcados como incumplidores; TN: cumplidores identificados.")
    _section("Curvas discriminantes")
    l,r=st.columns(2,gap="large")
    with l:
        fig=go.Figure()
        for name,(fpr,tpr) in model.auc_roc.items():
            fig.add_trace(go.Scatter(x=fpr,y=tpr,mode="lines",name=name,
                       line=dict(color=MODEL_COLOR if name=="XGBoost" else SECONDARY_COLOR,width=2.8)))
        fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",
                    name="Azar",line=dict(color="#858F89",dash="dash")))
        fig.update_layout(xaxis_title="Tasa de falsos positivos",
                          yaxis_title="Sensibilidad",title="Curva ROC")
        _plot(fig,425,legend=True)
    with r:
        fig=go.Figure()
        for name,col in (("XGBoost","PD_XGB"),("Logit","PD_LOGIT")):
            pre,rec,_=precision_recall_curve(model.scores.DEFAULT,model.scores[col])
            fig.add_trace(go.Scatter(x=rec,y=pre,mode="lines",name=name,
                       line=dict(color=MODEL_COLOR if name=="XGBoost" else SECONDARY_COLOR,width=2.8)))
        fig.update_layout(title="Curva Precision-Recall",
                          xaxis_title="Recall",yaxis_title="Precision")
        _plot(fig,425,legend=True)

    _section("Errores de clasificación y probabilidades")
    l,r=st.columns(2,gap="large")
    with l:
        cm=np.array([[mx.TN,mx.FP],[mx.FN,mx.TP]],dtype=int)
        fig=go.Figure(go.Heatmap(z=cm,x=["Predicho 0","Predicho 1"],
                                 y=["Real 0","Real 1"],colorscale="Greens",
                                 text=cm,texttemplate="%{text:,}",showscale=False))
        fig.update_layout(title="Matriz de confusión · XGBoost",yaxis=dict(autorange="reversed"))
        _plot(fig,405)
    with r:
        fig=go.Figure()
        for cls,col in ((0,MODEL_COLOR),(1,"#E9A0A8")):
            probs=model.scores.loc[model.scores.DEFAULT==cls,"PD_XGB"]
            fig.add_trace(go.Histogram(x=probs,nbinsx=35,histnorm="probability",
                    name=f"DEFAULT = {cls}",marker_color=col,opacity=.70))
        fig.update_layout(title="Distribución de PD en TEST",barmode="overlay",
                         xaxis_title="Probabilidad XGBoost",
                         yaxis_title="Proporción dentro de cada clase")
        _plot(fig,425,legend=True)

    _section("Variables y calibración")
    l,r=st.columns(2,gap="large")
    with l:
        importances=pd.Series(model.xgb.feature_importances_,index=COLS).sort_values().tail(10)
        fig=go.Figure(go.Bar(x=importances.values,y=[LABELS[c] for c in importances.index],
                   orientation="h",marker_color=MODEL_COLOR))
        fig.update_layout(title="Importancia interna · XGBoost",
                          xaxis_title="Importancia del modelo",
                          yaxis_title="")
        _plot(fig,470,wide_left=True)
        st.caption("Importancia interna de XGBoost; no equivale a causalidad "
                   "ni a una prueba de significancia estadística.")
    with r:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",
                       name="Calibración ideal",line=dict(color="#899992",dash="dash")))
        for name,col in (("XGBoost","PD_XGB"),("Logit","PD_LOGIT")):
            observed,estimated=calibration_curve(
                model.scores.DEFAULT,model.scores[col],n_bins=10,strategy="quantile")
            fig.add_trace(go.Scatter(x=estimated,y=observed,mode="lines+markers",
                         name=name,line=dict(color=MODEL_COLOR if name=="XGBoost" else SECONDARY_COLOR)))
        fig.update_layout(title="Calibración de probabilidades",
                          xaxis_title="PD media pronosticada",
                          yaxis_title="Frecuencia de incumplimiento")
        _plot(fig,470,legend=True)

    _section("Alertas de interpretación")
    st.warning(f"En TEST se observaron {int(mx['FN']):,} falsos negativos y "
               f"{int(mx['FP']):,} falsos positivos al corte F2. Son errores "
               "de evaluación, no incidencias operativas abiertas.")
    st.info("No puede calcularse drift productivo ni una tasa real de fallas "
            "del modelo porque no existen datos de producción. "
            "La selección de umbrales ocurrió en VALIDACIÓN; "
            "no debe retocarse usando TEST sin nueva evaluación independiente.")
    st.caption("FINANCIAL_LITERACY_SCORE podría actuar como proxy socioeconómico: "
               "requiere una revisión formal de sesgos antes de cualquier uso real.")
    st.link_button("Consultar código del modelo en GitHub",
         REPOSITORY_URL,icon=":material/code:")
