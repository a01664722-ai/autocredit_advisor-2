"""AutoCredit Advisor · tercera iteración académica: política de tres decisiones.
Modelo XGBoost vs Logit, TEST externo, corte gerencial compartido, trazabilidad.
NO es un sistema de aprobación crediticia en producción.
"""
from __future__ import annotations
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve
from sklearn.calibration import calibration_curve

from src.engine import bases, entrenar, COLS, LABELS, PERCENT, formato, sugerencia
from src import store

st.set_page_config(page_title='AutoCredit Advisor | Equipo 3', page_icon=':material/finance:', layout='wide')
st.markdown('''<style>
.block-container{max-width:1400px;padding-top:.75rem;padding-bottom:2.5rem}
h1{font-size:1.65rem!important;line-height:1.2!important} h2{font-size:1.3rem!important}
[data-testid="stMetric"]{border:1px solid #313d36;border-radius:12px;padding:.65rem .9rem;background:#161b18}
[data-testid="stMetricLabel"]{font-size:.83rem!important}
[data-testid="stDataFrame"]{font-size:.8rem}
.kpi{border:1px solid #37443d;border-radius:12px;padding:.85rem 1rem;min-height:103px;background:#161b18}
.kpi .label{font-size:.79rem;color:#b8c5bd;min-height:22px}.kpi .value{font-size:1.68rem;font-weight:720;line-height:1.35}
.kpi .sub{font-size:.72rem;color:#b8c5bd}.good{color:#52dc9a!important}.warn{color:#f5c65b!important}.bad{color:#f47b87!important}
.chip{border-radius:6px;padding:.18rem .45rem;display:inline-block;font-size:.78rem;font-weight:650}
.chip.good{background:#103a2a}.chip.warn{background:#423011}.chip.bad{background:#4b2027}
.helper{font-size:.84rem;color:#b2bcb5} .hint{border-left:4px solid #dca54c;padding:.6rem .85rem;background:#26231a;border-radius:6px}
[data-testid="stDataFrame"] [role="gridcell"]:focus-within{outline:2px solid #52dc9a!important;background:#243f32!important}
[data-testid="stDataFrame"] [aria-selected="true"]{background:#244636!important}
[data-testid="stDataFrame"] [role="columnheader"]{font-weight:700!important}
section[data-testid="stSidebar"]{width:270px!important}
[data-testid="stVerticalBlock"]{gap:.75rem}
</style>''',unsafe_allow_html=True)

PERSONAS={
 'Adrián · Analista A-017':('analista','A-017','Adrián Pérez'),
 'Sofía · Analista A-022':('analista','A-022','Sofía Reyes'),
 'Mariana · Gerente':('gerente',None,'Mariana Torres'),
 'Luis · Operación':('operacion',None,'Luis Ramírez'),
 'Especialista · Validación DTI':('dti',None,'Especialista DTI'),
}
METRICAS_OBJ={'Resueltas':'Casos resueltos','Con justificación':'Excepciones justificadas','Coincidencia con sugerencia':'Coincidencia modelo–analista'}

@st.cache_resource(show_spinner='Entrenando XGBoost y Logit exclusivamente con TRAIN…')
def artefactos():
    train,test=bases()
    return entrenar(train,test)

try:
    M=artefactos()
    store.initialize(M.corte_rechazo)
except Exception as exc:
    st.error(f'No se puede iniciar: {exc}')
    st.info('Copia los archivos TRAIN y TEST originales en data/. Verifica el esquema de las 12 variables y los Loan ID únicos.')
    st.stop()


def color_decision(dec):return 'good' if dec in ('Aprobar','Aceptar') else 'bad' if dec=='Rechazar' else 'warn'

def kpi(label,value,sub='',tone=''):
    return f'<div class="kpi"><div class="label">{html.escape(str(label))}</div><div class="value {tone}">{html.escape(str(value))}</div><div class="sub">{html.escape(str(sub))}</div></div>'

def strip_metrics(values):
    cols=st.columns(len(values),gap='small')
    for c,(lab,val,sub,tone) in zip(cols,values):
        c.markdown(kpi(lab,val,sub,tone),unsafe_allow_html=True)

def footnote():
    st.caption('* Dato operativo simulado (asignación, mensajes o fecha ficticia). ** Predicción calculada con un modelo entrenado en TRAIN; evaluada sobre TEST. '\
               'Los datos crediticios proceden de un conjunto sintético, no de créditos reales. u.m. = unidad monetaria no especificada en el origen. '\
               'La bitácora SQLite de esta demo puede borrarse si Streamlit Cloud reinicia la app.')

def active_threshold(segment):
    general=store.policy('General')
    specific=store.policy(segment)
    return float(specific['threshold']) if specific and specific['version']>1 else float(general['threshold'])

def rated(df):
    d=df.copy()
    d['CORTE']=d['SEG_DTI'].map(lambda s:active_threshold(s))
    d['CORTE_ACEPTAR']=float(M.corte_base)
    d['SUGERENCIA']=[sugerencia(p,M.corte_base,t) for p,t in zip(d.PD_XGB,d.CORTE)]
    return d

def send_decision(r,decision,reason='',detail=''):
    if r.ANALISTA_ID!=analyst_id:raise PermissionError('Solicitud no asignada')
    if decision not in ('Aceptar','Condicionar','Rechazar'):
        raise ValueError('Decisión no reconocida')
    if store.save_decision(r.LOAN_ID,analyst_id,decision,r.SUGERENCIA,
                           r.PD_XGB,r.PD_LOGIT,r.CORTE,reason,detail):
        st.toast('Decisión excepcional guardada y notificada a gerencia.',icon=':material/mail:')
    else:st.toast('Decisión guardada en la bitácora.',icon=':material/check_circle:')

@st.dialog('Confirmación de decisión contraria al modelo')
def override_dialog():
    p=st.session_state.get('pending_choice')
    if not p:return
    row=M.scores.loc[M.scores.LOAN_ID==str(p['loan_id'])]
    if row.empty:st.error('El Loan ID no existe en TEST');return
    row=rated(row).iloc[0]
    if row.ANALISTA_ID!=analyst_id:st.error('No tienes acceso a esta solicitud');return
    st.warning(f'Vas a **{p["choice"].lower()}** el Loan ID **{row.LOAN_ID}**, pero XGBoost sugiere **{row.SUGERENCIA.lower()}**. Cortes vigentes: aceptar < {M.corte_base:.2%}; rechazar ≥ {row.CORTE:.2%}.')
    st.caption('Debes justificar la excepción. Se enviará una alerta a la bandeja de la gerente.')
    motive=st.selectbox('Motivo obligatorio', ['Seleccionar','Información adicional verificada','Error en los datos de origen',
                                 'Excepción de política autorizada','Cambio documentado en capacidad de pago','Otro'],key='override_motive')
    note=st.text_area('Detalle y evidencia (sin datos personales)',max_chars=400,key='override_note',placeholder='Explica el fundamento crediticio de la excepción')
    c1,c2=st.columns(2)
    if c1.button('Cancelar',use_container_width=True,key='cancel_override'):
        st.session_state['pending_choice']=None
        st.rerun()
    if c2.button('Confirmar y notificar',type='primary',use_container_width=True,key='confirm_override'):
        if motive=='Seleccionar' or len(note.strip())<8:
            st.error('Selecciona un motivo y escribe una explicación de al menos 8 caracteres.')
        else:
            send_decision(row,p['choice'],motive,note)
            st.session_state['pending_choice']=None
            st.session_state['table_rev']=st.session_state.get('table_rev',0)+1
            st.rerun()


def open_loan(loan):
    st.session_state['loan_actual']=str(loan)
    st.session_state['page_to']='Ficha de solicitud'
    st.rerun()


def ask_decision(row,decision):
    if decision==row.SUGERENCIA:
        send_decision(row,decision)
        st.session_state['table_rev']=st.session_state.get('table_rev',0)+1
        st.rerun()
    st.session_state['pending_choice']={'loan_id':str(row.LOAN_ID),'choice':decision}
    st.session_state['loan_actual']=str(row.LOAN_ID)
    st.session_state['page_to']='Ficha de solicitud'
    st.rerun()

with st.sidebar:
    st.markdown('### AutoCredit Advisor')
    selected=st.selectbox('Perfil de demostración*',list(PERSONAS),key='perfil',help='El selector demuestra roles: NO es autenticación de producción.')
    role,analyst_id,name=PERSONAS[selected]
    st.caption(f'{name} · {role.title()}')
    if role in ('analista','gerente'):
        n=store.unread(role,analyst_id)
        if st.button(f'Mensajes ({n})',icon=':material/mail:',use_container_width=True):
            st.session_state['page_to']='Mensajes'
            st.rerun()
    if role=='analista':pages=['Bandeja','Ficha de solicitud','Mis indicadores','Mensajes']
    elif role=='gerente':pages=['Política y cartera','Analistas y KPI','Mensajes','Recorridos y gobierno']
    elif role=='dti':pages=['Validación del modelo','Recorridos y gobierno']
    else:pages=['Operación','Validación del modelo']
    if 'page' not in st.session_state or st.session_state.page not in pages:
        st.session_state.page=pages[0]
    if 'page_to' in st.session_state:
        dest=st.session_state.pop('page_to')
        if dest in pages:
            st.session_state.page=dest
            st.session_state[f'nav_{role}']=dest
    chosen=st.radio('Pantallas',pages,index=pages.index(st.session_state.page),key=f'nav_{role}')
    if chosen!=st.session_state.page:st.session_state.page=chosen
    st.divider()
    st.caption(f'XGBoost · 12 variables · aceptar < {M.corte_base:.2%} · rechazar ≥ {M.corte_rechazo:.2%} (base)')
    st.caption('Demostración académica. No utilizar para aprobar créditos reales.')
    if st.button('Actualizar',icon=':material/refresh:',use_container_width=True):st.rerun()

page=st.session_state.page

if page=='Mensajes':
    st.title(f'Mensajes · {name}')
    items=store.messages(role,analyst_id)
    strip_metrics([('Mensajes sin leer',str(store.unread(role,analyst_id)),'Alertas dentro de esta demo','warn'),
                   ('Mensajes totales',str(len(items)),'Últimos 50 eventos','')])
    if not items:st.info('Sin mensajes por ahora. Los cambios de política y las excepciones aparecerán aquí.')
    for x in items:
        with st.container(border=True):
            st.markdown(f'**{x["title"]}**'+(' · Sin leer' if not x['seen'] else ' · Leído'))
            st.caption(x['created_at'])
            st.write(x['body'])
            if not x['seen'] and st.button('Marcar como leído',key=f'msg_{x["id"]}'):
                store.mark_read(x['id'],role,analyst_id);st.rerun()
    footnote();st.stop()


if page == 'Bandeja':
    # P1 V3. Solo datos TEST y Loan ID originales; no cambiar estas reglas.
    # XGBoost genera la PD principal y Logit es un comparador, no una regla adicional.
    st.markdown("""
    <style>
    .ac-p1-head {margin:.20rem 0 1.1rem 0}
    .ac-p1-eyebrow {color:#87bda8;font-size:.78rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase}
    .ac-p1-title {color:#f1f7f3;font-size:1.85rem;font-weight:780;letter-spacing:-.045em;line-height:1.25;margin:.18rem 0 .3rem}
    .ac-p1-description {color:#abbab1;font-size:.89rem;line-height:1.55;max-width:1100px}
    .ac-p1-kpis {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:.65rem 0 1.1rem}
    .ac-p1-kpi {position:relative;overflow:hidden;min-width:0;min-height:128px;padding:17px 18px;
        border:1px solid rgba(119,162,141,.24);border-radius:15px;
        background:linear-gradient(140deg,rgba(36,63,52,.57),rgba(18,25,23,.65) 68%);
        box-shadow:0 5px 24px rgba(0,0,0,.13)}
    .ac-p1-kpi:before {content:'';position:absolute;top:0;left:18px;right:18px;height:2px;
        background:linear-gradient(90deg,rgba(75,214,151,.85),transparent)}
    .ac-p1-kpi.amber:before {background:linear-gradient(90deg,#e9b85f,transparent)}
    .ac-p1-kpi.blue:before {background:linear-gradient(90deg,#79b8df,transparent)}
    .ac-p1-kpi .name {font-size:.83rem;font-weight:650;color:#c5d3ca;line-height:1.45;
        white-space:normal;overflow-wrap:break-word}
    .ac-p1-kpi .number {font-size:clamp(1.55rem,2.25vw,2.10rem);font-weight:780;color:#eff8f1;
        letter-spacing:-.04em;line-height:1.28;margin:.28rem 0 .12rem;white-space:normal}
    .ac-p1-kpi .detail {font-size:.74rem;color:#aabdb1;line-height:1.4;
        white-space:normal;overflow-wrap:break-word}
    .ac-p1-inline {font-size:.81rem;color:#a7bbaf;margin:.15rem 0 .6rem}
    .ac-p1-inline b {color:#87dcb3}
    .ac-p1-legend {padding:.66rem .9rem;border:1px solid rgba(121,178,148,.25);
        border-radius:10px;background:linear-gradient(115deg,rgba(34,61,48,.4),rgba(19,29,24,.15));
        color:#c9d8cf;font-size:.83rem;line-height:1.55;margin:.4rem 0 .6rem}
    .ac-p1-legend strong {color:#b8efd0}
    div[data-testid="stDataFrame"] {border:1px solid rgba(100,166,130,.25);border-radius:11px;
        box-shadow:0 7px 26px rgba(0,0,0,.1);overflow:hidden}
    div[data-testid="stDataFrame"] [role="columnheader"] {font-weight:750!important}
    div[data-testid="stDataFrame"] [role="gridcell"]:focus-within {outline:2px solid #62d8a3!important;
        outline-offset:-2px;background:rgba(48,130,95,.20)!important}
    @media(max-width:1050px){.ac-p1-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media(max-width:570px){.ac-p1-kpis{grid-template-columns:1fr 1fr;gap:8px}
        .ac-p1-kpi{padding:13px;min-height:140px}.ac-p1-title{font-size:1.45rem}}
    /* Semáforos KPI: el avance bajo la meta no se confunde con riesgo crediticio. */
    .ac-p1-kpi.low {border-color:rgba(238,117,134,.35);background:linear-gradient(140deg,rgba(98,37,49,.38),rgba(19,26,23,.75) 75%)}
    .ac-p1-kpi.low:before {background:linear-gradient(90deg,#e58b9a,transparent)}
    .ac-p1-kpi.low .number {color:#ffb6bc}
    .ac-p1-kpi.mid {border-color:rgba(224,178,89,.3);background:linear-gradient(140deg,rgba(107,78,32,.27),rgba(19,26,23,.75) 75%)}
    .ac-p1-kpi.mid:before {background:linear-gradient(90deg,#e5bf78,transparent)}
    .ac-p1-kpi.mid .number {color:#f4d59e}
    .ac-p1-kpi.met {border-color:rgba(96,212,153,.35);background:linear-gradient(140deg,rgba(35,102,73,.3),rgba(19,26,23,.75) 75%)}
    .ac-p1-kpi.met .number {color:#8de5b3}
    .ac-p1-kpi.na:before {background:linear-gradient(90deg,#8faba0,transparent)}
    /* Botones por decisión. La clave de Streamlit mantiene este CSS solo en P1. */
    div[class*="st-key-p1_tipos_v3"] button:nth-of-type(1) {border-color:rgba(79,217,156,.62)!important;color:#7de8b1!important;background:rgba(19,106,70,.12)!important}
    div[class*="st-key-p1_tipos_v3"] button:nth-of-type(2) {border-color:rgba(236,190,88,.70)!important;color:#f8d17b!important;background:rgba(137,94,22,.13)!important}
    div[class*="st-key-p1_tipos_v3"] button:nth-of-type(3) {border-color:rgba(243,113,128,.68)!important;color:#ff9ba7!important;background:rgba(157,46,62,.13)!important}
    div[class*="st-key-p1_tipos_v3"] button:nth-of-type(1)[kind="pillsActive"] {background:rgba(35,133,89,.31)!important}
    div[class*="st-key-p1_tipos_v3"] button:nth-of-type(2)[kind="pillsActive"] {background:rgba(143,101,30,.34)!important}
    div[class*="st-key-p1_tipos_v3"] button:nth-of-type(3)[kind="pillsActive"] {background:rgba(147,49,64,.34)!important}
    </style>
    """, unsafe_allow_html=True)

    # Un solo acceso a SQLite para obtener toda la política; así no se realizan
    # miles de consultas por fila en cada interacción.
    politicas = {x['segment']: x for x in store.policies()}
    corte_general = float(politicas['General']['threshold'])
    cortes_dti = {}
    for segmento in ('DTI bajo', 'DTI medio', 'DTI alto'):
        p = politicas.get(segmento)
        cortes_dti[segmento] = (
            float(p['threshold']) if p and p['version'] > 1 else corte_general
        )

    todos = M.scores.loc[M.scores['ANALISTA_ID'].eq(analyst_id)].copy()
    todos['CORTE'] = todos['SEG_DTI'].map(cortes_dti).fillna(corte_general).astype(float)
    todos['SUGERENCIA'] = np.select(
        [todos['PD_XGB'].lt(M.corte_base), todos['PD_XGB'].lt(todos['CORTE'])],
        ['Aceptar', 'Condicionar'], default='Rechazar'
    )
    decisiones = store.decisions_map(analyst_id)
    todos['ESTADO'] = np.where(todos['LOAN_ID'].isin(decisiones), 'Resuelta', 'Pendiente')

    total = len(todos)
    resueltas = int(todos['ESTADO'].eq('Resuelta').sum())
    pendientes = total - resueltas
    priorizadas = int(todos['SUGERENCIA'].eq('Rechazar').sum())

    # Metas del MISMO repositorio SQLite que consulta gerencia.
    # "Resueltas" es, por ahora, la meta operativa que edita Mariana.
    # Su definición formal como "Decisiones por día" se renombrará en P3.
    metas_gerencia = store.targets()
    meta_diaria = max(1, int(metas_gerencia.get('Resueltas', 50)))
    meta_justificacion = float(metas_gerencia.get('Con justificación', 1.0))

    # Hoy en zona CDMX: SQLite guarda updated_at como UTC.
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    zona = ZoneInfo('America/Mexico_City')
    hoy_local = datetime.now(zona).date()
    decisiones_hoy = 0

elif page=='Ficha de solicitud':
    all_cases=rated(M.scores[M.scores.ANALISTA_ID==analyst_id])
    loan=st.session_state.get('loan_actual')
    if not loan:
        st.info('Primero selecciona un Loan ID desde la bandeja.')
        if st.button('Abrir bandeja'):st.session_state.page_to='Bandeja';st.rerun()
        st.stop()
    rows=all_cases[all_cases.LOAN_ID==str(loan)]
    if rows.empty:st.error('Loan ID no disponible para tu analista.');st.stop()
    r=rows.iloc[0]
    hist=float(M.train.DEFAULT.mean())
    tone='bad' if r.PD_XGB>=r.CORTE else 'warn' if r.PD_XGB>=M.corte_base else 'good'
    strip_metrics([('PD XGBoost**',f'{r.PD_XGB:.1%}',f'vs. corte {r.CORTE:.1%}',tone),
                   ('PD Logit**',f'{r.PD_LOGIT:.1%}','Referencia complementaria','warn' if r.PD_LOGIT>=r.CORTE else ''),
                   ('Incumplimiento histórico',f'{hist:.2%}','Tasa observada de TRAIN; no es un límite',''),
                   ('Deuda / ingreso',f'{r.DEBT_TO_INCOME:.1%}',f'vs. mediana TRAIN {M.train.DEBT_TO_INCOME.median():.1%}',
                    'bad' if r.DEBT_TO_INCOME>M.train.DEBT_TO_INCOME.median() else 'good')])
    if r.SUGERENCIA=='Rechazar':
        st.error(f'ALERTA · PD XGBoost {r.PD_XGB:.1%} supera el corte de rechazo {r.CORTE:.1%}.',icon=':material/warning:')
    elif r.SUGERENCIA=='Condicionar':
        st.warning(f'RIESGO INTERMEDIO · PD XGBoost {r.PD_XGB:.1%}: requiere análisis de condiciones documentadas.',icon=':material/info:')
    else:
        st.success(f'RIESGO INFERIOR · PD XGBoost {r.PD_XGB:.1%} por debajo del corte F2 {M.corte_base:.1%}; validar expediente.',icon=':material/check_circle:')
    pd_mediana=float(M.scores.PD_XGB.median())
    if r.PD_XGB>pd_mediana:
        st.error(f'Comparación con TEST: PD {r.PD_XGB:.1%} supera la mediana {pd_mediana:.1%}.',icon=':material/trending_up:')
    st.title('P2 · Ficha de solicitud')
    st.markdown(f'**Loan ID {html.escape(str(r.LOAN_ID))}** · {r.SEG_DTI} · Sugerencia: **{r.SUGERENCIA}**')
    st.caption('El modelo no toma la decisión final; el analista confirma y la bitácora registra el motivo cuando discrepa.')
    b1,b2,b3,b4=st.columns([1,1,1,2])
    if b1.button('Aceptar',icon=':material/check_circle:',use_container_width=True,type='primary'):
        ask_decision(r,'Aceptar')
    if b2.button('Condicionar',icon=':material/rule:',use_container_width=True):
        ask_decision(r,'Condicionar')
    if b3.button('Rechazar',icon=':material/block:',use_container_width=True):
        ask_decision(r,'Rechazar')
    if b4.button('Volver a bandeja',icon=':material/arrow_back:'):
        st.session_state.page_to='Bandeja';st.rerun()
    c1,c2=st.columns([1,1])
    with c1:
        st.subheader('Riesgo y política')
        fig=go.Figure(go.Indicator(mode='gauge+number',value=r.PD_XGB*100,
            number={'suffix':'%'},gauge={'axis':{'range':[0,100]},'bar':{'color':'#e56a72' if r.SUGERENCIA=='Rechazar' else '#36d78e'},
             'steps':[{'range':[0,r.CORTE*100],'color':'#133e2d'},{'range':[r.CORTE*100,100],'color':'#45292f'}],
             'threshold':{'line':{'color':'#ffffff','width':3},'value':r.CORTE*100}}))
        fig.update_layout(height=245,margin=dict(l=30,r=30,t=16,b=12),paper_bgcolor='rgba(0,0,0,0)',font_color='#e8f4ed')
        st.plotly_chart(fig,use_container_width=True)
        st.caption('Línea blanca = corte configurado por Mariana. Verde: bajo corte; rojo: sobre corte.')
    with c2:
        st.subheader('Comparación con pagadores cumplidos')
        fields=['DEBT_TO_INCOME','REVOLVING_UTILIZATION','DOWN_PAYMENT_PCT','LOAN_TO_VALUE']
        benchmark=M.train[M.train.DEFAULT==0][fields].median()
        yy=[LABELS[x] for x in fields]
        fg=go.Figure()
        fg.add_trace(go.Bar(name='Este Loan ID',y=yy,x=[r[k]*100 for k in fields],orientation='h',marker_color='#6ea8fe'))
        fg.add_trace(go.Bar(name='Mediana sin incumplimiento en TRAIN',y=yy,x=[benchmark[k]*100 for k in fields],orientation='h',marker_color='#88918a'))
        fg.update_layout(barmode='group',height=275,margin=dict(l=4,r=10,t=5,b=0),paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',font_color='#e8f4ed',xaxis_title='Porcentaje (%)',legend=dict(orientation='h',y=1.14))
        st.plotly_chart(fg,use_container_width=True)
    with st.expander('Expediente y variables de riesgo',expanded=False):
        df=pd.DataFrame([{'Variable':LABELS[k],'Solicitud':formato(k,r[k]),
             'Mediana buenos pagadores (TRAIN)':formato(k,M.train[M.train.DEFAULT==0][k].median())} for k in COLS if k!='FINANCIAL_LITERACY_SCORE'])
        st.dataframe(df,hide_index=True,use_container_width=True)
        st.caption('La variable de educación financiera se utiliza en la comparación académica de 12 predictores, pero se excluye del expediente del analista por riesgo de proxy socioeconómico.')
    if st.session_state.get('pending_choice') and str(st.session_state.pending_choice.get('loan_id'))==str(loan):
        override_dialog()
    footnote()

elif page=='Mis indicadores':
    st.title('Mis indicadores · Analista')
    all_cases=rated(M.scores[M.scores.ANALISTA_ID==analyst_id])
    recent=store.decisions_map(analyst_id)
    num=len(recent);override=sum(int(x['override']) for x in recent.values())
    matches=num-override
    strip_metrics([('Resueltas',str(num),'Registros guardados','good' if num else ''),
                   ('Pendientes',f'{len(all_cases)-num:,}','Asignadas en TEST*','warn'),
                   ('Coincidencia',f'{matches/num:.1%}' if num else '—','Solo decisiones registradas',''),
                   ('Excepciones',str(override),'Todas requieren justificación','bad' if override else '')])
    st.caption('Las métricas son decisiones registradas en SQLite; sin fechas reales de recepción no se inventan tiempo de atención ni productividad por hora. Las asignaciones de analistas son simuladas.')
    if recent:
        st.dataframe(pd.DataFrame(recent.values())[['loan_id','decision','suggested','override','motivo','updated_at']].rename(columns={
            'loan_id':'Loan ID','decision':'Decisión','suggested':'Sugerencia','override':'Excepción','motivo':'Motivo','updated_at':'Registrada'}),hide_index=True,use_container_width=True)
    footnote()

elif page=='Política y cartera':
    st.title('P3 · Política de riesgo y cartera')
    st.caption('La gerente decide los cortes. Cada ajuste modifica la sugerencia que verá el analista; ambos perfiles consultan el mismo estado compartido de esta instancia.')
    col1,col2=st.columns([2,1])
    with col1:segment=st.selectbox('Segmento a evaluar',['General','DTI bajo','DTI medio','DTI alto'])
    policy=store.policy(segment)
    with col2:st.metric('Corte activo',f'{policy["threshold"]:.1%}' if segment!='General' and policy['version']>1 else f'{active_threshold(segment):.1%}')
    cases=M.scores if segment=='General' else M.scores[M.scores.SEG_DTI==segment]
    active=active_threshold(segment)
    new=st.slider('Probar corte de rechazo sobre PD XGBoost',min_value=float(np.ceil(M.corte_base*1000+1)/10),max_value=60.0,value=round(active*100,1),step=0.1,format='%.1f%%')/100.0
    old_ap=(cases.PD_XGB<M.corte_base)
    new_ap=(cases.PD_XGB<M.corte_base)
    old_cond=(cases.PD_XGB>=M.corte_base)&(cases.PD_XGB<active)
    new_cond=(cases.PD_XGB>=M.corte_base)&(cases.PD_XGB<new)
    real_def=lambda m:float(cases.loc[m,'DEFAULT'].mean()) if m.sum() else float('nan')
    strip_metrics([('Solicitudes TEST',f'{len(cases):,}',f'Segmento {segment}',''),
                   ('Aceptación',f'{new_ap.mean():.1%}',f'Corte inferior fijo {M.corte_base:.2%}',''),
                   ('Default observado aprobado',f'{real_def(new_ap):.1%}' if new_ap.any() else '—',
                    'Histórico de TEST, no proyección','bad' if real_def(new_ap)>.15 else 'good'),
                   ('Cambiarían de sugerencia',f'{int((old_cond!=new_cond).sum()):,}','Condicionar ↔ Rechazar','warn')])
    if st.button('Aplicar corte y avisar a analistas',type='primary',icon=':material/send:'):
        if segment=='General':
            before=np.array([active_threshold(s) for s in M.scores.SEG_DTI])
            after=np.array([new if store.policy(s)['version']==1 else active_threshold(s) for s in M.scores.SEG_DTI])
            affected=pd.Series(((M.scores.PD_XGB.to_numpy()>=M.corte_base)&(M.scores.PD_XGB.to_numpy()<before))!=((M.scores.PD_XGB.to_numpy()>=M.corte_base)&(M.scores.PD_XGB.to_numpy()<after)),index=M.scores.index)
            affected_df=M.scores[affected]
        else:
            before=active_threshold(segment)
            affected_df=cases[(cases.PD_XGB>=min(before,new))&(cases.PD_XGB<max(before,new))]
        by_analyst={aid:int((affected_df.ANALISTA_ID==aid).sum()) for aid in ['A-017','A-022']}
        if store.update_policy(segment,new,name,by_analyst):
            st.success('Nuevo corte guardado. Los analistas recibirán una notificación con el efecto del cambio.')
            st.rerun()
        else:st.info('El corte propuesto coincide con el vigente.')
    st.caption(f'Política de tres decisiones: aceptar bajo {M.corte_base:.2%} (F2, inalterable); condicionar entre cortes; rechazar a partir del corte gerencial. Cambiar cortes consultando TEST compromete la independencia de evaluación y requiere validación posterior.')
    # El corte inferior queda fijo; mover rechazo cambia CONDICIONAR vs RECHAZAR,
    # no la proporción de créditos aceptados directamente.
    thresholds=np.arange(np.ceil(M.corte_base*1000+1)/1000,.601,.005)
    conditional=[];rejected=[];default_conditioned=[]
    for t in thresholds:
        mask=(cases.PD_XGB>=M.corte_base)&(cases.PD_XGB<t)
        conditional.append(mask.mean()*100)
        rejected.append((cases.PD_XGB>=t).mean()*100)
        default_conditioned.append(cases.loc[mask,'DEFAULT'].mean()*100 if mask.any() else np.nan)
    fc1,fc2=st.columns(2)
    with fc1:
        f=go.Figure()
        f.add_trace(go.Scatter(x=thresholds*100,y=conditional,mode='lines',line_color='#e4be65',name='Condicionar'))
        f.add_trace(go.Scatter(x=thresholds*100,y=rejected,mode='lines',line_color='#e56a72',name='Rechazar'))
        f.add_vline(x=new*100,line_dash='dot',line_color='#f5c65b')
        f.update_layout(title='Escenarios: condicionar y rechazar (TEST)',xaxis_title='Corte superior de PD (%)',yaxis_title='Porcentaje de solicitudes (%)',height=310,
            margin=dict(l=15,r=15,t=50,b=18),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed')
        st.plotly_chart(f,use_container_width=True)
    with fc2:
        f=go.Figure(go.Scatter(x=thresholds*100,y=default_conditioned,mode='lines',line_color='#f08565',name='Default observado condicional'))
        f.add_vline(x=new*100,line_dash='dot',line_color='#f5c65b')
        f.update_layout(title='Incumplimiento observado en zona condicional (TEST)',xaxis_title='Corte superior de PD (%)',yaxis_title='Default histórico (%)',height=310,
            margin=dict(l=15,r=15,t=50,b=18),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed')
        st.plotly_chart(f,use_container_width=True)
    st.caption('Curvas calculadas con la variable DEFAULT de TEST, exclusivamente en agregado. Si el corte cambia después de ver TEST, debe evaluarse de nuevo en una muestra futura independiente antes de producción.')
    footnote()

elif page=='Analistas y KPI':
    st.title('Gestión de analistas y KPI')
    st.caption('Ranking descriptivo de decisiones registradas por analista. Avatares de iniciales (no fotografías reales); las asignaciones son de demostración.')
    actions=pd.DataFrame(store.decisions())
    targets=store.targets()
    profiles=[('Adrián Pérez','A-017','AP'),('Sofía Reyes','A-022','SR')]
    rows=[]
    for person,aid,initials in profiles:
        sub=actions[actions.analyst_id==aid] if len(actions) else pd.DataFrame()
        n=len(sub)
        overrides=int(sub.override.sum()) if n else 0
        coinc=(n-overrides)/n if n else float('nan')
        just=1.0 if n and (sub.loc[sub.override==1,'motivo'].fillna('')!='').all() else (float('nan') if not n or not overrides else 0.0)
        rows.append({'Analista':person,'ID':aid,'Resueltas':n,'Coincidencia con sugerencia':coinc,
                     'Con justificación':just,'Excepciones':overrides})
    per=pd.DataFrame(rows)
    f1,f2=st.columns(2)
    for box,(person,aid,initials) in zip([f1,f2],profiles):
        ri=per[per.ID==aid].iloc[0]
        with box.container(border=True):
            st.markdown(f'<div style="display:flex;align-items:center;gap:12px"><div style="background:#253b32;color:#74e7b0;border-radius:50%;height:47px;width:47px;display:grid;place-items:center;font-weight:800">{initials}</div><div><b>{person}</b><div class="helper">Analista {aid} · identidad simulada*</div></div></div>',unsafe_allow_html=True)
            st.metric('Decisiones registradas',int(ri.Resueltas))
            st.caption(f'Coincidencia: {ri["Coincidencia con sugerencia"]:.1%}' if ri.Resueltas else 'Sin decisiones registradas')
    st.subheader('Clasificación por indicador')
    sel=st.selectbox('KPI para comparar',list(METRICAS_OBJ),format_func=lambda k:METRICAS_OBJ[k])
    val=targets[sel]
    default_max=500 if sel=='Resueltas' else 1.0
    new=st.number_input('Meta vigente',min_value=0.0,max_value=float(default_max),value=float(val),step=1.0 if sel=='Resueltas' else .05,format='%.0f' if sel=='Resueltas' else '%.2f')
    if st.button('Guardar meta KPI',icon=':material/save:'):store.set_target(sel,new);st.rerun()
    ranked=per.sort_values(sel,ascending=False,na_position='last')
    cmp=ranked[['Analista','ID',sel]].copy()
    cmp['Estado vs meta']=cmp[sel].apply(lambda x:'Sin información' if pd.isna(x) else ('En meta' if x>=new else 'Bajo meta'))
    st.dataframe(cmp,hide_index=True,use_container_width=True, column_config={sel:st.column_config.NumberColumn(METRICAS_OBJ[sel],format='%d' if sel=='Resueltas' else '%.1f')})
    st.caption('El orden representa volumen o cumplimiento de procedimiento, NO calidad crediticia ni evaluación laboral válida. Se requiere seguimiento real de resultados; no se atribuyen puntuaciones ficticias.')
    with st.expander('Auditoría de decisiones y excepciones'):
        if len(actions):st.dataframe(actions[['loan_id','analyst_id','decision','suggested','override','motivo','updated_at']],hide_index=True,use_container_width=True)
        else:st.info('Aún no hay decisiones guardadas.')
    footnote()

elif page=='Operación':
    st.title('P4 · Seguimiento operativo')
    action=store.decisions()
    strip_metrics([('TRAIN',f'{len(M.train):,}','Entrenamiento del modelo',''),
                   ('TEST',f'{len(M.test):,}','Muestra independiente',''),
                   ('Decisiones demo',str(len(action)),'Bitácora compartida',''),
                   ('AUC XGBoost',f'{M.metricas.iloc[0]["ROC-AUC"]:.3f}','Calculado sobre TEST','good')])
    st.info('Sin registros productivos, no se reportan incidentes en tiempo real, SLA o drift de producción. El seguimiento mostrado es el entorno académico de TEST.')
    st.caption('Para las gráficas técnicas consulta Validación del modelo.')
    footnote()

elif page=='Validación del modelo':
    st.title('P8 · Validación técnica del modelo · DTI')
    st.caption('XGBoost es el campeón seleccionado para el prototipo por ROC-AUC y F1 en validación; Random Forest supera marginalmente su KS. TRAIN: 80,000 filas; TEST externo: 20,000. No equivale a aprobación productiva.')
    threshold=M.corte_base
    mx=M.metricas[M.metricas.Modelo=='XGBoost'].iloc[0]
    strip_metrics([('ROC-AUC',f'{mx["ROC-AUC"]:.3f}','Discriminación en TEST','good'),
                   ('Accuracy',f'{mx.Accuracy:.1%}','TEST · umbral validado',''),
                   ('Recall default=1',f'{mx.Recall:.1%}','Incumplidores detectados','warn'),
                   ('KS',f'{mx.KS:.3f}','Máxima separación ROC','good'),
                   ('PR-AUC',f'{mx["PR-AUC"]:.3f}','Conjunto desbalanceado','')])
    st.warning(f'Umbrales de tres vías seleccionados exclusivamente en VALIDACIÓN: aceptar < {M.corte_base:.2%}; condicionar hasta {M.corte_rechazo:.2%}; rechazar ≥ {M.corte_rechazo:.2%}. La matriz de confusión usa clasificación binaria al corte inferior F2. Falsos positivos en TEST: {int(mx.FP):,}.',icon=':material/warning:')
    st.subheader('Comparación reproducible sobre TEST')
    st.dataframe(M.metricas.rename(columns={'TN':'Verdaderos negativos','FP':'Falsos positivos',
        'FN':'Falsos negativos','TP':'Verdaderos positivos'}),hide_index=True,use_container_width=True)
    g1,g2=st.columns(2)
    with g1:
        st.markdown('**Curva ROC**')
        fig=go.Figure()
        for model,(fpr,tpr) in M.auc_roc.items():fig.add_trace(go.Scatter(x=fpr,y=tpr,mode='lines',name=model))
        fig.add_trace(go.Scatter(x=[0,1],y=[0,1],line=dict(dash='dash',color='#707a73'),name='Azar'))
        fig.update_layout(xaxis_title='Tasa de falsos positivos',yaxis_title='Sensibilidad',height=330,
                          paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed',margin=dict(t=15,l=20,r=15,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with g2:
        st.markdown('**Matriz de confusión · XGBoost (TEST)**')
        cm=np.array([[mx.TN,mx.FP],[mx.FN,mx.TP]],dtype=int)
        fig=go.Figure(data=go.Heatmap(z=cm,x=['Predicho 0','Predicho 1'],y=['Real 0','Real 1'],
                                   colorscale='Tealgrn',text=cm,texttemplate='%{text:,}',showscale=False))
        fig.update_layout(height=330,paper_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed',
                          margin=dict(t=15,l=20,r=15,b=10),yaxis={'autorange':'reversed'})
        st.plotly_chart(fig,use_container_width=True)
    g3,g4=st.columns(2)
    with g3:
        st.markdown('**Distribución de PD por resultado real (TEST)**')
        fig=go.Figure()
        for cls,color_ in [(0,'#7b99bd'),(1,'#e66f77')]:
            pd_cls=M.scores.loc[M.scores.DEFAULT==cls,'PD_XGB']
            fig.add_trace(go.Histogram(x=pd_cls,nbinsx=35,opacity=.7,marker_color=color_,
                                     name=f'DEFAULT = {cls}',histnorm='probability'))
        fig.update_layout(barmode='overlay',height=320,xaxis_title='PD XGBoost',yaxis_title='Proporción dentro de clase',
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed',margin=dict(t=5,l=20,r=20,b=8))
        st.plotly_chart(fig,use_container_width=True)
    with g4:
        st.markdown('**Importancia de variables · XGBoost**')
        importances=pd.Series(M.xgb.feature_importances_,index=COLS).sort_values().tail(9)
        fig=go.Figure(go.Bar(x=importances.values,y=[LABELS[x] for x in importances.index],orientation='h',marker_color='#64b69d'))
        fig.update_layout(height=320,xaxis_title='Importancia interna (ganancia relativa)',
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed',margin=dict(t=5,l=15,r=15,b=8))
        st.plotly_chart(fig,use_container_width=True)
    st.markdown('**Calibración: probabilidad predicha vs incumplimiento observado**')
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(dash='dash',color='#9ca8a0'),name='Ideal'))
    for name,key in [('XGBoost','PD_XGB'),('Logit','PD_LOGIT')]:
        frac,means=calibration_curve(M.scores.DEFAULT,M.scores[key],n_bins=10,strategy='quantile')
        fig.add_trace(go.Scatter(x=means,y=frac,mode='lines+markers',name=name))
    fig.update_layout(height=280,xaxis_title='Probabilidad media estimada',yaxis_title='Default observado',
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#eaf3ed',margin=dict(t=5,l=20,r=20,b=8))
    st.plotly_chart(fig,use_container_width=True)
    st.caption('Precaución de sesgo: FINANCIAL_LITERACY_SCORE puede representar indirectamente características socioeconómicas. Se requiere evaluación formal antes de emplear este modelo fuera del ejercicio académico.')
    footnote()

elif page=='Recorridos y gobierno':
    st.title('P5/P6 · Recorridos, controles y gobierno')
    st.caption('Visible solo para gerencia y validación DTI; no se expone la matriz de permisos al analista de crédito.')
    with st.container(border=True):
        st.markdown('**Flujo autorizado**')
        st.write('Analista: bandeja → aceptar/condicionar/rechazar → bitácora. Si contradice XGBoost, se abre ficha y confirmación con motivo y aviso a gerencia.')
        st.write('Gerente: cartera TEST → revisar escenario de corte de rechazo (manteniendo corte inferior F2) → aplicar política → avisos a analistas → seguimiento de KPI y excepciones.')
        st.write('DTI: TRAIN (entrenamiento y validación) → TEST (evaluación cerrada) → curvas ROC/PR, matriz de confusión, calibración y sesgos.')
    st.subheader('Matriz de acceso de demostración')
    st.dataframe(pd.DataFrame([
       {'Rol':'Analista','Individuo TEST asignado':'Sí','Cambiar corte':'No','Ver ranking':'No','Ver métricas TEST agregadas':'No','Gobierno':'No'},
       {'Rol':'Gerente','Individuo TEST asignado':'No','Cambiar corte':'Sí','Ver ranking':'Sí','Ver métricas TEST agregadas':'Sí','Gobierno':'Sí'},
       {'Rol':'Operación','Individuo TEST asignado':'No','Cambiar corte':'No','Ver ranking':'No','Ver métricas TEST agregadas':'Sí','Gobierno':'No'},
       {'Rol':'DTI','Individuo TEST asignado':'No','Cambiar corte':'No','Ver ranking':'No','Ver métricas TEST agregadas':'Sí','Gobierno':'Sí'}]),hide_index=True,use_container_width=True)
    st.warning('Este selector de perfiles es únicamente un prototipo de interfaz. No implementa autenticación real ni control de acceso por servidor. Antes de usar datos sensibles: SSO institucional, controles RLS y PostgreSQL gestionado.')
    st.info('Los cambios de SQLite son compartidos solo mientras esta instancia esté activa. Para persistencia duradera se necesita una base de datos externa con control de acceso y auditoría.')
    footnote()
