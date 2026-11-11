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
        for seg in SEGMENTS:
            c.execute('INSERT OR IGNORE INTO policies(segment,threshold,author,changed_at) VALUES(?,?,?,?)',
                      (seg,float(corte),'Sistema',now()))
        for metric,val in [('Resueltas',10),('Con justificación',1.0),('Coincidencia con sugerencia',.8)]:
            c.execute('INSERT OR IGNORE INTO targets(metric,value) VALUES(?,?)',(metric,val))

def policy(segment):
    with db() as c:
        row=c.execute('SELECT * FROM policies WHERE segment=?',(segment,)).fetchone()
        return dict(row) if row else None

def policies():
    with db() as c:return [dict(x) for x in c.execute('SELECT * FROM policies ORDER BY segment')]

def update_policy(segment,threshold,author,affected_by_analyst=None):
    if segment not in SEGMENTS:raise ValueError('Segmento no válido')
    if not .05<=float(threshold)<=.50:raise ValueError('Corte fuera de [0.05,0.50]')
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
    if decision not in ('Aprobar','Rechazar'):raise ValueError('Decisión inválida')
    override=decision!=suggested
    if override and (not motivo or (motivo=='Otro' and len(detail.strip())<8)):
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

def set_target(metric,value):
    if metric not in ('Resueltas','Con justificación','Coincidencia con sugerencia'):raise ValueError('KPI no autorizado')
    if value<0 or (metric!='Resueltas' and value>1):raise ValueError('Meta inválida')
    with db() as c:c.execute('UPDATE targets SET value=? WHERE metric=?',(float(value),metric))
