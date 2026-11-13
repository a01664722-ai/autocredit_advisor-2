"""Pantalla 0 de acceso a perfiles de demostración de AutoCredit Advisor.

No solicita contraseñas ni promete autenticación. Es un flujo navegable
para presentación académica; la protección real requiere SSO/OIDC.
"""
from __future__ import annotations

import streamlit as st

from src.profile_state import demo_sign_in


LOGIN_CSS = """
<style>
section[data-testid="stSidebar"] {display:none!important}
[data-testid="collapsedControl"] {display:none!important}
[data-testid="stSidebarCollapsedControl"] {display:none!important}
div[data-testid="stAppViewContainer"] .block-container {
    max-width:1180px!important;padding-top:3.6rem!important;
    padding-bottom:2.6rem!important
}
.ac0-label{font-size:.76rem;font-weight:830;color:#5ce3a0;
  letter-spacing:.16em;margin-bottom:.85rem}
.ac0-title{font-size:clamp(2rem,4.3vw,3.75rem)!important;
  letter-spacing:-.045em!important;line-height:1.09!important;
  font-weight:850;color:#f4fcf6;margin:.1rem 0 1rem}
.ac0-title span{color:#5de3a3}
.ac0-hero-sub{color:#b3c7bb;font-size:1rem;line-height:1.65;max-width:520px}
.ac0-hero{padding:2.25rem 1rem 1rem 0}
.ac0-pillrow{display:flex;flex-wrap:wrap;gap:9px;margin:2.2rem 0 1.6rem}
.ac0-pill{border:1px solid rgba(95,220,153,.25);
  background:linear-gradient(120deg,rgba(44,88,66,.26),rgba(14,23,19,.75));
  border-radius:999px;padding:7px 12px;font-size:.77rem;color:#bde4cf;font-weight:670}
.ac0-sideintro{margin:0 0 .65rem;font-size:.77rem;color:#6de8ac;
  font-weight:800;letter-spacing:.12em}
.ac0-cardtitle{color:#f5faf6;font-size:1.45rem;font-weight:790;line-height:1.3}
.ac0-cardsub{color:#aec1b6;font-size:.87rem;line-height:1.55;margin:.6rem 0 1rem}
.ac0-note{margin:1.5rem 0 0;border-left:3px solid #46c98e;
  padding:10px 14px;background:linear-gradient(110deg,rgba(48,95,67,.22),
  rgba(15,24,21,.1));color:#b9c9bf;font-size:.8rem;line-height:1.5}
.ac0-footer{margin-top:3rem;font-size:.74rem;color:#829c8d;
  border-top:1px solid rgba(117,164,134,.19);padding-top:1.1rem}
@media(max-width:800px){.ac0-hero{padding:0 0 1rem}
  .ac0-title{font-size:2.2rem!important}
  .ac0-pillrow{margin:1.1rem 0}}
</style>
"""


def render_login(personas: dict) -> None:
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    left,right=st.columns([1.14,.86],gap="large",vertical_alignment="center")
    with left:
        st.markdown("""
        <div class="ac0-hero">
          <div class="ac0-label">CREDIT RISK / AUTOCREDIT ADVISOR</div>
          <div class="ac0-title">Del riesgo<br>a la <span>decisión.</span></div>
          <div class="ac0-hero-sub">
            Una plataforma de análisis crediticio que conecta predicciones
            XGBoost, decisiones y seguimiento operativo en una sola experiencia.
          </div>
          <div class="ac0-pillrow">
            <span class="ac0-pill">XGBoost · 12 variables</span>
            <span class="ac0-pill">Analistas</span>
            <span class="ac0-pill">Gerencia</span>
            <span class="ac0-pill">Validación DTI</span>
          </div>
        </div>
        """,unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown("""
            <div class="ac0-sideintro">PANTALLA 0 / ACCESO</div>
            <div class="ac0-cardtitle">Iniciar sesión</div>
            <div class="ac0-cardsub">
              Selecciona un perfil del equipo para abrir su dashboard.
              Cada analista tiene sus propias solicitudes, decisiones e indicadores.
            </div>
            """,unsafe_allow_html=True)
            with st.form("ac0_access_form",clear_on_submit=False):
                selected=st.selectbox(
                    "Perfil de usuario",options=list(personas),
                    index=None,placeholder="Selecciona tu perfil",
                    help="Perfiles de demostración sin verificación de identidad."
                )
                submitted=st.form_submit_button(
                    "Entrar al dashboard",type="primary",
                    icon=":material/login:",use_container_width=True
                )
            if submitted:
                if selected is None:
                    st.warning("Selecciona tu perfil antes de entrar.")
                else:
                    demo_sign_in(st.session_state,selected,personas)
                    st.rerun()
            st.markdown("""
            <div class="ac0-note">
              <strong>Acceso de demostración.</strong>
              No requiere contraseña ni verifica identidades. Las acciones
              que registres se comparten en la instancia de prueba.
              No ingreses información financiera personal.
            </div>
            """,unsafe_allow_html=True)
    st.markdown("""
        <div class="ac0-footer">
          EQUIPO 3 · PRESENTACIÓN ACADÉMICA
          &nbsp; · &nbsp; Dataset sintético
          &nbsp; · &nbsp; Las decisiones finales requieren revisión humana
        </div>
    """,unsafe_allow_html=True)
