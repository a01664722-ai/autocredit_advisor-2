"""Integración real de buzones internos de la demo Streamlit."""
import sqlite3
import pytest

from src import store


@pytest.fixture()
def mailbox(tmp_path,monkeypatch):
    monkeypatch.setattr(store,"DB",tmp_path/"messages.sqlite")
    store.initialize(.159)
    return store


def test_analista_gerente_respuesta_y_leidos(mailbox):
    identifier=mailbox.send_internal_message(
        "analista","A-017","Adrián Pérez","gerente",None,
        "Consulta sobre indicador","¿Podemos revisar la meta mensual?")
    assert identifier>0
    assert mailbox.unread("gerente")==1
    assert mailbox.unread("analista","A-017")==0
    assert mailbox.unread("analista","A-022")==0
    inbox=mailbox.messages("gerente")
    assert len(inbox)==1 and inbox[0]["title"]=="Consulta sobre indicador"
    assert inbox[0]["sender_id"]=="A-017"
    assert mailbox.sent_messages("analista","A-017")[0]["id"]==identifier
    mailbox.mark_read(identifier,"analista","A-022")
    assert mailbox.unread("gerente")==1
    mailbox.mark_read(identifier,"gerente")
    assert mailbox.unread("gerente")==0
    assert mailbox.sent_messages("analista","A-017")[0]["seen"]==1
    reply=mailbox.send_internal_message(
        "gerente",None,"Mariana Torres","analista","A-017",
        "Re: Consulta sobre indicador","Revisamos la meta mañana.",
        reply_to_id=identifier,priority="Alta")
    assert reply>identifier
    assert mailbox.unread("analista","A-017")==1
    assert mailbox.unread("analista","A-022")==0
    assert mailbox.messages("analista","A-017")[0]["reply_to_id"]==identifier
    assert mailbox.messages("analista","A-017")[0]["priority"]=="Alta"


def test_entre_analistas_y_soporte_dti(mailbox):
    msg=mailbox.send_internal_message("analista","A-017","Adrián",
             "analista","A-022","Solicitud compartida","Favor de verificar Loan ID.")
    assert mailbox.unread("analista","A-022")==1
    assert mailbox.unread("gerente")==0
    assert mailbox.unread("dti")==0
    assert mailbox.messages("analista","A-017")==[]
    assert len(mailbox.sent_messages("analista","A-017"))==1
    dti=mailbox.send_internal_message("analista","A-022","Sofía",
             "dti",None,"Consulta de modelo","¿Podemos revisar la curva ROC?")
    assert mailbox.unread("dti")==1
    assert mailbox.messages("dti")[0]["sender_id"]=="A-022"
    mailbox.send_internal_message("dti",None,"Especialista DTI",
             "analista","A-022","Re: Consulta de modelo",
             "La curva está en Validación del modelo.",
             reply_to_id=dti)
    assert mailbox.unread("analista","A-022")==2
    assert len(mailbox.sent_messages("dti"))==1


def test_validacion_y_no_respuestas_a_terceros(mailbox):
    orig=mailbox.send_internal_message("analista","A-017","Adrián",
               "gerente",None,"Prueba de acceso","Este mensaje es reservado.")
    with pytest.raises(PermissionError):
        mailbox.send_internal_message("analista","A-022","Sofía",
                    "gerente",None,"Re: Prueba de acceso",
                    "Intento no permitido.",reply_to_id=orig)
    with pytest.raises(ValueError):
        mailbox.send_internal_message("gerente",None,"Mariana",
                    "dti",None,"Respuesta errónea",
                    "Intento no permitido.",reply_to_id=orig)
    with pytest.raises(ValueError):
        mailbox.send_internal_message("analista","A-017","Adrián",
                    "analista","A-017","Autoenvío",
                    "Esto debe fallar.")
    with pytest.raises(ValueError):
        mailbox.send_internal_message("analista","A-017","Adrián",
                    "gerente",None,"Ok","Cuerpo válido.")
    with pytest.raises(ValueError):
        mailbox.send_internal_message("analista","A-017","Adrián",
                    "gerente",None,"Asunto válido","")
    with pytest.raises(ValueError):
        mailbox.send_internal_message("analista","A-017","Adrián",
                    "gerente",None,"Asunto válido","Texto válido.",priority="Urgentísimo")
    with pytest.raises(ValueError):
        mailbox.send_internal_message("operacion",None,"Luis",
                    "gerente",None,"Asunto válido","Texto válido.")
    assert len(mailbox.messages("gerente"))==1


def test_migracion_conserva_alertas_automaticas(tmp_path,monkeypatch):
    db_path=tmp_path/"legacy.sqlite"
    with sqlite3.connect(db_path) as con:
        con.executescript("""
            CREATE TABLE messages(
              id INTEGER PRIMARY KEY AUTOINCREMENT,audience TEXT NOT NULL,
              analyst_id TEXT,kind TEXT NOT NULL,title TEXT NOT NULL,
              body TEXT NOT NULL,created_at TEXT NOT NULL,seen INTEGER NOT NULL DEFAULT 0);
        """)
        con.execute("""INSERT INTO messages(audience,analyst_id,kind,title,body,created_at)
                       VALUES(?,?,?,?,?,?)""",
                 ("analista","A-017","Política","Aviso existente",
                  "El corte cambió.","2026-11-12T18:30:00+00:00"))
    monkeypatch.setattr(store,"DB",db_path)
    store.initialize(.159)
    store.initialize(.159)
    rows=store.messages("analista","A-017")
    assert len(rows)==1 and rows[0]["title"]=="Aviso existente"
    assert rows[0]["sender_role"] is None
    assert store.unread("analista","A-017")==1
    assert store.inbox_counts("analista","A-017")=={
        "total":1,"unread":1,"direct":0}
    store.send_internal_message("gerente",None,"Mariana",
        "analista","A-017","Cambio de metas","Consulta tus KPI mensuales.")
    assert store.inbox_counts("analista","A-017")["total"]==2


def test_alertas_automaticas_y_mensajes_comparten_buzon(mailbox):
    mailbox.set_targets_batch({"Decisiones mensuales":70},"Mariana")
    assert mailbox.unread("analista","A-017")==1
    assert mailbox.messages("analista","A-017")[0]["kind"]=="KPI"
    mailbox.send_internal_message("gerente",None,"Mariana",
        "analista","A-017","Seguimiento KPI","La meta mensual fue actualizada.")
    inbox=mailbox.messages("analista","A-017")
    assert {r["kind"] for r in inbox}=={"KPI","Directo"}
    assert mailbox.unread("analista","A-017")==2
    assert mailbox.inbox_counts("analista","A-017")["direct"]==1
