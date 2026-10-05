import re
import io
import base64
import tempfile
import unicodedata
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="MásOnline | Resumen",
    page_icon="📋",
    layout="wide"
)

APP_CSS = """
    .stApp { background: #ffffff; }
    .block-container { max-width: 1500px; padding: 0 1.2rem 1.2rem; }

    .hero {
        background: #ffffff;
        margin: -1rem -1.2rem 1.2rem;
        padding: 22px 28px;
        color: #20252b;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 4px solid #ff5a1f;
    }
    .hero-brand { font-size: 26px; font-weight: 800; letter-spacing: -.5px; }
    .hero-sub { font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }
    .hero-date { text-align: right; font-size: 15px; font-weight: 700; color:#6b7280; }
    .hero-date small { display: block; font-size: 12px; font-weight: 400; margin-top: 4px; }

    .upload-box {
        background: white; border-radius: 14px; padding: 14px 16px 10px;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.05);
        margin-bottom: 6px; min-height: 74px; border-top: 4px solid #ff5a1f;
    }
    .upload-title { color:#20252b; font-size:13px; font-weight:800; }
    .upload-text { color:#6b7280; font-size:11.5px; margin-top:4px; }

    .section {
        font-size: 19px; font-weight: 800; color: #20252b;
        margin: 26px 0 4px; display:flex; align-items:center; gap:10px;
    }
    .section-desc { color:#6b7280; font-size:12.5px; margin: -2px 0 10px; }

    .badge {
        display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 700;
        padding: 3px 10px; border-radius: 999px; white-space: nowrap;
    }
    .badge.good { background: #e6f5e6; color: #0ca30c; }
    .badge.warning { background: #fdf1d9; color: #c98500; }
    .badge.serious { background: #fdeae1; color: #ec835a; }
    .badge.critical { background: #fbe6e6; color: #d03b3b; }
    .badge.neutral { background: #eef0eb; color: #565d5f; }

    .empty-box {
        background:#fafaf8; border:1px dashed #dfe2db; border-radius:12px;
        padding: 22px; text-align:center; color:#868d8e; font-size:13px; margin-top:8px;
    }

    .resumen-title {
        font-size: 12.5px; font-weight: 800; color:#565d5f; text-transform:uppercase;
        letter-spacing:.04em; margin: 4px 0 6px;
    }
    table.dashtable {
        width: 100%; border-collapse: collapse; font-size: 13px;
        background: white; border-radius: 10px; overflow: hidden;
    }
    table.dashtable thead th {
        background: #20252b; color: #ffffff; text-align: left;
        padding: 9px 12px; font-size: 11.5px; font-weight: 700;
        text-transform: uppercase; letter-spacing: .03em;
        position: sticky; top: 0;
    }
    table.dashtable tbody td {
        padding: 8px 12px; border-bottom: 1px solid #eef0ef; color:#20252b;
    }
    table.dashtable tbody tr:nth-child(even) { background: #fafaf8; }
    table.dashtable tbody tr:hover { background: #fdf1e8; }

    div[data-testid="stDownloadButton"] button {
        background: #ffffff; color: #ff5a1f; border: 1.5px solid #ff5a1f;
        border-radius: 8px; font-size: 12.5px; font-weight: 700; padding: 4px 14px;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: #ff5a1f; color: #ffffff; border-color: #ff5a1f;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #e8ebef; border-radius: 10px; margin-top: 6px;
    }
    div[data-testid="stExpander"] summary {
        background: #f4f5f4; border-radius: 10px; padding: 10px 14px;
    }
    div[data-testid="stExpander"] summary:hover {
        background: #fdeee5;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #20252b !important; font-weight: 800 !important; font-size: 13.5px !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #ff5a1f !important;
    }

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }

    .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin-top: 10px; }
    .kpi {
        background: white; border-radius: 14px; padding: 16px 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06); border: 1px solid #e8ebef;
    }
    .kpi .label { color: #6b7280; font-size: 11.5px; font-weight: 700; text-transform:uppercase; letter-spacing:.04em;}
    .kpi .value { color: #20252b; font-size: 26px; font-weight: 800; margin-top: 6px; }
    .kpi .sub { color: #6b7280; font-size: 12px; margin-top: 6px; }
    .kpi.good .value { color:#0ca30c; }
    .kpi.warn .value { color:#c98500; }
    .kpi.crit .value { color:#d03b3b; }

    a.kpi-link { text-decoration: none; display: block; }
    a.kpi-link .kpi { cursor: pointer; transition: box-shadow .15s, transform .15s; position: relative; }
    a.kpi-link .kpi::after {
        content: "⬇ HTML"; position: absolute; top: 10px; right: 12px;
        font-size: 9.5px; font-weight: 700; color: #ff5a1f; opacity: 0;
        transition: opacity .15s; letter-spacing: .03em;
    }
    a.kpi-link:hover .kpi { box-shadow: 0 6px 18px rgba(0,0,0,.14); transform: translateY(-2px); }
    a.kpi-link:hover .kpi::after { opacity: 1; }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero img { max-width: 170px !important; height: 38px !important; }
        .hero-brand { font-size: 20px; }
        .section { font-size: 16px; margin: 20px 0 4px; }
        table.dashtable { font-size: 12px; }
        table.dashtable thead th, table.dashtable tbody td { padding: 7px 8px; }
        .kpi-row { grid-template-columns: 1fr; gap: 8px; }
        .kpi .value { font-size: 22px; }
    }
"""

st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Helpers — los mismos que en Operativo, para poder leer el mismo
# "Reporte diario.xlsx" (con sus mismas rarezas de formato día a día).
# ---------------------------------------------------------------------

def norm_cols(df):
    df = df.copy()
    df.columns = [str(c).replace("\xa0", " ").strip() for c in df.columns]
    return df

def get_col_ci(df, name):
    """Devuelve la columna que coincide con `name` sin importar mayúsc/minúsc
    (por si el export cambia el casing de una columna de un día a otro).
    Si no la encuentra, devuelve una serie vacía del mismo largo que df."""
    if df is None:
        return pd.Series([], dtype=object)
    for c in df.columns:
        if str(c).strip().lower() == name.lower():
            return df[c]
    return pd.Series([""] * len(df), index=df.index)

def norm_txt(v):
    if pd.isna(v):
        return ""
    return str(v).replace("\xa0", " ").strip()

def norm_codigo(v):
    """Como norm_txt, pero evita que un código (ej. de barras) quede como
    '7790580146115.0' por venir de una columna numérica del Excel."""
    if pd.isna(v):
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return norm_txt(v)

def kpi_card(label, value, sub, cls=""):
    # Todo en una sola línea (sin \n): un f-string multilínea acá hace que
    # Streamlit interprete la 2da tarjeta en adelante como bloque de código
    # (indentado + precedido de línea en blanco) en vez de HTML.
    return (
        '<div class="kpi ' + cls + '">'
        '<div class="label">' + str(label) + '</div>'
        '<div class="value">' + str(value) + '</div>'
        '<div class="sub">' + str(sub) + '</div>'
        '</div>'
    )

# ---------------------------------------------------------------------
# Tipificaciones de Reclamos (misma lógica que Operativo): cada tipo de
# reclamo es "Operativo" (problema del sector Ecom) o "No operativo" (otro
# problema, ajeno a Ecom). El Top 5 tiendas y el ranking por tipo de este
# resumen solo cuentan los reclamos Operativos.
# ---------------------------------------------------------------------
TIPIFICACIONES_OPS = {
    "cobrado no entregado": "Operativo",
    "producto equivocado": "Operativo",
    "producto danado gm": "No operativo",
    "fuera de fecha y hora": "Operativo",
    "disconformidad con criterio de sustitucion": "Operativo",
    "producto vencido / danado / mal estado": "Operativo",
    "faltante de partes y piezas": "Operativo",
    "reclamo factura a": "Operativo",
    "otros": "No operativo",
    "anulaciones desde tienda": "Operativo",
    "faltante de comprobante de pago": "Operativo",
    "reagendamiento desde tienda": "Operativo",
    "devolucion no aplicada fiserv": "No operativo",
    "devolucion no aplicada mercadopago": "No operativo",
    "mala actitud ecommerce": "Operativo",
    "problema con cupon": "No operativo",
    "problema sitio web": "No operativo",
    "diferencia de precio entre pedido y facturado": "No operativo",
    "descuento bancario no aplicado": "No operativo",
    "errores con medios de pago": "No operativo",
    "errores masivos": "No operativo",
    "solicitud de reagendamiento": "No operativo",
    "solicitud de cambio o devolucion": "No operativo",
    "servicio tecnico": "No operativo",
    "solicitud de anulacion o boton de arrepentimiento": "No operativo",
    "solicitud de tercero autorizado": "No operativo",
    "solicitud de factura a": "No operativo",
    "anulacion o disconformidad por falta de stock": "Operativo",
    "pedido equivocado": "Operativo",
    "anulacion o demora por validacion": "No operativo",
    "devolucion no aplicada modo": "No operativo",
    "devolucion de cobro de envases de cerveza": "Operativo",
}

# Alias para variantes de redacción que aparecen en el export real de
# Reclamos pero no coinciden letra a letra con "Nombre de la tipificacion"
# del archivo de referencia (plural/singular, con o sin "Solicitud de").
_TIPIFICACION_ALIASES = {
    "devolucion no aplicada mercado pago": "devolucion no aplicada mercadopago",
    "anulacion o demoras por validacion": "anulacion o demora por validacion",
    "problemas con cupon": "problema con cupon",
    "factura a": "reclamo factura a",
    "3ero autorizado": "solicitud de tercero autorizado",
    "3ro autorizado": "solicitud de tercero autorizado",
    "reagendamiento cd/proveedor": "solicitud de reagendamiento",
}

def _norm_tipificacion(v):
    """Normaliza un 'Tipo' de reclamo para buscarlo en TIPIFICACIONES_OPS.
    El export de Reclamos trae el 'Tipo' como ruta completa separada por
    '|' (ej. 'Stock de tienda|Reclamo Stock|Cobrado no entregado') — acá
    nos quedamos con el último tramo, que es la tipificación en sí.
    También colapsa espacios alrededor de '/' (ej. 'vencido/dañado' vs
    'vencido / dañado'), minúsculas y sin acentos."""
    s = norm_txt(v)
    if "|" in s:
        s = s.split("|")[-1]
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\s*/\s*", "/", s)
    return " ".join(s.split())

_TIPIFICACIONES_NORM = {_norm_tipificacion(k): v for k, v in TIPIFICACIONES_OPS.items()}

def clasificar_tipo_reclamo(tipo):
    """'Operativo' / 'No operativo' según la tipificación, o 'Sin clasificar'
    si el tipo no está en la lista (para que se vea en vez de asumir mal)."""
    key = _norm_tipificacion(tipo)
    key = _TIPIFICACION_ALIASES.get(key, key)
    return _TIPIFICACIONES_NORM.get(key, "Sin clasificar")

TIENDA_ALIASES = {
    "grafa": "Constituyentes",
}

def strip_sucursal(v):
    s = norm_txt(v)
    s = re.sub(r"(?i)^sucursal\s+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    alias = TIENDA_ALIASES.get(s.lower())
    if alias:
        return alias
    return s

def fold_tienda_key(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()

# Código de tienda (columna "warehouseName" del archivo de Faltantes, cuando
# viene como número, ej. "Inv-Full-1006") -> nombre. Mismo listado que se usa
# en "app", "Productividad Pickers" y Operativo.
TIENDA_CODE_MAP = {
    "1002": "Rio IV", "1003": "San Luis", "1004": "San Fernando", "1005": "Las Heras",
    "1006": "San Juan", "1007": "La Rioja", "1008": "Corrientes", "1010": "Córdoba Sur",
    "1011": "Salta", "1012": "Santiago", "1013": "Tigre", "1014": "Lujan",
    "1015": "Maipú", "1016": "Avellaneda 2", "1017": "La Tablada", "1018": "Quilmes",
    "1020": "Tucumán", "1021": "Neuquén 2", "1022": "Bariloche", "1023": "La Pampa",
    "1024": "Formosa", "1026": "Catamarca", "1027": "Mataderos", "1028": "Alte Brown",
    "1029": "Moreno", "1030": "José C Paz", "1031": "Jujuy", "1032": "Malvinas Arg",
    "1033": "Rio Salí", "1035": "3 de Febrero", "1036": "Moreno Shopping", "1037": "San Martin",
    "1038": "Cipolletti", "1039": "Paraná 2", "1042": "Trelew", "1043": "Laferrere",
    "1044": "Hurlingham (AV, Villegas)", "1045": "Hurlingham (AV, Vergara)", "1046": "Pergamino",
    "1050": "Lanús", "1051": "Posadas", "1052": "Oran", "1053": "Viedma",
    "1054": "Olavarría", "1055": "Villa Mercedes", "1056": "Villa Nueva",
    "1057": "Comodoro Rivadavia", "1058": "Resistencia", "1059": "Gonzalez Catán",
    "1060": "Fuerza Aérea (Cba)", "1061": "Junín", "1067": "San Martín (Mza)",
    "1068": "Palmares (Mza)", "1069": "STS", "1074": "Goya (Ctes)",
    "1075": "Salta Fuerza Aérea", "1076": "Lomas de Zamora", "1077": "Gral Pico (La Pampa)",
    "1078": "Salta Tartagal", "1080": "Santiago del Estero Sur", "1081": "Rawson San Juan",
    "1082": "Tucumán (Av, Jujuy)", "1084": "San Vicente", "1085": "Corrientes (Av, Maipú)",
    "1086": "Formosa II", "1087": "Pilar", "1088": "Tuc, Concepción", "1092": "San Juan Norte",
    "1093": "Comodoro Rivadavia Norte", "1096": "Caseros", "1097": "Donato Alvarez (Cba)",
    "1098": "R,S, Peña, Chaco", "1099": "Posadas II", "1100": "Santa Rosa (La Pampa) II",
    "1106": "Tuc, Ejército Del Norte", "1108": "Puerto Madryn", "1110": "Claypole",
    "1111": "San Pedro de Jujuy", "1114": "Clorinda", "1115": "General Roca",
    "1116": "Moron", "1119": "Moreno Derqui", "2997": "Constituyentes", "2998": "San Justo",
    "2999": "Avellaneda", "3601": "La Plata", "3602": "Bahía Blanca", "3603": "Santa Fe",
    "3604": "Paraná", "3605": "Córdoba Oeste", "3606": "Córdoba Este", "3608": "Neuquén",
    "3613": "Mendoza", "4001": "Campana",
}

WAREHOUSE_NAME_ALIASES = {
    "larioja": "La Rioja",
}

_WAREHOUSE_PREFIX_RE = re.compile(r"(?i)^inv-(fullgm|full|mg|pp)-")

def warehouse_to_tienda(v):
    """El archivo de Faltantes mensual trae el depósito como
    'Inv-Full-San Fernando', 'inv-fullgm-viedma', 'Inv-Full-1006' (código),
    etc. en vez del nombre de tienda tal cual. Le saca el prefijo técnico y
    lo deja como nombre de tienda; strip_sucursal/apply_tienda_canon
    terminan de unificarlo con la ortografía que ya usan las demás hojas."""
    s = norm_txt(v)
    s = _WAREHOUSE_PREFIX_RE.sub("", s)
    s = re.sub(r"[-_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return s
    if s.isdigit():
        return TIENDA_CODE_MAP.get(s, s)
    alias = WAREHOUSE_NAME_ALIASES.get(s.lower())
    if alias:
        return alias
    return s.title()

def clean_shipping_location(v):
    """El archivo de Pedidos trae 'shippingLocationName', que casi siempre
    ya es el nombre de tienda legible (ej. 'Sucursal San Justo', alguna vez
    con la errata 'Sucurcal'), a veces con un código de depósito pegado al
    final (ej. 'Sucursal Tucuman 1020'). Devuelve '' si no había nada útil,
    para que warehouse_to_tienda(shippingWarehouseName) sirva de respaldo."""
    s = norm_txt(v)
    if not s:
        return ""
    s = re.sub(r"(?i)^sucur[sc]al\s+", "", s)
    s = re.sub(r"\s+\d{3,6}$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_pedidos_monto(v):
    """El archivo de Pedidos trae el monto como '$122014.84' (punto decimal,
    sin separador de miles) — a diferencia del '$46K' del Reporte diario de
    siempre, que sí espera la notación argentina que usa ar_number(). Lo
    dejamos como número de una — ar_number() más abajo, al recibir ya un
    número, lo deja pasar tal cual."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = norm_txt(v).replace("$", "").replace(" ", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

# Mapa Tienda -> Auditor (el mismo que en Operativo). Pendiente de confirmar
# con Emi: "Comodoro Rivadavia" / "Comodoro Rivadavia Norte" y "R.S. Peña,
# Chaco" — hasta aclararlo, esas tiendas no muestran auditor.
AUDITOR_MAP = {
    "3 de febrero": "Pedro",
    "alte brown": "Nicolas",
    "avellaneda": "Nicolas",
    "bahia blanca": "Nicolas",
    "bariloche": "Nicolas",
    "campana": "Nicolas",
    "caseros": "Nicolas",
    "catamarca": "German",
    "cipolletti": "Nicolas",
    "claypole": "German",
    "clorinda": "Pedro",
    "constituyentes": "German",
    "cordoba este": "German",
    "cordoba oeste": "German",
    "cordoba sur": "German",
    "corrientes": "Pedro",
    "corrientes av. maipu": "Pedro",
    "donato alvarez": "German",
    "formosa": "Pedro",
    "formosa 2": "Pedro",
    "fuerza aerea cba.": "German",
    "fuerza aerea salta": "Pedro",
    "general roca": "Nicolas",
    "gonzalez catan": "Pedro",
    "goya": "Pedro",
    "gral pico": "Nicolas",
    "guaymallen": "German",
    "hc avellaneda 2": "German",
    "hurlingham vergara": "Pedro",
    "hurlingham villegas": "Pedro",
    "jose c paz": "Pedro",
    "jujuy": "Pedro",
    "junin": "Nicolas",
    "la pampa": "Nicolas",
    "la plata": "Pedro",
    "la rioja": "German",
    "laferrere": "Pedro",
    "lanus": "Nicolas",
    "las heras": "German",
    "lomas de zamora": "Nicolas",
    "lujan": "Nicolas",
    "maipu": "German",
    "malvinas": "Nicolas",
    "mataderos": "Pedro",
    "moreno": "Pedro",
    "moreno derqui": "Pedro",
    "moreno shopping": "Pedro",
    "moron": "Nicolas",
    "neuquen": "Nicolas",
    "neuquen 2": "Nicolas",
    "olavarria": "Nicolas",
    "oran": "Pedro",
    "palmares": "German",
    "parana": "German",
    "parana 2": "German",
    "pergamino": "Nicolas",
    "pilar": "Pedro",
    "posadas": "Pedro",
    "posadas 2": "Pedro",
    "puerto madryn": "Nicolas",
    "quilmes": "Nicolas",
    "rawson san juan": "German",
    "resistencia": "Pedro",
    "rio cuarto": "German",
    "rio sali": "Pedro",
    "salta": "Pedro",
    "san fernando": "German",
    "san juan": "German",
    "san juan norte": "German",
    "san justo": "Pedro",
    "san luis": "German",
    "san martin": "German",
    "san martin mendoza": "German",
    "san pedro jujuy": "Pedro",
    "san vicente": "Nicolas",
    "santa fe": "German",
    "santa rosa": "Nicolas",
    "santiago": "Pedro",
    "santiago del estero sur": "Pedro",
    "tablada": "Pedro",
    "tartagal": "Pedro",
    "tigre": "Nicolas",
    "trelew": "Nicolas",
    "tucuman": "Pedro",
    "tucuman av. jujuy": "Pedro",
    "tucuman concepcion": "Pedro",
    "tucuman ejercito nor.": "Pedro",
    "viedma": "Nicolas",
    "villa mercedes": "German",
    "villa nueva": "German",
}

def get_auditor(tienda):
    """Devuelve el auditor/coordinador de una tienda ya canonicalizada, o
    None si no lo tenemos mapeado."""
    return AUDITOR_MAP.get(fold_tienda_key(norm_txt(tienda)))

def build_tienda_canon_map(dfs):
    from collections import Counter
    counts = {}
    for d in dfs:
        if d is None or "Tienda" not in d.columns:
            continue
        for v in d["Tienda"]:
            s = strip_sucursal(v)
            if not s:
                continue
            key = fold_tienda_key(s)
            counts.setdefault(key, Counter())[s] += 1
    return {key: c.most_common(1)[0][0] for key, c in counts.items()}

def apply_tienda_canon(d, canon_map):
    if d is None or "Tienda" not in d.columns:
        return d
    d = d.copy()
    d["Tienda"] = d["Tienda"].apply(strip_sucursal).apply(
        lambda s: canon_map.get(fold_tienda_key(s), s)
    )
    return d

def ar_number(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = norm_txt(v)
    if not s:
        return 0.0
    token = s.split(" ")[0]
    token = token.replace("$", "")
    mult = 1.0
    if token.upper().endswith("K"):
        mult = 1_000.0
        token = token[:-1]
    elif token.upper().endswith("M"):
        mult = 1_000_000.0
        token = token[:-1]
    token = token.replace("%", "")
    token = token.replace(".", "").replace(",", ".")
    try:
        return float(token) * mult
    except ValueError:
        return 0.0

def ar_pct(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = norm_txt(v)
    if not s:
        return None
    token = s.split(" ")[0].replace("%", "").strip()
    try:
        return float(token)
    except ValueError:
        return None

def find_sheet(xl, required_cols):
    required = {c.lower() for c in required_cols}
    for name in xl.sheet_names:
        try:
            df = xl.parse(name)
        except Exception:
            continue
        df = norm_cols(df)
        cols = {c.lower() for c in df.columns}
        if required.issubset(cols):
            return name, df
    return None, None

def safe_open_excel(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return pd.ExcelFile(uploaded_file)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return None

# ---------------------------------------------------------------------
# Guardado compartido: usa el mismo archivo que se sube en la pestaña
# Operativo (y viceversa), para que cualquiera que entre con el link vea
# el último reporte subido sin tener que subir nada. Además de la copia
# local (rápida), cada reporte queda guardado en GitHub (carpeta
# shared_uploads/), así que aunque Streamlit reinicie la app por
# inactividad o por una actualización, el último reporte sigue disponible
# y no hace falta volver a subirlo.
# ---------------------------------------------------------------------

SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_DIR.mkdir(parents=True, exist_ok=True)
SHARED_REPORTE_PATH = SHARED_DIR / "reporte_diario.xlsx"
SHARED_FALTANTES_PATH = SHARED_DIR / "faltantes.xlsx"
SHARED_PEDIDOS_PATH = SHARED_DIR / "pedidos.xlsx"
SHARED_RECLAMOS_PATH = SHARED_DIR / "reclamos.xlsx"

def _github_headers():
    token = st.secrets.get("GITHUB_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Masonline-Dashboard",
    }

def fetch_shared_from_github(shared_path):
    """Trae de GitHub la última copia guardada de este reporte (para cuando
    el servidor se reinició y la copia local temporal ya no está)."""
    headers = _github_headers()
    if not headers:
        return None
    import urllib.request
    import json
    import base64
    repo = "2026-Masonline/masonline-dashboard"
    branch = "main"
    repo_path = f"shared_uploads/{shared_path.name}"
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}?ref={branch}"
    try:
        request_get = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request_get, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return base64.b64decode(data["content"])
    except Exception:
        return None

def get_shared_bytes(uploaded_file, shared_path):
    """Esta pestaña no tiene uploader propio (siempre se llama con
    uploaded_file=None): lee el último reporte subido en la pestaña "app",
    primero de la copia local y, si no está (reinicio del servidor), de
    GitHub (donde queda guardado para siempre)."""
    if uploaded_file is not None:
        data = uploaded_file.getvalue()
        try:
            shared_path.write_bytes(data)
        except Exception:
            pass
        return data, True
    if shared_path.exists():
        try:
            return shared_path.read_bytes(), False
        except Exception:
            pass
    content = fetch_shared_from_github(shared_path)
    if content is not None:
        try:
            shared_path.write_bytes(content)
        except Exception:
            pass
        return content, False
    return None, False

def load_section_from_xl(xl, required_cols, required=True):
    if xl is None:
        return None
    name, df = find_sheet(xl, required_cols)
    if df is None:
        if required:
            st.error(
                "No encontré una hoja con las columnas esperadas "
                f"({', '.join(required_cols)}) en el archivo subido."
            )
        return None
    return df

def load_section(uploaded_file, required_cols):
    return load_section_from_xl(safe_open_excel(uploaded_file), required_cols)

def _fr_read_positional(xl, sheet_name):
    try:
        raw = xl.parse(sheet_name, header=None)
    except Exception:
        return None
    if raw.shape[1] < 6 or not len(raw):
        return None
    raw = raw.iloc[:, :6].copy()
    first_cell = re.sub(r"[▾▼▲]+\s*$", "", norm_txt(raw.iloc[0, 0])).strip()
    if fold_tienda_key(first_cell) == "tienda":
        raw = raw.iloc[1:].reset_index(drop=True)
    if not len(raw):
        return None
    raw.columns = [f"col{i}" for i in range(raw.shape[1])]
    return raw

def _fr_headerless_candidate(xl, sheet_name):
    raw = _fr_read_positional(xl, sheet_name)
    if raw is None:
        return None
    first_col = raw.iloc[:, 0].apply(norm_txt).apply(
        lambda s: re.sub(r"[▾▼▲]+\s*$", "", s).strip()
    )
    if not first_col.str.upper().isin(["TOTAL", "TOTA"]).any():
        return None
    last_col = raw.iloc[:, 5].apply(norm_txt)
    pct_like = last_col.str.contains("%", na=False)
    if pct_like.mean() < 0.5:
        return None
    return raw

def load_fr_from_xl(xl):
    if xl is None:
        return None
    name, df = find_sheet(xl, ["Tienda", "FR", "Limpio"])
    if df is not None:
        return df
    named = [s for s in xl.sheet_names if "fr" in s.lower()]
    for sheet_name in named:
        raw = _fr_read_positional(xl, sheet_name)
        if raw is not None:
            return raw
    for sheet_name in xl.sheet_names:
        if sheet_name in named:
            continue
        raw = _fr_headerless_candidate(xl, sheet_name)
        if raw is not None:
            return raw
    st.error(
        "No encontré una hoja con las columnas esperadas (Tienda, FR, Limpio) "
        "en el archivo subido."
    )
    return None

def load_cancelados_from_xl(xl, required=True):
    """required=False porque los cancelados ahora salen del archivo de
    Pedidos — esta hoja del Reporte diario puede faltar sin que sea error."""
    if xl is None:
        return None
    named = [s for s in xl.sheet_names if "cancel" in s.lower()]
    for sheet_name in named:
        try:
            df = xl.parse(sheet_name)
        except Exception:
            continue
        df = norm_cols(df)
        cols = {c.lower() for c in df.columns}
        if {"pedido", "tienda", "fecha", "estado"}.issubset(cols):
            return df
    name, df = find_sheet(xl, ["Pedido", "Tienda", "Fecha", "Estado", "Total $"])
    if df is not None:
        return df
    if required:
        st.error(
            "No encontré una hoja con las columnas esperadas "
            "(Pedido, Tienda, Fecha, Estado, Total $) en el archivo subido."
        )
    return None

def load_reclamos_from_xl(xl, required=True):
    if xl is None:
        return None
    name, df = find_sheet(xl, ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha"])
    if df is not None:
        return df
    raw_cols = ["displayId", "typeName", "orderCommerceSequentialId", "storeName", "statusName", "dateCreated"]
    name, raw = find_sheet(xl, raw_cols)
    if raw is None:
        if required:
            st.error(
                "No encontré una hoja con las columnas esperadas de Reclamos "
                "(Reclamo/Pedido/Tienda/Tipo/Estado/Fecha, o el export crudo con "
                "displayId/typeName/orderCommerceSequentialId/storeName/statusName/dateCreated) "
                "en el archivo subido."
            )
        return None
    raw = raw[raw["typeName"].apply(norm_txt).str.lower().str.contains("reclamo", na=False)].copy()
    return pd.DataFrame({
        "Reclamo": raw["displayId"].apply(norm_txt),
        # norm_codigo (no int() a secas): la mayoría son ids numéricos, pero
        # algunos pedidos con más de un reclamo vienen con sufijo, ej.
        # "11404682-1", y forzar int() ahí rompía toda la carga.
        "Pedido": raw["orderCommerceSequentialId"].apply(norm_codigo),
        "Tienda": raw["storeName"].apply(norm_txt),
        "Tipo": raw["typeName"].apply(norm_txt),
        "Estado": raw["statusName"].apply(norm_txt),
        "Fecha": pd.to_datetime(raw["dateCreated"], format="%d/%m/%Y %H:%M:%S", errors="coerce"),
    })

def money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "$0"
    return f"${v:,.0f}".replace(",", ".")

def pct1(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:.1f}%".replace(".", ",")

def table_html(df):
    """Va envuelta en un contenedor con scroll horizontal para que en el
    celular, si la tabla no entra en el ancho de la pantalla, se pueda
    desplazar en vez de romper el diseño de la página."""
    inner = df.to_html(escape=False, index=False, classes="dashtable", border=0)
    return f'<div class="table-scroll">{inner}</div>'

def resumen_table_html(agg, label_col, col_formatters):
    """Tabla de ranking simple (sin fila de total — acá lo que importa es el
    orden, no la suma)."""
    cols = list(col_formatters.keys())
    thead = "".join(f"<th>{c}</th>" for c in [label_col] + cols)
    body_rows = []
    for _, r in agg.iterrows():
        tds = f"<td>{r[label_col]}</td>" + "".join(
            f"<td>{col_formatters[c](r[c])}</td>" for c in cols
        )
        body_rows.append(f"<tr>{tds}</tr>")
    inner = (
        '<table class="dashtable"><thead><tr>' + thead + '</tr></thead>'
        '<tbody>' + "".join(body_rows) + '</tbody></table>'
    )
    return f'<div class="table-scroll">{inner}</div>'

def section_block(title, desc, body_html):
    if not body_html:
        return ""
    return (
        f'<div class="section">{title}</div>'
        f'<div class="section-desc">{desc}</div>'
        f'{body_html}<div style="height:8px;"></div>'
    )

def export_resumen_html(now_ref, sections):
    corte_html = ""
    if now_ref is not None:
        corte_html = (
            '<div class="hero-date">Corte del reporte<br>'
            f'<small>{now_ref.strftime("%d/%m/%Y %H:%M")}</small></div>'
        )
    blocks_html = "".join(
        section_block(title, desc, body) for title, desc, body in sections if body
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>MásOnline · Resumen</title>
<style>
{APP_CSS}
body {{ margin:0; background:#fafaf8; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }}
.wrap {{ max-width: 1400px; margin: 0 auto; padding: 0 20px 28px; }}
</style>
</head>
<body>
<div class="hero">
  <div>
    <div class="hero-brand">📋 Resumen</div>
    <div class="hero-sub">RANKING DE TIENDAS — TOP 5</div>
  </div>
  {corte_html}
</div>
<div class="wrap">
{blocks_html}
</div>
</body>
</html>"""

def export_section_html(now_ref, section_title, section_desc, body_html):
    """Arma un HTML standalone (con el mismo look del panel) para descargar
    una sola sección — usado para el detalle que se baja clickeando una
    tarjeta KPI en vez de mostrarse en pantalla."""
    if not body_html:
        return None
    corte_html = ""
    if now_ref is not None:
        corte_html = (
            '<div class="hero-date">Corte del reporte<br>'
            f'<small>{now_ref.strftime("%d/%m/%Y %H:%M")}</small></div>'
        )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>MásOnline · {section_title}</title>
<style>
{APP_CSS}
body {{ margin:0; background:#fafaf8; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }}
.wrap {{ max-width: 1400px; margin: 0 auto; padding: 0 20px 28px; }}
</style>
</head>
<body>
<div class="hero">
  <div>
    <div class="hero-brand">📋 Resumen</div>
    <div class="hero-sub">{section_title.upper()}</div>
  </div>
  {corte_html}
</div>
<div class="wrap">
{section_block(section_title, section_desc, body_html)}
</div>
</body>
</html>"""

def kpi_link_wrap(inner_html, html_doc, filename):
    """Envuelve una tarjeta KPI en un link que descarga el HTML de esa
    sección al clickearla (en vez de mostrar el detalle abajo en pantalla)."""
    if not html_doc:
        return inner_html
    b64 = base64.b64encode(html_doc.encode("utf-8")).decode("utf-8")
    return (
        f'<a class="kpi-link" href="data:text/html;base64,{b64}" download="{filename}" '
        'title="Descargar el detalle como HTML">' + inner_html + '</a>'
    )

def slug_filename(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s or "archivo"

# ---------------------------------------------------------------------
# Header — esta página no tiene uploaders propios: siempre muestra el
# último "Reporte diario.xlsx" y Faltantes que se hayan subido en la
# pestaña app (mismo archivo compartido, ver get_shared_bytes).
# ---------------------------------------------------------------------

st.markdown("""
<div class="hero">
  <div>
    <div class="hero-brand">📋 Resumen</div>
    <div class="hero-sub">RANKING DE TIENDAS — TOP 5</div>
  </div>
</div>
""", unsafe_allow_html=True)

reporte_bytes, _ = get_shared_bytes(None, SHARED_REPORTE_PATH)
faltantes_bytes, _ = get_shared_bytes(None, SHARED_FALTANTES_PATH)
pedidos_bytes, _ = get_shared_bytes(None, SHARED_PEDIDOS_PATH)
reclamos_bytes, _ = get_shared_bytes(None, SHARED_RECLAMOS_PATH)

if reporte_bytes is not None or faltantes_bytes is not None or pedidos_bytes is not None or reclamos_bytes is not None:
    st.markdown(
        '<div style="font-size:11.5px;color:#0ca30c;font-weight:700;margin:-2px 0 10px;">'
        '● Mostrando el último reporte subido en la pestaña app — no hace falta subir nada acá.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown("""
    <div style="background:white;border:1px solid #e8ebef;border-radius:12px;
    padding:12px 16px;margin-bottom:14px;">
      <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
        TODAVÍA NO HAY DATOS CARGADOS
      </div>
      <div style="font-size:12px;color:#6b7280;">
        Subí "Pedidos", "Reclamos Operativos" y el archivo de Faltantes en la pestaña
        <b>app</b>. Esta página va a mostrar el Top 5 automáticamente con esos mismos datos.
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Parse (misma lógica que Operativo)
# ---------------------------------------------------------------------

now_ref = None

xl_reporte = safe_open_excel(io.BytesIO(reporte_bytes)) if reporte_bytes is not None else None
# "Pedido" adentro del Reporte diario: se deja de requerir (required=False)
# porque Pedidos ahora se sube en su propio archivo aparte, así que esta
# hoja puede faltar sin que sea un error — queda solo como respaldo mientras
# se termina de migrar.
df_72h_raw = load_section_from_xl(xl_reporte, ["Pedido", "Tienda", "Fecha", "Estado", "Monto"], required=False)
xl_reclamos = safe_open_excel(io.BytesIO(reclamos_bytes)) if reclamos_bytes is not None else None
df_reclamos_raw = load_reclamos_from_xl(xl_reclamos)
if df_reclamos_raw is None:
    # Todavía no se subió el archivo nuevo de Reclamos Operativos (aparte) —
    # por ahora seguimos leyendo la hoja vieja del Reporte diario, si está.
    df_reclamos_raw = load_reclamos_from_xl(xl_reporte, required=False)
df_ontime_raw = load_section_from_xl(xl_reporte, ["Tienda", "Pedifod", "Fuera", "ONTIME"])
df_fr_raw = load_fr_from_xl(xl_reporte)
df_cancelados_raw = load_cancelados_from_xl(xl_reporte, required=False)
xl_faltantes = safe_open_excel(io.BytesIO(faltantes_bytes)) if faltantes_bytes is not None else None
df_faltantes_raw = load_section_from_xl(
    xl_faltantes,
    ["warehouseName", "refName", "missingQuantity", "substitutedQuantity", "noSubstitutedQuantity"]
)
xl_pedidos = safe_open_excel(io.BytesIO(pedidos_bytes)) if pedidos_bytes is not None else None
df_pedidos_raw = load_section_from_xl(
    xl_pedidos,
    ["commerceId", "commerceDateCreated", "deliveryFinishDate", "status", "totalAmount", "shippingWarehouseName"],
    required=False
)

candidate_times = []

pedidos_72h = None
if df_pedidos_raw is not None:
    # Archivo nuevo de Pedidos (export "order-operation"): mismo esquema
    # Pedido/Tienda/Fecha/Estado/Monto que ya usa el resto de esta sección
    # (misma lógica que en Operativo).
    d = df_pedidos_raw.copy()
    d["Pedido"] = d.get("commerceId", "").apply(norm_txt)
    tienda_loc = d.get("shippingLocationName", "").apply(clean_shipping_location)
    tienda_wh = d.get("shippingWarehouseName", "").apply(warehouse_to_tienda)
    d["Tienda"] = tienda_loc.where(tienda_loc.astype(bool), tienda_wh)
    d["Estado"] = d.get("status", "").apply(norm_txt)
    d["Monto"] = d.get("totalAmount").apply(parse_pedidos_monto)
    fecha_creacion = pd.to_datetime(d.get("commerceDateCreated"), errors="coerce")
    # "Sin mover +72h" se mide contra el FIN de la ventana de entrega
    # prometida (deliveryFinishDate), no contra la fecha del pedido (misma
    # lógica que en Operativo). Los cancelados se sacan de acá y van a la
    # sección de Cancelados aparte (más abajo).
    d["Fecha"] = pd.to_datetime(d.get("deliveryFinishDate"), errors="coerce")
    d = d[~d["Estado"].astype(str).str.lower().isin(["delivered", "canceled", "cancelled"])]
    d = d.dropna(subset=["Fecha"])
    if fecha_creacion.notna().any():
        candidate_times.append(fecha_creacion.max())
    pedidos_72h = d[["Pedido", "Tienda", "Fecha", "Estado", "Monto"]]
elif df_72h_raw is not None:
    d = df_72h_raw.copy()
    d = d[~d["Estado"].astype(str).str.lower().isin(["delivered", "canceled", "cancelled"])]
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    pedidos_72h = d

reclamos = None
if df_reclamos_raw is not None:
    d = df_reclamos_raw.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    reclamos = d

cancelados = None
if df_pedidos_raw is not None:
    # Los cancelados del archivo nuevo de Pedidos (separados de "sin
    # mover +72h" más arriba) van a esta sección (misma lógica que en
    # Operativo).
    d = df_pedidos_raw.copy()
    d = d[d.get("status", "").apply(norm_txt).str.lower().isin(["canceled", "cancelled"])].copy()
    d["Pedido"] = d.get("commerceId", "").apply(norm_txt)
    tienda_loc = d.get("shippingLocationName", "").apply(clean_shipping_location)
    tienda_wh = d.get("shippingWarehouseName", "").apply(warehouse_to_tienda)
    d["Tienda"] = tienda_loc.where(tienda_loc.astype(bool), tienda_wh)
    d["Fecha"] = pd.to_datetime(d.get("commerceDateCreated"), errors="coerce")
    d["Estado"] = d.get("status", "").apply(norm_txt)
    d["Monto"] = d.get("totalAmount").apply(parse_pedidos_monto)
    d = d.dropna(subset=["Fecha"])
    if len(d):
        candidate_times.append(d["Fecha"].max())
    cancelados = d[["Pedido", "Tienda", "Fecha", "Estado", "Monto"]]
elif df_cancelados_raw is not None:
    d = df_cancelados_raw.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    cancelados = d

if candidate_times:
    valid = [t for t in candidate_times if pd.notna(t)]
    now_ref = max(valid) if valid else None
if now_ref is None:
    now_ref = pd.Timestamp(datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None))

# ---- Pedidos +72h ----
if pedidos_72h is not None:
    pedidos_72h["Dias"] = (now_ref - pedidos_72h["Fecha"]).dt.total_seconds() / 86400
    pedidos_72h = pedidos_72h[pedidos_72h["Dias"] >= 3].copy()
    pedidos_72h["MontoNum"] = pedidos_72h["Monto"].apply(ar_number)
    pedidos_72h["Tienda"] = pedidos_72h["Tienda"].apply(norm_txt)

# ---- Reclamos ----
if reclamos is not None:
    reclamos["Horas"] = (now_ref - reclamos["Fecha"]).dt.total_seconds() / 3600
    reclamos["Tienda"] = reclamos["Tienda"].apply(norm_txt)
    reclamos["Estado"] = reclamos["Estado"].apply(norm_txt)
    reclamos["Tipo"] = reclamos["Tipo"].apply(norm_txt)

# ---- On Time Preparación ----
ontime_prepa = None
if df_ontime_raw is not None:
    d = df_ontime_raw.copy()
    for c in ["Pedifod", "Fuera"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
        else:
            d[c] = 0
    d["Tienda"] = d["Tienda"].apply(norm_txt)
    d = d[~d["Tienda"].str.upper().isin(["TOTAL", "TOTA"])]
    d = d.rename(columns={"Pedifod": "Pedidos"})
    if "ONTIME" in d.columns:
        ontime_parsed = d["ONTIME"].apply(ar_pct)
    else:
        ontime_parsed = pd.Series([None] * len(d), index=d.index)
    ontime_raw = ontime_parsed.astype(float).fillna(0.0)
    valid_max = ontime_parsed.dropna().max() if ontime_parsed.notna().any() else 0
    d["OntimePct"] = ontime_raw * 100 if (pd.notna(valid_max) and valid_max <= 1.5) else ontime_raw
    ontime_prepa = d[["Tienda", "Pedidos", "Fuera", "OntimePct"]].copy()

# ---- Fill Rate ----
fill_rate = None
if df_fr_raw is not None:
    d = df_fr_raw.copy()
    fr_cols = list(d.columns)
    unidades_plus_col = "Unidades +" if "Unidades +" in d.columns else None
    no_entregado_plus_col = "No entregado +" if "No entregado +" in d.columns else None
    reemplazo_plus_col = "Reemplazo +" if "Reemplazo +" in d.columns else None

    tail_cols = fr_cols[6:]
    fr_compacted = len(fr_cols) >= 6 and (not tail_cols or d[tail_cols].isna().all().all())

    def _clean_tienda_plus(v):
        s = norm_txt(v)
        return re.sub(r"[▾▼▲]+\s*$", "", s).strip()

    rows = []
    for _, r in d.iterrows():
        if fr_compacted:
            vals = r.iloc[:6]
            tienda = _clean_tienda_plus(vals.iloc[0])
            if tienda.strip().upper() in ("TOTAL", "TOTA"):
                continue
            unidades = ar_number(vals.iloc[1])
            sin_sustituto = ar_number(vals.iloc[2])
            con_sustituto = ar_number(vals.iloc[3])
            fr_pct = ar_pct(vals.iloc[5])
            fr_pct = fr_pct if fr_pct is not None else 0.0
        else:
            tienda = norm_txt(r.get("Tienda"))
            if tienda.strip().upper() in ("TOTAL", "TOTA"):
                continue
            unidades = ar_number(r.get(unidades_plus_col)) if unidades_plus_col else ar_number(r.get("Unidades"))
            sin_sustituto = ar_number(r.get(no_entregado_plus_col)) if no_entregado_plus_col else ar_number(r.get("no entregado"))
            con_sustituto = ar_number(r.get(reemplazo_plus_col)) if reemplazo_plus_col else ar_number(r.get("Reemplazo"))
            limpio = r.get("Limpio")
            if pd.notna(limpio):
                fr_pct = float(limpio) * 100
            else:
                fr_pct = ar_pct(r.get("FR"))
                fr_pct = fr_pct if fr_pct is not None else 0.0
        rows.append({
            "Tienda": tienda, "Unidades": unidades, "SinSustituto": sin_sustituto,
            "ConSustituto": con_sustituto, "FRPct": fr_pct
        })
    fill_rate = pd.DataFrame(rows)

# ---- Cancelados ----
if cancelados is not None:
    cancelados["Tienda"] = cancelados["Tienda"].apply(norm_txt)
    if "Total $" in cancelados.columns:
        _total_num = pd.to_numeric(cancelados["Total $"], errors="coerce")
    else:
        _total_num = pd.Series([np.nan] * len(cancelados), index=cancelados.index)
    _monto_num = cancelados.get("Monto", pd.Series([np.nan] * len(cancelados), index=cancelados.index)).apply(ar_number)
    cancelados["Total $"] = _total_num.fillna(_monto_num).fillna(0)

# ---- Faltantes ----
# Formato nuevo (archivo "Faltantes_Mensual"): una fila por cada producto
# faltante dentro de cada pedido (tienda, producto, cantidad faltante,
# sustituido o no, fecha) — igual que en Operativo.
faltantes = None
if df_faltantes_raw is not None:
    d = df_faltantes_raw.copy()
    d["Tienda"] = d["warehouseName"].apply(warehouse_to_tienda)
    d["Producto"] = d["refName"].apply(norm_txt)
    d["SKU"] = d.get("skuId", "").apply(norm_codigo)
    d["CantidadFaltante"] = pd.to_numeric(d.get("missingQuantity"), errors="coerce").fillna(0)
    d["Sustituido"] = pd.to_numeric(d.get("substitutedQuantity"), errors="coerce").fillna(0)
    d["NoSustituido"] = pd.to_numeric(d.get("noSubstitutedQuantity"), errors="coerce").fillna(0)
    _comprado = pd.to_numeric(d.get("purchasedQuantity"), errors="coerce")
    # El archivo trae el mes completo (una fila por pedido) con la fecha real
    # de cada fila, no una sola foto del día.
    d["FechaArchivo"] = pd.to_datetime(d.get("dateCreated"), errors="coerce").dt.normalize()
    # Los productos "pesables" (se venden por peso, no por unidad —
    # sellingMeasurementUnit = "KG") no se cuentan como faltante acá.
    _unidad_venta = get_col_ci(d, "sellingMeasurementUnit").apply(norm_txt).str.upper()
    # Filtro de sanidad: nunca puede faltar más cantidad de la que se compró
    # en ese pedido (ver mismo comentario en Operativo — una minoría de
    # filas del archivo trae valores absurdos).
    d = d[
        (d["CantidadFaltante"] > 0)
        & d["FechaArchivo"].notna()
        & (d["CantidadFaltante"] <= _comprado.fillna(float("inf")))
        & (_unidad_venta != "KG")
    ]
    faltantes = d.groupby(
        ["FechaArchivo", "Tienda", "Producto", "SKU"], as_index=False
    ).agg(
        CantidadFaltante=("CantidadFaltante", "sum"),
        Sustituido=("Sustituido", "sum"),
        NoSustituido=("NoSustituido", "sum"),
    )

# ---------------------------------------------------------------------
# Unificar nombres de tienda entre hojas
# ---------------------------------------------------------------------

_canon_map = build_tienda_canon_map(
    [pedidos_72h, reclamos, ontime_prepa, fill_rate, cancelados, faltantes]
)
pedidos_72h = apply_tienda_canon(pedidos_72h, _canon_map)
reclamos = apply_tienda_canon(reclamos, _canon_map)
ontime_prepa = apply_tienda_canon(ontime_prepa, _canon_map)
fill_rate = apply_tienda_canon(fill_rate, _canon_map)
cancelados = apply_tienda_canon(cancelados, _canon_map)
faltantes = apply_tienda_canon(faltantes, _canon_map)

any_data_loaded = any(
    d is not None and len(d) for d in [pedidos_72h, reclamos, ontime_prepa, fill_rate, cancelados, faltantes]
)

if not any_data_loaded:
    st.markdown(
        '<div class="empty-box" style="margin-top:20px;">'
        'Subí al menos un archivo arriba para armar el resumen.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(f"""
    <div style="font-size:12px;color:#6b7280;margin-top:6px;">
      Corte del reporte: <b style="color:#20252b;">{now_ref.strftime('%d/%m/%Y %H:%M')}</b>
    </div>
    """, unsafe_allow_html=True)

    all_stores = set()
    for d in [pedidos_72h, reclamos, ontime_prepa, fill_rate, cancelados, faltantes]:
        if d is not None and "Tienda" in d.columns:
            all_stores.update([s for s in d["Tienda"].unique() if s])

    auditores = sorted({a for a in (get_auditor(s) for s in all_stores) if a})
    col_aud, col_tda = st.columns([1, 2])
    with col_aud:
        auditor_sel = st.selectbox("Auditor", ["Todos los auditores"] + auditores, key="resumen_auditor")
    filtro_auditor = None if auditor_sel == "Todos los auditores" else auditor_sel

    # Si hay un auditor elegido, el desplegable de Tienda se acota a sus tiendas.
    stores_disponibles = (
        {s for s in all_stores if get_auditor(s) == filtro_auditor}
        if filtro_auditor else all_stores
    )
    with col_tda:
        tienda_sel = st.selectbox("Tienda", ["Todas las tiendas"] + sorted(stores_disponibles), key="resumen_tienda")
    filtro_tienda = None if tienda_sel == "Todas las tiendas" else tienda_sel

    def ftr(d):
        if d is None:
            return d
        if filtro_tienda is not None:
            return d[d["Tienda"] == filtro_tienda]
        if filtro_auditor is not None:
            return d[d["Tienda"].apply(get_auditor) == filtro_auditor]
        return d

    # Días con datos de Faltantes (sobre el total, antes de filtrar por
    # tienda/auditor) — "actual" es el más reciente del archivo, "anterior"
    # el día anterior a ese.
    fecha_actual_falt = None
    fecha_anterior_falt = None
    if faltantes is not None and len(faltantes) and faltantes["FechaArchivo"].notna().any():
        _fechas_falt = sorted(faltantes["FechaArchivo"].dropna().dt.normalize().unique(), reverse=True)
        fecha_actual_falt = _fechas_falt[0] if len(_fechas_falt) >= 1 else None
        fecha_anterior_falt = _fechas_falt[1] if len(_fechas_falt) >= 2 else None

    pedidos_72h = ftr(pedidos_72h)
    reclamos = ftr(reclamos)
    ontime_prepa = ftr(ontime_prepa)
    fill_rate = ftr(fill_rate)
    cancelados = ftr(cancelados)
    faltantes = ftr(faltantes)

    FR_OBJETIVO = 98
    sections = []  # (title, desc, body_html) para el HTML combinado

    # ---- 1) Pedidos +72h sin mover: Top 5 tiendas ----
    st.markdown(
        '<div class="section">📦 Pedidos +72h sin mover — Top 5 tiendas</div>'
        '<div class="section-desc">Tiendas con más pedidos que llevan más de 3 días en el mismo estado sin avanzar.</div>',
        unsafe_allow_html=True
    )
    body = None
    if pedidos_72h is not None and len(pedidos_72h):
        agg = pedidos_72h.groupby("Tienda").agg(
            Cantidad=("Pedido", "count"), Monto=("MontoNum", "sum")
        ).reset_index().sort_values("Cantidad", ascending=False).head(5)
        body = resumen_table_html(agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}", "Monto": money})
        st.write(body, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Sin datos de Pedidos +72h 🎉</div>', unsafe_allow_html=True)
    sections.append((
        "📦 Pedidos +72h sin mover — Top 5 tiendas",
        "Tiendas con más pedidos que llevan más de 3 días en el mismo estado sin avanzar.",
        body
    ))

    # ---- 2) Reclamos abiertos: Top 5 tiendas + ranking por tipo ----
    # Solo se cuentan los reclamos Operativos (problema del sector Ecom) —
    # los No operativos / ajenos a Ecom no entran en este ranking.
    st.markdown(
        '<div class="section">🗣️ Reclamos abiertos (Operativos) — Top 5 tiendas y ranking por tipo</div>'
        '<div class="section-desc">Reclamos Operativos en estado Nuevo o En proceso.</div>',
        unsafe_allow_html=True
    )
    body = None
    if reclamos is not None and len(reclamos):
        abiertos = reclamos[reclamos["Estado"].isin(["Nuevo", "En proceso"])].copy()
        abiertos = abiertos[abiertos["Tipo"].apply(clasificar_tipo_reclamo) == "Operativo"]
        if len(abiertos):
            agg_tienda = abiertos.groupby("Tienda").agg(
                Cantidad=("Pedido", "count")
            ).reset_index().sort_values("Cantidad", ascending=False).head(5)
            agg_tipo = abiertos.groupby("Tipo").agg(
                Cantidad=("Pedido", "count")
            ).reset_index().sort_values("Cantidad", ascending=False)
            html_tienda = resumen_table_html(agg_tienda, "Tienda", {"Cantidad": lambda v: f"{int(v)}"})
            html_tipo = resumen_table_html(agg_tipo, "Tipo", {"Cantidad": lambda v: f"{int(v)}"})
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="resumen-title">Top 5 tiendas con más reclamos Operativos abiertos</div>', unsafe_allow_html=True)
                st.write(html_tienda, unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="resumen-title">Ranking por tipo de reclamo (Operativos)</div>', unsafe_allow_html=True)
                st.write(html_tipo, unsafe_allow_html=True)
            body = (
                '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Top 5 tiendas con más reclamos Operativos abiertos</div>' + html_tienda + '</div>'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Ranking por tipo de reclamo (Operativos)</div>' + html_tipo + '</div>'
                '</div>'
            )
        else:
            st.markdown('<div class="empty-box">Sin reclamos Operativos abiertos 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Sin datos de Reclamos 🎉</div>', unsafe_allow_html=True)
    sections.append((
        "🗣️ Reclamos abiertos (Operativos) — Top 5 tiendas y ranking por tipo",
        "Reclamos Operativos en estado Nuevo o En proceso.",
        body
    ))

    # ---- 3) On Time Preparación: Top 5 peores tiendas (<95%) ----
    st.markdown(
        '<div class="section">⏱️ On Time Preparación — Top 5 peores tiendas</div>'
        '<div class="section-desc">Tiendas que no llegan al objetivo del 95%.</div>',
        unsafe_allow_html=True
    )
    body = None
    if ontime_prepa is not None and len(ontime_prepa):
        peores = ontime_prepa[ontime_prepa["OntimePct"] < 95].sort_values("OntimePct").head(5).copy()
        if len(peores):
            peores["Ontime %"] = peores["OntimePct"].apply(pct1)
            peores["Pedidos"] = peores["Pedidos"].astype(int)
            peores["Fuera de horario"] = peores["Fuera"].astype(int)
            cols = ["Tienda", "Pedidos", "Fuera de horario", "Ontime %"]
            body = table_html(peores[cols])
            st.write(body, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-box">Ninguna tienda por debajo del 95% 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Sin datos de On Time 🎉</div>', unsafe_allow_html=True)
    sections.append((
        "⏱️ On Time Preparación — Top 5 peores tiendas",
        "Tiendas que no llegan al objetivo del 95%.",
        body
    ))

    # ---- 4) Fill Rate: Top 5 peores tiendas (<98%, con venta) ----
    st.markdown(
        f'<div class="section">🧩 Fill Rate — Top 5 peores tiendas</div>'
        f'<div class="section-desc">Tiendas con venta que no llegan al objetivo ({FR_OBJETIVO}%).</div>',
        unsafe_allow_html=True
    )
    body = None
    if fill_rate is not None and len(fill_rate):
        peores = fill_rate[(fill_rate["Unidades"] > 0) & (fill_rate["FRPct"] < FR_OBJETIVO)].sort_values("FRPct").head(5).copy()
        if len(peores):
            peores["Unidades"] = peores["Unidades"].astype(int)
            peores["Sin sustituto"] = peores["SinSustituto"].astype(int)
            peores["FR %"] = peores["FRPct"].apply(pct1)
            cols = ["Tienda", "Unidades", "Sin sustituto", "FR %"]
            body = table_html(peores[cols])
            st.write(body, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="empty-box">Todas las tiendas con venta llegan al objetivo ({FR_OBJETIVO}%) 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Sin datos de Fill Rate 🎉</div>', unsafe_allow_html=True)
    sections.append((
        "🧩 Fill Rate — Top 5 peores tiendas",
        f"Tiendas con venta que no llegan al objetivo ({FR_OBJETIVO}%).",
        body
    ))

    # ---- 5) Pedidos cancelados: Top 5 tiendas ----
    st.markdown(
        '<div class="section">🚫 Pedidos cancelados — Top 5 tiendas</div>'
        '<div class="section-desc">Tiendas con más cancelaciones en el período del reporte.</div>',
        unsafe_allow_html=True
    )
    body = None
    if cancelados is not None and len(cancelados):
        agg = cancelados.groupby("Tienda").agg(
            Cancelados=("Pedido", "count"), Monto=("Total $", "sum")
        ).reset_index().sort_values("Cancelados", ascending=False).head(5)
        body = resumen_table_html(agg, "Tienda", {"Cancelados": lambda v: f"{int(v)}", "Monto": money})
        st.write(body, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Sin cancelaciones 🎉</div>', unsafe_allow_html=True)
    sections.append((
        "🚫 Pedidos cancelados — Top 5 tiendas",
        "Tiendas con más cancelaciones en el período del reporte.",
        body
    ))

    # ---- 6) Faltantes ----
    if filtro_tienda is not None:
        # Con una tienda puntual elegida: resumen de esa tienda en vez del
        # ranking entre tiendas (que no tendría sentido con una sola).
        titulo_falt = f"📉 Faltantes ECOM — {filtro_tienda}"
        desc_falt = "Resumen de faltantes de esta tienda: acumulado del mes, día anterior y día actual."
        st.markdown(
            f'<div class="section">{titulo_falt}</div>'
            f'<div class="section-desc">{desc_falt}</div>',
            unsafe_allow_html=True
        )
        body = None
        if faltantes is not None and len(faltantes):
            cantidad_mes = int(faltantes["CantidadFaltante"].sum())
            _fecha_norm = faltantes["FechaArchivo"].dt.normalize()
            cantidad_actual = (
                int(faltantes.loc[_fecha_norm == fecha_actual_falt, "CantidadFaltante"].sum())
                if fecha_actual_falt is not None else 0
            )
            cantidad_anterior = (
                int(faltantes.loc[_fecha_norm == fecha_anterior_falt, "CantidadFaltante"].sum())
                if fecha_anterior_falt is not None else 0
            )
            label_actual = f"Día actual ({fecha_actual_falt.strftime('%d/%m')})" if fecha_actual_falt is not None else "Día actual"
            label_anterior = f"Día anterior ({fecha_anterior_falt.strftime('%d/%m')})" if fecha_anterior_falt is not None else "Día anterior"

            # Detalle de faltantes por día (Producto, SKU, Cantidad faltante)
            # — no se muestra en pantalla: se baja clickeando la tarjeta de
            # "Día anterior" / "Día actual" (ver kpi_link_wrap).
            _detail_cols = ["Producto", "SKU", "CantidadFaltante"]
            _detail_rename = {"CantidadFaltante": "Cantidad faltante"}

            def _detalle_dia_html(fecha_ref):
                if fecha_ref is None:
                    return None
                sub = faltantes[_fecha_norm == fecha_ref]
                if not len(sub):
                    return None
                sub = sub[_detail_cols].rename(columns=_detail_rename).sort_values("Producto")
                return table_html(sub)

            _slug_tienda = slug_filename(filtro_tienda)
            doc_anterior = export_section_html(
                now_ref,
                f"Faltantes {filtro_tienda} — {label_anterior}",
                f"Listado de productos faltantes en {filtro_tienda} el {label_anterior.split('(')[-1].rstrip(')')}.",
                _detalle_dia_html(fecha_anterior_falt)
            )
            doc_actual = export_section_html(
                now_ref,
                f"Faltantes {filtro_tienda} — {label_actual}",
                f"Listado de productos faltantes en {filtro_tienda} el {label_actual.split('(')[-1].rstrip(')')}.",
                _detalle_dia_html(fecha_actual_falt)
            )

            card_mes = kpi_card("ACUMULADO DEL MES", f"{cantidad_mes}", "Unidades faltantes este mes")
            card_anterior = kpi_link_wrap(
                kpi_card(label_anterior.upper(), f"{cantidad_anterior}", "Unidades faltantes ese día · click para ver el detalle", cls="warn" if cantidad_anterior else "good"),
                doc_anterior, f"faltantes_{_slug_tienda}_dia_anterior.html"
            )
            card_actual = kpi_link_wrap(
                kpi_card(label_actual.upper(), f"{cantidad_actual}", "Unidades faltantes ese día · click para ver el detalle", cls="crit" if cantidad_actual else "good"),
                doc_actual, f"faltantes_{_slug_tienda}_dia_actual.html"
            )
            kpi_html = '<div class="kpi-row">' + card_mes + card_anterior + card_actual + '</div>'
            st.markdown(kpi_html, unsafe_allow_html=True)
            if cantidad_anterior or cantidad_actual:
                st.markdown(
                    '<div style="font-size:11.5px;color:#6b7280;margin-top:-4px;">'
                    '⬇ Tocá la tarjeta de "Día anterior" o "Día actual" para bajar el listado completo de ese día.</div>',
                    unsafe_allow_html=True
                )

            agg_sku_tienda = faltantes.groupby("Producto", as_index=False).agg(
                CantidadFaltante=("CantidadFaltante", "sum"),
            ).sort_values("CantidadFaltante", ascending=False).head(5)
            agg_sku_tienda = agg_sku_tienda.rename(columns={"Producto": "SKU", "CantidadFaltante": "Cantidad faltante"})
            html_sku_tienda = resumen_table_html(
                agg_sku_tienda, "SKU", {"Cantidad faltante": lambda v: f"{int(v)}"}
            )
            st.markdown(
                '<div class="resumen-title" style="margin-top:14px;">Top 5 productos con más faltantes (acumulado del mes)</div>',
                unsafe_allow_html=True
            )
            st.write(html_sku_tienda, unsafe_allow_html=True)
            body = kpi_html + (
                '<div class="resumen-title" style="margin-top:14px;">Top 5 productos con más faltantes (acumulado del mes)</div>'
                + html_sku_tienda
            )
        else:
            st.markdown('<div class="empty-box">Sin faltantes 🎉</div>', unsafe_allow_html=True)
        sections.append((titulo_falt, desc_falt, body))
    else:
        titulo_falt = "📉 Faltantes ECOM — Top 5 tiendas y Top 5 productos"
        desc_falt = (
            f"Acumulado del mes{' para ' + filtro_auditor if filtro_auditor else ''}. "
            "Unidades faltantes por tienda y producto."
        )
        st.markdown(
            f'<div class="section">{titulo_falt}</div>'
            f'<div class="section-desc">{desc_falt}</div>',
            unsafe_allow_html=True
        )
        body = None
        if faltantes is not None and len(faltantes):
            agg_tienda = faltantes.groupby("Tienda", as_index=False).agg(
                CantidadFaltante=("CantidadFaltante", "sum")
            ).sort_values("CantidadFaltante", ascending=False).head(5)
            agg_sku = faltantes.groupby("Producto", as_index=False).agg(
                CantidadFaltante=("CantidadFaltante", "sum"),
                Tiendas=("Tienda", "nunique"),
            ).sort_values("CantidadFaltante", ascending=False).head(5)
            agg_sku = agg_sku.rename(columns={"Producto": "SKU", "CantidadFaltante": "Cantidad faltante"})
            agg_sku["Cantidad faltante"] = agg_sku["Cantidad faltante"].apply(lambda v: f"{int(v)}")
            html_tienda = resumen_table_html(agg_tienda, "Tienda", {"CantidadFaltante": lambda v: f"{int(v)}"})
            html_sku = table_html(agg_sku[["SKU", "Cantidad faltante", "Tiendas"]])
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="resumen-title">Top 5 tiendas con más faltantes</div>', unsafe_allow_html=True)
                st.write(html_tienda, unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="resumen-title">Top 5 productos con más faltantes (todas las tiendas)</div>', unsafe_allow_html=True)
                st.write(html_sku, unsafe_allow_html=True)
            body = (
                '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Top 5 tiendas con más faltantes</div>' + html_tienda + '</div>'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Top 5 productos con más faltantes (todas las tiendas)</div>' + html_sku + '</div>'
                '</div>'
            )
        else:
            st.markdown('<div class="empty-box">Sin faltantes 🎉</div>', unsafe_allow_html=True)
        sections.append((titulo_falt, desc_falt, body))

    # ---- Descargar todo junto ----
    full_html = export_resumen_html(now_ref, sections)
    # La fecha va también en el NOMBRE del archivo (no solo adentro, en
    # "Corte del reporte") para que se vea de una en la carpeta de
    # Descargas o en el mail, sin tener que abrirlo.
    _fecha_archivo = now_ref.strftime("%Y-%m-%d") if now_ref is not None else None
    _nombre_resumen = f"resumen_top5_tiendas_{_fecha_archivo}.html" if _fecha_archivo else "resumen_top5_tiendas.html"
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.download_button(
        "📋 Descargar Resumen completo (HTML) — para mandar a las tiendas",
        data=full_html.encode("utf-8"),
        file_name=_nombre_resumen,
        mime="text/html",
        key="dl_resumen_full",
        use_container_width=True,
    )

    st.markdown(
        '<div style="color:#6b7280;font-size:11.5px;text-align:center;margin-top:18px;">'
        'Resumen · datos del Reporte diario · esta página no guarda historial: volvé a subir los archivos '
        'actualizados para regenerar el ranking.</div>',
        unsafe_allow_html=True
    )
