"""
Módulo de base de datos con soporte multisesión
Cada usuario tiene su propio archivo .db
"""

import sqlite3
import streamlit as st
import os
import tempfile
from pathlib import Path
import hashlib
import time

def get_session_id():
    """Obtiene o crea un ID único para la sesión actual"""
    if "session_id" not in st.session_state:
        # Crear ID único basado en timestamp + usuario anónimo
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]
    return st.session_state.session_id

def get_db_path():
    """
    Devuelve la ruta de la base de datos específica para esta sesión
    Cada sesión tiene su propio archivo .db
    """
    session_id = get_session_id()
    
    # Usar carpeta temporal del sistema (se limpia sola al reiniciar)
    temp_dir = Path(tempfile.gettempdir()) / "monitor_agricola_sessions"
    temp_dir.mkdir(exist_ok=True)
    
    db_path = temp_dir / f"session_{session_id}.db"
    return str(db_path)

def inicializar():
    """Inicializa la base de datos de la sesión actual"""
    db_path = get_db_path()
    
    # Log para debugging (opcional)
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = True
        print(f"Base de datos para esta sesión: {db_path}")
    
    conn = sqlite3.connect(db_path)
    crear_tablas(conn)
    conn.close()

def crear_tablas(conn):
    """Crea las tablas si no existen"""
    cursor = conn.cursor()
    
    # Tabla de lotes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campana TEXT,
            establecimiento TEXT,
            lote TEXT,
            localidad TEXT,
            provincia TEXT,
            lat REAL,
            lon REAL,
            cultivo TEXT,
            variedad TEXT,
            fecha_siembra TEXT,
            rinde_potencial REAL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de monitoreos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoreos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            fecha TEXT,
            etapa_fenologica TEXT,
            gdc_acumulado REAL,
            malezas_presentes BOOLEAN,
            malezas_detalle TEXT,
            malezas_cobertura REAL,
            malezas_accion TEXT,
            insectos_presentes BOOLEAN,
            insectos_detalle TEXT,
            insectos_conteo TEXT,
            insectos_accion TEXT,
            enf_presentes BOOLEAN,
            enf_detalle TEXT,
            enf_incidencia REAL,
            enf_severidad REAL,
            enf_accion TEXT,
            estres_presente BOOLEAN,
            estres_tipo TEXT,
            estres_intensidad TEXT,
            estres_distribucion TEXT,
            observaciones TEXT,
            decision TEXT,
            tecnico TEXT,
            fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lote_id) REFERENCES lotes (id)
        )
    ''')
    
    conn.commit()

def get_connection():
    """Obtiene conexión a la base de datos de la sesión actual"""
    db_path = get_db_path()
    return sqlite3.connect(db_path)

# ============================================================
# FUNCIONES PARA LOTES
# ============================================================

def guardar_lote(datos):
    """Guarda un nuevo lote en la base de datos de la sesión"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO lotes (
            campana, establecimiento, lote, localidad, provincia,
            lat, lon, cultivo, variedad, fecha_siembra, rinde_potencial
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datos['campana'], datos['establecimiento'], datos['lote'],
        datos['localidad'], datos.get('provincia', ''),
        datos['lat'], datos['lon'], datos['cultivo'],
        datos['variedad'], datos['fecha_siembra'], datos['rinde_potencial']
    ))
    
    lote_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lote_id

def listar_lotes():
    """Lista todos los lotes de la sesión actual"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, campana, establecimiento, lote, localidad, provincia,
               lat, lon, cultivo, variedad, fecha_siembra, rinde_potencial
        FROM lotes
        ORDER BY id DESC
    ''')
    
    columnas = [desc[0] for desc in cursor.description]
    resultados = []
    
    for row in cursor.fetchall():
        lote = dict(zip(columnas, row))
        resultados.append(lote)
    
    conn.close()
    return resultados

def actualizar_lote(lote_id, datos):
    """Actualiza un lote existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE lotes SET
            campana = ?, establecimiento = ?, lote = ?,
            localidad = ?, provincia = ?, lat = ?, lon = ?,
            cultivo = ?, variedad = ?, fecha_siembra = ?,
            rinde_potencial = ?
        WHERE id = ?
    ''', (
        datos['campana'], datos['establecimiento'], datos['lote'],
        datos['localidad'], datos.get('provincia', ''),
        datos['lat'], datos['lon'], datos['cultivo'],
        datos['variedad'], datos['fecha_siembra'],
        datos['rinde_potencial'], lote_id
    ))
    
    conn.commit()
    conn.close()

def eliminar_lote(lote_id):
    """Elimina un lote y sus monitoreos asociados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Eliminar monitoreos del lote
    cursor.execute('DELETE FROM monitoreos WHERE lote_id = ?', (lote_id,))
    
    # Eliminar el lote
    cursor.execute('DELETE FROM lotes WHERE id = ?', (lote_id,))
    
    conn.commit()
    conn.close()

# ============================================================
# FUNCIONES PARA MONITOREOS
# ============================================================

def guardar_monitoreo(datos):
    """Guarda un nuevo monitoreo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ', '.join(['?'] * len(datos))
    columnas = ', '.join(datos.keys())
    
    query = f'INSERT INTO monitoreos ({columnas}) VALUES ({placeholders})'
    cursor.execute(query, list(datos.values()))
    
    mon_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mon_id

def listar_monitoreos(lote_id=None, etapa=None, fecha_desde=None, fecha_hasta=None):
    """Lista monitoreos con filtros opcionales"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM monitoreos WHERE 1=1'
    params = []
    
    if lote_id:
        query += ' AND lote_id = ?'
        params.append(lote_id)
    
    if etapa and etapa != 'Todas':
        query += ' AND etapa_fenologica = ?'
        params.append(etapa)
    
    if fecha_desde:
        query += ' AND fecha >= ?'
        params.append(fecha_desde)
    
    if fecha_hasta:
        query += ' AND fecha <= ?'
        params.append(fecha_hasta)
    
    query += ' ORDER BY fecha DESC'
    
    cursor.execute(query, params)
    
    columnas = [desc[0] for desc in cursor.description]
    resultados = []
    
    for row in cursor.fetchall():
        monitoreo = dict(zip(columnas, row))
        resultados.append(monitoreo)
    
    conn.close()
    return resultados

def eliminar_monitoreo(monitoreo_id):
    """Elimina un monitoreo"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM monitoreos WHERE id = ?', (monitoreo_id,))
    conn.commit()
    conn.close()

# Función para limpiar sesiones viejas (opcional)
def limpiar_sesiones_antiguas(horas=24):
    """
    Elimina archivos de base de datos de sesiones inactivas
    (para ejecutar periódicamente si se desea)
    """
    temp_dir = Path(tempfile.gettempdir()) / "monitor_agricola_sessions"
    if not temp_dir.exists():
        return
    
    ahora = time.time()
    for archivo in temp_dir.glob("session_*.db"):
        # Si el archivo tiene más de 'horas' horas, eliminarlo
        if ahora - archivo.stat().st_mtime > horas * 3600:
            archivo.unlink()
