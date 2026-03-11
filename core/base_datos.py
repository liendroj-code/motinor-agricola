# core/base_datos.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "datos", "monitor.db")

def _conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def inicializar():
    con = _conectar()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lotes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            campana         TEXT NOT NULL,
            establecimiento TEXT NOT NULL,
            lote            TEXT NOT NULL,
            localidad       TEXT NOT NULL,
            provincia       TEXT,
            lat             REAL NOT NULL,
            lon             REAL NOT NULL,
            cultivo         TEXT NOT NULL,
            variedad        TEXT NOT NULL,
            fecha_siembra   TEXT NOT NULL,
            rinde_potencial INTEGER DEFAULT 3000,
            activo          INTEGER DEFAULT 1,
            creado          TEXT DEFAULT (date('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monitoreos (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id             INTEGER NOT NULL,
            fecha               TEXT NOT NULL,
            etapa_fenologica    TEXT,
            gdc_acumulado       REAL,
            malezas_presentes   INTEGER DEFAULT 0,
            malezas_detalle     TEXT,
            malezas_cobertura   REAL,
            malezas_accion      TEXT,
            insectos_presentes  INTEGER DEFAULT 0,
            insectos_detalle    TEXT,
            insectos_conteo     TEXT,
            insectos_accion     TEXT,
            enf_presentes       INTEGER DEFAULT 0,
            enf_detalle         TEXT,
            enf_incidencia      REAL,
            enf_severidad       REAL,
            enf_accion          TEXT,
            estres_presente     INTEGER DEFAULT 0,
            estres_tipo         TEXT,
            estres_intensidad   TEXT,
            estres_distribucion TEXT,
            observaciones       TEXT,
            decision            TEXT,
            tecnico             TEXT,
            creado              TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (lote_id) REFERENCES lotes(id)
        )
    """)
    con.commit()
    con.close()

# ---- LOTES ----

def guardar_lote(d: dict) -> int:
    con = _conectar()
    cur = con.cursor()
    cur.execute("""INSERT INTO lotes
        (campana,establecimiento,lote,localidad,provincia,lat,lon,
         cultivo,variedad,fecha_siembra,rinde_potencial)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (d["campana"],d["establecimiento"],d["lote"],d["localidad"],
         d.get("provincia",""),d["lat"],d["lon"],
         d["cultivo"],d["variedad"],d["fecha_siembra"],
         d.get("rinde_potencial",3000)))
    nid = cur.lastrowid
    con.commit(); con.close()
    return nid

def actualizar_lote(lote_id: int, d: dict):
    con = _conectar()
    cur = con.cursor()
    cur.execute("""UPDATE lotes SET
        campana=?,establecimiento=?,lote=?,localidad=?,provincia=?,
        lat=?,lon=?,cultivo=?,variedad=?,fecha_siembra=?,rinde_potencial=?
        WHERE id=?""",
        (d["campana"],d["establecimiento"],d["lote"],d["localidad"],
         d.get("provincia",""),d["lat"],d["lon"],
         d["cultivo"],d["variedad"],d["fecha_siembra"],
         d.get("rinde_potencial",3000),lote_id))
    con.commit(); con.close()

def eliminar_lote(lote_id: int):
    con = _conectar()
    con.execute("UPDATE lotes SET activo=0 WHERE id=?", (lote_id,))
    con.commit(); con.close()

def listar_lotes() -> list:
    con = _conectar()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM lotes WHERE activo=1 ORDER BY campana DESC, establecimiento, lote")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def obtener_lote(lote_id: int) -> dict:
    con = _conectar()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM lotes WHERE id=?", (lote_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None

# ---- MONITOREOS ----

def guardar_monitoreo(d: dict) -> int:
    con = _conectar()
    cur = con.cursor()
    cur.execute("""INSERT INTO monitoreos
        (lote_id,fecha,etapa_fenologica,gdc_acumulado,
         malezas_presentes,malezas_detalle,malezas_cobertura,malezas_accion,
         insectos_presentes,insectos_detalle,insectos_conteo,insectos_accion,
         enf_presentes,enf_detalle,enf_incidencia,enf_severidad,enf_accion,
         estres_presente,estres_tipo,estres_intensidad,estres_distribucion,
         observaciones,decision,tecnico)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d["lote_id"],d["fecha"],d.get("etapa_fenologica",""),d.get("gdc_acumulado",0),
         int(d.get("malezas_presentes",False)),d.get("malezas_detalle",""),
         d.get("malezas_cobertura",0),d.get("malezas_accion",""),
         int(d.get("insectos_presentes",False)),d.get("insectos_detalle",""),
         d.get("insectos_conteo",""),d.get("insectos_accion",""),
         int(d.get("enf_presentes",False)),d.get("enf_detalle",""),
         d.get("enf_incidencia",0),d.get("enf_severidad",0),d.get("enf_accion",""),
         int(d.get("estres_presente",False)),d.get("estres_tipo",""),
         d.get("estres_intensidad",""),d.get("estres_distribucion",""),
         d.get("observaciones",""),d.get("decision",""),d.get("tecnico","")))
    nid = cur.lastrowid
    con.commit(); con.close()
    return nid

def listar_monitoreos(lote_id: int, etapa: str = None,
                      fecha_desde: str = None, fecha_hasta: str = None) -> list:
    con = _conectar()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    q = "SELECT * FROM monitoreos WHERE lote_id=?"
    p = [lote_id]
    if etapa:      q += " AND etapa_fenologica=?"; p.append(etapa)
    if fecha_desde: q += " AND fecha>=?";          p.append(fecha_desde)
    if fecha_hasta: q += " AND fecha<=?";          p.append(fecha_hasta)
    q += " ORDER BY fecha DESC"
    cur.execute(q, p)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def eliminar_monitoreo(mon_id: int):
    con = _conectar()
    con.execute("DELETE FROM monitoreos WHERE id=?", (mon_id,))
    con.commit(); con.close()
