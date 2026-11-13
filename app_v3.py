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
from src.monthly_kpis import monthly_summary, level
from src.kpi_views import render_analyst_month, render_manager_month
from src.message_views import render_messages
from src.profile_state import (
    reset_profile_navigation, demo_current_profile, demo_sign_out
)
from src.login_view import render_login

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

# Pantalla 0: acceso demo primero, SIN entrenar el modelo hasta entrar al dashboard.
# Este flujo no autentica identidades; es solo navegación por roles académicos.
selected_profile = demo_current_profile(st.session_state, PERSONAS)
if selected_profile is None:
    render_login(PERSONAS)
    st.stop()

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
    # Evitar que una búsqueda anterior suplante el Loan ID seleccionado en P1.
    st.session_state.pop('p2_buscar_loan', None)
    st.session_state.pop('p2_selector_loan', None)
    st.session_state['page_to']='Ficha de solicitud'
    st.rerun()


def ask_decision(row,decision):
    if decision==row.SUGERENCIA:
        send_decision(row,decision)
        st.session_state['table_rev']=st.session_state.get('table_rev',0)+1
        st.rerun()
    st.session_state['pending_choice']={'loan_id':str(row.LOAN_ID),'choice':decision}
    st.session_state['loan_actual']=str(row.LOAN_ID)
    # La excepción debe abrir exactamente el préstamo de la bandeja.
    st.session_state.pop('p2_buscar_loan', None)
    st.session_state.pop('p2_selector_loan', None)
    st.session_state['page_to']='Ficha de solicitud'
    st.rerun()

with st.sidebar:
    st.markdown('### AutoCredit Advisor')
    # El rol se elige únicamente en la pantalla de acceso, no en la barra lateral.
    role,analyst_id,name=PERSONAS[selected_profile]
    # No reutilizar Loan ID, filtros ni decisiones pendientes de otro perfil.
    # La bitácora SQLite permanece intacta y cada analista conserva sus casos.
    reset_profile_navigation(st.session_state, role, analyst_id)
    st.caption(f'{name} · {role.title()}')
    if role in ('analista','gerente','dti'):
        n=store.unread(role,analyst_id)
        if st.button(f'Mensajes ({n})',icon=':material/mail:',use_container_width=True):
            st.session_state['page_to']='Mensajes'
            st.rerun()
    if role=='analista':pages=['Bandeja','Ficha de solicitud','Mis indicadores','Mensajes']
    elif role=='gerente':pages=['Política y cartera','Analistas y KPI','Mensajes','Recorridos y gobierno']
    elif role=='dti':pages=['Validación del modelo','Mensajes','Recorridos y gobierno']
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
    st.divider()
    if st.button('Cerrar sesión',icon=':material/logout:',
                 use_container_width=True,type='secondary',key='ac_logout_sidebar'):
        # Solo se limpia el estado de este navegador; no afecta la bitácora SQLite.
        demo_sign_out(st.session_state)
        st.rerun()

page=st.session_state.page

if page=='Mensajes':
    render_messages(role,analyst_id,name)
    footnote()
    st.stop()


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
    /* Semáforos para cumplimiento de metas operativas */
    .ac-p1-kpi.low {border-color:rgba(222,114,130,.35);
        background:linear-gradient(140deg,rgba(95,40,48,.38),rgba(18,25,23,.74) 75%)}
    .ac-p1-kpi.low:before {background:linear-gradient(90deg,#e58b9a,transparent)}
    .ac-p1-kpi.low .number {color:#ffc0c6}
    .ac-p1-kpi.mid {border-color:rgba(221,174,90,.34);
        background:linear-gradient(140deg,rgba(90,68,32,.31),rgba(18,25,23,.74) 75%)}
    .ac-p1-kpi.mid:before {background:linear-gradient(90deg,#e5bf78,transparent)}
    .ac-p1-kpi.mid .number {color:#f3d597}
    .ac-p1-kpi.met {border-color:rgba(92,209,144,.36);
        background:linear-gradient(140deg,rgba(30,99,69,.3),rgba(18,25,23,.74) 75%)}
    .ac-p1-kpi.met .number {color:#8de5b3}
    .ac-p1-kpi.na:before {background:linear-gradient(90deg,#a0b1ab,transparent)}
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

    # KPI mensuales: fuente única del estado gerencial y decisiones registradas.
    metas_gerencia = store.targets()
    mensual = monthly_summary(decisiones, analyst_id)
    meta_mensual = float(metas_gerencia.get("Decisiones mensuales", 50))
    decisiones_mes = mensual["count"]
    avance_mes = decisiones_mes / meta_mensual
    semaforo_mes = level(decisiones_mes, meta_mensual)
    meta_justificacion = float(metas_gerencia.get("Con justificación", 1.0))
    tasa_justificacion = mensual["metrics"]["Con justificación"]
    semaforo_justificacion = level(tasa_justificacion, meta_justificacion)
    if tasa_justificacion is None:
        valor_justificacion = "—"
        detalle_justificacion = f"Sin excepciones en el mes · meta {meta_justificacion:.0%}"
    else:
        valor_justificacion = f"{tasa_justificacion:.0%}"
        detalle_justificacion = (
            f'{mensual["justified"]} de {mensual["overrides"]} excepciones · '
            f'meta mensual {meta_justificacion:.0%}'
        )

    st.markdown(f"""
    <div class="ac-p1-head">
      <div class="ac-p1-eyebrow">AutoCredit Advisor · Operación crediticia</div>
      <div class="ac-p1-title">P1 · Bandeja de solicitudes</div>
      <div class="ac-p1-description">{html.escape(name)} · {html.escape(analyst_id)} ·
      Préstamos originales de TEST, predichos por XGBoost (12 variables). La asignación a analistas es demostrativa.</div>
    </div>
    <div class="ac-p1-kpis">
      <div class="ac-p1-kpi blue"><div class="name">Solicitudes asignadas</div>
        <div class="number">{total:,}</div><div class="detail">Registros de TEST bajo este perfil*</div></div>
      <div class="ac-p1-kpi amber"><div class="name">Pendientes de decisión</div>
        <div class="number">{pendientes:,}</div><div class="detail">Aún sin decisión registrada</div></div>
      <div class="ac-p1-kpi {semaforo_mes}"><div class="name">Decisiones registradas · mes</div>
        <div class="number">{decisiones_mes:,} / {int(meta_mensual):,}</div>
        <div class="detail">Meta mensual de gerencia* · {avance_mes:.0%} de avance</div></div>
      <div class="ac-p1-kpi {semaforo_justificacion}"><div class="name">Excepciones justificadas · mes</div>
        <div class="number">{valor_justificacion}</div>
        <div class="detail">{detalle_justificacion}*</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div class="ac-p1-inline"><b>{priorizadas:,}</b> casos clasificados para rechazo '
        f'por la política vigente · Aceptar bajo <b>{M.corte_base:.2%}</b> '
        f'· Cortes de rechazo por DTI: '
        + ' / '.join(f'{x.replace("DTI ", "").capitalize()} {v:.1%}' for x, v in cortes_dti.items())
        + '</div>', unsafe_allow_html=True
    )

    # Filtros intuitivos como la antigua P1, pero sobre las predicciones V3.
    def _p1_restaurar():
        st.session_state['p1_estado_v3'] = 'Pendiente'
        st.session_state['p1_tipos_v3'] = ['Aceptar', 'Condicionar', 'Rechazar']
        st.session_state['p1_buscar_v3'] = ''
        st.session_state['p1_orden_v3'] = 'Intercalado · tres decisiones'
        st.session_state['p1_filas_v3'] = 15
        st.session_state['p1_pagina_v3'] = 1

    f1, f2 = st.columns([1.1, 1.6], gap='large')
    with f1:
        estado = st.segmented_control('Estado de la solicitud',
            options=['Pendiente', 'Resuelta', 'Todas'], default='Pendiente',
            key='p1_estado_v3', help='Filtra tus casos; no muestra solicitudes de otros analistas.')
    with f2:
        tipos = st.pills('Recomendación XGBoost',
            options=['Aceptar', 'Condicionar', 'Rechazar'],
            format_func=lambda opcion: {
                'Aceptar':'Aceptar', 'Condicionar':'Condicionar', 'Rechazar':'Rechazar'
            }[opcion],
            default=['Aceptar', 'Condicionar', 'Rechazar'],
            selection_mode='multi', key='p1_tipos_v3',
            help='Selecciona una o varias recomendaciones; las tres aparecen mezcladas por defecto.')

    c1, c2, c3, c4 = st.columns([2.1, 1.65, .9, 1.05], gap='small', vertical_alignment='bottom')
    with c1:
        busqueda = st.text_input('Buscar Loan ID', placeholder='Ej. 468086', key='p1_buscar_v3')
    with c2:
        orden = st.selectbox('Ordenar', [
            'Intercalado · tres decisiones', 'PD más alta primero',
            'PD más baja primero', 'Loan ID ascendente'], key='p1_orden_v3')
    with c3:
        tamano = st.selectbox('Filas', [15, 25, 50], key='p1_filas_v3')
    with c4:
        st.button('Restablecer', icon=':material/restart_alt:',
                  on_click=_p1_restaurar, use_container_width=True)

    filtrada = todos
    if estado != 'Todas':
        filtrada = filtrada.loc[filtrada['ESTADO'].eq(estado)]
    if not tipos:
        filtrada = filtrada.iloc[0:0]
    else:
        filtrada = filtrada.loc[filtrada['SUGERENCIA'].isin(tipos)]
    if busqueda.strip():
        filtrada = filtrada.loc[
            filtrada['LOAN_ID'].astype(str).str.contains(busqueda.strip(), case=False, regex=False)
        ]

    if orden == 'PD más alta primero':
        filtrada = filtrada.sort_values(['PD_XGB', 'LOAN_ID'], ascending=[False, True])
    elif orden == 'PD más baja primero':
        filtrada = filtrada.sort_values(['PD_XGB', 'LOAN_ID'])
    elif orden == 'Loan ID ascendente':
        filtrada = filtrada.sort_values('LOAN_ID')
    else:
        # Mezcla reproducible de las tres decisiones. No mezcla analistas ni TRAIN.
        # En cada nivel, Loan IDs quedan aleatorizados de forma estable.
        mezclada = filtrada.assign(
            _hash=pd.util.hash_pandas_object(filtrada['LOAN_ID'].astype(str), index=False).to_numpy()
        )
        grupos = [
            mezclada.loc[mezclada['SUGERENCIA'].eq(tipo)].sort_values('_hash').index.to_numpy()
            for tipo in ('Rechazar', 'Aceptar', 'Condicionar')
        ]
        posiciones = []
        for i in range(max((len(g) for g in grupos), default=0)):
            for grupo in grupos:
                if i < len(grupo):
                    posiciones.append(grupo[i])
        filtrada = mezclada.loc[posiciones].drop(columns='_hash')

    n_filtradas = len(filtrada)
    if not n_filtradas:
        st.warning('No hay solicitudes para esta combinación. Modifica los filtros o pulsa Restablecer.',
                   icon=':material/filter_alt_off:')
        footnote()
        st.stop()

    paginas = max(1, (n_filtradas + tamano - 1) // tamano)
    if 'p1_pagina_v3' not in st.session_state or not 1 <= st.session_state['p1_pagina_v3'] <= paginas:
        st.session_state['p1_pagina_v3'] = 1

    def _p1_anterior():
        st.session_state['p1_pagina_v3'] = max(1, st.session_state['p1_pagina_v3'] - 1)

    def _p1_siguiente():
        st.session_state['p1_pagina_v3'] = min(paginas, st.session_state['p1_pagina_v3'] + 1)

    barra, anterior, pagina, siguiente = st.columns([3.0, 1.2, 1.0, 1.2],
                                                      gap='small', vertical_alignment='bottom')
    with barra:
        st.caption(f'{n_filtradas:,} resultados · datos de TEST · {paginas:,} páginas. '
                   f'Orden: {orden.lower()}.')
    with anterior:
        st.button('← Anterior', disabled=st.session_state['p1_pagina_v3'] <= 1,
                  use_container_width=True, on_click=_p1_anterior)
    with pagina:
        actual = st.number_input('Página', min_value=1, max_value=paginas,
                                 step=1, key='p1_pagina_v3')
    with siguiente:
        st.button('Siguiente →', disabled=actual >= paginas,
                  use_container_width=True, on_click=_p1_siguiente)

    vista = filtrada.iloc[(actual - 1) * tamano:actual * tamano].copy()

    # Monto como precio legible, con separador de miles y 2 decimales.
    # Se usa u.m. porque la moneda de origen no está validada (no inventar MXN).
    tabla = pd.DataFrame({
        'Loan ID': vista['LOAN_ID'].astype(str).to_numpy(),
        'Decisión rápida': ['Seleccionar'] * len(vista),
        'Sugerencia': vista['SUGERENCIA'].to_numpy(),
        'XGBoost': np.where(vista['PRED_XGB'].eq(1), 'Default (1)', 'No default (0)'),
        'PD XGB': vista['PD_XGB'].map(lambda x: f'{x:.1%}').to_numpy(),
        'PD Logit': vista['PD_LOGIT'].map(lambda x: f'{x:.1%}').to_numpy(),
        'DTI': vista['DEBT_TO_INCOME'].map(lambda x: f'{x:.1%}').to_numpy(),
        'Monto (u.m.)': vista['LOAN_AMOUNT'].map(lambda x: f'{x:,.2f}').to_numpy(),
        'Pagos 12m': vista['MISSED_PAYMENTS_12M'].astype(int).to_numpy(),
    })

    def _color_fila(fila):
        colores = {
            'Aceptar': ('#82eac0', 'rgba(24,137,94,.14)'),
            'Condicionar': ('#f4ce82', 'rgba(165,111,22,.14)'),
            'Rechazar': ('#fb9fa7', 'rgba(169,45,66,.15)'),
        }
        fg, bg = colores[fila['Sugerencia']]
        resultado = [''] * len(fila)
        resultado[fila.index.get_loc('Sugerencia')] = (
            f'color:{fg};background-color:{bg};font-weight:730;'
        )
        resultado[fila.index.get_loc('PD XGB')] = (
            f'color:{fg};background-color:{bg};font-weight:750;'
        )
        resultado[fila.index.get_loc('Decisión rápida')] = (
            'color:#bce5d0;background-color:rgba(37,103,81,.13);font-weight:650;'
        )
        return resultado

    st.markdown('''<div class="ac-p1-legend"><strong>Decisión rápida:</strong>
      elige una opción en la segunda columna. Si coincide con la recomendación se guarda
      sin abrir otra pantalla. Si difiere, se abrirá la ficha con confirmación, motivo
      obligatorio y aviso a gerencia. <strong>Rojo</strong> = rechazar,
      <strong>ámbar</strong> = condicionar, <strong>verde</strong> = aceptar.
      La PD Logit es solo una referencia.</div>''', unsafe_allow_html=True)

    editada = st.data_editor(
        tabla.style.apply(_color_fila, axis=1),
        hide_index=True, num_rows='fixed', use_container_width=True,
        row_height=41, height=min(590, (len(tabla) + 1) * 41 + 13),
        key=f'p1_editor_v3_{analyst_id}_{st.session_state.get("table_rev", 0)}_'
            f'{actual}_{tamano}_{estado}_{"-".join(tipos)}_{orden}_{busqueda}',
        disabled=[c for c in tabla.columns if c != 'Decisión rápida'],
        column_config={
            'Loan ID': st.column_config.TextColumn('Loan ID', width='small'),
            'Decisión rápida': st.column_config.SelectboxColumn(
                'Decisión rápida', width='medium', required=True,
                options=['Seleccionar', 'Aceptar', 'Condicionar', 'Rechazar', 'Ver detalle']),
            'Sugerencia': st.column_config.TextColumn('Sugerencia', width='small',
                help='XGBoost, tres zonas. Corte inferior F2 fijo y corte superior gerencial por DTI.'),
            'XGBoost': st.column_config.TextColumn('XGB clase', width='small',
                help='Clasificación binaria del modelo con el umbral inferior F2. 1 indica riesgo de default.'),
            'PD XGB': st.column_config.TextColumn('PD XGB', width='small',
                help='Probabilidad de incumplimiento estimada por el modelo campeón XGBoost.'),
            'PD Logit': st.column_config.TextColumn('PD Logit', width='small',
                help='Modelo complementario; no altera la recomendación de crédito.'),
            'DTI': st.column_config.TextColumn('DTI', width='small',
                help='Deuda total sobre ingreso.'),
            'Monto (u.m.)': st.column_config.TextColumn('Monto (u.m.)', width='small',
                help='Monto solicitado; valores con separador de miles y decimales. Moneda aún no certificada.'),
            'Pagos 12m': st.column_config.NumberColumn('Pagos 12m', format='%d', width='small',
                help='Número de pagos incumplidos durante los últimos 12 meses.'),
        }
    )

    cambio = editada.index[editada['Decisión rápida'].ne('Seleccionar')].tolist()
    if cambio:
        pos = cambio[0]
        loan = str(editada.at[pos, 'Loan ID'])
        accion = str(editada.at[pos, 'Decisión rápida'])
        registro = vista.loc[vista['LOAN_ID'].astype(str).eq(loan)]
        if registro.empty:
            st.error('El Loan ID seleccionado ya no pertenece a la vista filtrada.')
        elif accion == 'Ver detalle':
            open_loan(loan)
        elif accion in ('Aceptar', 'Condicionar', 'Rechazar'):
            # Mantiene el flujo compartido de app_v3: guarda coincidencias desde
            # P1, y ante una excepción abre P2 y el cuadro de confirmación.
            ask_decision(registro.iloc[0], accion)

    st.caption('Fuente: archivos TRAIN/TEST de 12 variables del equipo. Loan ID original de TEST. '
               'Predicciones calculadas con XGBoost y Logit. Asignaciones de analistas, '
               'decisiones operativas y mensajes: demostración académica; no producción.')


elif page=='Ficha de solicitud':
    all_cases = rated(M.scores[M.scores.ANALISTA_ID == analyst_id]).copy()

    st.markdown("""
    <style>
    /* Margen negro de seguridad bajo la barra superior de Streamlit. */
    .ac-p2-top-spacer {
        height: 20px;
        width: 100%;
        background: transparent;
        margin: 0 0 4px 0;
        border: 0;
    }
    .ac-p2-consulta-title {
        color:#f1f7f3;
        font-size:1.05rem;
        font-weight:760;
        line-height:1.45;
        margin:.15rem 0 .75rem 0;
    }
    .ac-p2-head {margin:.15rem 0 1rem 0}
    .ac-p2-title {color:#f1f7f3;font-size:1.8rem;font-weight:790;letter-spacing:-.04em;line-height:1.2;margin:.15rem 0 .25rem}
    .ac-p2-sub {color:#aebbb4;font-size:.9rem;line-height:1.55}
    .ac-p2-cards {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:.55rem 0 1rem}
    .ac-p2-card {position:relative;overflow:hidden;min-height:116px;padding:15px 18px;border-radius:15px;
        border:1px solid rgba(119,162,141,.24);
        background:linear-gradient(140deg,rgba(36,63,52,.57),rgba(18,25,23,.66) 68%);
        box-shadow:0 5px 24px rgba(0,0,0,.13)}
    .ac-p2-card:before {content:'';position:absolute;top:0;left:16px;right:16px;height:2px;
        background:linear-gradient(90deg,rgba(75,214,151,.85),transparent)}
    .ac-p2-card .label {font-size:.79rem;color:#c6d5cc;font-weight:650;line-height:1.4}
    .ac-p2-card .value {font-size:clamp(1.35rem,2.2vw,2.45rem);font-weight:800;color:#eff8f1;line-height:1.22;margin:.28rem 0 .12rem}
    .ac-p2-card .sub {font-size:.73rem;color:#a9bbb1;line-height:1.45}
    .ac-p2-card.alert {border-color:rgba(231,113,130,.34);background:linear-gradient(140deg,rgba(95,38,48,.40),rgba(19,26,23,.76) 73%)}
    .ac-p2-card.alert:before {background:linear-gradient(90deg,#f08290,transparent)}
    .ac-p2-card.alert .value {color:#ffb7bf}
    .ac-p2-card.warn {border-color:rgba(227,182,90,.32);background:linear-gradient(140deg,rgba(103,75,28,.33),rgba(19,26,23,.76) 73%)}
    .ac-p2-card.warn:before {background:linear-gradient(90deg,#f0c56b,transparent)}
    .ac-p2-card.warn .value {color:#f8d58c}
    .ac-p2-card.ok {border-color:rgba(92,209,144,.34);background:linear-gradient(140deg,rgba(28,100,69,.30),rgba(19,26,23,.76) 73%)}
    .ac-p2-card.ok:before {background:linear-gradient(90deg,#61d99a,transparent)}
    .ac-p2-card.ok .value {color:#97e8ba}
    .ac-p2-card.blue:before {background:linear-gradient(90deg,#7ab9e6,transparent)}
    .ac-p2-banner {padding:.8rem 1rem;border-radius:12px;border:1px solid rgba(255,255,255,.06);margin:.28rem 0 .65rem;font-size:.93rem;line-height:1.5}
    .ac-p2-banner strong {font-weight:780}
    .ac-p2-banner.danger {background:rgba(122,39,54,.50);color:#ffd3d8;border-color:rgba(237,118,134,.18)}
    .ac-p2-banner.warn {background:rgba(103,73,24,.42);color:#fde2aa;border-color:rgba(229,184,92,.18)}
    .ac-p2-banner.ok {background:rgba(25,86,60,.40);color:#c7f2da;border-color:rgba(98,218,157,.18)}
    .ac-p2-toolbar {padding:.72rem .9rem;border:1px solid rgba(100,166,130,.18);border-radius:12px;
        background:linear-gradient(115deg,rgba(33,59,48,.40),rgba(20,30,24,.12));margin:.2rem 0 .85rem}
    .ac-p2-section {padding:.15rem 0 .1rem 0}
    .ac-p2-section h3 {font-size:1.55rem!important;letter-spacing:-.03em}
    .ac-p2-chip {display:inline-block;padding:.2rem .55rem;border-radius:999px;font-size:.76rem;font-weight:700;margin-right:.35rem}
    .ac-p2-chip.r-low {background:rgba(40,125,83,.28);color:#8fe1b5}
    .ac-p2-chip.r-mid {background:rgba(128,92,24,.30);color:#f2d48f}
    .ac-p2-chip.r-high {background:rgba(134,45,60,.30);color:#ffb3bd}
    @media(max-width:1180px){.ac-p2-cards{grid-template-columns:repeat(3,minmax(0,1fr))}}
    @media(max-width:760px){.ac-p2-cards{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>
    """, unsafe_allow_html=True)

    if all_cases.empty:
        st.warning('No hay solicitudes asignadas a este analista.', icon=':material/inbox:')
        footnote()
        st.stop()

    # ========= Helpers =========
    def _nivel_relativo(valor, serie):
        q1 = float(serie.quantile(.25))
        q2 = float(serie.quantile(.50))
        q3 = float(serie.quantile(.75))
        if valor <= q1:
            return 'Bajo'
        elif valor <= q3:
            return 'Medio'
        return 'Alto'

    def _card_tone(sugerencia):
        return 'alert' if sugerencia == 'Rechazar' else 'warn' if sugerencia == 'Condicionar' else 'ok'

    def _pct_pp(valor):
        return f'{valor:.1%}'

    def _pp_diff(valor, referencia):
        dif = (valor - referencia) * 100
        signo = '+' if dif >= 0 else ''
        return f'{signo}{dif:.1f} pp'

    # ========= Margen superior y encabezado simplificado =========
    # Evita que el primer contenido visible quede bajo la barra de Streamlit.
    st.markdown("""
    <div class="ac-p2-top-spacer" aria-hidden="true"></div>
    <div class="ac-p2-consulta-title">Consulta del expediente</div>
    """, unsafe_allow_html=True)

    # ========= Selector de folio desde P2 =========
    actual_guardado = str(st.session_state.get('loan_actual') or '')
    cbar1, cbar2, cbar3 = st.columns([1.9, 1.25, .8], gap='small', vertical_alignment='bottom')

    with cbar1:
        buscar = st.text_input(
            'Buscar Loan ID · original de TEST',
            value=actual_guardado,
            placeholder='Ej. 277432',
            key='p2_buscar_loan',
            help='Escribe el identificador completo o parte de él. Solo se consultan solicitudes asignadas a tu perfil.'
        )

    coincidencias = all_cases.copy()
    if buscar.strip():
        coincidencias = coincidencias[
            coincidencias['LOAN_ID'].astype(str).str.contains(buscar.strip(), case=False, regex=False)
        ]

    coincidencias = coincidencias.sort_values(['PD_XGB', 'LOAN_ID'], ascending=[False, True])

    opciones = coincidencias['LOAN_ID'].astype(str).tolist()[:250]
    if not opciones:
        st.warning('No hay coincidencias para ese Loan ID dentro de las solicitudes asignadas.', icon=':material/search_off:')
        if st.button('Volver a bandeja', icon=':material/arrow_back:'):
            st.session_state.page_to = 'Bandeja'
            st.rerun()
        footnote()
        st.stop()

    idx_default = opciones.index(actual_guardado) if actual_guardado in opciones else 0
    with cbar2:
        loan = st.selectbox('Selecciona el folio', opciones, index=idx_default, key='p2_selector_loan')

    with cbar3:
        if st.button('Cargar detalle', use_container_width=True, icon=':material/visibility:'):
            st.session_state['loan_actual'] = str(loan)
            st.rerun()

    st.session_state['loan_actual'] = str(loan)

    rows = all_cases[all_cases['LOAN_ID'].astype(str) == str(loan)]
    if rows.empty:
        st.error('El Loan ID seleccionado no está disponible para este analista.')
        footnote()
        st.stop()

    r = rows.iloc[0]

    # ========= Referencias TRAIN / TEST =========
    train_good = M.train[M.train.DEFAULT == 0]
    train_bad = M.train[M.train.DEFAULT == 1]

    hist_train = float(M.train.DEFAULT.mean())
    med_pd_test = float(M.scores.PD_XGB.median())

    dti_med_good = float(train_good.DEBT_TO_INCOME.median())
    pti_med_good = float(train_good.PAYMENT_TO_INCOME.median())
    ru_med_good = float(train_good.REVOLVING_UTILIZATION.median())
    ltv_med_good = float(train_good.LOAN_TO_VALUE.median())
    dp_med_good = float(train_good.DOWN_PAYMENT_PCT.median())

    dti_nivel = _nivel_relativo(float(r.DEBT_TO_INCOME), M.train.DEBT_TO_INCOME)
    riesgo_nivel = 'Alto' if r.SUGERENCIA == 'Rechazar' else 'Medio' if r.SUGERENCIA == 'Condicionar' else 'Bajo'
    tone = _card_tone(r.SUGERENCIA)

    st.markdown(f"""
    <div class="ac-p2-head">
      <div class="ac-p2-title">Análisis de la solicitud {html.escape(str(r.LOAN_ID))}</div>
      <div class="ac-p2-sub">
        <strong>Loan ID {html.escape(str(r.LOAN_ID))}</strong> · {html.escape(str(r.SEG_DTI))} ·
        Sugerencia del modelo: <strong>{html.escape(str(r.SUGERENCIA))}</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ========= Main insights =========
    st.markdown(f"""
    <div class="ac-p2-cards">
      <div class="ac-p2-card {tone}">
        <div class="label">PD XGBoost</div>
        <div class="value">{r.PD_XGB:.1%}</div>
        <div class="sub">vs. corte de rechazo {r.CORTE:.1%}</div>
      </div>
      <div class="ac-p2-card {'alert' if r.PD_LOGIT >= r.CORTE else 'warn' if r.PD_LOGIT >= M.corte_base else 'ok'}">
        <div class="label">PD Logit</div>
        <div class="value">{r.PD_LOGIT:.1%}</div>
        <div class="sub">Referencia complementaria</div>
      </div>
      <div class="ac-p2-card {tone}">
        <div class="label">Decisión propuesta</div>
        <div class="value">{html.escape(str(r.SUGERENCIA))}</div>
        <div class="sub">Según XGBoost y la política vigente</div>
      </div>
      <div class="ac-p2-card {'alert' if riesgo_nivel=='Alto' else 'warn' if riesgo_nivel=='Medio' else 'ok'}">
        <div class="label">Nivel de riesgo</div>
        <div class="value">{riesgo_nivel}</div>
        <div class="sub">Interpretación operativa del caso</div>
      </div>
      <div class="ac-p2-card {'alert' if dti_nivel=='Alto' else 'warn' if dti_nivel=='Medio' else 'ok'}">
        <div class="label">Endeudamiento</div>
        <div class="value">{dti_nivel}</div>
        <div class="sub">DTI {r.DEBT_TO_INCOME:.1%} vs. mediana TRAIN {M.train.DEBT_TO_INCOME.median():.1%}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ========= Banners =========
    if r.SUGERENCIA == 'Rechazar':
        st.markdown(
            f'<div class="ac-p2-banner danger"><strong>ALERTA ·</strong> '
            f'La PD XGBoost es <strong>{r.PD_XGB:.1%}</strong> y supera el corte de rechazo '
            f'(<strong>{r.CORTE:.1%}</strong>). La decisión propuesta por el modelo es <strong>RECHAZAR</strong>.</div>',
            unsafe_allow_html=True
        )
    elif r.SUGERENCIA == 'Condicionar':
        st.markdown(
            f'<div class="ac-p2-banner warn"><strong>RIESGO INTERMEDIO ·</strong> '
            f'La PD XGBoost es <strong>{r.PD_XGB:.1%}</strong>. El caso cae en la zona de '
            f'<strong>CONDICIONAR</strong>; revisar capacidad de pago, documentación y condiciones del crédito.</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="ac-p2-banner ok"><strong>RIESGO INFERIOR ·</strong> '
            f'La PD XGBoost es <strong>{r.PD_XGB:.1%}</strong>, por debajo del corte inferior. '
            f'La decisión propuesta es <strong>ACEPTAR</strong>, sujeta a validación documental.</div>',
            unsafe_allow_html=True
        )

    if r.PD_XGB > med_pd_test:
        st.markdown(
            f'<div class="ac-p2-banner danger"><strong>Comparación con TEST ·</strong> '
            f'La PD de este caso (<strong>{r.PD_XGB:.1%}</strong>) supera la mediana de TEST '
            f'(<strong>{med_pd_test:.1%}</strong>).</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="ac-p2-banner ok"><strong>Comparación con TEST ·</strong> '
            f'La PD de este caso (<strong>{r.PD_XGB:.1%}</strong>) está por debajo de la mediana de TEST '
            f'(<strong>{med_pd_test:.1%}</strong>).</div>',
            unsafe_allow_html=True
        )

    if st.session_state.get('pending_choice') and str(st.session_state['pending_choice'].get('loan_id')) == str(r.LOAN_ID):
        eleccion = st.session_state['pending_choice'].get('choice')
        st.markdown(
            f'<div class="ac-p2-banner warn"><strong>Advertencia de excepción ·</strong> '
            f'Estás intentando registrar <strong>{eleccion}</strong>, que difiere de la '
            f'recomendación del modelo. Al confirmar, se pedirá justificación y se notificará a gerencia.</div>',
            unsafe_allow_html=True
        )

    # ========= Barra de acciones =========
    st.markdown('<div class="ac-p2-toolbar">El modelo no toma la decisión final; el analista confirma. '
                'Si la decisión contradice la recomendación, se abrirá una confirmación con motivo obligatorio.</div>',
                unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns([1, 1, 1, .85], gap='small')
    with b1:
        if st.button('Aceptar', icon=':material/check_circle:',
                     use_container_width=True, type='primary' if r.SUGERENCIA == 'Aceptar' else 'secondary'):
            ask_decision(r, 'Aceptar')
    with b2:
        if st.button('Condicionar', icon=':material/rule:',
                     use_container_width=True, type='primary' if r.SUGERENCIA == 'Condicionar' else 'secondary'):
            ask_decision(r, 'Condicionar')
    with b3:
        if st.button('Rechazar', icon=':material/block:',
                     use_container_width=True, type='primary' if r.SUGERENCIA == 'Rechazar' else 'secondary'):
            ask_decision(r, 'Rechazar')
    with b4:
        if st.button('Volver a bandeja', icon=':material/arrow_back:', use_container_width=True):
            st.session_state.page_to = 'Bandeja'
            st.rerun()

    # ========= Gráficas 1 =========
    st.markdown('<div class="ac-p2-section"></div>', unsafe_allow_html=True)
    g1, g2 = st.columns([1.05, .95], gap='large')

    with g1:
        st.subheader('Mapa de decisión del modelo')
        fig = go.Figure()

        fig.add_trace(go.Indicator(
            mode='gauge+number',
            value=float(r.PD_XGB * 100),
            number={'suffix': '%'},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': '#e56a72' if r.SUGERENCIA == 'Rechazar' else '#e1bb63' if r.SUGERENCIA == 'Condicionar' else '#37d58e'},
                'steps': [
                    {'range': [0, float(M.corte_base * 100)], 'color': '#163b2d'},
                    {'range': [float(M.corte_base * 100), float(r.CORTE * 100)], 'color': '#5f4a1f'},
                    {'range': [float(r.CORTE * 100), 100], 'color': '#5a2730'}
                ],
                'threshold': {
                    'line': {'color': '#ffffff', 'width': 4},
                    'value': float(r.CORTE * 100)
                }
            }
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=18, r=18, t=15, b=15),
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e8f4ed'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f'Zonas: aceptar bajo {M.corte_base:.2%} · condicionar entre {M.corte_base:.2%} y {r.CORTE:.2%} · rechazar sobre {r.CORTE:.2%}.'
        )

    with g2:
        st.subheader('Distribución de PD en TEST')
        hist = go.Figure()
        hist.add_trace(go.Histogram(
            x=M.scores['PD_XGB'],
            nbinsx=35,
            marker_color='#5d8cc9',
            opacity=.75,
            name='TEST',
            histnorm='probability'
        ))
        hist.add_vline(
            x=float(r.PD_XGB),
            line_dash='solid',
            line_color='#f07f8b' if r.SUGERENCIA == 'Rechazar' else '#f0c56b' if r.SUGERENCIA == 'Condicionar' else '#51d79a',
            line_width=3
        )
        hist.add_vline(x=float(M.corte_base), line_dash='dash', line_color='#72e5a8', line_width=2)
        hist.add_vline(x=float(r.CORTE), line_dash='dot', line_color='#ffffff', line_width=2)
        hist.update_layout(
            height=300,
            xaxis_title='PD XGBoost',
            yaxis_title='Proporción',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#eaf3ed',
            margin=dict(t=10, l=18, r=18, b=15),
            showlegend=False
        )
        st.plotly_chart(hist, use_container_width=True)
        st.caption('Línea sólida: esta solicitud · línea verde: corte de aceptación · línea blanca: corte de rechazo.')

    # ========= Gráficas 2 =========
    g3, g4 = st.columns([1.08, .92], gap='large')

    with g3:
        st.subheader('Endeudamiento y estructura del caso vs referencias')
        campos = [
            'DEBT_TO_INCOME', 'PAYMENT_TO_INCOME', 'REVOLVING_UTILIZATION',
            'LOAN_TO_VALUE', 'DOWN_PAYMENT_PCT'
        ]
        etiquetas = [
            'Deuda / ingreso', 'Pago / ingreso', 'Uso revolvente',
            'Préstamo / valor', 'Enganche'
        ]
        caso = [float(r[c] * 100) for c in campos]
        buenos = [float(train_good[c].median() * 100) for c in campos]
        malos = [float(train_bad[c].median() * 100) for c in campos]

        comp = go.Figure()
        comp.add_trace(go.Bar(
            name='Esta solicitud', y=etiquetas, x=caso,
            orientation='h', marker_color='#78aaf5'
        ))
        comp.add_trace(go.Bar(
            name='Mediana sin incumplimiento', y=etiquetas, x=buenos,
            orientation='h', marker_color='#a8b1ac'
        ))
        comp.add_trace(go.Bar(
            name='Mediana con incumplimiento', y=etiquetas, x=malos,
            orientation='h', marker_color='#e4818c'
        ))
        comp.update_layout(
            barmode='group',
            height=360,
            xaxis_title='Porcentaje (%)',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#eaf3ed',
            margin=dict(t=8, l=10, r=10, b=5),
            legend=dict(orientation='h', y=1.13)
        )
        st.plotly_chart(comp, use_container_width=True)

    with g4:
        st.subheader('Perfil relativo del caso')
        perfil_campos = ['DEBT_TO_INCOME', 'PAYMENT_TO_INCOME', 'REVOLVING_UTILIZATION', 'LOAN_TO_VALUE', 'DOWN_PAYMENT_PCT', 'MISSED_PAYMENTS_12M']
        perfil_etiquetas = ['DTI', 'PTI', 'Uso revolvente', 'LTV', 'Enganche', 'Pagos omitidos']

        caso_rel = []
        bueno_rel = []
        malo_rel = []

        for c in perfil_campos:
            base_good = float(train_good[c].median())
            base_bad = float(train_bad[c].median())
            if base_good == 0:
                caso_rel.append(100.0)
            else:
                caso_rel.append(float(r[c] / base_good * 100))
            bueno_rel.append(100.0)
            malo_rel.append(100.0 if base_good == 0 else float(base_bad / base_good * 100))

        perfil = go.Figure()
        perfil.add_trace(go.Scatter(
            x=perfil_etiquetas, y=caso_rel, mode='lines+markers',
            line=dict(color='#7fb0ff', width=3), marker=dict(size=8), name='Solicitud / mediana buenos'
        ))
        perfil.add_trace(go.Scatter(
            x=perfil_etiquetas, y=bueno_rel, mode='lines',
            line=dict(color='#8fd7b1', dash='dash'), name='Referencia buenos = 100'
        ))
        perfil.add_trace(go.Scatter(
            x=perfil_etiquetas, y=malo_rel, mode='lines+markers',
            line=dict(color='#e17a86', width=2), marker=dict(size=7), name='Mediana incumplidos / buenos'
        ))
        perfil.update_layout(
            height=360,
            yaxis_title='Índice relativo (100 = mediana de buenos pagadores)',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#eaf3ed',
            margin=dict(t=8, l=10, r=10, b=25),
            legend=dict(orientation='h', y=1.12)
        )
        st.plotly_chart(perfil, use_container_width=True)
        st.caption('Valores por arriba de 100 indican que la solicitud está por encima de la mediana de buenos pagadores.')

    # ========= Gráficas 3 =========
    g5, g6 = st.columns([1, 1], gap='large')

    with g5:
        st.subheader('Ubicación de la solicitud dentro de TRAIN')
        percentil_vars = [
            ('DEBT_TO_INCOME', 'DTI'),
            ('PAYMENT_TO_INCOME', 'PTI'),
            ('REVOLVING_UTILIZATION', 'Uso revolvente'),
            ('LOAN_TO_VALUE', 'LTV'),
            ('DOWN_PAYMENT_PCT', 'Enganche')
        ]
        nombres = []
        percentiles = []
        colores = []
        for var, nom in percentil_vars:
            serie = M.train[var].dropna()
            pct = float((serie <= float(r[var])).mean() * 100)
            nombres.append(nom)
            percentiles.append(pct)
            colores.append('#e56a72' if pct >= 75 else '#e6bf66' if pct >= 40 else '#52d88f')

        fig_pct = go.Figure(go.Bar(
            x=percentiles, y=nombres, orientation='h',
            marker_color=colores, text=[f'{x:.0f}%' for x in percentiles],
            textposition='outside'
        ))
        fig_pct.update_layout(
            height=310,
            xaxis_title='Percentil dentro de TRAIN',
            xaxis=dict(range=[0, 100]),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#eaf3ed',
            margin=dict(t=5, l=12, r=18, b=8)
        )
        st.plotly_chart(fig_pct, use_container_width=True)
        st.caption('Percentiles altos en DTI, PTI, LTV o uso revolvente suelen reflejar mayor presión financiera.')

    with g6:
        st.subheader('Resumen visual de decisión')
        resumen = pd.DataFrame([
            ['PD XGBoost', f'{r.PD_XGB:.1%}', f'Corte rechazo {r.CORTE:.1%}'],
            ['PD Logit', f'{r.PD_LOGIT:.1%}', 'Modelo complementario'],
            ['DTI', f'{r.DEBT_TO_INCOME:.1%}', f'Mediana buenos {dti_med_good:.1%}'],
            ['Pago / ingreso', f'{r.PAYMENT_TO_INCOME:.1%}', f'Mediana buenos {pti_med_good:.1%}'],
            ['Uso revolvente', f'{r.REVOLVING_UTILIZATION:.1%}', f'Mediana buenos {ru_med_good:.1%}'],
            ['Préstamo / valor', f'{r.LOAN_TO_VALUE:.1%}', f'Mediana buenos {ltv_med_good:.1%}'],
            ['Enganche', f'{r.DOWN_PAYMENT_PCT:.1%}', f'Mediana buenos {dp_med_good:.1%}'],
            ['Incumplimiento histórico TRAIN', f'{hist_train:.2%}', 'No es límite ni recomendación']
        ], columns=['Indicador', 'Solicitud', 'Referencia'])

        st.dataframe(
            resumen,
            hide_index=True,
            use_container_width=True,
            height=310,
            column_config={
                'Indicador': st.column_config.TextColumn('Indicador', width='medium'),
                'Solicitud': st.column_config.TextColumn('Solicitud', width='small'),
                'Referencia': st.column_config.TextColumn('Referencia', width='medium')
            }
        )

    # ========= Insights ejecutivos =========
    st.subheader('Insights ejecutivos del caso')
    insights = []

    if r.PD_XGB >= r.CORTE:
        insights.append(
            f'La PD XGBoost ({r.PD_XGB:.1%}) rebasa el corte de rechazo ({r.CORTE:.1%}), por lo que la decisión propuesta es RECHAZAR.'
        )
    elif r.PD_XGB >= M.corte_base:
        insights.append(
            f'La PD XGBoost ({r.PD_XGB:.1%}) cae en zona intermedia, por eso el modelo propone CONDICIONAR.'
        )
    else:
        insights.append(
            f'La PD XGBoost ({r.PD_XGB:.1%}) está debajo del corte inferior ({M.corte_base:.1%}), por lo que el modelo propone ACEPTAR.'
        )

    insights.append(
        f'El DTI es {r.DEBT_TO_INCOME:.1%}, {_pp_diff(float(r.DEBT_TO_INCOME), dti_med_good)} respecto a la mediana de buenos pagadores ({dti_med_good:.1%}).'
    )
    insights.append(
        f'El uso revolvente es {r.REVOLVING_UTILIZATION:.1%}, {_pp_diff(float(r.REVOLVING_UTILIZATION), ru_med_good)} respecto a la referencia de buenos pagadores.'
    )
    insights.append(
        f'El préstamo/valor (LTV) es {r.LOAN_TO_VALUE:.1%}, {_pp_diff(float(r.LOAN_TO_VALUE), ltv_med_good)} frente a la mediana de buenos pagadores.'
    )
    insights.append(
        f'La PD de esta solicitud está {"por arriba" if r.PD_XGB > med_pd_test else "por debajo"} de la mediana de TEST ({med_pd_test:.1%}).'
    )

    for txt in insights:
        st.markdown(f'- {txt}')

    # ========= Expediente =========
    with st.expander('Expediente y variables del modelo', expanded=False):
        detalle = pd.DataFrame([
            {
                'Variable': LABELS[k],
                'Solicitud': formato(k, r[k]),
                'Mediana buenos pagadores (TRAIN)': formato(k, train_good[k].median()),
                'Mediana con incumplimiento (TRAIN)': formato(k, train_bad[k].median())
            }
            for k in COLS
        ])
        st.dataframe(detalle, hide_index=True, use_container_width=True)
        st.caption(
            'Las referencias usan TRAIN. FINANCIAL_LITERACY_SCORE permanece en el modelo de 12 variables del ejercicio académico; '
            'cualquier uso fuera del prototipo requiere evaluación formal de sesgos.'
        )

    if st.session_state.get('pending_choice') and str(st.session_state.pending_choice.get('loan_id')) == str(loan):
        override_dialog()

    footnote()

elif page=='Mis indicadores':
    render_analyst_month(name, analyst_id, M.scores)
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
    render_manager_month(name)
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
