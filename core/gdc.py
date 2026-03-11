# core/gdc.py
import math
import pandas as pd
from datetime import datetime, date

def calcular_fotoperiodo(lat: float, doy: int) -> float:
    """Fotoperíodo astronómico — Brock (1981)"""
    lat_rad = math.radians(lat)
    decl    = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
    ws      = math.acos(max(-1, min(1, -math.tan(lat_rad) * math.tan(decl))))
    return round(24 * ws / math.pi, 2)

def factor_fotoperiodo(fp: float, fp_critico: float) -> float:
    """Factor reductor por fotoperíodo (0-1). fp_critico=99 desactiva el ajuste."""
    if fp_critico >= 99 or fp <= fp_critico:
        return 1.0
    return max(0.0, round(1 - (fp - fp_critico) / (16 - fp_critico), 3))

def temp_efectiva(t_media: float, t_base: float, t_opt: float, t_max: float) -> float:
    """Temperatura efectiva con techo máximo (modelo beta)"""
    if t_media <= t_base: return 0.0
    if t_media <= t_opt:  return t_media - t_base
    if t_media <= t_max:  return (t_opt - t_base) * (t_max - t_media) / (t_max - t_opt)
    return 0.0

def determinar_etapa(gdc_acum: float, variedad: dict) -> str:
    """Retorna etapa fenológica según GDC acumulado"""
    etapa_actual = "Pre-VE"
    for nombre, umbral in variedad["gdc"].items():
        if gdc_acum >= umbral:
            etapa_actual = nombre
    return etapa_actual

def procesar_datos(datos_api: dict, lat: float, fecha_siembra: date,
                   variedad: dict, cultivo_mod) -> pd.DataFrame:
    """Construye DataFrame completo con GDC, fotoperíodo, etapas y estrés"""
    d    = datos_api["daily"]
    rows = []
    gdc_acum = 0.0

    for i, fecha_str in enumerate(d["time"]):
        fecha   = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        doy     = fecha.timetuple().tm_yday
        dias    = (fecha - fecha_siembra).days + 1

        t_max   = d["temperature_2m_max"][i]            or 0
        t_min   = d["temperature_2m_min"][i]            or 0
        t_media = d["temperature_2m_mean"][i]           or 0
        lluvia  = d["precipitation_sum"][i]             or 0
        humedad = d["relative_humidity_2m_mean"][i]     or 0
        viento  = d["wind_speed_10m_max"][i]            or 0
        rad     = d["shortwave_radiation_sum"][i]       or 0
        et0     = d["et0_fao_evapotranspiration"][i]    or 0

        t_efec  = temp_efectiva(t_media, variedad["t_base"], variedad["t_opt"], variedad["t_max"])
        fp      = calcular_fotoperiodo(lat, doy)
        fact_fp = factor_fotoperiodo(fp, variedad["fp_critico"])
        gdc_dia = round(t_efec * fact_fp, 2)
        gdc_acum = round(gdc_acum + gdc_dia, 1)

        balance = round(lluvia - et0, 1)
        etapa   = determinar_etapa(gdc_acum, variedad)

        # Estrés térmico
        t_calor_flor = getattr(cultivo_mod, "T_CALOR_CRITICO_FLOR",    33)
        t_calor_lle  = getattr(cultivo_mod, "T_CALOR_CRITICO_LLENADO", 35)
        ec = cultivo_mod.ETAPAS_CRITICAS

        estres_t = "🔴 Severo"   if (t_max > t_calor_lle and etapa in ec) else \
                   "🟡 Moderado" if (t_max > t_calor_flor) else \
                   "🟡 Frío"     if t_media < 15 else "🟢 Normal"

        estres_h = "🔴 Déficit"  if balance < -5 else \
                   "🟡 Leve"     if balance < -2 else \
                   "🟡 Exceso"   if balance > 20 else "🟢 Normal"

        rows.append({
            "fecha": fecha, "dias": dias,
            "t_max": round(t_max,1), "t_min": round(t_min,1), "t_media": round(t_media,1),
            "t_efec": round(t_efec,1), "lluvia": round(lluvia,1), "humedad": round(humedad,1),
            "viento": round(viento,1), "rad": round(rad,1),
            "et0": round(et0,1), "balance": balance,
            "fp": fp, "fact_fp": fact_fp,
            "gdc_dia": gdc_dia, "gdc_acum": gdc_acum,
            "etapa": etapa, "estres_t": estres_t, "estres_h": estres_h,
        })

    df = pd.DataFrame(rows)
    df["lluvia_acum"] = df["lluvia"].cumsum().round(1)
    df["et0_acum"]    = df["et0"].cumsum().round(1)
    return df

def predecir_etapas(df: pd.DataFrame, variedad: dict,
                    desc_etapas: dict, etapas_criticas: list) -> list[dict]:
    """Calcula fechas reales o estimadas para cada etapa"""
    if df.empty:
        return []

    gdc_actual   = df["gdc_acum"].iloc[-1]
    ultima_fecha = df["fecha"].iloc[-1]
    dias_actuales = df["dias"].iloc[-1]

    ultimos = df.tail(14)
    if len(ultimos) > 1:
        delta = ultimos["gdc_acum"].iloc[-1] - ultimos["gdc_acum"].iloc[0]
        prom_diario = max(0.5, delta / len(ultimos))
    else:
        prom_diario = 5.0

    from datetime import timedelta, datetime
    import math

    predicciones = []
    for etapa, umbral in variedad["gdc"].items():
        alcanzado = df[df["gdc_acum"] >= umbral]
        if not alcanzado.empty:
            fecha_real = alcanzado.iloc[0]["fecha"]
            dias_real  = alcanzado.iloc[0]["dias"]
            predicciones.append({
                "etapa": etapa, "descripcion": desc_etapas.get(etapa, etapa),
                "umbral": umbral, "fecha": fecha_real.strftime("%d/%m/%Y"),
                "dias": int(dias_real), "estado": "completada", "dias_faltan": 0,
            })
        else:
            dias_faltan = math.ceil((umbral - gdc_actual) / prom_diario)
            from datetime import timedelta
            fecha_est = ultima_fecha + timedelta(days=dias_faltan)
            estado = "proxima" if dias_faltan <= 10 else "pendiente"
            predicciones.append({
                "etapa": etapa, "descripcion": desc_etapas.get(etapa, etapa),
                "umbral": umbral, "fecha": fecha_est.strftime("%d/%m/%Y"),
                "dias": dias_actuales + dias_faltan, "estado": estado,
                "dias_faltan": dias_faltan,
            })

    return predicciones

def estimar_etapas_futuras(datos_pronostico: dict, lat: float, fecha_siembra: date, variedad: dict, gdc_acum_actual: float, dias_actual: int) -> pd.DataFrame:
    """Proyecta etapa fenológica con datos de pronóstico"""
    if not datos_pronostico or "daily" not in datos_pronostico:
        return pd.DataFrame()
        
    d = datos_pronostico["daily"]
    rows = []
    gdc_acum = gdc_acum_actual
    
    for i, fecha_str in enumerate(d["time"]):
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        doy = fecha.timetuple().tm_yday
        dias = dias_actual + i + 1  # Estimado si el pronóstico empieza mañana
        
        t_max = d["temperature_2m_max"][i] or 0
        t_min = d["temperature_2m_min"][i] or 0
        lluvia = d["precipitation_sum"][i] or 0
        et0 = d["et0_fao_evapotranspiration"][i] or 0
        humedad = d.get("relative_humidity_2m_mean", [])
        humedad_val = humedad[i] if humedad else 0
        
        t_media = (t_max + t_min) / 2
        
        t_efec = temp_efectiva(t_media, variedad["t_base"], variedad["t_opt"], variedad["t_max"])
        fp = calcular_fotoperiodo(lat, doy)
        fact_fp = factor_fotoperiodo(fp, variedad["fp_critico"])
        gdc_dia = round(t_efec * fact_fp, 2)
        gdc_acum = round(gdc_acum + gdc_dia, 1)
        
        balance = round(lluvia - et0, 1)
        etapa = determinar_etapa(gdc_acum, variedad)
        
        rows.append({
            "fecha": fecha,
            "dias": dias,
            "t_max": round(t_max, 1),
            "t_min": round(t_min, 1),
            "lluvia": round(lluvia, 1),
            "et0": round(et0, 1),
            "humedad": round(humedad_val, 1),
            "balance": balance,
            "gdc_dia": gdc_dia,
            "gdc_acum": gdc_acum,
            "etapa": etapa
        })
        
    return pd.DataFrame(rows)
