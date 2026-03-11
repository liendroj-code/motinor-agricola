"""
============================================================
 MONITOR AGRÍCOLA — v2.5
 Stack: Python + Streamlit + Open-Meteo + Plotly + SQLite
 Cultivos: Soja · Maíz · Sorgo
============================================================
"""
import streamlit as st
import pandas as pd
import statistics
from datetime import date, datetime
from io import BytesIO

from cultivos import CULTIVOS
from core import clima, gdc, rinde, base_datos
from ui import estilos, graficos

st.set_page_config(page_title="Monitor Agrícola", page_icon="🌾",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(estilos.CSS, unsafe_allow_html=True)
base_datos.inicializar()

# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0 0.5rem 0;'>
        <div style='font-size:2.2rem;'>🌾</div>
        <div style='font-size:1rem;font-weight:700;color:#34d399;letter-spacing:1px;'>MONITOR AGRÍCOLA</div>
        <div style='font-size:0.72rem;color:#64748b;margin-top:2px;'>v2.5</div>
    </div><hr>
    """, unsafe_allow_html=True)

    lotes_guardados = base_datos.listar_lotes()
    modo_lote = st.radio("", ["📂 Usar lote guardado", "➕ Nuevo lote"],
                          horizontal=True, label_visibility="collapsed")

    if modo_lote == "📂 Usar lote guardado" and lotes_guardados:
        opciones = {
            f"{l['establecimiento']} — {l['lote']} ({l['cultivo']} {l['campana']})": l
            for l in lotes_guardados
        }
        sel_label = st.selectbox("Seleccioná el lote", list(opciones.keys()))
        lote_sel  = opciones[sel_label]

        cultivo_nombre  = lote_sel["cultivo"]
        cultivo_mod     = CULTIVOS[cultivo_nombre]
        variedad_nombre = lote_sel["variedad"]
        variedad        = cultivo_mod.VARIEDADES.get(variedad_nombre,
                          list(cultivo_mod.VARIEDADES.values())[0])
        nombre_lote     = f"{lote_sel['establecimiento']} — {lote_sel['lote']}"
        lat             = lote_sel["lat"]
        lon             = lote_sel["lon"]
        fecha_siembra   = datetime.strptime(lote_sel["fecha_siembra"], "%Y-%m-%d").date()
        rinde_potencial = lote_sel["rinde_potencial"]
        lote_id_activo  = lote_sel["id"]

        st.markdown(f"""<div class="info-box" style='font-size:0.78rem;margin-top:0.5rem;'>
        📍 {lote_sel['localidad']} · {lote_sel.get('provincia','')}<br>
        🌱 {cultivo_nombre} — {variedad_nombre}<br>
        📅 Siembra: {fecha_siembra.strftime("%d/%m/%Y")}<br>
        🌐 {lat:.4f}, {lon:.4f}
        </div>""", unsafe_allow_html=True)

        with st.expander("✏️ Editar este lote"):
            campana_e   = st.text_input("Campaña",          value=lote_sel["campana"],       key="e_camp")
            estab_e     = st.text_input("Establecimiento",  value=lote_sel["establecimiento"],key="e_est")
            lote_e      = st.text_input("Lote N°",          value=lote_sel["lote"],           key="e_lot")
            localidad_e = st.text_input("Localidad",        value=lote_sel["localidad"],      key="e_loc")
            prov_e      = st.text_input("Provincia",        value=lote_sel.get("provincia",""),key="e_prov")
            rp_e        = st.number_input("Rinde potencial (kg/ha)", value=rinde_potencial, step=100, key="e_rp")
            if st.button("💾 Guardar cambios", key="btn_editar"):
                base_datos.actualizar_lote(lote_id_activo, {
                    "campana": campana_e, "establecimiento": estab_e,
                    "lote": lote_e, "localidad": localidad_e, "provincia": prov_e,
                    "lat": lat, "lon": lon, "cultivo": cultivo_nombre,
                    "variedad": variedad_nombre,
                    "fecha_siembra": fecha_siembra.strftime("%Y-%m-%d"),
                    "rinde_potencial": rp_e,
                })
                st.success("✅ Actualizado"); st.rerun()
            if st.button("🗑️ Eliminar lote", key="btn_del"):
                base_datos.eliminar_lote(lote_id_activo); st.rerun()

    else:
        st.markdown('<div class="section-header">📋 Datos del lote</div>', unsafe_allow_html=True)
        campana_n   = st.text_input("Campaña",          value="2025/26")
        estab_n     = st.text_input("Establecimiento",  value="")
        lote_n      = st.text_input("Lote N°",          value="")
        localidad_n = st.text_input("Localidad",        value="")
        prov_n      = st.text_input("Provincia",        value="")

        st.markdown('<div class="section-header">🌿 Cultivo</div>', unsafe_allow_html=True)
        cultivo_nombre  = st.selectbox("Cultivo", list(CULTIVOS.keys()))
        cultivo_mod     = CULTIVOS[cultivo_nombre]
        variedad_nombre = st.selectbox("Variedad / Ciclo", list(cultivo_mod.VARIEDADES.keys()))
        variedad        = cultivo_mod.VARIEDADES[variedad_nombre]

        st.markdown('<div class="section-header">📍 Ubicación</div>', unsafe_allow_html=True)
        lat = st.number_input("Latitud",  value=-24.549412, format="%.6f", step=0.0001)
        lon = st.number_input("Longitud", value=-64.087162, format="%.6f", step=0.0001)

        st.markdown('<div class="section-header">📅 Campaña</div>', unsafe_allow_html=True)
        fecha_siembra   = st.date_input("Fecha de siembra", value=date(2025, 12, 20),
                                         min_value=date(2020,1,1), max_value=date.today())
        rinde_potencial = st.number_input("Rinde potencial (kg/ha)",
                                           value=cultivo_mod.RINDE_POTENCIAL_BASE,
                                           step=100, min_value=500, max_value=20000)
        nombre_lote    = f"{estab_n} — {lote_n}" if estab_n and lote_n else "Nuevo lote"
        lote_id_activo = None

        if st.button("💾 Guardar lote", key="btn_guardar_lote", type="primary"):
            if not estab_n or not lote_n or not localidad_n:
                st.error("⚠️ Completá establecimiento, lote y localidad.")
            else:
                lote_id_activo = base_datos.guardar_lote({
                    "campana": campana_n, "establecimiento": estab_n,
                    "lote": lote_n, "localidad": localidad_n, "provincia": prov_n,
                    "lat": lat, "lon": lon, "cultivo": cultivo_nombre,
                    "variedad": variedad_nombre,
                    "fecha_siembra": fecha_siembra.strftime("%Y-%m-%d"),
                    "rinde_potencial": rinde_potencial,
                })
                st.success(f"✅ Lote guardado"); st.rerun()

    st.markdown('<div class="section-header">⚙️ Opciones</div>', unsafe_allow_html=True)
    mostrar_datos = st.checkbox("Mostrar tabla de datos diarios", value=False)
    st.markdown("<hr>", unsafe_allow_html=True)
    btn_calcular = st.button(f"▶️ Calcular {cultivo_mod.ICONO}",
                              use_container_width=True, type="primary")
    st.markdown("""<div style='margin-top:1rem;font-size:0.72rem;color:#475569;text-align:center;'>
        Open-Meteo Archive API · GDC + Fotoperíodo</div>""", unsafe_allow_html=True)

# ============================================================
#  HEADER
# ============================================================
st.markdown(f"""
<div class="main-header">
    <h1>{cultivo_mod.ICONO} Monitor Agrícola — {cultivo_nombre}</h1>
    <p>Seguimiento climático · GDC + Fotoperíodo · Predicción fenológica · Gestión de lote</p>
</div>""", unsafe_allow_html=True)

for k in ["df","predicciones","variedad","nombre_lote","cultivo_mod","resultado_rinde","lote_id","df_pronostico"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ============================================================
#  CALCULAR
# ============================================================
if btn_calcular:
    if fecha_siembra >= date.today():
        st.error("⚠️ La fecha de siembra debe ser anterior a hoy.")
    else:
        with st.spinner(f"🌍 Descargando datos para {nombre_lote}..."):
            datos_api = clima.obtener_datos(lat, lon,
                            fecha_siembra.strftime("%Y-%m-%d"),
                            clima.fecha_fin_disponible())
            datos_pronostico = clima.obtener_pronostico(lat, lon, dias=7)
        if datos_api is None or datos_pronostico is None:
            st.error("❌ No se pudo obtener datos o pronóstico.")
        else:
            with st.spinner("⚙️ Procesando modelo fenológico..."):
                df           = gdc.procesar_datos(datos_api, lat, fecha_siembra, variedad, cultivo_mod)
                predicciones = gdc.predecir_etapas(df, variedad, cultivo_mod.DESC_ETAPAS, cultivo_mod.ETAPAS_CRITICAS)
                res_rinde    = rinde.calcular_rinde_climatico(df, cultivo_mod, rinde_potencial)
                df_pronostico = gdc.estimar_etapas_futuras(datos_pronostico, lat, fecha_siembra, variedad, df["gdc_acum"].iloc[-1], df["dias"].iloc[-1])
            st.session_state.update({
                "df": df, "predicciones": predicciones, "variedad": variedad,
                "nombre_lote": nombre_lote, "cultivo_mod": cultivo_mod,
                "cultivo_nombre": cultivo_nombre, "variedad_nombre": variedad_nombre,
                "resultado_rinde": res_rinde, "rinde_potencial": rinde_potencial,
                "fecha_siembra": fecha_siembra, "lote_id": lote_id_activo,
                "df_pronostico": df_pronostico,
            })
            st.success(f"✅ {len(df)} días procesados para **{nombre_lote}**")

# ============================================================
#  RESULTADOS
# ============================================================
if st.session_state.df is not None:
    df          = st.session_state.df
    pred        = st.session_state.predicciones
    variedad    = st.session_state.variedad
    nombre_lote = st.session_state.nombre_lote
    cult_mod    = st.session_state.cultivo_mod
    cult_nombre = st.session_state.cultivo_nombre
    var_nombre  = st.session_state.variedad_nombre
    res_rinde   = st.session_state.resultado_rinde
    rinde_pot   = st.session_state.rinde_potencial
    f_siembra   = st.session_state.fecha_siembra
    lote_id_ss  = st.session_state.lote_id or lote_id_activo
    df_pronostico = st.session_state.df_pronostico

    ultima       = df.iloc[-1]
    etapa_actual = ultima["etapa"]
    gdc_actual   = ultima["gdc_acum"]
    dias_actual  = ultima["dias"]
    etapas_comp  = sum(1 for p in pred if p["estado"] == "completada")
    prox         = next((p for p in pred if p["estado"] != "completada"), None)

    st.markdown(f"""<div style='margin-bottom:0.5rem;'>
        <span style='color:#94a3b8;font-size:0.8rem;'>
        📍 {nombre_lote} &nbsp;·&nbsp; {cult_nombre} {var_nombre} &nbsp;·&nbsp;
        Siembra: {f_siembra.strftime("%d/%m/%Y")} &nbsp;·&nbsp;
        Datos al: {df["fecha"].iloc[-1].strftime("%d/%m/%Y")}
        </span></div>""", unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    for col, lbl, val, sub in [
        (c1,"Etapa Actual",      etapa_actual,                    cult_mod.DESC_ETAPAS.get(etapa_actual,"")),
        (c2,"GDC Acumulado",     f"{gdc_actual:.0f}",             "°C·día desde siembra"),
        (c3,"Días desde Siembra",str(dias_actual),                f"Etapas: {etapas_comp}/{len(pred)}"),
        (c4,"Lluvia Acumulada",  f"{df['lluvia'].sum():.0f}",     "mm desde siembra"),
        (c5,"Rinde Estimado",    f"{res_rinde['rinde_estimado']:,}","kg/ha (modelo climático)"),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{lbl}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    ultimos7     = df.tail(7)
    dias_calor   = int((ultimos7["t_max"] > cult_mod.T_CALOR_CRITICO_FLOR).sum())
    dias_deficit = int((ultimos7["balance"] < -3).sum())
    etapa_crit   = etapa_actual in cult_mod.ETAPAS_CRITICAS

    if dias_calor >= 3 and etapa_crit:
        st.markdown(f'<div class="alerta-stress">⚠️ <strong>Alerta térmica:</strong> {dias_calor} días con T° >{cult_mod.T_CALOR_CRITICO_FLOR}°C en etapa crítica ({etapa_actual}).</div>', unsafe_allow_html=True)
    if dias_deficit >= 4 and etapa_crit:
        st.markdown(f'<div class="alerta-stress">⚠️ <strong>Alerta hídrica:</strong> {dias_deficit} días con balance negativo en etapa crítica ({etapa_actual}).</div>', unsafe_allow_html=True)
    if dias_calor < 2 and dias_deficit < 3:
        st.markdown('<div class="alerta-ok">✅ <strong>Sin alertas activas</strong> — Condiciones dentro de parámetros normales en los últimos 7 días.</div>', unsafe_allow_html=True)
    if prox:
        st.markdown(f"""<div class="info-box">
            🔮 <strong>Próxima etapa:</strong> <strong>{prox['etapa']}</strong> — {prox['descripcion']} &nbsp;·&nbsp;
            Estimada para el <strong>{prox['fecha']}</strong> (en ~{prox['dias_faltan']} días)
        </div>""", unsafe_allow_html=True)

    # ============================================================
    #  TABS
    # ============================================================
    tab_clima, tab_pred, tab_rinde, tab_campo, tab_monitoreo, tab_pronostico, tab_export = st.tabs([
        "📈 Seguimiento Climático",
        "🔮 Predicción Fenológica",
        "🌾 Estimación de Rinde",
        "🌿 Gestión de Lote",
        "📋 Monitoreo",
        "🔮 Pronóstico 7 días",
        "📥 Exportar",
    ])

    # ---- CLIMA ----
    with tab_clima:
        t1,t2,t3,t4 = st.tabs(["🌡️ Temperaturas","🌧️ Lluvia & ET₀","💧 Balance","📊 GDC"])
        with t1: st.plotly_chart(graficos.grafico_temperaturas(df, var_nombre), use_container_width=True, config={"displayModeBar":False})
        with t2: st.plotly_chart(graficos.grafico_lluvia_et0(df, var_nombre),  use_container_width=True, config={"displayModeBar":False})
        with t3: st.plotly_chart(graficos.grafico_balance(df, var_nombre),     use_container_width=True, config={"displayModeBar":False})
        with t4: st.plotly_chart(graficos.grafico_gdc(df, variedad, var_nombre), use_container_width=True, config={"displayModeBar":False})
        if mostrar_datos:
            st.markdown('<div class="section-header">📋 Datos Diarios</div>', unsafe_allow_html=True)
            df_show = df[["fecha","dias","t_max","t_min","t_media","lluvia","humedad","et0","balance","gdc_acum","etapa","estres_t","estres_h"]].copy()
            df_show.columns = ["Fecha","Días","T°Máx","T°Mín","T°Media","Lluvia","Humedad","ET₀","Balance","GDC Acum","Etapa","Estrés T°","Estrés H"]
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=350)

    # ---- PREDICCIÓN ----
    with tab_pred:
        st.markdown('<div class="section-header">🔮 Predicción de Etapas Fenológicas</div>', unsafe_allow_html=True)
        filas = []
        for p in pred:
            est = "✅ Completada" if p["estado"]=="completada" else f"🟡 En ~{p['dias_faltan']} días" if p["estado"]=="proxima" else f"⚪ En ~{p['dias_faltan']} días"
            filas.append({"Etapa":p["etapa"],"Descripción":p["descripcion"],"Umbral GDC":p["umbral"],"Fecha Est.":p["fecha"],"Día ciclo":f"Día {p['dias']}","Estado":est})
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True, height=480,
                     column_config={"Umbral GDC": st.column_config.NumberColumn(format="%d °C·día")})

    # ---- RINDE CLIMÁTICO ----
    with tab_rinde:
        st.markdown('<div class="section-header">🌾 Estimación de Rinde — Modelo Climático</div>', unsafe_allow_html=True)
        r = res_rinde
        color_rc = "#34d399" if r["rinde_estimado"]>=rinde_pot*0.85 else "#fbbf24" if r["rinde_estimado"]>=rinde_pot*0.65 else "#f87171"
        st.markdown(f"""<div class="rinde-card">
            <div style='font-size:0.8rem;color:#6ee7b7;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.5rem;'>Rinde Estimado — {nombre_lote}</div>
            <div class="rinde-valor" style='color:{color_rc};'>{r["rinde_estimado"]:,} kg/ha</div>
            <div class="rinde-rango">Rango: {r["rinde_min"]:,} – {r["rinde_max"]:,} kg/ha · Incertidumbre ±18%</div>
            <div style='margin-top:1rem;display:flex;gap:2rem;flex-wrap:wrap;'>
                <div><span style='color:#60a5fa;font-size:0.78rem;'>💧 Pérd. hídrica</span><br><strong style='color:#93c5fd;'>{r["pen_hidrica"]}%</strong> ({round(rinde_pot*r["pen_hidrica"]/100):,} kg/ha)</div>
                <div><span style='color:#f87171;font-size:0.78rem;'>🌡️ Pérd. térmica</span><br><strong style='color:#fca5a5;'>{r["pen_termica"]}%</strong> ({round(rinde_pot*r["pen_termica"]/100):,} kg/ha)</div>
                <div><span style='color:#fb923c;font-size:0.78rem;'>🌊 Pérd. exceso</span><br><strong style='color:#fdba74;'>{r["pen_exceso"]}%</strong> ({round(rinde_pot*r["pen_exceso"]/100):,} kg/ha)</div>
                <div><span style='color:#a78bfa;font-size:0.78rem;'>📉 Pérd. total</span><br><strong style='color:#c4b5fd;'>{r["pen_total"]}%</strong> ({round(rinde_pot*r["pen_total"]/100):,} kg/ha)</div>
            </div></div>""", unsafe_allow_html=True)
        df_det = pd.DataFrame(r["detalle"])
        df_det.columns = ["Etapa","Estado","Ky","Días","Completada","ETa/ETp","Días T° crítica","Pen. Hídr. %","Pen. Térm. %","Pen. Exc. %","Pen. Total %","Pérdida kg/ha"]
        st.dataframe(df_det, use_container_width=True, hide_index=True,
                     column_config={"Pen. Total %": st.column_config.ProgressColumn(min_value=0, max_value=50, format="%.1f%%"),
                                    "Pérdida kg/ha": st.column_config.NumberColumn(format="%d kg/ha")})
        st.plotly_chart(graficos.grafico_rinde_comparativo(r, var_nombre), use_container_width=True, config={"displayModeBar":False})
        st.markdown("""<div class="info-box">⚠️ <strong>Nota:</strong> Modelo semi-empírico basado en estrés hídrico (FAO Ky) y térmico. Precisión ±15-25%.<br>📌 Las etapas futuras muestran pérdida 0% (aún no ocurrieron).</div>""", unsafe_allow_html=True)

    # ============================================================
    #  GESTIÓN DE LOTE
    # ============================================================
    with tab_campo:
        st.markdown('<div class="section-header">🌿 Gestión de Lote — Calculadoras de Campo</div>', unsafe_allow_html=True)
        calc1, calc2, calc3, calc4 = st.tabs([
            "🌱 1. Densidad de siembra",
            "🌿 2. Plantas establecidas",
            "🌾 3. Rinde estimado",
            "🔧 4. Pérdidas de cosecha",
        ])

        # -- 1. DENSIDAD --
        with calc1:
            st.markdown('<div class="section-header">🌱 Densidad de Siembra</div>', unsafe_allow_html=True)
            st.markdown("""<div class="info-box">
            Calculá semillas necesarias corrigiendo por <strong>poder germinativo</strong>.<br>
            Fórmula: Semillas/ha = Plantas objetivo / (PG% / 100) &nbsp;·&nbsp; kg/ha = Semillas/ha × PMG / 1.000.000
            </div>""", unsafe_allow_html=True)
            d1c, d2c = st.columns(2)
            with d1c:
                plantas_obj = st.number_input("Plantas objetivo (plantas/ha)", value=300000, step=10000, min_value=50000, max_value=1000000, key="ds_obj")
                poder_germ  = st.number_input("Poder germinativo (%)", value=90, step=1, min_value=50, max_value=100, key="ds_pg")
                pmg_sem     = st.number_input("PMG de la semilla (g)", value=float(getattr(cult_mod,"PMG_TIPICO",150)), step=5.0, min_value=10.0, key="ds_pmg")
            with d2c:
                dist_sem    = st.number_input("Distancia entre surcos (cm)", value=52, step=1, min_value=10, max_value=100, key="ds_surco")
            if st.button("🌱 Calcular densidad", key="btn_densidad"):
                semillas_ha = round(plantas_obj / (poder_germ / 100))
                kg_sem      = round(semillas_ha * pmg_sem / 1_000_000, 1)
                sem_metro   = round(semillas_ha * (dist_sem / 100) / 10_000, 1)
                pct_extra   = round((semillas_ha - plantas_obj) / plantas_obj * 100, 1)
                da,db,dc,dd = st.columns(4)
                with da: st.markdown(f"""<div class="metric-card"><div class="metric-label">Semillas / ha</div><div class="metric-value" style='color:#34d399;'>{semillas_ha:,}</div><div class="metric-sub">+{pct_extra}% por PG</div></div>""", unsafe_allow_html=True)
                with db: st.markdown(f"""<div class="metric-card"><div class="metric-label">kg semilla / ha</div><div class="metric-value">{kg_sem}</div><div class="metric-sub">PMG {pmg_sem}g</div></div>""", unsafe_allow_html=True)
                with dc: st.markdown(f"""<div class="metric-card"><div class="metric-label">Semillas / metro</div><div class="metric-value">{sem_metro}</div><div class="metric-sub">a {dist_sem}cm entre surcos</div></div>""", unsafe_allow_html=True)
                with dd: st.markdown(f"""<div class="metric-card"><div class="metric-label">Plantas objetivo</div><div class="metric-value">{plantas_obj:,}</div><div class="metric-sub">con PG {poder_germ}%</div></div>""", unsafe_allow_html=True)

        # -- 2. PLANTAS ESTABLECIDAS --
        with calc2:
            st.markdown('<div class="section-header">🌿 Plantas Establecidas por Hectárea</div>', unsafe_allow_html=True)
            st.markdown("""<div class="info-box">
            Hacé al menos <strong>5 repeticiones</strong> en distintos puntos del lote.
            </div>""", unsafe_allow_html=True)
            pe1c, pe2c = st.columns(2)
            with pe1c:
                dist_pe  = st.number_input("Distancia entre surcos (cm)", value=52, step=1, min_value=10, max_value=100, key="pe_surco")
                metodo_pe = st.radio("Longitud de conteo", ["1 metro lineal","10 metros lineales"], horizontal=True, key="pe_met")
            largo_pe   = 1.0 if "1 metro" in metodo_pe else 10.0
            area_pe    = (dist_pe/100) * largo_pe
            st.markdown(f"**Área de conteo por repetición: {area_pe:.3f} m²**")
            cols_pe = st.columns(5)
            conteos_pe = []
            for i in range(10):
                with cols_pe[i%5]:
                    conteos_pe.append(st.number_input(f"Rep. {i+1}", value=0, step=1, min_value=0, key=f"pe_{i}"))
            if st.button("🌿 Calcular plantas/ha", key="btn_plantas"):
                validos = [c for c in conteos_pe if c > 0]
                if not validos:
                    st.error("⚠️ Ingresá al menos un conteo mayor a cero.")
                else:
                    prom_pe    = sum(validos)/len(validos)
                    plantas_ha = round((prom_pe/area_pe)*10_000)
                    pl_m2      = round(prom_pe/area_pe, 1)
                    cv_pe      = round(statistics.stdev(validos)/prom_pe*100,1) if len(validos)>1 else 0
                    pa,pb,pc_,pd_ = st.columns(4)
                    color_cv = "#34d399" if cv_pe<15 else "#fbbf24" if cv_pe<25 else "#f87171"
                    with pa: st.markdown(f"""<div class="metric-card"><div class="metric-label">Plantas / ha</div><div class="metric-value" style='color:#34d399;'>{plantas_ha:,}</div><div class="metric-sub">stand logrado</div></div>""", unsafe_allow_html=True)
                    with pb: st.markdown(f"""<div class="metric-card"><div class="metric-label">Plantas / m²</div><div class="metric-value">{pl_m2}</div><div class="metric-sub">promedio conteos</div></div>""", unsafe_allow_html=True)
                    with pc_: st.markdown(f"""<div class="metric-card"><div class="metric-label">Repeticiones</div><div class="metric-value">{len(validos)}</div><div class="metric-sub">conteos válidos</div></div>""", unsafe_allow_html=True)
                    with pd_: st.markdown(f"""<div class="metric-card"><div class="metric-label">Variabilidad CV</div><div class="metric-value" style='color:{color_cv};'>{cv_pe}%</div><div class="metric-sub">{'✅ Uniforme' if cv_pe<15 else '🟡 Moderada' if cv_pe<25 else '🔴 Alta'}</div></div>""", unsafe_allow_html=True)
                    est_stand = "✅ Stand óptimo" if plantas_ha>=350000 else "🟡 Stand aceptable — impacto leve" if plantas_ha>=250000 else "🔴 Stand bajo — rinde comprometido"
                    c_stand   = "alerta-ok" if plantas_ha>=350000 else "alerta-stress"
                    st.markdown(f'<div class="{c_stand}" style="margin-top:1rem;">{est_stand} — {plantas_ha:,} plantas/ha</div>', unsafe_allow_html=True)

        # -- 3. RINDE ESTIMADO --
        with calc3:
            st.markdown('<div class="section-header">🌾 Rinde Estimado por Componentes</div>', unsafe_allow_html=True)
            st.markdown("""<div class="info-box">
            Fórmula: <strong>Plantas/m² × Vainas/planta × Granos/vaina × PMG(g) / 100 = kg/ha</strong>
            </div>""", unsafe_allow_html=True)
            pmg_def = float(getattr(cult_mod,"PMG_TIPICO",150))
            rc1c, rc2c = st.columns(2)
            with rc1c:
                pl_r = st.number_input("Plantas/m²",        value=20.0, step=0.5, min_value=0.1, key="rc_pl")
                vai_r = st.number_input("Vainas por planta", value=20.0, step=1.0, min_value=0.1, key="rc_vai")
            with rc2c:
                gr_r  = st.number_input("Granos por vaina",  value=2.5,  step=0.1, min_value=0.1, key="rc_gr")
                pmg_r = st.number_input("PMG (g)",           value=pmg_def, step=5.0, min_value=10.0, key="rc_pmg")
            vai_prev = round(pl_r*vai_r,1); gr_prev = round(vai_prev*gr_r,1); rp = round(gr_prev*pmg_r/100)
            st.markdown(f"""<div class="info-box">📐 Vista previa: Vainas/m²: <strong>{vai_prev}</strong> · Granos/m²: <strong>{gr_prev}</strong> · Rinde: <strong style='color:#34d399;font-size:1.1rem;'>{rp:,} kg/ha</strong></div>""", unsafe_allow_html=True)
            if st.button("🌾 Calcular rinde", key="btn_rinde_campo"):
                res_rc = rinde.calcular_rinde_aro(pl_r, vai_r, gr_r, pmg_r)
                c_rc = "#34d399" if res_rc["rinde"]>=rinde_pot*0.85 else "#fbbf24" if res_rc["rinde"]>=rinde_pot*0.65 else "#f87171"
                ra,rb,rc_ = st.columns(3)
                with ra: st.markdown(f"""<div class="metric-card"><div class="metric-label">Rinde Estimado</div><div class="metric-value" style='color:{c_rc};'>{res_rc["rinde"]:,}</div><div class="metric-sub">kg/ha</div></div>""", unsafe_allow_html=True)
                with rb: st.markdown(f"""<div class="metric-card"><div class="metric-label">Vainas / m²</div><div class="metric-value">{res_rc["vainas_m2"]:,}</div><div class="metric-sub">componente principal</div></div>""", unsafe_allow_html=True)
                with rc_: st.markdown(f"""<div class="metric-card"><div class="metric-label">Granos / m²</div><div class="metric-value">{res_rc["granos_m2"]:,}</div><div class="metric-sub">determinante del rinde</div></div>""", unsafe_allow_html=True)
                if res_rc["rinde"]>0 and res_rinde["rinde_estimado"]>0:
                    diff  = res_rc["rinde"]-res_rinde["rinde_estimado"]
                    pct_d = round(diff/res_rinde["rinde_estimado"]*100,1)
                    c_d   = "#34d399" if abs(pct_d)<=15 else "#fbbf24" if abs(pct_d)<=30 else "#f87171"
                    sgn   = "+" if diff>=0 else ""
                    interp = "✅ Confirma el modelo climático." if abs(pct_d)<=15 else "🟡 Diferencia moderada — posible factor no climático." if abs(pct_d)<=30 else "🔴 Diferencia importante — factores limitantes no climáticos."
                    st.markdown(f"""<div class="info-box" style='margin-top:1rem;'>
                        <strong>🔄 vs Modelo climático:</strong> Campo: <strong>{res_rc["rinde"]:,} kg/ha</strong> · Clima: <strong>{res_rinde["rinde_estimado"]:,} kg/ha</strong> · Dif: <strong style='color:{c_d};'>{sgn}{diff:,} kg/ha ({sgn}{pct_d}%)</strong><br>
                        <span style='color:#94a3b8;'>{interp}</span></div>""", unsafe_allow_html=True)

        # -- 4. PÉRDIDAS DE COSECHA --
        with calc4:
            st.markdown('<div class="section-header">🔧 Pérdidas de Cosecha — Aro Ciego (Metodología INTA)</div>', unsafe_allow_html=True)
            tol_c = rinde.TOLERANCIAS_CULTIVO.get(cult_nombre, rinde.TOLERANCIAS_CULTIVO["Soja"])
            equiv = rinde.EQUIV_GRANOS.get(cult_nombre, 60)
            st.markdown(f"""<div class="info-box">
            <strong>Equivalencia INTA para {cult_nombre}:</strong> {equiv} granos/m² = 100 kg/ha<br>
            <strong>Tolerancias:</strong> Cabezal {tol_c['cabezal']} kg/ha · Cola {tol_c['cola']} kg/ha · Total {tol_c['total']} kg/ha<br><br>
            1️⃣ Contar granos en suelo <strong>antes</strong> de que pase la máquina (precosecha)<br>
            2️⃣ Tirar aro ciego <strong>debajo</strong> de la cosechadora → contar granos (cabezal + cola)<br>
            3️⃣ Contar granos <strong>sobre</strong> el aro (solo cola/sacudores)<br>
            📌 Pérdida cabezal = debajo del aro − precosecha
            </div>""", unsafe_allow_html=True)
            pc1c, pc2c = st.columns(2)
            with pc1c:
                area_sel = st.selectbox("Tamaño del aro", ["0.25 m² (aro de 56 cm Ø)","0.5 m² (aro de 80 cm Ø)"], key="pc_area")
                area_m2s = 0.25 if "0.25" in area_sel else 0.5
                st.markdown("**📋 Granos máximos permitidos en tu aro:**")
                t1p,t2p,t3p = st.columns(3)
                with t1p: st.metric("Cabezal", f"{rinde.kgha_a_granos(tol_c['cabezal'],area_m2s,cult_nombre):.0f} gr", f"{tol_c['cabezal']} kg/ha")
                with t2p: st.metric("Cola",    f"{rinde.kgha_a_granos(tol_c['cola'],   area_m2s,cult_nombre):.0f} gr", f"{tol_c['cola']} kg/ha")
                with t3p: st.metric("Total",   f"{rinde.kgha_a_granos(tol_c['total'],  area_m2s,cult_nombre):.0f} gr", f"{tol_c['total']} kg/ha")
            with pc2c:
                g_pre = st.number_input("1️⃣ Granos precosecha",     value=0, step=1, min_value=0, key="pc_pre")
                g_deb = st.number_input("2️⃣ Granos debajo del aro", value=0, step=1, min_value=0, key="pc_deb")
                g_sob = st.number_input("3️⃣ Granos sobre el aro",   value=0, step=1, min_value=0, key="pc_sob")
            if st.button("🔧 Calcular pérdidas", key="btn_perdidas"):
                res_p = rinde.calcular_perdidas_aro_ciego(area_m2s,float(g_pre),float(g_deb),float(g_sob),cult_nombre)
                pp1,pp2,pp3,pp4 = st.columns(4)
                with pp1: st.markdown(f"""<div class="metric-card"><div class="metric-label">Pre-cosecha</div><div class="metric-value">{res_p["pre_kgha"]}</div><div class="metric-sub">kg/ha (ya estaba caído)</div></div>""", unsafe_allow_html=True)
                for col_p, lbl_p, key_p in [(pp2,"Pérd. Cabezal","cabezal"),(pp3,"Pérd. Cola","cola"),(pp4,"Total Máquina","total")]:
                    kgha_p = res_p["cabezal_kgha"] if key_p=="cabezal" else res_p["cola_kgha"] if key_p=="cola" else res_p["total_maq"]
                    est_p  = res_p[f"estado_{'cabezal' if key_p=='cabezal' else 'cola' if key_p=='cola' else 'total'}"]
                    cp_    = "#f87171" if "Supera" in est_p else "#fbbf24" if "límite" in est_p else "#34d399"
                    with col_p: st.markdown(f"""<div class="metric-card"><div class="metric-label">{lbl_p}</div><div class="metric-value" style='color:{cp_};'>{kgha_p}</div><div class="metric-sub">kg/ha · {est_p}</div></div>""", unsafe_allow_html=True)
                st.markdown('<div class="section-header">🔧 Diagnóstico y Ajustes</div>', unsafe_allow_html=True)
                for d in res_p["diagnostico"]:
                    c_d = "alerta-ok" if "✅" in d["zona"] else "alerta-stress"
                    aj  = "".join(f"<li style='margin:0.3rem 0;'>{a}</li>" for a in d["ajustes"])
                    st.markdown(f"""<div class="{c_d}" style='margin-bottom:0.8rem;'><strong>{d["zona"]}</strong> — {d["problema"]}<br><ul style='margin:0.5rem 0 0 0;padding-left:1.2rem;'>{aj}</ul></div>""", unsafe_allow_html=True)

    # ============================================================
    #  MONITOREO
    # ============================================================
    with tab_monitoreo:
        st.markdown('<div class="section-header">📋 Monitoreo Fitosanitario del Lote</div>', unsafe_allow_html=True)
        if not lote_id_ss:
            st.warning("⚠️ Guardá el lote primero (sidebar) para poder registrar monitoreos.")
        else:
            mon_nuevo, mon_historial = st.tabs(["➕ Nuevo registro","📊 Historial"])

            with mon_nuevo:
                st.markdown('<div class="section-header">📝 Datos del monitoreo</div>', unsafe_allow_html=True)
                mn1c, mn2c = st.columns(2)
                with mn1c:
                    fecha_mon = st.date_input("Fecha", value=date.today(), key="mon_fecha")
                    etapa_mon = st.selectbox("Etapa fenológica", [""]+list(cult_mod.DESC_ETAPAS.keys()), key="mon_etapa")
                    gdc_mon   = st.number_input("GDC acumulado", value=float(gdc_actual), step=10.0, key="mon_gdc")
                with mn2c:
                    tecnico_mon = st.text_input("Técnico / responsable", key="mon_tec")

                # Malezas
                st.markdown('<div class="section-header">🌿 Malezas</div>', unsafe_allow_html=True)
                mal_p = st.checkbox("Presencia de malezas", key="mon_mal_p")
                if mal_p:
                    mc1,mc2 = st.columns(2)
                    with mc1: mal_d = st.text_area("Especies", key="mon_mal_d", height=80); mal_c = st.number_input("Cobertura (%)", value=0.0, step=5.0, key="mon_mal_c")
                    with mc2: mal_a = st.selectbox("Acción", ["Sin acción","Monitorear en 7 días","Aplicación herbicida","Control mecánico"], key="mon_mal_a")
                else:
                    mal_d, mal_c, mal_a = "", 0.0, ""

                # Insectos
                st.markdown('<div class="section-header">🐛 Insectos</div>', unsafe_allow_html=True)
                ins_p = st.checkbox("Presencia de insectos", key="mon_ins_p")
                if ins_p:
                    ic1,ic2 = st.columns(2)
                    with ic1: ins_d = st.text_area("Especie / complejo", key="mon_ins_d", height=80); ins_c = st.text_input("Conteo (ej: 2/m², 15% defoliación)", key="mon_ins_c")
                    with ic2: ins_a = st.selectbox("Acción", ["Sin acción","Monitorear en 5 días","Aplicación insecticida","Daño económico alcanzado"], key="mon_ins_a")
                else:
                    ins_d, ins_c, ins_a = "", "", ""

                # Enfermedades
                st.markdown('<div class="section-header">🍄 Enfermedades</div>', unsafe_allow_html=True)
                enf_p = st.checkbox("Presencia de enfermedades", key="mon_enf_p")
                if enf_p:
                    ec1,ec2 = st.columns(2)
                    with ec1:
                        enf_d = st.text_area("Nombre / órgano afectado", key="mon_enf_d", height=80)
                        enf_i = st.number_input("Incidencia (%)", value=0.0, step=5.0, key="mon_enf_i")
                        enf_s = st.number_input("Severidad (%)",  value=0.0, step=5.0, key="mon_enf_s")
                    with ec2: enf_a = st.selectbox("Acción", ["Sin acción","Monitorear en 7 días","Aplicación fungicida","Umbral alcanzado"], key="mon_enf_a")
                else:
                    enf_d, enf_i, enf_s, enf_a = "", 0.0, 0.0, ""

                # Estrés
                st.markdown('<div class="section-header">⚠️ Estrés</div>', unsafe_allow_html=True)
                est_p = st.checkbox("Presencia de estrés", key="mon_est_p")
                if est_p:
                    est_t = st.selectbox("Tipo", ["Hídrico","Térmico","Nutricional","Vuelco","Granizo","Otro"], key="mon_est_t")
                    est_i = st.selectbox("Intensidad", ["Leve","Moderado","Severo"], key="mon_est_i")
                    est_d = st.selectbox("Distribución", ["Uniforme","Focalizado","Manchones","Bordes"], key="mon_est_d")
                else:
                    est_t, est_i, est_d = "", "", ""

                # Conclusión
                st.markdown('<div class="section-header">📝 Conclusión</div>', unsafe_allow_html=True)
                obs_mon = st.text_area("Observaciones generales", key="mon_obs", height=100)
                dec_mon = st.selectbox("Decisión", ["Sin acción","Re-monitoreo en 7 días","Aplicación fitosanitaria","Aplicación nutricional","Intervención mecánica","Otro"], key="mon_dec")

                if st.button("💾 Guardar monitoreo", key="btn_guardar_mon", type="primary"):
                    base_datos.guardar_monitoreo({
                        "lote_id": lote_id_ss, "fecha": fecha_mon.strftime("%Y-%m-%d"),
                        "etapa_fenologica": etapa_mon, "gdc_acumulado": gdc_mon,
                        "malezas_presentes": mal_p, "malezas_detalle": mal_d, "malezas_cobertura": mal_c, "malezas_accion": mal_a,
                        "insectos_presentes": ins_p, "insectos_detalle": ins_d, "insectos_conteo": ins_c, "insectos_accion": ins_a,
                        "enf_presentes": enf_p, "enf_detalle": enf_d, "enf_incidencia": enf_i, "enf_severidad": enf_s, "enf_accion": enf_a,
                        "estres_presente": est_p, "estres_tipo": est_t, "estres_intensidad": est_i, "estres_distribucion": est_d,
                        "observaciones": obs_mon, "decision": dec_mon, "tecnico": tecnico_mon,
                    })
                    st.success("✅ Monitoreo guardado.")

            with mon_historial:
                st.markdown('<div class="section-header">📊 Historial de Monitoreos</div>', unsafe_allow_html=True)
                hf1,hf2,hf3 = st.columns(3)
                with hf1: etapa_filt = st.selectbox("Etapa", ["Todas"]+list(cult_mod.DESC_ETAPAS.keys()), key="h_et")
                with hf2: desde_filt = st.date_input("Desde", value=f_siembra, key="h_desde")
                with hf3: hasta_filt = st.date_input("Hasta", value=date.today(), key="h_hasta")

                regs = base_datos.listar_monitoreos(
                    lote_id_ss,
                    etapa=etapa_filt if etapa_filt!="Todas" else None,
                    fecha_desde=desde_filt.strftime("%Y-%m-%d"),
                    fecha_hasta=hasta_filt.strftime("%Y-%m-%d"),
                )
                if not regs:
                    st.info("No hay monitoreos registrados con los filtros seleccionados.")
                else:
                    st.markdown(f"**{len(regs)} registro(s) encontrado(s)**")
                    for reg in regs:
                        probs = []
                        if reg["malezas_presentes"]:  probs.append("🌿 Malezas")
                        if reg["insectos_presentes"]: probs.append("🐛 Insectos")
                        if reg["enf_presentes"]:      probs.append("🍄 Enfermedades")
                        if reg["estres_presente"]:    probs.append("⚠️ Estrés")
                        prob_s = " · ".join(probs) if probs else "✅ Sin problemas"
                        with st.expander(f"📅 {reg['fecha']} — Etapa: {reg['etapa_fenologica'] or 'N/D'} — {prob_s}"):
                            cr1,cr2 = st.columns(2)
                            with cr1:
                                if reg["malezas_presentes"]:  st.markdown(f"**🌿 Malezas:** {reg['malezas_detalle']} — {reg['malezas_cobertura']}% — {reg['malezas_accion']}")
                                if reg["insectos_presentes"]: st.markdown(f"**🐛 Insectos:** {reg['insectos_detalle']} — {reg['insectos_conteo']} — {reg['insectos_accion']}")
                            with cr2:
                                if reg["enf_presentes"]:     st.markdown(f"**🍄 Enferm.:** {reg['enf_detalle']} — Inc:{reg['enf_incidencia']}% Sev:{reg['enf_severidad']}% — {reg['enf_accion']}")
                                if reg["estres_presente"]:   st.markdown(f"**⚠️ Estrés:** {reg['estres_tipo']} — {reg['estres_intensidad']} — {reg['estres_distribucion']}")
                            if reg["observaciones"]: st.markdown(f"**📝 Obs:** {reg['observaciones']}")
                            st.markdown(f"**✅ Decisión:** {reg['decision']} · **Técnico:** {reg['tecnico'] or 'N/D'}")
                            if st.button("🗑️ Eliminar", key=f"del_{reg['id']}"):
                                base_datos.eliminar_monitoreo(reg["id"]); st.rerun()

    # ---- PRONÓSTICO 7 DÍAS ----
    with tab_pronostico:
        st.markdown('<div class="section-header">🔮 Pronóstico Extendido y Alertas (7 Días)</div>', unsafe_allow_html=True)
        if df_pronostico is None or df_pronostico.empty:
            st.warning("No hay datos de pronóstico disponibles.")
        else:
            t_crit = 32 if cult_nombre == "Soja" else 35 if cult_nombre == "Maíz" else 38
            
            dias_sin_lluvia = 0
            
            for idx, row in df_pronostico.iterrows():
                fecha_str = row['fecha'].strftime('%d/%m/%Y')
                t_max = row['t_max']
                t_min = row['t_min']
                lluvia = row['lluvia']
                humedad = row['humedad']
                etapa_pron = row['etapa']
                
                # Alertas T°
                alerta_t = "🟢 Normal"
                rec_t = ""
                if t_max > t_crit:
                    alerta_t = "🔴 Alta"
                    rec_t = f"T° ({t_max}°C) supera el umbral crítico de {t_crit}°C para {cult_nombre}. Evaluar riego de apoyo o impacto en rinde."
                elif t_max >= t_crit - 2:
                    alerta_t = "🟡 Moderada"
                    rec_t = f"T° ({t_max}°C) cercana al umbral crítico. Mantener monitoreo."
                
                if lluvia == 0:
                    dias_sin_lluvia += 1
                else:
                    dias_sin_lluvia = 0
                
                critica = etapa_pron in cult_mod.ETAPAS_CRITICAS
                alerta_h = "🟢 Normal"
                rec_h = ""
                if dias_sin_lluvia >= 5 and critica:
                    alerta_h = "🔴 Alta"
                    rec_h = f"{dias_sin_lluvia} días sin lluvia durante etapa crítica ({etapa_pron}). Alto riesgo para el rinde."
                elif dias_sin_lluvia >= 3 and critica:
                    alerta_h = "🟡 Moderada"
                    rec_h = f"{dias_sin_lluvia} días sin lluvia en etapa crítica. Monitorear humedad del suelo."

                # Alertas Exceso
                alerta_e = "🟢 Normal"
                rec_e = ""
                if lluvia > 30 or (humedad > 85 and lluvia > 0):
                    alerta_e = "🔴 Alta"
                    rec_e = "Riesgo extremo de enfermedades o anoxia por exceso de agua/humedad."
                elif lluvia >= 15:
                    alerta_e = "🟡 Moderada"
                    rec_e = "Lluvias significativas pronosticadas, vigilar escurrimiento."

                # Cards
                html_card = f"""<div style='background:#1e293b;border-radius:8px;padding:15px;margin-bottom:15px;'>
                    <h4 style='color:#38bdf8;margin:0 0 10px 0;'>📅 {fecha_str} — Etapa Estimada: {etapa_pron}</h4>
                    <div style='display:flex;gap:20px;margin-bottom:10px;font-size:0.95rem;'>
                        <div>🌡️ Máx: <strong>{t_max}°C</strong> / Mín: <strong>{t_min}°C</strong></div>
                        <div>🌧️ Lluvia: <strong>{lluvia} mm</strong></div>
                        <div>💧 Humedad: <strong>{humedad}%</strong></div>
                    </div>
                """
                
                alertas_html = ""
                if "Normal" not in alerta_t:
                    bg = "#450a0a" if "Alta" in alerta_t else "#422006"
                    color = "#fca5a5" if "Alta" in alerta_t else "#fde047"
                    border = "#f87171" if "Alta" in alerta_t else "#eab308"
                    alertas_html += f"<div style='background:{bg};color:{color};border-left:4px solid {border};padding:8px;margin-bottom:5px;font-size:0.9rem;'>🌡️ <strong>Estrés Térmico ({alerta_t})</strong> - {rec_t}</div>"
                if "Normal" not in alerta_h:
                    bg = "#450a0a" if "Alta" in alerta_h else "#422006"
                    color = "#fca5a5" if "Alta" in alerta_h else "#fde047"
                    border = "#f87171" if "Alta" in alerta_h else "#eab308"
                    alertas_html += f"<div style='background:{bg};color:{color};border-left:4px solid {border};padding:8px;margin-bottom:5px;font-size:0.9rem;'>💧 <strong>Estrés Hídrico ({alerta_h})</strong> - {rec_h}</div>"
                if "Normal" not in alerta_e:
                    bg = "#450a0a" if "Alta" in alerta_e else "#422006"
                    color = "#fca5a5" if "Alta" in alerta_e else "#fde047"
                    border = "#f87171" if "Alta" in alerta_e else "#eab308"
                    alertas_html += f"<div style='background:{bg};color:{color};border-left:4px solid {border};padding:8px;margin-bottom:5px;font-size:0.9rem;'>🌊 <strong>Exceso de Agua ({alerta_e})</strong> - {rec_e}</div>"
                
                if alertas_html == "":
                    alertas_html = f"<div style='color:#34d399;font-size:0.9rem;'>✅ Condiciones óptimas sin alertas pronosticadas.</div>"
                    
                st.markdown(html_card + alertas_html + "</div>", unsafe_allow_html=True)
            
            st.markdown('<div class="section-header">📋 Tabla Resumen Pronóstico</div>', unsafe_allow_html=True)
            df_show_pron = df_pronostico[["fecha", "etapa", "t_max", "t_min", "lluvia", "humedad", "et0", "balance"]].copy()
            df_show_pron.columns = ["Fecha", "Etapa Estimada", "T° Máx", "T° Mín", "Lluvia (mm)", "Humedad (%)", "ET₀", "Balance"]
            st.dataframe(df_show_pron, hide_index=True, use_container_width=True)

    # ---- EXPORTAR ----
    with tab_export:
        st.markdown('<div class="section-header">📥 Exportar datos para Power BI / Excel</div>', unsafe_allow_html=True)
        st.markdown("""<div class="info-box">Excel con 5 hojas: <strong>Datos Diarios · Predicción · Rinde · Resumen · Monitoreos</strong></div>""", unsafe_allow_html=True)
        if st.button("📊 Generar Excel", key="btn_export"):
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_e = df.copy(); df_e["fecha"] = df_e["fecha"].astype(str); df_e.columns = [c.upper() for c in df_e.columns]
                df_e.to_excel(w, sheet_name="Datos Diarios", index=False)
                pd.DataFrame(pred).to_excel(w, sheet_name="Predicción Fenológica", index=False)
                df_r = pd.DataFrame(res_rinde["detalle"]); df_r["rinde_estimado"]=res_rinde["rinde_estimado"]; df_r["rinde_min"]=res_rinde["rinde_min"]; df_r["rinde_max"]=res_rinde["rinde_max"]
                df_r.to_excel(w, sheet_name="Estimación de Rinde", index=False)
                pd.DataFrame([{"Lote":nombre_lote,"Cultivo":cult_nombre,"Variedad":var_nombre,
                    "Fecha Siembra":f_siembra.strftime("%d/%m/%Y"),"Datos al":df["fecha"].iloc[-1].strftime("%d/%m/%Y"),
                    "Días":dias_actual,"Etapa":etapa_actual,"GDC":gdc_actual,
                    "Lluvia mm":round(df["lluvia"].sum(),1),"T media":round(df["t_media"].mean(),1),
                    "Rinde est.":res_rinde["rinde_estimado"],"Rinde min":res_rinde["rinde_min"],"Rinde max":res_rinde["rinde_max"],
                    "Pérd. hídr.%":res_rinde["pen_hidrica"],"Pérd. térm.%":res_rinde["pen_termica"],
                }]).to_excel(w, sheet_name="Resumen General", index=False)
                if lote_id_ss:
                    mons = base_datos.listar_monitoreos(lote_id_ss)
                    if mons: pd.DataFrame(mons).to_excel(w, sheet_name="Monitoreos", index=False)
            buf.seek(0)
            st.download_button("⬇️ Descargar Excel", data=buf,
                file_name=f"monitor_{cult_nombre.lower()}_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.markdown("""<div style='text-align:center;padding:3rem 2rem;'>
        <div style='font-size:4rem;margin-bottom:1rem;'>🌾</div>
        <div style='font-size:1.1rem;color:#64748b;margin-bottom:0.5rem;'>
            Seleccioná o creá un lote en el panel izquierdo y presioná
            <strong style='color:#34d399;'>▶ Calcular</strong></div>
        <div style='font-size:0.85rem;color:#334155;margin-top:1.5rem;'>
            Open-Meteo Archive API · GDC + Fotoperíodo Brock (1981) · FAO Ky · SQLite</div>
    </div>""", unsafe_allow_html=True)

st.markdown("""<div class="footer">Monitor Agrícola v2.5 · Open-Meteo · GDC + Fotoperíodo · FAO Ky · SQLite</div>""", unsafe_allow_html=True)
