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
