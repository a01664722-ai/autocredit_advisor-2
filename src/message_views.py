"""Centro interno de mensajes: bandeja, enviados y composición para perfiles demo.

Los avisos del motor de riesgo y las metas utilizan la misma tabla SQLite.
Este es un buzón dentro de Streamlit, no correo electrónico externo.
"""
from __future__ import annotations
import html

import streamlit as st

from src import store
from src.monthly_kpis import as_local

DESTINATIONS=(
    ("gerente",None,"Gerencia · Mariana Torres"),
    ("analista","A-017","Analista · Adrián Pérez (A-017)"),
    ("analista","A-022","Analista · Sofía Reyes (A-022)"),
    ("dti",None,"Soporte DTI · Validación del modelo"),
)
DEST_BY_TOKEN={
    f"{role}|{aid or '-'}":(role,aid,label)
    for role,aid,label in DESTINATIONS
}
STYLE="""
<style>
.ac-mail-intro{margin:0 0 .8rem 0}
.ac-mail-eyebrow{color:#70e6ac;font-size:.75rem;font-weight:800;letter-spacing:.12em}
.ac-mail-title{font-size:1.86rem;color:#f2f9f4;line-height:1.24;font-weight:820;
  letter-spacing:-.035em;margin:.18rem 0}
.ac-mail-sub{color:#aebfb5;font-size:.86rem;line-height:1.5}
.ac-mail-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
  gap:12px;margin:.85rem 0 1.1rem}
.ac-mail-metric{border-radius:14px;min-height:100px;padding:14px 16px;
  border:1px solid rgba(102,165,131,.24);
  background:linear-gradient(125deg,rgba(33,59,44,.45),rgba(15,23,20,.9) 85%);
  overflow-wrap:break-word;box-sizing:border-box;position:relative}
.ac-mail-metric:before{content:"";position:absolute;top:0;left:12px;width:45%;height:2px;
  background:linear-gradient(90deg,#51dfa2,transparent)}
.ac-mail-metric span{display:block;color:#b9c9be;font-size:.78rem}
.ac-mail-metric strong{font-size:1.75rem;color:#eff9f1;line-height:1.3;font-weight:820}
.ac-mail-metric small{display:block;font-size:.73rem;color:#9cb6a5;line-height:1.3}
.ac-mail-meta{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}
.ac-mail-subject{font-size:1.04rem;color:#f2f9f4;font-weight:770;line-height:1.35;overflow-wrap:anywhere}
.ac-mail-who{font-size:.82rem;color:#add3bd;margin-top:3px;overflow-wrap:anywhere}
.ac-mail-when{font-size:.73rem;color:#9aafa4;white-space:nowrap}
.ac-mail-content{color:#d4e3d8;font-size:.86rem;line-height:1.58;margin:.75rem 0 .45rem;
  white-space:pre-wrap;overflow-wrap:anywhere}
.ac-mail-tag{display:inline-block;margin-right:7px;padding:3px 8px;border-radius:30px;
  background:rgba(75,142,104,.14);color:#83ddb0;border:1px solid rgba(96,190,134,.28);
  font-size:.68rem;font-weight:750}
.ac-mail-tag.important{background:rgba(149,65,71,.2);color:#ffacb2;
  border-color:rgba(204,95,104,.26)}
.ac-mail-empty{border:1px dashed rgba(91,160,119,.35);padding:28px 20px;border-radius:15px;
  background:linear-gradient(125deg,rgba(30,49,38,.35),rgba(15,22,19,.65));text-align:center;
  color:#a9c5b4;line-height:1.6}
.ac-mail-empty strong{display:block;color:#f0f9f2;font-size:1.04rem;margin-bottom:6px}
@media(max-width:760px){
  .ac-mail-grid{grid-template-columns:1fr;gap:8px}
  .ac-mail-title{font-size:1.5rem}
  .ac-mail-metric{min-height:87px}
}
</style>
"""


def _key(role,aid):
    return f"internal_mail_{role}_{aid or 'general'}"


def _visible_targets(role,aid):
    return [
        (f"{dest_role}|{dest_id or '-'}",label)
        for dest_role,dest_id,label in DESTINATIONS
        if (role,aid)!=(dest_role,dest_id)
    ]


def _other_party(message, sender_role,sender_id):
    """For an inbound DIRECT message, return sender as the reply recipient."""
    if message.get("kind")!="Directo" or not message.get("sender_role"):
        return None
    if message["audience"]!=sender_role or (
        sender_role=="analista" and message.get("analyst_id")!=sender_id):
        return None
    token=f"{message['sender_role']}|{message.get('sender_id') or '-'}"
    return token if token in DEST_BY_TOKEN else None


def _date(value):
    dt=as_local(value)
    return dt.strftime("%d/%m/%Y · %H:%M") if dt else "Fecha no disponible"


def _header():
    st.markdown(STYLE,unsafe_allow_html=True)


def _meta_card(title,value,detail):
    return (
        '<div class="ac-mail-metric"><span>'+html.escape(title)+'</span>'
        '<strong>'+html.escape(str(value))+'</strong>'
        '<small>'+html.escape(detail)+'</small></div>'
    )


def _display_card(item, direction, role,aid,prefix):
    identifier=int(item["id"])
    manual=(item.get("kind")=="Directo")
    who=item.get("sender_name") or "Sistema · Aviso automático"
    if direction=="enviado":
        match=next((label for dest_role,dest_id,label in DESTINATIONS
                   if (dest_role,dest_id)==(item["audience"],item.get("analyst_id"))),
                   "Destinatario interno")
        who="Para: "+match
    tag="Mensaje interno" if manual else "Aviso del sistema"
    priority=item.get("priority") or "Normal"
    if manual and priority=="Alta":tag="Prioridad alta"
    tag_css="important" if priority=="Alta" and manual else ""
    unread=direction=="recibido" and not bool(item["seen"])
    state="Sin leer" if unread else ("Leído" if direction=="recibido" else
                                   ("Leído por destinatario" if item["seen"] else "Enviado"))
    subject=html.escape(str(item.get("title") or "Sin asunto"))
    content=html.escape(str(item.get("body") or ""))
    who=html.escape(who)
    st.markdown(
        '<div class="ac-mail-meta"><div>'
        f'<div class="ac-mail-subject">{subject}</div>'
        f'<div class="ac-mail-who">{who}</div></div>'
        f'<div class="ac-mail-when">{html.escape(_date(item.get("created_at")))}</div></div>'
        f'<div style="margin-top:8px"><span class="ac-mail-tag {tag_css}">'
        f'{html.escape(tag)}</span><span class="ac-mail-tag">{state}</span></div>'
        f'<div class="ac-mail-content">{content}</div>',unsafe_allow_html=True
    )
    if direction!="recibido":
        return
    reply_to=_other_party(item,role,aid)
    c1,c2,c3=st.columns([1,1,3],gap="small")
    if unread:
        if c1.button("Marcar leído",key=f"{prefix}_seen_{identifier}",
                     icon=":material/done:",use_container_width=True):
            store.mark_read(identifier,role,aid)
            st.rerun()
    if reply_to is not None:
        if c2.button("Responder",key=f"{prefix}_reply_{identifier}",
                     icon=":material/reply:",use_container_width=True):
            # Se precargan los campos antes de instanciar los widgets de redacción.
            st.session_state[f"{prefix}_prefill"]={
                "to":reply_to,
                "subject":str(item.get("title") or "Mensaje"),
                "reply_to":identifier
            }
            st.session_state[f"{prefix}_navigate"]="Redactar"
            st.rerun()


def render_messages(role,analyst_id,name):
    if role not in ("analista","gerente","dti"):
        st.error("Este perfil no tiene habilitado el buzón interno.")
        return
    prefix=_key(role,analyst_id)
    section_key=f"{prefix}_section"
    recipients=_visible_targets(role,analyst_id)
    allowed=dict(recipients)

    # Actualizar estado antes de crear controles Streamlit (evita errores de sesión).
    if st.session_state.pop(f"{prefix}_reset",False):
        for key in (f"{prefix}_to",f"{prefix}_subject",f"{prefix}_body",
                    f"{prefix}_priority"):
            st.session_state.pop(key,None)
        st.session_state.pop(f"{prefix}_reply_id",None)
    draft=st.session_state.pop(f"{prefix}_prefill",None)
    if draft:
        token=draft["to"]
        if token in allowed:
            st.session_state[f"{prefix}_to"]=token
            title=str(draft["subject"])
            st.session_state[f"{prefix}_subject"]=(
                title if title.lower().startswith("re:") else "Re: "+title
            )[:120]
            st.session_state[f"{prefix}_body"]=""
            st.session_state[f"{prefix}_reply_id"]=int(draft["reply_to"])
    nav=st.session_state.pop(f"{prefix}_navigate",None)
    if nav:
        st.session_state[section_key]=nav

    _header()
    lead,action=st.columns([3.7,1.1],gap="large",vertical_alignment="bottom")
    with lead:
        st.markdown(
            f'<div class="ac-mail-intro"><div class="ac-mail-eyebrow">AUTOCREDIT / COMUNICACIÓN INTERNA</div>'
            f'<div class="ac-mail-title">Centro de mensajes</div>'
            f'<div class="ac-mail-sub">{html.escape(name)} · Avisos, consultas y seguimiento entre perfiles.</div>'
            '</div>',unsafe_allow_html=True)
    with action:
        if st.button("Nuevo mensaje",type="primary",icon=":material/edit_square:",
                     use_container_width=True,key=f"{prefix}_compose_start"):
            st.session_state[f"{prefix}_navigate"]="Redactar"
            st.rerun()

    inbox_stats=store.inbox_counts(role,analyst_id)
    sent=store.sent_messages(role,analyst_id,100)
    st.markdown(
        '<div class="ac-mail-grid">'+
        _meta_card("Sin leer",inbox_stats["unread"],"Mensajes pendientes de revisar")+
        _meta_card("Recibidos",inbox_stats["total"],"Alertas y mensajes internos")+
        _meta_card("Enviados",len(sent),"Últimos 100 mensajes registrados")+
        '</div>',unsafe_allow_html=True)
    if st.session_state.pop(f"{prefix}_flash",False):
        st.success("Mensaje enviado al buzón del destinatario. Quedó registrado en Enviados.")

    section=st.segmented_control(
        "Buzón",options=["Recibidos","Enviados","Redactar"],default="Recibidos",
        key=section_key
    )
    if section=="Redactar":
        st.markdown("#### Redactar mensaje")
        st.caption("Este es un mensaje interno de la aplicación. No se envía por correo electrónico.")
        st.session_state.setdefault(f"{prefix}_to",recipients[0][0])
        current_to=st.session_state[f"{prefix}_to"]
        if current_to not in allowed:
            st.session_state[f"{prefix}_to"]=recipients[0][0]
        with st.form(f"{prefix}_form",clear_on_submit=False):
            to=st.selectbox("Destinatario",options=list(allowed),
                      format_func=lambda x:allowed[x],key=f"{prefix}_to")
            subject=st.text_input("Asunto",max_chars=120,
                         placeholder="Ej. Consulta sobre solicitud / indicador",key=f"{prefix}_subject")
            priority=st.selectbox("Prioridad",["Normal","Alta"],key=f"{prefix}_priority")
            body=st.text_area("Mensaje",max_chars=2000,height=155,
                        placeholder="Escribe un mensaje claro. Evita incluir datos personales o contraseñas.",
                        key=f"{prefix}_body")
            reply_id=st.session_state.get(f"{prefix}_reply_id")
            if reply_id:
                st.caption(f"Respuesta al mensaje interno #{reply_id}")
            submitted=st.form_submit_button("Enviar mensaje",type="primary",
                         icon=":material/send:",use_container_width=True)
        if submitted:
            destination,recipient_id,_=DEST_BY_TOKEN[to]
            try:
                store.send_internal_message(
                    role,analyst_id,name,destination,recipient_id,
                    subject,body,reply_to_id=reply_id,priority=priority)
            except (ValueError,PermissionError) as exc:
                st.error(str(exc))
            else:
                st.session_state[f"{prefix}_flash"]=True
                st.session_state[f"{prefix}_reset"]=True
                st.session_state[f"{prefix}_navigate"]="Enviados"
                st.rerun()
        return

    inbox=store.messages(role,analyst_id) if section=="Recibidos" else sent
    caption="Los 50 más recientes" if section=="Recibidos" else "Los 100 más recientes"
    if section=="Recibidos":
        st.markdown("#### Bandeja de entrada")
        filters=st.columns([1.3,2.0],gap="medium")
        with filters[0]:
            chosen=st.selectbox("Filtrar",["Todos","Sin leer","Mensajes internos","Avisos automáticos"],
                                key=f"{prefix}_filter")
        with filters[1]:
            query=st.text_input("Buscar",placeholder="Asunto, remitente o contenido...",
                                 key=f"{prefix}_search")
        if chosen=="Sin leer":
            inbox=[m for m in inbox if not m["seen"]]
        elif chosen=="Mensajes internos":
            inbox=[m for m in inbox if m["kind"]=="Directo"]
        elif chosen=="Avisos automáticos":
            inbox=[m for m in inbox if m["kind"]!="Directo"]
        if query.strip():
            q=query.casefold().strip()
            inbox=[m for m in inbox if q in " ".join([
                 str(m.get("title","")),str(m.get("body","")),
                 str(m.get("sender_name") or "Sistema")]).casefold()]
    else:
        st.markdown("#### Mensajes enviados")
        st.caption("Aquí puedes comprobar el destinatario y si leyó cada mensaje.")

    st.caption(f"{len(inbox)} mensajes mostrados · {caption} · ordenados del más reciente")
    if not inbox:
        heading="No hay mensajes en esta vista"
        subtitle=("Las actualizaciones de gerencia, excepciones y mensajes del equipo "
                  "aparecerán automáticamente aquí." if section=="Recibidos" else
                  "Envía tu primer mensaje desde la pestaña Redactar.")
        st.markdown('<div class="ac-mail-empty"><strong>'+heading+'</strong>'+
                    html.escape(subtitle)+'</div>',unsafe_allow_html=True)
    for message in inbox:
        with st.container(border=True):
            _display_card(message,
                "recibido" if section=="Recibidos" else "enviado",
                role,analyst_id,prefix)
    st.caption("* Mensajería interna de una demo académica con perfiles simulados, "
               "sin autenticación real. Todos los mensajes se almacenan en SQLite temporal "
               "y pueden perderse si la instancia reinicia. No introduzcas información sensible.")
