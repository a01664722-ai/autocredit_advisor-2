"""Estado compartido entre pantallas de la instancia Streamlit (SQLite DEMO).
En Cloud el disco es efímero: migrar a PostgreSQL para persistencia real.
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import os
from src.monthly_kpis import KPI_SPECS, validate_target

DB=Path(os.getenv('AUTOCREDIT_DB','/tmp/autocredit_v2_demo.sqlite3'))
SEGMENTS=('General','DTI bajo','DTI medio','DTI alto')

@contextmanager
def db():
    c=sqlite3.connect(str(DB), timeout=15)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA busy_timeout=15000')
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback();raise
    finally:c.close()

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')

def initialize(corte:float):
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS decisions(
            loan_id TEXT PRIMARY KEY, analyst_id TEXT NOT NULL, decision TEXT NOT NULL,
            suggested TEXT NOT NULL, pd_xgb REAL NOT NULL, pd_logit REAL NOT NULL,
            threshold REAL NOT NULL, override INTEGER NOT NULL, motivo TEXT,
            text_detail TEXT, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS policies(
            segment TEXT PRIMARY KEY, threshold REAL NOT NULL, version INTEGER NOT NULL DEFAULT 1,
            author TEXT NOT NULL, changed_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT, audience TEXT NOT NULL,
            analyst_id TEXT, kind TEXT NOT NULL, title TEXT NOT NULL,
            body TEXT NOT NULL, created_at TEXT NOT NULL, seen INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS targets(metric TEXT PRIMARY KEY, value REAL NOT NULL);
        ''')
        # Migración compatible: las alertas históricas siguen en messages.
        # Los mensajes manuales incorporan remitente, destinatario y relación de respuesta.
        columns={row['name'] for row in c.execute('PRAGMA table_info(messages)')}
        added={
            'sender_role':'TEXT', 'sender_id':'TEXT', 'sender_name':'TEXT',
            'reply_to_id':'INTEGER', 'priority':"TEXT NOT NULL DEFAULT 'Normal'"
        }
        for column,decl in added.items():
            if column not in columns:
                c.execute(f'ALTER TABLE messages ADD COLUMN {column} {decl}')
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(audience,analyst_id,id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_role,sender_id,id)')
        for seg in SEGMENTS:
            c.execute('INSERT OR IGNORE INTO policies(segment,threshold,author,changed_at) VALUES(?,?,?,?)',
                      (seg,float(corte),'Sistema',now()))
        # Migración segura desde V2: solo políticas iniciales de Sistema
        # sin modificaciones (version=1). Mantener intactos cambios gerenciales.
        c.execute("""UPDATE policies SET threshold=?, changed_at=?
                     WHERE author='Sistema' AND version=1 AND ABS(threshold-?)>0.0000001""",
                  (float(corte), now(), float(corte)))
        # Mantener metas heredadas y crear las seis nuevas metas mensuales.
        for metric,val in [('Resueltas',10),('Con justificación',1.0),('Coincidencia con sugerencia',.8)]:
            c.execute('INSERT OR IGNORE INTO targets(metric,value) VALUES(?,?)',(metric,val))
        for metric, _label, _kind, default, _desc in KPI_SPECS:
            c.execute('INSERT OR IGNORE INTO targets(metric,value) VALUES(?,?)',(metric,float(default)))

def policy(segment):
    with db() as c:
        row=c.execute('SELECT * FROM policies WHERE segment=?',(segment,)).fetchone()
        return dict(row) if row else None

def policies():
    with db() as c:return [dict(x) for x in c.execute('SELECT * FROM policies ORDER BY segment')]

def update_policy(segment,threshold,author,affected_by_analyst=None):
    if segment not in SEGMENTS:raise ValueError('Segmento no válido')
    if not .05<=float(threshold)<=.60:raise ValueError('Corte fuera de [0.05,0.60]')
    with db() as c:
        old=c.execute('SELECT threshold FROM policies WHERE segment=?',(segment,)).fetchone()
        if old is None:raise ValueError('No existe la política')
        prev=float(old[0])
        if abs(prev-threshold)<1e-9:return False
        c.execute('UPDATE policies SET threshold=?,version=version+1,author=?,changed_at=? WHERE segment=?',
                  (float(threshold),author,now(),segment))
        for ana,n in (affected_by_analyst or {}).items():
            txt=f'El corte de {segment} pasó de {prev:.1%} a {threshold:.1%}. Cambiarían {n:,} sugerencias en TEST asignadas a tu perfil (simulado).'
            c.execute('INSERT INTO messages(audience,analyst_id,kind,title,body,created_at) VALUES(?,?,?,?,?,?)',
                      ('analista',ana,'Política',f'Corte actualizado: {segment}',txt,now()))
        return True

def save_decision(loan_id,analyst_id,decision,suggested,pd_xgb,pd_logit,threshold,motivo='',detail=''):
    if decision not in ('Aceptar','Condicionar','Rechazar','Aprobar'):raise ValueError('Decisión inválida')
    override=decision!=suggested
    if override and (not motivo or len(detail.strip())<8):
        raise ValueError('Una decisión contraria al modelo requiere un motivo justificado')
    with db() as c:
        existing=c.execute('SELECT analyst_id FROM decisions WHERE loan_id=?',(str(loan_id),)).fetchone()
        if existing and existing['analyst_id'] != analyst_id:raise PermissionError('La solicitud pertenece a otro analista')
        c.execute('''INSERT INTO decisions(loan_id,analyst_id,decision,suggested,pd_xgb,pd_logit,threshold,override,motivo,text_detail,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(loan_id) DO UPDATE SET
            decision=excluded.decision,suggested=excluded.suggested,pd_xgb=excluded.pd_xgb,
            pd_logit=excluded.pd_logit,threshold=excluded.threshold,override=excluded.override,
            motivo=excluded.motivo,text_detail=excluded.text_detail,updated_at=excluded.updated_at''',
            (str(loan_id),analyst_id,decision,suggested,float(pd_xgb),float(pd_logit),float(threshold),int(override),motivo,detail[:400],now()))
        if override:
            body=f'Loan ID {loan_id}: {analyst_id} decidió {decision} frente a sugerencia {suggested}. Motivo: {motivo}. {detail[:200]}'
            c.execute('INSERT INTO messages(audience,analyst_id,kind,title,body,created_at) VALUES(?,?,?,?,?,?)',
                      ('gerente',analyst_id,'Excepción','Decisión contraria al modelo',body,now()))
    return override

def decisions():
    with db() as c:return [dict(x) for x in c.execute('SELECT * FROM decisions ORDER BY updated_at DESC')]

def decisions_map(analyst_id):
    with db() as c:
        return {row['loan_id']:dict(row) for row in c.execute('SELECT * FROM decisions WHERE analyst_id=?',(analyst_id,))}

def unread(audience,analyst_id=None):
    with db() as c:
        if audience=='analista':
            return c.execute('SELECT COUNT(*) FROM messages WHERE audience=? AND analyst_id=? AND seen=0',(audience,analyst_id)).fetchone()[0]
        return c.execute('SELECT COUNT(*) FROM messages WHERE audience=? AND seen=0',(audience,)).fetchone()[0]

def messages(audience,analyst_id=None):
    with db() as c:
        if audience=='analista':
            return [dict(x) for x in c.execute('SELECT * FROM messages WHERE audience=? AND analyst_id=? ORDER BY id DESC LIMIT 50',(audience,analyst_id))]
        return [dict(x) for x in c.execute('SELECT * FROM messages WHERE audience=? ORDER BY id DESC LIMIT 50',(audience,))]

def mark_read(msg_id,audience,analyst_id=None):
    with db() as c:
        if audience=='analista':c.execute('UPDATE messages SET seen=1 WHERE id=? AND audience=? AND analyst_id=?',(msg_id,audience,analyst_id))
        else:c.execute('UPDATE messages SET seen=1 WHERE id=? AND audience=?',(msg_id,audience))

def targets():
    with db() as c:return {x['metric']:x['value'] for x in c.execute('SELECT * FROM targets')}

def set_targets_batch(changes, author='Gerencia', analyst_ids=('A-017', 'A-022')):
    """Actualiza metas mensuales de forma atómica; notifica a cada analista.
    La confirmación explícita se solicita en la interfaz ANTES de esta función.
    """
    clean = {metric: validate_target(metric, value) for metric, value in changes.items()}
    if not clean:
        return False
    with db() as c:
        old = {x['metric']:float(x['value']) for x in c.execute('SELECT metric,value FROM targets')}
        changed = {key:(old[key], val) for key,val in clean.items()
                   if key in old and abs(old[key] - val)>1e-10}
        if not changed:
            return False
        for key, (_before, val) in changed.items():
            c.execute('UPDATE targets SET value=? WHERE metric=?',(val,key))
        from src.monthly_kpis import KPI_MAP
        def displayed(metric, val):
            return f'{val:.0%}' if KPI_MAP[metric][2] == 'rate' else f'{val:,.0f}'
        details = '; '.join(
            f'{KPI_MAP[key][1]}: {displayed(key, before)} → {displayed(key, after)}'
            for key,(before,after) in changed.items())
        for analyst_id in analyst_ids:
            c.execute('''INSERT INTO messages(audience,analyst_id,kind,title,body,created_at)
                         VALUES(?,?,?,?,?,?)''',
                      ('analista', analyst_id, 'KPI',
                       'Metas mensuales actualizadas por gerencia',
                       f'{author} actualizó las metas operativas mensuales. {details}. '
                       'Consulta Mis indicadores para ver el avance y el semáforo.',
                       now()))
    return True


def set_target(metric,value):
    """Compatibilidad: actualizar una sola meta mensual y notificar."""
    return set_targets_batch({metric:value})


# ---------------- MENSAJERÍA INTERNA (DEMO) ----------------
# Mismo repositorio SQLite de metas y excepciones; respeta avisos preexistentes.
ALLOWED_ROLES=('analista','gerente','dti')
ANALYST_IDS=('A-017','A-022')


def _user_key(role, analyst_id=None):
    if role not in ALLOWED_ROLES:
        raise ValueError('Perfil sin acceso a mensajería')
    if role=='analista':
        if analyst_id not in ANALYST_IDS:
            raise ValueError('Identificador de analista no autorizado')
        return role, analyst_id
    if analyst_id is not None:
        raise ValueError('El perfil no requiere identificador de analista')
    return role, None


def _visible(row,role,analyst_id):
    recipient=(row['audience']==role and
               (role!='analista' or row['analyst_id']==analyst_id))
    sender=(row['sender_role']==role and
            (role!='analista' or row['sender_id']==analyst_id))
    return recipient or sender


def send_internal_message(sender_role, sender_id, sender_name,
                          to_role, to_id, subject, body,
                          reply_to_id=None, priority='Normal'):
    """Envía un mensaje interno a un perfil de la misma instancia.
    No envía email, no usa información privada y no autentica identidades.
    """
    sender_role,sender_id=_user_key(sender_role,sender_id)
    to_role,to_id=_user_key(to_role,to_id)
    if sender_role==to_role and sender_id==to_id:
        raise ValueError('No puedes enviarte mensajes a ti mismo')
    subject=' '.join(str(subject).split())
    body=str(body).strip()
    if not 4<=len(subject)<=120:
        raise ValueError('El asunto debe tener de 4 a 120 caracteres')
    if not 5<=len(body)<=2000:
        raise ValueError('El mensaje debe tener de 5 a 2,000 caracteres')
    if priority not in ('Normal','Alta'):
        raise ValueError('Prioridad inválida')
    sender_name=' '.join(str(sender_name).split())[:80]
    if not sender_name:
        raise ValueError('Remitente no identificado')
    with db() as c:
        if reply_to_id is not None:
            original=c.execute('SELECT * FROM messages WHERE id=?',(int(reply_to_id),)).fetchone()
            if original is None or original['sender_role'] is None:
                raise ValueError('El mensaje original no permite respuesta directa')
            if not _visible(original,sender_role,sender_id):
                raise PermissionError('No tienes acceso a este mensaje')
            # Evitar cambios arbitrarios del destinatario de la respuesta.
            other=(original['sender_role'],original['sender_id']) if (
                original['audience']==sender_role and
                (sender_role!='analista' or original['analyst_id']==sender_id)
            ) else (original['audience'],original['analyst_id'])
            if other!=(to_role,to_id):
                raise ValueError('La respuesta debe dirigirse al otro participante')
        c.execute('''INSERT INTO messages(
            audience,analyst_id,kind,title,body,created_at,seen,
            sender_role,sender_id,sender_name,reply_to_id,priority)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
            (to_role,to_id,'Directo',subject,body,now(),0,
             sender_role,sender_id,sender_name,reply_to_id,priority))
        return c.execute('SELECT last_insert_rowid()').fetchone()[0]


def sent_messages(sender_role, sender_id=None, limit=100):
    sender_role,sender_id=_user_key(sender_role,sender_id)
    if not 1<=int(limit)<=500:
        raise ValueError('Límite inválido')
    with db() as c:
        if sender_role=='analista':
            rows=c.execute('''SELECT * FROM messages
                WHERE sender_role=? AND sender_id=? ORDER BY id DESC LIMIT ?''',
                (sender_role,sender_id,int(limit)))
        else:
            rows=c.execute('''SELECT * FROM messages
                WHERE sender_role=? ORDER BY id DESC LIMIT ?''',(sender_role,int(limit)))
        return [dict(row) for row in rows]


def inbox_counts(audience, analyst_id=None):
    """Totales reales (sin límite de los últimos 50 mensajes)."""
    role,aid=_user_key(audience,analyst_id)
    where='audience=? AND analyst_id=?' if role=='analista' else 'audience=?'
    args=(role,aid) if role=='analista' else (role,)
    with db() as c:
        row=c.execute(f'''SELECT COUNT(*) AS total,
            SUM(CASE WHEN seen=0 THEN 1 ELSE 0 END) AS unread,
            SUM(CASE WHEN kind='Directo' THEN 1 ELSE 0 END) AS direct
            FROM messages WHERE {where}''',args).fetchone()
        return {'total':int(row['total']),
                'unread':int(row['unread'] or 0),
                'direct':int(row['direct'] or 0)}
