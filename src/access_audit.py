"""Vista breve de auditoría de accesos del prototipo académico.

Documenta las pantallas y acciones visibles; no sustituye controles RBAC
por servidor ni una auditoría de cambios inmutable.
"""
from __future__ import annotations
import html
import streamlit as st

ACCESS = (
    ("Mariana Torres", "Gerente", "MT",
     "Métricas del área · Analistas y KPI · Mensajes · Auditoría",
     "Monitorear el equipo; ajustar metas y política; recibir alertas DTI y excepciones."),
    ("Adrián Pérez", "Analista A-017", "AP",
     "Bandeja · Ficha de solicitud · Mis indicadores · Mensajes",
     "Revisar sus Loan ID asignados; registrar decisiones y justificaciones; reportar DTI."),
    ("Sofía Reyes", "Analista A-022", "SR",
     "Bandeja · Ficha de solicitud · Mis indicadores · Mensajes",
     "Revisar sus Loan ID asignados; registrar decisiones y justificaciones; reportar DTI."),
    ("Especialista DTI", "Validación y soporte", "DT",
     "Incidencias DTI · Validación del modelo · Mensajes · Auditoría",
     "Consultar métricas técnicas de TEST y documentar resolución de incidencias."),
    ("Luis Ramírez", "Operación", "LR",
     "Operación · Validación del modelo",
     "Consultar el resumen operativo y las métricas agregadas del modelo."),
)

CSS = """
<style>
.ac-audit-head {height:22px}
.ac-audit-eyebrow{color:#67e4aa;font-size:.75rem;letter-spacing:.13em;font-weight:800}
.ac-audit-title{color:#f4faf6;font-size:1.85rem;font-weight:820;letter-spacing:-.03em;margin:.18rem 0}
.ac-audit-sub{color:#b0c4b7;font-size:.86rem;margin:0 0 18px;line-height:1.6}
.ac-audit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin-top:12px}
.ac-audit-card{border:1px solid rgba(109,159,127,.28);border-radius:15px;
 background:linear-gradient(120deg,rgba(32,58,43,.45),rgba(13,21,18,.87));
 padding:18px;box-shadow:0 7px 18px rgba(0,0,0,.10);min-height:192px}
.ac-audit-top{display:flex;gap:12px;align-items:center;margin-bottom:14px}
.ac-audit-avatar{width:43px;height:43px;border:1px solid #4c8c66;border-radius:50%;
 color:#7aefb2;background:#1b3326;font-weight:800;display:flex;align-items:center;
 justify-content:center;flex:none}
.ac-audit-name{color:#f5fbf6;font-size:1rem;font-weight:770;overflow-wrap:anywhere}
.ac-audit-role{color:#91b69e;font-size:.78rem;margin-top:3px}
.ac-audit-label{color:#6ee3a5;font-size:.7rem;font-weight:780;letter-spacing:.05em;margin-top:9px}
.ac-audit-content{font-size:.82rem;color:#c0d0c4;line-height:1.55;overflow-wrap:break-word}
@media(max-width:790px){.ac-audit-grid{grid-template-columns:1fr}
.ac-audit-card{min-height:0}.ac-audit-title{font-size:1.5rem}}
</style>
"""


def render_access_audit():
    st.markdown(CSS,unsafe_allow_html=True)
    st.markdown(
        '<div class="ac-audit-head"></div>'
        '<div class="ac-audit-eyebrow">AUTOCREDIT / AUDITORÍA DE PERFILES</div>'
        '<div class="ac-audit-title">Roles y accesos</div>'
        '<div class="ac-audit-sub">Consulta de responsabilidades y pantallas '
        'disponibles por perfil de demostración.</div>',
        unsafe_allow_html=True)
    cards=[]
    for name,role,initials,pages,actions in ACCESS:
        cards.append(
            '<section class="ac-audit-card">'
            '<div class="ac-audit-top"><div class="ac-audit-avatar">'+html.escape(initials)+'</div>'
            '<div><div class="ac-audit-name">'+html.escape(name)+'</div>'
            '<div class="ac-audit-role">'+html.escape(role)+'</div></div></div>'
            '<div class="ac-audit-label">PANTALLAS</div>'
            '<div class="ac-audit-content">'+html.escape(pages)+'</div>'
            '<div class="ac-audit-label">ALCANCE</div>'
            '<div class="ac-audit-content">'+html.escape(actions)+'</div>'
            '</section>')
    st.markdown('<div class="ac-audit-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
    st.caption("Este registro describe permisos de interfaz en el prototipo, "
        "no demuestra que se hayan aplicado mediante autenticación o reglas de servidor.")
    with st.expander("Límites del control de acceso y la auditoría"):
        st.info("Los perfiles son simulados: hoy pueden seleccionarse sin contraseña. "
                "Antes de operar con información sensible se necesitarían "
                "autenticación institucional, autorización por rol validada en servidor, "
                "restricciones por registro y una bitácora de auditoría inmutable.")
        st.caption("La instancia emplea SQLite temporal; los registros pueden desaparecer "
                   "si Streamlit Cloud reinicia. No se deben usar para decisiones crediticias reales.")
