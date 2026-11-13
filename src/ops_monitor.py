"""Seguimiento operativo académico: incidencias DTI y sesiones con inicio/cierre registrados.

No confundir tiempos de sesión con productividad activa. Todo se guarda en SQLite
local, no hay autenticación real ni persistencia garantizada en Streamlit Cloud.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.monthly_kpis import as_local, local_now

CATEGORIES=(
    "Error en el dashboard",
    "Predicción o variables",
    "Datos / Loan ID",
    "Gráficas / métricas",
    "Acceso / rendimiento",
    "Otro",
)
STATES=("Abierto","En revisión","Resuelto")
ROLES=("analista","gerente","dti","operacion")
PROFILE_KEYS=(
    ("analista","A-017","Adrián Pérez"),
    ("analista","A-022","Sofía Reyes"),
    ("gerente",None,"Mariana Torres"),
    ("dti",None,"Especialista DTI"),
    ("operacion",None,"Luis Ramírez"),
)


def ensure_tables(c):
    c.executescript("""
        CREATE TABLE IF NOT EXISTS dti_incidents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyst_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT NOT NULL,
            loan_id TEXT,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Abierto',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            resolution_note TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_dti_incidents_created ON dti_incidents(created_at);
        CREATE INDEX IF NOT EXISTS idx_dti_incidents_reporter ON dti_incidents(analyst_id,id);
        CREATE TABLE IF NOT EXISTS profile_sessions(
            session_token TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            analyst_id TEXT,
            display_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            closed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_close ON profile_sessions(closed_at);
    """)


def create_incident(analyst_id,category,title,details,priority="Normal",loan_id=""):
    from src import store
    if analyst_id not in ("A-017","A-022"):
        raise ValueError("Solo analistas identificados pueden crear incidencias")
    if category not in CATEGORIES:
        raise ValueError("Categoría no reconocida")
    if priority not in ("Normal","Alta"):
        raise ValueError("Prioridad no válida")
    title=" ".join(str(title).split())
    details=str(details).strip()
    loan_id=str(loan_id or "").strip()
    if len(title)<5 or len(title)>100:
        raise ValueError("Describe el problema en un título de 5 a 100 caracteres")
    if len(details)<12 or len(details)>2000:
        raise ValueError("Explica la incidencia con 12 a 2,000 caracteres")
    if len(loan_id)>40:
        raise ValueError("Loan ID demasiado largo")
    timestamp=store.now()
    with store.db() as c:
        c.execute("""INSERT INTO dti_incidents(
            analyst_id,category,title,details,loan_id,priority,status,created_at,updated_at)
            VALUES(?,?,?,?,?,?, 'Abierto',?,?)""",
            (analyst_id,category,title,details,loan_id or None,priority,timestamp,timestamp))
        incident_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        summary=(f"Incidencia DTI #{incident_id} · {analyst_id} · {category}"
                 + (f" · Loan ID {loan_id}" if loan_id else "")
                 + f"\n{title}\n{details[:400]}")
        for audience in ("dti","gerente"):
            c.execute("""INSERT INTO messages(audience,analyst_id,kind,title,body,created_at,
                        sender_role,sender_id,sender_name,priority)
                        VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (audience,None,"Incidencia DTI",
                     f"Incidencia DTI #{incident_id}: {title}",
                     summary,timestamp,"analista",analyst_id,
                     "Adrián Pérez" if analyst_id=="A-017" else "Sofía Reyes",priority))
    return incident_id


def incidents(limit=500,analyst_id=None):
    from src import store
    if analyst_id is not None and analyst_id not in ("A-017","A-022"):
        raise ValueError("Analista no autorizado")
    with store.db() as c:
        if analyst_id is None:
            rows=c.execute("SELECT * FROM dti_incidents ORDER BY id DESC LIMIT ?",(int(limit),))
        else:
            rows=c.execute(
                "SELECT * FROM dti_incidents WHERE analyst_id=? ORDER BY id DESC LIMIT ?",
                (analyst_id,int(limit)))
        return [dict(row) for row in rows]


def change_incident(incident_id,new_status,resolution_note="",handler="Especialista DTI"):
    from src import store
    if new_status not in STATES:
        raise ValueError("Estado desconocido")
    note=str(resolution_note).strip()
    if new_status=="Resuelto" and len(note)<12:
        raise ValueError("Para resolver una incidencia describe la solución (mínimo 12 caracteres)")
    if len(note)>2000:
        raise ValueError("Descripción demasiado extensa")
    with store.db() as c:
        previous=c.execute("SELECT * FROM dti_incidents WHERE id=?",(int(incident_id),)).fetchone()
        if previous is None:
            raise ValueError("No existe la incidencia")
        if previous["status"]==new_status and (new_status!="Resuelto" or previous["resolution_note"]==note):
            return False
        stamp=store.now()
        resolved=stamp if new_status=="Resuelto" else None
        c.execute("""UPDATE dti_incidents SET status=?, resolution_note=?,
                     resolved_at=?, updated_at=? WHERE id=?""",
                  (new_status,note if new_status=="Resuelto" else "",resolved,stamp,int(incident_id)))
        message=(f"Incidencia DTI #{incident_id} · {new_status}. {previous['title']}"
                 + (f"\nResolución: {note}" if new_status=="Resuelto" else ""))
        for audience,aid in (("analista",previous["analyst_id"]),("gerente",None)):
            c.execute("""INSERT INTO messages(audience,analyst_id,kind,title,body,created_at,
                         sender_role,sender_id,sender_name,priority) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                      (audience,aid,"DTI seguimiento",
                       f"Incidencia #{incident_id} · {new_status}",message,stamp,
                       "dti",None,handler,"Normal"))
    return True


def incident_month_summary(rows=None,reference=None):
    reference=reference or local_now()
    if rows is None:
        rows=incidents()
    monthly=[x for x in rows if (lambda d: d is not None and
                      (d.year,d.month)==(reference.year,reference.month))(as_local(x["created_at"]))]
    total=len(monthly)
    solved=sum(x["status"]=="Resuelto" for x in monthly)
    review=sum(x["status"]=="En revisión" for x in monthly)
    opened=sum(x["status"]=="Abierto" for x in monthly)
    # El objetivo es resolver las incidencias reportadas durante el propio mes.
    return {"total":total,"solved":solved,"review":review,"open":opened,
            "rate":solved/total if total else None,"rows":monthly}


def begin_session(role,analyst_id,display_name,token=None):
    from src import store
    if role not in ROLES or (role=="analista" and analyst_id not in ("A-017","A-022")):
        raise ValueError("Perfil no reconocido")
    if role!="analista" and analyst_id is not None:
        raise ValueError("Identificador incorrecto para el perfil")
    token=str(token or uuid4())
    timestamp=store.now()
    with store.db() as c:
        c.execute("""INSERT OR IGNORE INTO profile_sessions
           (session_token,role,analyst_id,display_name,started_at,last_seen_at)
           VALUES(?,?,?,?,?,?)""",
           (token,role,analyst_id,str(display_name),timestamp,timestamp))
    return token


def touch_session(token):
    from src import store
    with store.db() as c:
        c.execute("""UPDATE profile_sessions SET last_seen_at=?
                   WHERE session_token=? AND closed_at IS NULL""",(store.now(),str(token)))


def end_session(token):
    from src import store
    if not token:
        return False
    with store.db() as c:
        c.execute("""UPDATE profile_sessions
                   SET closed_at=?,last_seen_at=?
                   WHERE session_token=? AND closed_at IS NULL""",
                   (store.now(),store.now(),str(token)))
        return c.total_changes>0


def monthly_session_stats(reference=None):
    """Suma solo sesiones CERRADAS en el mes local; evita medir actividad no observada."""
    from src import store
    reference=reference or local_now()
    with store.db() as c:
        rows=[dict(r) for r in c.execute("SELECT * FROM profile_sessions")]
    report={}
    for role,aid,name in PROFILE_KEYS:
        matching=[r for r in rows if r["role"]==role and r["analyst_id"]==aid]
        closed=[r for r in matching if (lambda d:d is not None and
                 (d.year,d.month)==(reference.year,reference.month))(as_local(r["closed_at"]))]
        minutes=0.0
        for r in closed:
            start=as_local(r["started_at"])
            stop=as_local(r["closed_at"])
            if start and stop:
                minutes+=max(0.0,(stop-start).total_seconds()/60)
        report[(role,aid)]={"name":name,"closed":len(closed),
           "minutes":round(minutes,2) if closed else None,
           "open_without_logout":sum(r["closed_at"] is None for r in matching)}
    return report
