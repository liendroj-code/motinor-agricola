"""
Módulo de base de datos interconectando capa Supabase
"""

import streamlit as st
from supabase import create_client

def get_supabase():
    """Obtiene el cliente de Supabase con la sesión del usuario actual"""
    # Usar las credenciales de st.secrets
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    # Si hay sesión activa, usar el token del usuario
    if "supabase_session" in st.session_state:
        # Crear cliente con el token de sesión
        client = create_client(url, key)
        client.auth.set_session(
            st.session_state.supabase_session.access_token,
            st.session_state.supabase_session.refresh_token
        )
        return client
    else:
        # Cliente sin autenticación
        return create_client(url, key)

def get_session_id():
    """Devuelve el ID UUID del usuario autenticado de la sesión"""
    if "user_id" in st.session_state:
        return st.session_state.user_id
    raise ValueError("Usuario no validado/ausente. Por favor, inicie sesión.")

def inicializar():
    """Inicializa la conexión"""
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = True

# ============================================================
# FUNCIONES PARA LOTES (CRUD SUPABASE)
# ============================================================

def guardar_lote(datos):
    """Inserta un nuevo lote en la tabla 'lotes' asociado al usuario activo"""
    supabase = get_supabase()
    user_uid = get_session_id()
    
    data_to_insert = {
        "user_id": user_uid,
        "campana": datos['campana'],
        "establecimiento": datos['establecimiento'],
        "lote": datos['lote'],
        "localidad": datos['localidad'],
        "provincia": datos.get('provincia', ''),
        "lat": datos['lat'],
        "lon": datos['lon'],
        "cultivo": datos['cultivo'],
        "variedad": datos['variedad'],
        "fecha_siembra": datos['fecha_siembra'],
        "rinde_potencial": datos['rinde_potencial']
    }
    
    try:
        res = supabase.table("lotes").insert(data_to_insert).execute()
        lote_id = res.data[0]['id'] if res.data else None
        return lote_id
    except Exception as e:
        st.error(f"Error al guardar lote: {e}")
        raise

# El resto de funciones (listar_lotes, actualizar_lote, eliminar_lote) siguen igual

# ============================================================
# FUNCIONES PARA MONITOREOS (CRUD SUPABASE)
# ============================================================

def guardar_monitoreo(datos):
    """Guarda un nuevo monitoreo. Recordar setear context de user_id."""
    supabase = get_supabase()
    user_uid = get_session_id()
    
    datos["user_id"] = user_uid
    res = supabase.table("monitoreos").insert(datos).execute()
    mon_id = res.data[0]['id'] if res.data else None
    return mon_id

def listar_monitoreos(lote_id=None, etapa=None, fecha_desde=None, fecha_hasta=None):
    """Lista monitoreos con Supabase filtering"""
    supabase = get_supabase()
    user_uid = get_session_id()
    
    query = supabase.table("monitoreos").select("*").eq("user_id", user_uid)
    
    if lote_id:
        query = query.eq("lote_id", lote_id)
    if etapa and etapa != 'Todas':
        query = query.eq("etapa_fenologica", etapa)
    if fecha_desde:
        query = query.gte("fecha", fecha_desde)
    if fecha_hasta:
        query = query.lte("fecha", fecha_hasta)
        
    query = query.order("fecha", desc=True)
    res = query.execute()
    return res.data

def eliminar_monitoreo(monitoreo_id):
    """Elimina un monitoreo de la nube Supabase"""
    supabase = get_supabase()
    user_uid = get_session_id()
    
    supabase.table("monitoreos").delete().eq("id", monitoreo_id).eq("user_id", user_uid).execute()
