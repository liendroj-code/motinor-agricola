# core/clima.py
import requests
import streamlit as st
from datetime import date, timedelta

@st.cache_data(ttl=3600)
def obtener_datos(lat: float, lon: float, fecha_inicio: str, fecha_fin: str) -> dict | None:
    """Consulta Open-Meteo Archive API"""
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={fecha_inicio}&end_date={fecha_fin}"
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean"
        ",relative_humidity_2m_mean,precipitation_sum"
        ",wind_speed_10m_max,shortwave_radiation_sum,et0_fao_evapotranspiration"
        "&timezone=America%2FArgentina%2FSalta"
    )
    try:
        r = requests.get(url, timeout=20)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def fecha_fin_disponible() -> str:
    """Retorna la fecha más reciente disponible en Open-Meteo (2 días de rezago)"""
    return (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")

@st.cache_data(ttl=3600)
def obtener_pronostico(lat: float, lon: float, dias: int = 7) -> dict | None:
    """Consulta Open-Meteo Forecast API para pronóstico extendido"""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration,relative_humidity_2m_mean"
        f"&forecast_days={dias}"
        "&timezone=America%2FArgentina%2FSalta"
    )
    try:
        r = requests.get(url, timeout=20)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None
