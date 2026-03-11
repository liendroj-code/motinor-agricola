# cultivos/sorgo.py
NOMBRE = "Sorgo"
ICONO  = "🌾"
COLOR  = "#f97316"

VARIEDADES = {
    "Sorgo Granífero Ciclo Corto": {
        "gdc": {"VE":55,"V3":140,"V6":290,"V9":460,"IF":580,"H":680,"R1":750,"R2":880,"R3":1020,"R4":1180,"R5":1350},
        "fp_critico": 12.5,  # Sorgo es planta de día corto
        "t_base": 10, "t_opt": 33, "t_max": 44,
    },
    "Sorgo Granífero Ciclo Largo": {
        "gdc": {"VE":60,"V3":155,"V6":320,"V9":510,"IF":650,"H":760,"R1":840,"R2":990,"R3":1150,"R4":1330,"R5":1520},
        "fp_critico": 12.5,
        "t_base": 10, "t_opt": 33, "t_max": 44,
    },
    "Sorgo Forrajero": {
        "gdc": {"VE":50,"V3":130,"V6":270,"V9":430,"IF":550,"H":640,"R1":710,"R2":840,"R3":980,"R4":1130,"R5":1290},
        "fp_critico": 12.0,
        "t_base": 10, "t_opt": 33, "t_max": 44,
    },
}

DESC_ETAPAS = {
    "VE":  "Emergencia",
    "V3":  "3° hoja",
    "V6":  "6° hoja",
    "V9":  "9° hoja",
    "IF":  "Inicio floración (panoja visible)",
    "H":   "Floración plena (antesis) 🌸",
    "R1":  "Grano acuoso",
    "R2":  "Grano lechoso",
    "R3":  "Grano pastoso ⭐",
    "R4":  "Grano harinoso",
    "R5":  "Madurez fisiológica 🌾",
}

ETAPAS_CRITICAS = ["IF","H","R1","R2","R3"]

KY = {
    "vegetativo": 0.20,
    "IF_H":       0.55,
    "R1_R2":      0.45,
    "R3_R4":      0.40,
    "R5":         0.20,
}

ETAPAS_RINDE_GDC = {
    "vegetativo": {"min": 0,    "max": 680},
    "IF_H":       {"min": 680,  "max": 840},
    "R1_R2":      {"min": 840,  "max": 1150},
    "R3_R4":      {"min": 1150, "max": 1350},
    "R5":         {"min": 1350, "max": 1520},
}

RINDE_POTENCIAL_BASE = 5500  # kg/ha
PMG_TIPICO = 30               # gramos (grano pequeño)
T_CALOR_CRITICO_FLOR    = 35  # más tolerante al calor que soja/maíz
T_CALOR_CRITICO_LLENADO = 38
