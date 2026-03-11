# core/rinde.py
import math

def calcular_rinde_climatico(df, cultivo_mod, rinde_potencial: float) -> dict:
    """
    Estima rinde con pérdidas por estrés hídrico (FAO Ky),
    térmico y exceso hídrico.
    """
    ky_dict        = getattr(cultivo_mod, "KY", {})
    etapas_gdc     = getattr(cultivo_mod, "ETAPAS_RINDE_GDC", {})
    t_calor_flor   = getattr(cultivo_mod, "T_CALOR_CRITICO_FLOR",    33)
    t_calor_llenado = getattr(cultivo_mod, "T_CALOR_CRITICO_LLENADO", 35)

    # Inicializar acumuladores por etapa
    acum = {e: {"sumaETp":0,"sumaETa":0,"diasCalor":0,"diasTotal":0,"diasExceso":0,"completada":False, "estado": "Futura"}
            for e in etapas_gdc}

    cons_exceso = 0
    
    # Determinar última etapa alcanzada
    gdc_final = df["gdc_acum"].iloc[-1] if not df.empty else 0
    etapa_actual = None
    for e, rango in etapas_gdc.items():
        if rango["min"] <= gdc_final < rango["max"]:
            etapa_actual = e
            break
    if not etapa_actual and gdc_final > 0:
        etapa_actual = list(etapas_gdc.keys())[-1]

    # Marcar estados
    encontrada_actual = False
    for e in etapas_gdc:
        if e == etapa_actual:
            acum[e]["estado"] = "En curso"
            encontrada_actual = True
        elif not encontrada_actual:
            acum[e]["estado"] = "Completada"
            acum[e]["completada"] = True
        else:
            acum[e]["estado"] = "Futura"

    for _, row in df.iterrows():
        gdc_p = row["gdc_acum"]
        t_max = row["t_max"]
        lluvia = row["lluvia"]
        et0   = row["et0"] if row["et0"] > 0 else 4
        balance = row["balance"]

        # Determinar etapa de rinde
        etapa_r = None
        for e, rango in etapas_gdc.items():
            if rango["min"] <= gdc_p < rango["max"]:
                etapa_r = e
                break
        if gdc_p >= max(r["max"] for r in etapas_gdc.values()):
            etapa_r = list(etapas_gdc.keys())[-1]
        if not etapa_r:
            continue

        a = acum[etapa_r]
        if a["estado"] == "Futura":
            continue

        a["diasTotal"] += 1

        # ETa estimada (secano)
        eta = min(lluvia + 5, et0)
        a["sumaETp"] += et0
        a["sumaETa"] += eta

        # Calor crítico
        etapas_calor = list(etapas_gdc.keys())[1:4]  # etapas reproductivas
        if etapa_r in etapas_calor:
            if t_max > t_calor_llenado:
                a["diasCalor"] += 1
            elif t_max > t_calor_flor:
                a["diasCalor"] += 0.5

        # Exceso hídrico
        if balance > 20:
            cons_exceso += 1
            if cons_exceso >= 3:
                a["diasExceso"] += 1
        else:
            cons_exceso = 0

    # Calcular penalidades usando modelo multiplicativo
    factor_global_h = 1.0
    factor_global_t = 1.0
    factor_global_e = 1.0
    detalle     = []

    for etapa, a in acum.items():
        ky = ky_dict.get(etapa, 0.3)
        
        estado = a["estado"]
        
        if estado == "Futura":
            factor_hid = 1.0
            factor_term = 1.0
            factor_exc = 1.0
            factor_total_etapa = 1.0
            ratio_et = 1.0
            perdida_kg = 0
        else:
            # Hídrica
            ratio_et = (a["sumaETa"] / a["sumaETp"]) if a["sumaETp"] > 0 else 1
            pen_h    = ky * max(0, 1 - ratio_et)

            # Térmica
            pen_t = 0
            if a["diasTotal"] > 0:
                pen_t = min((a["diasCalor"] / a["diasTotal"]) * 0.40, 0.30)

            # Exceso
            pen_e = min(a["diasExceso"] * 0.05, 0.15)
            
            # Factores etapa
            factor_hid = max(0, 1 - pen_h)
            factor_term = max(0, 1 - pen_t)
            factor_exc = max(0, 1 - pen_e)
            
            # En curso proporcional
            if estado == "En curso" and a["diasTotal"] > 0:
                # Si está en curso, las penalidades acumuladas hasta hoy ya reflejan el impacto real transcurrido
                # El modelo asume penalidad sobre el % de días medidos reales. No escalamos hacia arriba artificialmente.
                pass
            
            factor_total_etapa = factor_hid * factor_term * factor_exc
            perdida_kg = round(rinde_potencial * (1 - factor_total_etapa))

        # Acumular globalmente multiplicando
        factor_global_h *= factor_hid
        factor_global_t *= factor_term
        factor_global_e *= factor_exc

        detalle.append({
            "etapa":         etapa,
            "estado":        estado,
            "ky":            ky,
            "dias":          a["diasTotal"],
            "completada":    a["completada"],
            "ratio_et":      round(ratio_et, 2),
            "dias_calor":    round(a["diasCalor"], 1),
            "pen_hidrica":   round((1 - factor_hid) * 100, 1),
            "pen_termica":   round((1 - factor_term) * 100, 1),
            "pen_exceso":    round((1 - factor_exc) * 100, 1),
            "pen_total":     round((1 - factor_total_etapa) * 100, 1),
            "perdida_kg":    perdida_kg,
        })

    # Calcular penalidad total global multiplicativa
    factor_total_global = factor_global_h * factor_global_t * factor_global_e
    
    # Evitar pérdida del 100% total por artefactos (cap a ~80% máx por seguridad agronomica o dejar libre)
    factor_total_global = max(factor_total_global, 0.20)  # Límite opcional de penalidad máxima (80% pérdida)
    
    pen_total_h_pct = (1 - factor_global_h) * 100
    pen_total_t_pct = (1 - factor_global_t) * 100
    pen_total_e_pct = (1 - factor_global_e) * 100
    pen_total_pct = (1 - factor_total_global) * 100
    
    rinde_est = round(rinde_potencial * factor_total_global)

    return {
        "rinde_estimado": rinde_est,
        "rinde_min":      round(rinde_est * 0.82),
        "rinde_max":      round(rinde_est * 1.18),
        "pen_hidrica":    round(pen_total_h_pct, 1),
        "pen_termica":    round(pen_total_t_pct, 1),
        "pen_exceso":     round(pen_total_e_pct, 1),
        "pen_total":      round(pen_total_pct, 1),
        "rinde_potencial": rinde_potencial,
        "detalle":        detalle,
    }


def calcular_rinde_aro(plantas_m2: float, vainas_planta: float,
                        granos_vaina: float, pmg: float) -> dict:
    """
    Estimación de rinde por componentes.
    Fórmula correcta:
      granos/m² = plantas/m² × vainas/planta × granos/vaina
      kg/m²     = granos/m² × PMG(g) / 1.000.000
      kg/ha     = kg/m² × 10.000
      Simplificado: granos/m² × PMG / 100  (÷100, NO ÷100.000)
    """
    if any(v <= 0 for v in [plantas_m2, vainas_planta, granos_vaina, pmg]):
        return {"rinde": 0, "granos_m2": 0, "vainas_m2": 0}

    vainas_m2 = plantas_m2 * vainas_planta
    granos_m2 = vainas_m2  * granos_vaina
    rinde     = round(granos_m2 * pmg / 100)   # ÷100 es correcto

    return {
        "rinde":     rinde,
        "granos_m2": round(granos_m2),
        "vainas_m2": round(vainas_m2),
    }


# ============================================================
#  EQUIVALENCIAS Y TOLERANCIAS POR CULTIVO (Metodología INTA)
# ============================================================

# Granos/m² equivalentes a 100 kg/ha según cultivo
EQUIV_GRANOS = {
    "Soja":  60,   # 60 granos medianos/m² = 100 kg/ha  (PMG ~150g)
    "Maíz":  6,    # 1 grano/m² ≈ 56 kg/ha  → ~6 granos/m² ≈ 100 kg/ha (PMG ~300g)
    "Sorgo": 333,  # PMG ~30g → ~333 granos/m² = 100 kg/ha
}

# Tolerancias máximas de pérdida por cultivo (kg/ha) — fuente INTA
TOLERANCIAS_CULTIVO = {
    "Soja":  {"precosecha": 10, "cabezal": 60, "cola": 20, "total": 80},
    "Maíz":  {"precosecha": 15, "cabezal": 40, "cola": 40, "total": 80},
    "Sorgo": {"precosecha":  5, "cabezal": 30, "cola": 30, "total": 60},
}

# Por defecto (soja) para compatibilidad con código anterior
TOLERANCIAS = TOLERANCIAS_CULTIVO["Soja"]

def _equiv_granos(cultivo: str) -> int:
    return EQUIV_GRANOS.get(cultivo, 60)

def granos_a_kgha(granos: float, area_aro_m2: float, cultivo: str = "Soja") -> float:
    """Convierte granos contados en un aro a kg/ha según cultivo"""
    equiv = _equiv_granos(cultivo)
    granos_por_m2 = granos / area_aro_m2
    return round(granos_por_m2 * 100 / equiv, 1)

def kgha_a_granos(kgha: float, area_aro_m2: float, cultivo: str = "Soja") -> float:
    """Convierte kg/ha a cantidad de granos esperados en un aro según cultivo"""
    equiv = _equiv_granos(cultivo)
    granos_m2 = kgha * equiv / 100
    return round(granos_m2 * area_aro_m2, 1)

def calcular_perdidas_aro_ciego(
    area_aro_m2: float,
    granos_precosecha: float,
    granos_debajo_aro: float,
    granos_sobre_aro: float,
    cultivo: str = "Soja",
) -> dict:
    """
    Metodología INTA — aro ciego. Tolerancias y equivalencias según cultivo.
    Pérdida real cabezal = granos_debajo_aro - granos_precosecha
    """
    tol = TOLERANCIAS_CULTIVO.get(cultivo, TOLERANCIAS_CULTIVO["Soja"])

    pre_kgha    = granos_a_kgha(granos_precosecha, area_aro_m2, cultivo)
    debajo_kgha = granos_a_kgha(granos_debajo_aro, area_aro_m2, cultivo)
    cola_kgha   = granos_a_kgha(granos_sobre_aro,  area_aro_m2, cultivo)

    cabezal_kgha = max(0, round(debajo_kgha - pre_kgha, 1))
    total_maq    = round(cabezal_kgha + cola_kgha, 1)
    total_campo  = round(pre_kgha + total_maq, 1)

    estado_cabezal = "🔴 Supera tolerancia" if cabezal_kgha > tol["cabezal"] else \
                     "🟡 En el límite"       if cabezal_kgha > tol["cabezal"] * 0.8 else \
                     "🟢 Dentro de tolerancia"
    estado_cola    = "🔴 Supera tolerancia" if cola_kgha > tol["cola"] else \
                     "🟡 En el límite"       if cola_kgha > tol["cola"] * 0.8 else \
                     "🟢 Dentro de tolerancia"
    estado_total   = "🔴 Supera tolerancia" if total_maq > tol["total"] else \
                     "🟡 En el límite"       if total_maq > tol["total"] * 0.8 else \
                     "🟢 Dentro de tolerancia"

    tol_granos = {
        "cabezal_aro": kgha_a_granos(tol["cabezal"], area_aro_m2, cultivo),
        "cola_aro":    kgha_a_granos(tol["cola"],    area_aro_m2, cultivo),
        "total_aro":   kgha_a_granos(tol["total"],   area_aro_m2, cultivo),
    }

    diagnostico = _diagnostico_ajustes(cabezal_kgha, cola_kgha,
                                        granos_debajo_aro, granos_sobre_aro, tol)

    return {
        # Resultados en kg/ha
        "pre_kgha":      pre_kgha,
        "cabezal_kgha":  cabezal_kgha,
        "cola_kgha":     cola_kgha,
        "total_maq":     total_maq,
        "total_campo":   total_campo,
        # Estados
        "estado_cabezal": estado_cabezal,
        "estado_cola":    estado_cola,
        "estado_total":   estado_total,
        # Tolerancias de referencia
        "tol_cabezal":   tol["cabezal"],
        "tol_cola":      tol["cola"],
        "tol_total":     tol["total"],
        "tol_granos":    tol_granos,
        # Diagnóstico
        "diagnostico":   diagnostico,
        # Inputs originales
        "area_aro":      area_aro_m2,
        "granos_pre":    granos_precosecha,
        "granos_debajo": granos_debajo_aro,
        "granos_sobre":  granos_sobre_aro,
    }


def _diagnostico_ajustes(cabezal_kg: float, cola_kg: float,
                          granos_debajo: float, granos_sobre: float,
                          tol: dict = None) -> list:
    """
    Genera lista de diagnósticos y ajustes recomendados
    según el nivel y tipo de pérdida.
    """
    if tol is None:
        tol = TOLERANCIAS_CULTIVO["Soja"]
    diag = []

    # ---- CABEZAL ----
    if cabezal_kg > tol["cabezal"]:
        diag.append({
            "zona":     "🔴 Cabezal",
            "problema": f"Pérdida de {cabezal_kg} kg/ha supera tolerancia de {tol['cabezal']} kg/ha",
            "ajustes": [
                "Verificar índice cinemático del molinete: debe girar 15-25% más rápido que la velocidad de avance. Si gira muy rápido desgrana, si gira muy lento empuja las plantas.",
                "Revisar posición del molinete: eje a 15-20 cm por delante de la barra de corte, púas tocando el tercio superior de la planta.",
                "Controlar afilado de cuchillas y registro con los puntones. Cuchillas gastadas 'mastican' el tallo y sacuden las vainas.",
                "Bajar la barra de corte lo más posible (ideal 3-5 cm del suelo) para no dejar vainas bajas en el rastrojo.",
            ]
        })
    elif cabezal_kg > tol["cabezal"] * 0.8:
        diag.append({
            "zona":     "🟡 Cabezal",
            "problema": f"Pérdida de {cabezal_kg} kg/ha cerca del límite ({tol['cabezal']} kg/ha). Monitorear.",
            "ajustes":  ["Verificar velocidad del molinete y altura de corte como medida preventiva."]
        })

    # ---- COLA ----
    if cola_kg > tol["cola"]:
        # Distinguir tipo de grano perdido para orientar ajuste
        diag.append({
            "zona":     "🔴 Cola (trilla/limpieza)",
            "problema": f"Pérdida de {cola_kg} kg/ha supera tolerancia de {tol['cola']} kg/ha",
            "ajustes": [
                "Si encontrás VAINAS ENTERAS sin abrir: aumentar RPM del cilindro/rotor o cerrar la luz del cóncavo (más agresividad de trilla).",
                "Si el grano sale PARTIDO o hay vainas hechas polvo: bajar RPM del cilindro/rotor o abrir la luz del cóncavo (menos agresividad).",
                "Si hay GRANOS SUELTOS Y LIMPIOS: reducir RPM del ventilador (viento excesivo vuela los granos) o abrir aletas del zarandón.",
                "Si el grano en tolva sale SUCIO con palos: aumentar viento o cerrar zaranda inferior para mandar material al retorno.",
            ]
        })
    elif cola_kg > tol["cola"] * 0.8:
        diag.append({
            "zona":     "🟡 Cola",
            "problema": f"Pérdida de {cola_kg} kg/ha cerca del límite ({tol['cola']} kg/ha). Monitorear.",
            "ajustes":  ["Revisar estado del grano en la tolva (si sale partido o limpio) para anticipar el ajuste necesario."]
        })

    if not diag:
        diag.append({
            "zona":     "✅ Máquina dentro de tolerancias",
            "problema": f"Cabezal: {cabezal_kg} kg/ha (tol. {tol['cabezal']}) · Cola: {cola_kg} kg/ha (tol. {tol['cola']})",
            "ajustes":  ["La cosechadora opera correctamente. Mantener monitoreo cada 2-3 horas o ante cambios de condición del cultivo."]
        })

    return diag
