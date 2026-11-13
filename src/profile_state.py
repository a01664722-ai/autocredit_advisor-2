"""Estado de navegación por perfil en la demo Streamlit.

Los préstamos, decisiones y mensajes persisten en SQLite. Solo se limpian
controles de UI al cambiar de persona para no conservar un Loan ID ni una
excepción pendiente de otro analista en la sesión del navegador.
"""
from __future__ import annotations
from collections.abc import MutableMapping


_UI_KEYS = frozenset({
    "page", "page_to", "loan_actual", "pending_choice",
    "override_motive", "override_note", "table_rev",
    "target_save_notice",
})
_UI_PREFIXES = ("nav_", "p1_", "p2_", "internal_mail_")


def reset_profile_navigation(
    session: MutableMapping, role: str, analyst_id: str | None
) -> bool:
    """Restablece únicamente navegación y borradores si cambia la identidad.

    Returns True cuando es un perfil diferente; False si es el mismo.
    Nunca altera el selector 'perfil' ni los registros persistidos de SQLite.
    """
    identity = f"{role}:{analyst_id or '-'}"
    if session.get("_active_profile_identity") == identity:
        return False

    for key in list(session):
        if key in _UI_KEYS or key.startswith(_UI_PREFIXES):
            session.pop(key, None)
    session["_active_profile_identity"] = identity
    return True


# ---------------- ACCESO DE DEMOSTRACIÓN ----------------
# El acceso es una selección de rol por sesión de navegador, NO autenticación.
# La persistencia de decisiones, metas y mensajes vive fuera de session_state.

LOGIN_KEY = "_demo_login_profile"


def demo_sign_in(session: MutableMapping, selected_profile: str, personas: dict) -> tuple:
    """Inicia la vista de un perfil de demostración registrado.

    No valida credenciales. Para un entorno real debe sustituirse por SSO/OIDC
    más controles de autorización en el servidor y en la base de datos.
    """
    if selected_profile not in personas:
        raise ValueError("El perfil solicitado no está disponible")
    role, analyst_id, name = personas[selected_profile]
    reset_profile_navigation(session, role, analyst_id)
    session[LOGIN_KEY] = selected_profile
    return role, analyst_id, name


def demo_sign_out(session: MutableMapping) -> None:
    """Cierra la sesión de interfaz sin alterar decisiones ni mensajes en SQLite."""
    for key in list(session):
        session.pop(key, None)


def demo_current_profile(session: MutableMapping, personas: dict):
    """Devuelve perfil activo o None; nunca confía en un ID fuera del catálogo."""
    selected = session.get(LOGIN_KEY)
    return selected if selected in personas else None
