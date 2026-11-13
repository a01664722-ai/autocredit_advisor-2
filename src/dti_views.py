"""Interfaz compartida de reportes para analistas y centro de Soporte."""
from __future__ import annotations
import html
import pandas as pd
import streamlit as st
from src.ops_monitor import (
    CATEGORIES, STATES, create_incident, incidents, change_incident,
    incident_month_summary
)
from src.monthly_kpis import as_local


@st.dialog("Reportar incidencia a Soporte",width="large")
def report_dti_dialog(analyst_id,score_df):
    st.markdown("**Notificar una falla del tablero o del modelo**")
    st.caption("Se abrirá un ticket real en esta instancia y se notificará en "
               "las bandejas de Soporte y de gerencia.")
    with st.form(f"report_dti_{analyst_id}"):
        a,b=st.columns(2,gap="medium")
        with a:
            category=st.selectbox("Tipo de incidencia",list(CATEGORIES))
        with b:
            priority=st.selectbox("Prioridad",["Normal","Alta"])
        title=st.text_input("Asunto*",max_chars=100,
                placeholder="Ej. No se muestra la gráfica de riesgo")
        loan_id=st.text_input("Loan ID involucrado (opcional)",max_chars=40,
                placeholder="Solo si se relaciona con un préstamo asignado")
        detail=st.text_area("Descripción de la falla*",max_chars=2000,height=165,
                placeholder="¿Qué pantalla falló? ¿Qué esperabas ver? ¿Qué ocurrió?")
        submitted=st.form_submit_button("Enviar alerta a Soporte y gerencia",
                         type="primary",icon=":material/report_problem:",
                         use_container_width=True)
    if submitted:
        if loan_id.strip():
            exists=score_df.loc[
               (score_df.LOAN_ID.astype(str)==loan_id.strip())&
               (score_df.ANALISTA_ID==analyst_id)]
            if exists.empty:
                st.error("El Loan ID indicado no pertenece a este analista en TEST.")
                return
        try:
            ticket=create_incident(analyst_id,category,title,detail,priority,loan_id.strip())
        except (ValueError,PermissionError) as exc:
            st.error(str(exc))
        else:
            st.session_state[f"dti_reported_{analyst_id}"]=ticket
            st.rerun()


def render_analyst_dti_sidebar(analyst_id,score_df):
    """Un solo botón discreto, fuera del flujo de decisiones crediticias."""
    st.caption("Soporte técnico")
    if st.button("Reportar falla a Soporte",icon=":material/report_problem:",
                 key=f"report_dti_open_{analyst_id}",use_container_width=True,
                 help="Reporta fallas de datos, predicción, métricas o interfaz. Se genera un ticket."):
        report_dti_dialog(analyst_id,score_df)
    reported=st.session_state.pop(f"dti_reported_{analyst_id}",None)
    if reported is not None:
        st.success(f"Incidencia #{reported} enviada a Soporte y gerencia.")


def render_dti_incidents(show_heading=True,show_kpis=True):
    """Bandeja compartida; permite incrustarla sin duplicar KPI en la portada."""
    if show_heading:
        st.markdown('<div style="height:16px"></div>',unsafe_allow_html=True)
        st.markdown("### Incidencias de soporte")
        st.caption("Reportes de Adrián y Sofía; al resolverlos se avisa "
                   "al analista y a gerencia.")
    current=incidents(limit=100000)
    summary=incident_month_summary(current)
    if show_kpis:
        x,y,z,w=st.columns(4,gap="small")
        x.metric("Reportadas este mes",summary["total"])
        y.metric("Abiertas",summary["open"])
        z.metric("En revisión",summary["review"])
        w.metric("Resueltas",summary["solved"])
        st.caption(f"Resolución de incidencias creadas este mes: "
                   f"{summary['rate']:.1%}" if summary["rate"] is not None
                   else "Sin incidencias este mes; tasa de resolución no evaluable.")

    a,b=st.columns([1.1,2],gap="medium")
    with a:
        state=st.selectbox("Estado",["Todas",*STATES],key="dti_ticket_filter")
    with b:
        query=st.text_input("Buscar",placeholder="Número de ticket, asunto o Loan ID",
                            key="dti_ticket_search")
    visible=[r for r in current if state=="Todas" or r["status"]==state]
    if query.strip():
        q=query.casefold().strip().lstrip("#")
        visible=[r for r in visible if any(
            q in str(r.get(field) or "").casefold()
            for field in ("id","title","details","loan_id","analyst_id"))]
    if not visible:
        st.info("No hay incidencias con estos filtros. Cuando un analista reporte un problema, aparecerá aquí.")
        return
    data=[{
        "Ticket":f"#{r['id']}",
        "Origen":"Adrián · A-017" if r["analyst_id"]=="A-017" else "Sofía · A-022",
        "Categoría":r["category"],"Prioridad":r["priority"],
        "Estado":r["status"],"Loan ID":r.get("loan_id") or "—",
        "Reportado":(as_local(r["created_at"]).strftime("%d/%m/%Y %H:%M")
                     if as_local(r["created_at"]) else "—")
    } for r in visible]
    st.dataframe(pd.DataFrame(data),hide_index=True,use_container_width=True)
    options={r["id"]:r for r in visible}
    selected=st.selectbox("Abrir expediente de incidencia",options=list(options),
                     format_func=lambda ticket:(
                         f"#{ticket} · {options[ticket]['title']} "
                         f"({options[ticket]['status']})"),
                     key="dti_ticket_selected")
    item=options[selected]
    with st.container(border=True):
        st.markdown(f"**#{item['id']} · {html.escape(item['title'])}**")
        st.caption(f"Reportó: {item['analyst_id']} · {item['category']} · "
                   f"Prioridad: {item['priority']}")
        st.write(item["details"])
        if item.get("loan_id"):
            st.caption(f"Loan ID de referencia: {item['loan_id']}")
        if item["status"]=="Resuelto":
            st.success(f"Resuelto: {item['resolution_note']}")
        with st.form(f"dti_ticket_resolve_{item['id']}"):
            status=st.selectbox("Cambiar estado",list(STATES),
               index=STATES.index(item["status"]),key=f"dti_ticket_status_{item['id']}")
            note=st.text_area("Solución implementada (obligatoria al resolver)",
               max_chars=2000,value=item.get("resolution_note") or "",
               key=f"dti_ticket_note_{item['id']}",height=120)
            submitted=st.form_submit_button("Guardar estado y notificar",
                                type="primary",icon=":material/check_circle:",
                                use_container_width=True)
        if submitted:
            try:
                changed=change_incident(item["id"],status,note)
            except ValueError as exc:
                st.error(str(exc))
            else:
                if changed:
                    st.toast("Incidencia actualizada. Analista y gerencia fueron notificados.")
                    st.rerun()
                else:
                    st.info("No hay cambios por guardar.")
