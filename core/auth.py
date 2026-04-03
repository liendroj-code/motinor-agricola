"""
Módulo de autenticación de usuarios (Supabase)
Maneja registro, login y sesiones
"""

import streamlit as st
from supabase import create_client


def get_supabase():
    """Obtiene el cliente de Supabase desde st.secrets"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def inicializar_tabla_usuarios():
    """En Supabase, las tablas y roles se manejan externamente o por SQL.
    Esta función se mantiene para compatibilidad con la inicialización en app.py
    pero no hace falta ejecutar nada aquí."""
    pass


def registrar_usuario(email, nombre, password):
    """Registra un nuevo usuario en Supabase Auth y luego en la tabla pública de usuarios"""
    supabase = get_supabase()
    
    try:
        # Registrar en Supabase Auth
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"nombre": nombre}
            }
        })
        
        if res.user:
            # ✅ Comentamos la inserción manual - el trigger de Supabase se encarga
            # supabase.table("usuarios").insert({
            #     "id": res.user.id,
            #     "email": email,
            #     "nombre": nombre
            # }).execute()
            
            return {"success": True, "user": res.user}
        else:
            return {"success": False, "error": "No se pudo crear el usuario"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def verificar_login(email, password):
    """Verifica credenciales y retorna el usuario si son correctas"""
    supabase = get_supabase()
    
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if res.user:
            # Guardar la sesión en st.session_state
            st.session_state.supabase_session = res.session
            st.session_state.user_id = res.user.id
            st.session_state.user_name = res.user.user_metadata.get('nombre', email)
            
            return {"success": True, "user": res.user, "session": res.session}
        else:
            return {"success": False, "error": "Credenciales inválidas"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
