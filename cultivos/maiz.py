# cultivos/maiz.py
NOMBRE = "Maíz"
ICONO  = "🌽"
COLOR  = "#fbbf24"

VARIEDADES = {
    "Ciclo Corto (90-95 días)": {
        "gdc": {"VE":60,"V3":150,"V6":320,"V10":520,"VT":700,"R1":780,"R2":900,"R3":1050,"R4":1200,"R5":1380,"R6":1550},
        "fp_critico": 99,  # Maíz no es sensible al fotoperíodo de forma crítica
        "t_base": 10, "t_opt": 30, "t_max": 45,
    },
    "Ciclo Intermedio (100-110 días)": {
        "gdc": {"VE":65,"V3":165,"V6":350,"V10":570,"VT":780,"R1":870,"R2":1010,"R3":1180,"R4":1360,"R5":1560,"R6":1750},
        "fp_critico": 99,
        "t_base": 10, "t_opt": 30, "t_max": 45,
    },
    "Ciclo Largo (115-125 días)": {
        "gdc": {"VE":70,"V3":180,"V6":380,"V10":620,"VT":860,"R1":960,"R2":1120,"R3":1310,"R4":1510,"R5":1730,"R6":1950},
        "fp_critico": 99,
        "t_base": 10, "t_opt": 30, "t_max": 45,
    },
}

DESC_ETAPAS = {
    "VE":  "Emergencia",
    "V3":  "3° hoja",
    "V6":  "6° hoja",
    "V10": "10° hoja",
    "VT":  "Floración masculina (espiga) 🌽",
    "R1":  "Floración femenina (estigmas) 🌸",
    "R2":  "Ampolla (grano acuoso)",
    "R3":  "Lechoso",
    "R4":  "Pastoso",
    "R5":  "Dentado ⭐",
    "R6":  "Madurez fisiológica 🌾",
}

ETAPAS_CRITICAS = ["VT","R1","R2","R3"]

# Ky FAO adaptado para maíz
KY = {
    "vegetativo": 0.25,
    "VT_R1":      1.25,  # floración es la etapa MÁS sensible en maíz
    "R2_R3":      0.60,
    "R4_R5":      0.50,
    "R6":         0.20,
}

ETAPAS_RINDE_GDC = {
    "vegetativo": {"min": 0,    "max": 780},
    "VT_R1":      {"min": 780,  "max": 960},
    "R2_R3":      {"min": 960,  "max": 1310},
    "R4_R5":      {"min": 1310, "max": 1730},
    "R6":         {"min": 1730, "max": 1950},
}

RINDE_POTENCIAL_BASE = 8000  # kg/ha — referencia zona pampeana/NOA
PMG_TIPICO = 300              # gramos
T_CALOR_CRITICO_FLOR    = 32  # más sensible que soja en floración
T_CALOR_CRITICO_LLENADO = 35
