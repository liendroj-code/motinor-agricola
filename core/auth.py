"""
Módulo de autenticación de usuarios
Maneja registro, login y sesiones
"""

import streamlit as st
import sqlite3
import hashlib
import os
from pathlib import Path
import uuid

# Configuración
# Base de datos global unificada para usuarios
# La guardamos en el workspace para persistencia o en temp como se pidió.
# El prompt la pidió en /tmp/monitor_agricola_users.db
import tempfile
temp_dir = Path(tempfile.gettempdir())
DB_AUTH_PATH = temp_dir / "monitor_agricola_users.db"

def get_db_connection():
    """Conexión a la base de datos de usuarios"""
    conn = sqlite3.connect(str(DB_AUTH_PATH))
    return conn

def inicializar_tabla_usuarios():
    """Crea la tabla de usuarios si no existe"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_acceso TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Convierte contraseña en hash seguro"""
    salt = "monitor_agricola_salt"  # En producción, usar salt aleatorio por usuario
    return hashlib.sha256((password + salt).encode()).hexdigest()

def registrar_usuario(email, nombre, password):
    """Registra un nuevo usuario"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO usuarios (email, nombre, password_hash)
            VALUES (?, ?, ?)
        ''', (email, nombre, password_hash))
        conn.commit()
        return True, "Usuario registrado correctamente"
    except sqlite3.IntegrityError:
        return False, "El email ya está registrado"
    finally:
        conn.close()

def verificar_login(email, password):
    """Verifica credenciales de usuario"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute('''
        SELECT id, email, nombre FROM usuarios
        WHERE email = ? AND password_hash = ?
    ''', (email, password_hash))
    
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        # Actualizar último acceso
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (usuario[0],))
        conn.commit()
        conn.close()
        
        return {
            "id": usuario[0],
            "email": usuario[1],
            "nombre": usuario[2]
        }
    return None

def logout():
    """Cierra la sesión del usuario"""
    for key in ['usuario', 'user_id', 'user_email', 'user_name']:
        if key in st.session_state:
            del st.session_state[key]
