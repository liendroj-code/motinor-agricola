# cultivos/soja.py
NOMBRE = "Soja"
ICONO  = "🌱"
COLOR  = "#34d399"

VARIEDADES = {
    "GM III":     {"gdc":{"VE":55,"VC":110,"V1":180,"V3":310,"V6":480,"R1":580,"R2":660,"R3":760,"R4":870,"R5":980,"R6":1160,"R7":1310,"R8":1450},"fp_critico":14.5,"t_base":10,"t_opt":30,"t_max":45},
    "GM IV":      {"gdc":{"VE":58,"VC":115,"V1":183,"V3":325,"V6":495,"R1":620,"R2":705,"R3":805,"R4":925,"R5":1050,"R6":1235,"R7":1395,"R8":1555},"fp_critico":14.0,"t_base":10,"t_opt":30,"t_max":45},
    "GM V":       {"gdc":{"VE":60,"VC":118,"V1":187,"V3":335,"V6":510,"R1":655,"R2":740,"R3":845,"R4":965,"R5":1100,"R6":1290,"R7":1460,"R8":1630},"fp_critico":13.8,"t_base":10,"t_opt":30,"t_max":45},
    "GM VI Largo":{"gdc":{"VE":65,"VC":130,"V1":200,"V3":350,"V6":550,"R1":700,"R2":780,"R3":880,"R4":1000,"R5":1150,"R6":1350,"R7":1520,"R8":1700},"fp_critico":13.5,"t_base":10,"t_opt":30,"t_max":45},
    "GM VII Medio":{"gdc":{"VE":60,"VC":120,"V1":190,"V3":340,"V6":530,"R1":750,"R2":840,"R3":950,"R4":1080,"R5":1250,"R6":1480,"R7":1660,"R8":1850},"fp_critico":13.0,"t_base":10,"t_opt":30,"t_max":45},
    "GM VIII":    {"gdc":{"VE":62,"VC":122,"V1":192,"V3":345,"V6":535,"R1":800,"R2":895,"R3":1010,"R4":1155,"R5":1350,"R6":1600,"R7":1800,"R8":2000},"fp_critico":12.5,"t_base":10,"t_opt":30,"t_max":45},
}

DESC_ETAPAS = {
    "VE":"Emergencia","VC":"Cotiledones expandidos","V1":"1° hoja trifoliada",
    "V3":"3° nudo","V6":"6° nudo","R1":"Inicio floración 🌸","R2":"Floración plena",
    "R3":"Inicio formación vainas","R4":"Vainas llenas","R5":"Inicio llenado granos ⭐",
    "R6":"Granos llenos","R7":"Madurez fisiológica","R8":"Madurez cosecha 🌾",
}

ETAPAS_CRITICAS = ["R1","R2","R3","R4","R5","R6"]
KY = {"vegetativo":0.20,"R1_R2":0.65,"R3_R4":0.80,"R5_R6":1.00,"R7_R8":0.25}
ETAPAS_RINDE_GDC = {
    "vegetativo":{"min":0,"max":700},"R1_R2":{"min":700,"max":880},
    "R3_R4":{"min":880,"max":1080},"R5_R6":{"min":1080,"max":1415},"R7_R8":{"min":1415,"max":1775},
}
RINDE_POTENCIAL_BASE = 3250
PMG_TIPICO = 150
T_CALOR_CRITICO_FLOR   = 33
T_CALOR_CRITICO_LLENADO = 35
