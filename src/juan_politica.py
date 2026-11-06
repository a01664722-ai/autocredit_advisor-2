"""Metas configurables y avisos de seguimiento; no altera aprobaciones ni el modelo."""
from __future__ import annotations
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from src import config as C

CLAVES = ("incumplimiento", "dti", "dti_alto")

def conexion(ruta=None):
    p = Path(ruta or C.RUTA_BD)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p), timeout=20)
    con.execute("CREATE TABLE IF NOT EXISTS juan_metas (clave TEXT PRIMARY KEY, valor REAL NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS juan_avisos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, autor TEXT, texto TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS juan_lecturas (email TEXT PRIMARY KEY, ultimo_id INTEGER)")
    con.commit()
    return con

def leer_metas(ruta=None):
    with conexion(ruta) as con:
        return {k: float(v) for k,v in con.execute("SELECT clave,valor FROM juan_metas") if k in CLAVES}

def guardar_metas(metas, autor, ruta=None):
    if set(metas) != set(CLAVES) or any(v is not None and not (0 <= float(v) <= 1) for v in metas.values()):
        raise ValueError("Metas inválidas")
    con = conexion(ruta)
    try:
        con.execute("BEGIN IMMEDIATE")
        antes = {k: float(v) for k,v in con.execute("SELECT clave,valor FROM juan_metas")}
        despues = {k: float(v) for k,v in metas.items() if v is not None}
        if antes == despues:
            con.rollback()
            return False
        con.execute("DELETE FROM juan_metas")
        con.executemany("INSERT INTO juan_metas VALUES (?,?)", despues.items())
        etiquetas = {"incumplimiento":"incumplimiento","dti":"DTI medio","dti_alto":"incumplimiento en DTI alto"}
        cambios = []
        for clave in CLAVES:
            valor = despues.get(clave)
            v_ant = antes.get(clave)
            if valor != v_ant:
                antes_txt = f"{v_ant:.2%}" if v_ant is not None else "sin meta"
                ahora_txt = f"{valor:.2%}" if valor is not None else "sin meta"
                cambios.append(f"{etiquetas[clave]}: {antes_txt} → {ahora_txt}")
        fecha = datetime.now(ZoneInfo(C.ZONA_HORARIA)).isoformat(timespec="minutes")
        con.execute("INSERT INTO juan_avisos(fecha,autor,texto) VALUES (?,?,?)",
                    (fecha,autor,"; ".join(cambios)+". Cambio de metas de seguimiento, no de dictámenes."))
        con.commit()
        return True
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def avisos_no_leidos(email, ruta=None):
    with conexion(ruta) as con:
        fila = con.execute("SELECT ultimo_id FROM juan_lecturas WHERE email=?", (email,)).fetchone()
        ultimo = fila[0] if fila else 0
        return [dict(id=i, fecha=f, autor=a, texto=t) for i,f,a,t in con.execute(
            "SELECT id,fecha,autor,texto FROM juan_avisos WHERE id>? ORDER BY id DESC LIMIT 10", (ultimo,))]

def marcar_leidos(email, ruta=None):
    with conexion(ruta) as con:
        ultimo = con.execute("SELECT COALESCE(MAX(id),0) FROM juan_avisos").fetchone()[0]
        con.execute("INSERT OR REPLACE INTO juan_lecturas VALUES (?,?)", (email,ultimo))
