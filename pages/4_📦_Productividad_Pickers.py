import base64
import io
import json
import re
import tempfile
import unicodedata
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

# Historial día a día: se guarda en el mismo Google Sheet que Faltantes (hoja
# "HistorialPickers"), escrito desde la pestaña Operativo cada vez que se sube
# un Reporte diario nuevo. Import "blindado": si la librería no está o las
# credenciales no están configuradas, esta pestaña sigue funcionando igual,
# solo que sin la evolución día a día.
try:
    import gspread
    from google.oauth2.service_account import Credentials as _GCreds
    _GSHEETS_LIB_OK = True
except Exception:
    _GSHEETS_LIB_OK = False

st.set_page_config(
    page_title="MásOnline | Productividad Pickers",
    page_icon="📦",
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

    .section {
        font-size: 19px; font-weight: 800; color: #20252b;
        margin: 26px 0 4px; display:flex; align-items:center; gap:10px;
    }
    .section-desc { color:#6b7280; font-size:12.5px; margin: -2px 0 10px; }

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

    .kpi-row { display:flex; gap:14px; margin-top:6px; flex-wrap:wrap; }
    .kpi {
        background:#fafaf8; border:1px solid #eef0ef; border-radius:12px;
        padding:14px 18px; flex:1; min-width:150px;
    }
    .kpi .label { color:#6b7280; font-size:11.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
    .kpi .value { color:#ff5a1f; font-size:26px; font-weight:800; margin-top:6px; }

    a.kpi-link { text-decoration:none; display:block; flex:1; min-width:150px; }
    a.kpi-link .kpi { cursor:pointer; transition:box-shadow .15s, transform .15s; position:relative; min-width:0; }
    a.kpi-link .kpi::after {
        content: "⬇ HTML"; position:absolute; top:10px; right:12px;
        font-size:9.5px; font-weight:700; color:#ff5a1f; opacity:0;
        transition:opacity .15s; letter-spacing:.03em;
    }
    a.kpi-link:hover .kpi { box-shadow: 0 6px 18px rgba(0,0,0,.14); transform: translateY(-2px); }
    a.kpi-link:hover .kpi::after { opacity: 1; }

    .field-label {
        color:#ff5a1f; font-size:13px; font-weight:700; margin-bottom:2px;
    }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero-brand { font-size: 20px; }
        .section { font-size: 16px; margin: 20px 0 4px; }
        table.dashtable { font-size: 12px; }
        table.dashtable thead th, table.dashtable tbody td { padding: 7px 8px; }
        .kpi { min-width: 130px; padding: 12px 14px; }
        .kpi .value { font-size: 22px; }
    }
"""

st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Helpers (los mismos que en Operativo/Resumen, para leer el mismo
# Reporte diario.xlsx)
# ---------------------------------------------------------------------

def norm_cols(df):
    df = df.copy()
    df.columns = [str(c).replace("\xa0", " ").strip() for c in df.columns]
    return df

def norm_txt(v):
    if pd.isna(v):
        return ""
    return str(v).replace("\xa0", " ").strip()

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

def table_html(df):
    """Va envuelta en un contenedor con scroll horizontal para que en el
    celular, si la tabla no entra en el ancho de la pantalla, se pueda
    desplazar en vez de romper el diseño de la página."""
    inner = df.to_html(escape=False, index=False, classes="dashtable", border=0)
    return f'<div class="table-scroll">{inner}</div>'

def pct1(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:.1f}%".replace(".", ",")

def num1(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:,.1f}".replace(",", "@").replace(".", ",").replace("@", ".")

def num0(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:,.0f}".replace(",", ".")

def kpi_card(label, value):
    return (
        '<div class="kpi">'
        '<div class="label">' + str(label) + '</div>'
        '<div class="value">' + str(value) + '</div>'
        '</div>'
    )

def slug_filename(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s or "archivo"

def card_export_html(section_title, section_desc, body_html):
    """Arma un HTML standalone (con el mismo look de la página) para
    descargar el detalle de una card KPI al clickearla."""
    if not body_html:
        return None
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>MásOnline · {section_title}</title>
<style>
{APP_CSS}
body {{ margin:0; background:#fafaf8; }}
.wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px 20px 28px; }}
</style>
</head>
<body>
<div class="hero">
  <div>
    <div class="hero-brand">📦 Productividad Pickers</div>
    <div class="hero-sub">{section_title.upper()}</div>
  </div>
</div>
<div class="wrap">
<div class="section">{section_title}</div>
<div class="section-desc">{section_desc}</div>
{body_html}
</div>
</body>
</html>"""

def kpi_link_wrap(inner_html, html_doc, filename):
    """Envuelve una tarjeta KPI en un link que descarga el HTML de detalle
    al clickearla (en vez de mostrar la info abajo en pantalla)."""
    if not html_doc:
        return inner_html
    b64 = base64.b64encode(html_doc.encode("utf-8")).decode("utf-8")
    return (
        f'<a class="kpi-link" href="data:text/html;base64,{b64}" download="{filename}" '
        'title="Descargar el detalle como HTML">' + inner_html + '</a>'
    )

# ---------------------------------------------------------------------
# Archivo compartido: esta pestaña NO tiene uploader propio. Usa el último
# Reporte diario.xlsx que se haya subido en la pestaña Operativo (misma
# carpeta compartida que usan Operativo y Resumen).
# ---------------------------------------------------------------------

SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_DIR.mkdir(parents=True, exist_ok=True)
SHARED_REPORTE_PATH = SHARED_DIR / "reporte_diario.xlsx"

def get_shared_bytes(shared_path):
    if shared_path.exists():
        try:
            return shared_path.read_bytes()
        except Exception:
            return None
    return None

# ---------------------------------------------------------------------
# Historial día a día (Google Sheets) — lectura. La escritura pasa en la
# pestaña Operativo cada vez que se sube un Reporte diario nuevo.
# ---------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _gsheets_debug_box():
    return {"msg": None}

@st.cache_resource(show_spinner=False)
def _gsheets_client():
    if not _GSHEETS_LIB_OK:
        _gsheets_debug_box()["msg"] = "La librería gspread no se instaló (revisá requirements.txt)."
        return None
    try:
        raw_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if raw_json:
            creds_dict = json.loads(raw_json)
        else:
            creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = _GCreds.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        _gsheets_debug_box()["msg"] = None
        return client
    except Exception as e:
        _gsheets_debug_box()["msg"] = f"Error de credenciales ({type(e).__name__}): {e}"
        return None

# Código de depósito (warehouseRefId, tal como viene en "Data Picker") -> nombre
# de tienda. Sacado del listado "Picker x tienda" que subió Emi. Un código que
# no esté acá (por ejemplo uno nuevo, o un centro que no es de venta al público)
# simplemente se muestra tal cual, sin romper nada.
TIENDA_MAP = {
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

def tienda_nombre(codigo):
    codigo = norm_txt(codigo)
    return TIENDA_MAP.get(codigo, codigo)

# Códigos de depósito que en realidad no son una tienda válida (error de carga
# en el Reporte diario). Para estos casos no mostramos el código crudo: en vez
# de "tienda", se muestra el nombre del picker.
DEPOSITO_INVALIDO = {"7460"}

def tienda_nombre_row(codigo, picker=None):
    codigo = norm_txt(codigo)
    if codigo in DEPOSITO_INVALIDO:
        picker = norm_txt(picker) if picker else ""
        return picker if picker else codigo
    return TIENDA_MAP.get(codigo, codigo)

PICKER_LOG_HEADERS = [
    "Fecha", "Picker", "Deposito", "Pedidos", "Unidades",
    "Rendimiento", "RendimientoPicking", "FoundRate", "FillRate"
]

def _pickers_log_ws():
    client = _gsheets_client()
    if client is None:
        return None
    sheet_id = st.secrets.get("FALTANTES_SHEET_ID")
    if not sheet_id:
        _gsheets_debug_box()["msg"] = "Falta FALTANTES_SHEET_ID en Secrets."
        return None
    try:
        sh = client.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("HistorialPickers")
        except gspread.exceptions.WorksheetNotFound:
            return None  # todavía nadie subió un Reporte diario con hoja de pickers
        _gsheets_debug_box()["msg"] = None
        return ws
    except Exception as e:
        _gsheets_debug_box()["msg"] = f"Error abriendo la planilla ({type(e).__name__}): {e}"
        return None

@st.cache_data(ttl=180, show_spinner=False)
def load_pickers_log():
    """Lee todo el historial acumulado (cacheado 3 minutos). None = todavía
    no conectado. DataFrame vacío = conectado pero sin filas cargadas aún."""
    ws = _pickers_log_ws()
    if ws is None:
        return None
    try:
        records = ws.get_all_records()
    except Exception:
        return None
    df = pd.DataFrame(records) if records else pd.DataFrame(columns=PICKER_LOG_HEADERS)
    if "Fecha" in df.columns:
        df["FechaDt"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    if "Deposito" in df.columns:
        pickers_col = df["Picker"] if "Picker" in df.columns else [""] * len(df)
        df["Tienda"] = [
            tienda_nombre_row(dep, pic) for dep, pic in zip(df["Deposito"], pickers_col)
        ]
    for c in ["Pedidos", "Unidades", "Rendimiento", "RendimientoPicking", "FoundRate", "FillRate"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.markdown("""
<div class="hero">
  <div>
    <div class="hero-brand">📦 Productividad Pickers</div>
    <div class="hero-sub">RANKING Y EVOLUCIÓN DIARIA</div>
  </div>
</div>
""", unsafe_allow_html=True)

reporte_bytes = get_shared_bytes(SHARED_REPORTE_PATH)

if reporte_bytes is not None:
    st.markdown(
        '<div style="font-size:11.5px;color:#0ca30c;font-weight:700;margin:-2px 0 10px;">'
        '● Mostrando el último Reporte diario subido en la pestaña Operativo — no hace falta subir nada acá.</div>',
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
        Subí el "Reporte diario.xlsx" en la pestaña <b>Operativo</b> (tiene que incluir la hoja
        "Data Picker"). Esta página va a mostrar el ranking automáticamente con esos mismos datos.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Parse "Data Picker" (ranking de hoy, sin filtrar todavía)
# ---------------------------------------------------------------------

pickers_all = None
if reporte_bytes is not None:
    xl_reporte = safe_open_excel(io.BytesIO(reporte_bytes))
    name, df_picker_raw = find_sheet(
        xl_reporte,
        ["firstName", "lastName", "warehouseRefId", "orders", "items", "performance"]
    ) if xl_reporte is not None else (None, None)
    if df_picker_raw is not None:
        d = df_picker_raw.copy()
        d["Picker"] = (d["firstName"].apply(norm_txt) + " " + d["lastName"].apply(norm_txt)).str.strip()
        d["Tienda"] = [
            tienda_nombre_row(dep, pic) for dep, pic in zip(d["warehouseRefId"], d["Picker"])
        ]
        d["Pedidos"] = pd.to_numeric(d["orders"], errors="coerce").fillna(0)
        d["Unidades"] = pd.to_numeric(d["items"], errors="coerce").fillna(0)
        d["Rendimiento"] = pd.to_numeric(d["performance"], errors="coerce")
        d["Rend. picking"] = pd.to_numeric(d.get("pickingPerformance"), errors="coerce")
        d["Found Rate"] = pd.to_numeric(d.get("foundRate"), errors="coerce")
        d["Fill Rate"] = pd.to_numeric(d.get("fillRate"), errors="coerce")
        d["Deposito"] = d["warehouseRefId"].apply(norm_txt)
        d = d[d["Picker"] != ""]
        pickers_all = d[[
            "Picker", "Tienda", "Deposito", "Pedidos", "Unidades",
            "Rendimiento", "Rend. picking", "Found Rate", "Fill Rate"
        ]].sort_values("Unidades", ascending=False)
    elif xl_reporte is not None:
        st.markdown(
            '<div class="empty-box">El Reporte diario subido no tiene una hoja "Data Picker" '
            'con las columnas esperadas.</div>',
            unsafe_allow_html=True
        )

log_df = load_pickers_log()

# ---------------------------------------------------------------------
# Filtro: Tienda/Depósito. Se aplica al ranking de hoy y a todo el
# historial (que siempre muestra el período completo disponible).
# ---------------------------------------------------------------------

tiendas = set()
if pickers_all is not None and "Deposito" in pickers_all.columns:
    tiendas.update([
        t for dep, t in zip(pickers_all["Deposito"], pickers_all["Tienda"])
        if t and norm_txt(dep) not in DEPOSITO_INVALIDO
    ])
if log_df is not None and len(log_df) and "Tienda" in log_df.columns and "Deposito" in log_df.columns:
    tiendas.update([
        t for dep, t in zip(log_df["Deposito"], log_df["Tienda"])
        if t and norm_txt(dep) not in DEPOSITO_INVALIDO
    ])
tiendas = sorted(tiendas)

st.markdown('<div class="field-label">Tienda</div>', unsafe_allow_html=True)
filtro_tienda = st.selectbox(
    "Tienda", ["Todas"] + tiendas, key="pickers_filtro_tienda", label_visibility="collapsed"
)

pickers = pickers_all
if pickers is not None and filtro_tienda != "Todas":
    pickers = pickers[pickers["Tienda"] == filtro_tienda]

log_filtrado = None
if log_df is not None and len(log_df):
    log_filtrado = log_df.copy()
    if filtro_tienda != "Todas":
        log_filtrado = log_filtrado[log_filtrado["Tienda"] == filtro_tienda]

# ---------------------------------------------------------------------
# Ranking de pickers — último día con datos en el historial (sin selector:
# siempre el más reciente).
# ---------------------------------------------------------------------

fechas_disponibles_dia = []
if log_df is not None and len(log_df) and log_df["FechaDt"].notna().any():
    fechas_disponibles_dia = sorted(log_df["FechaDt"].dropna().dt.normalize().unique(), reverse=True)

fecha_dia_sel = fechas_disponibles_dia[0] if fechas_disponibles_dia else None

st.markdown(
    '<div class="section">🏆 Ranking de pickers</div>',
    unsafe_allow_html=True
)

if fecha_dia_sel is None:
    if reporte_bytes is not None:
        st.markdown(
            '<div class="empty-box">Todavía no hay historial conectado — se activa solo la próxima vez '
            'que subas un Reporte diario con la hoja "Data Picker" en Operativo.</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="empty-box">Subí un Reporte diario en Operativo para ver esta sección.</div>', unsafe_allow_html=True)
else:
    dia_df = log_df[log_df["FechaDt"].dt.normalize() == fecha_dia_sel].copy()
    if filtro_tienda != "Todas":
        dia_df = dia_df[dia_df["Tienda"] == filtro_tienda]
    dia_df = dia_df.sort_values("Unidades", ascending=False)

    if len(dia_df):
        fecha_label = fecha_dia_sel.strftime("%d/%m/%Y") if fecha_dia_sel is not None else "hoy"
        tienda_desc = "" if filtro_tienda == "Todas" else f" — tienda {filtro_tienda}"

        def _detalle_metric_html(cols, sort_col, fmts):
            d = dia_df[["Tienda", "Picker"] + cols].sort_values(sort_col, ascending=False).copy()
            for c, fmt in zip(cols, fmts):
                d[c] = d[c].apply(fmt)
            return table_html(d)

        doc_pickers = card_export_html(
            f"Pickers activos — {fecha_label}",
            f"Los {int(dia_df['Picker'].nunique())} pickers activos ese día{tienda_desc}.",
            _detalle_metric_html(["Pedidos", "Unidades"], "Unidades", [num0, num0]),
        )
        doc_pedidos = card_export_html(
            f"Pedidos totales — {fecha_label}",
            f"Pedidos por picker ese día{tienda_desc}.",
            _detalle_metric_html(["Pedidos"], "Pedidos", [num0]),
        )
        doc_unidades = card_export_html(
            f"Unidades totales — {fecha_label}",
            f"Unidades por picker ese día{tienda_desc}.",
            _detalle_metric_html(["Unidades"], "Unidades", [num0]),
        )
        doc_rendimiento = card_export_html(
            f"Rendimiento promedio — {fecha_label}",
            f"Rendimiento por picker ese día{tienda_desc}.",
            _detalle_metric_html(["Rendimiento"], "Rendimiento", [num1]),
        )

        kpi_html = (
            '<div class="kpi-row">'
            + kpi_link_wrap(
                kpi_card("Pickers activos", num0(dia_df["Picker"].nunique())),
                doc_pickers,
                f"pickers_activos_{slug_filename(fecha_label)}.html",
            )
            + kpi_link_wrap(
                kpi_card("Pedidos totales", num0(dia_df["Pedidos"].sum())),
                doc_pedidos,
                f"pedidos_totales_{slug_filename(fecha_label)}.html",
            )
            + kpi_link_wrap(
                kpi_card("Unidades totales", num0(dia_df["Unidades"].sum())),
                doc_unidades,
                f"unidades_totales_{slug_filename(fecha_label)}.html",
            )
            + kpi_link_wrap(
                kpi_card("Rendimiento promedio", num1(dia_df["Rendimiento"].mean())),
                doc_rendimiento,
                f"rendimiento_promedio_{slug_filename(fecha_label)}.html",
            )
            + '</div>'
        )
        st.markdown(kpi_html, unsafe_allow_html=True)

        # Cuadro chico: Top 10 mejores pickers (más unidades pickeadas), con
        # solo lo esencial — Tienda, Picker, Pedidos, Unidades y Fill Rate.
        st.markdown('<div class="resumen-title" style="margin-top:14px;">Top 10 mejores pickers</div>', unsafe_allow_html=True)
        top10 = dia_df[["Tienda", "Picker", "Pedidos", "Unidades", "FillRate"]].head(10).copy()
        top10["Pedidos"] = top10["Pedidos"].apply(num0)
        top10["Unidades"] = top10["Unidades"].apply(num0)
        top10["FillRate"] = top10["FillRate"].apply(pct1)
        top10 = top10.rename(columns={"FillRate": "Fill Rate"})
        st.write(table_html(top10), unsafe_allow_html=True)

        cols_dia = ["Picker", "Tienda", "Pedidos", "Unidades", "Rendimiento", "RendimientoPicking", "FoundRate", "FillRate"]
        rename_dia = {"RendimientoPicking": "Rend. picking", "FoundRate": "Found Rate", "FillRate": "Fill Rate"}
        with st.expander(f"Ver el detalle completo ({len(dia_df)} pickers)"):
            with st.container(height=420):
                full = dia_df[cols_dia].rename(columns=rename_dia).copy()
                for c in ["Rendimiento", "Rend. picking"]:
                    full[c] = full[c].apply(num1)
                for c in ["Found Rate", "Fill Rate"]:
                    full[c] = full[c].apply(pct1)
                full["Pedidos"] = full["Pedidos"].apply(num0)
                full["Unidades"] = full["Unidades"].apply(num0)
                st.write(table_html(full), unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Sin pickers para esta tienda en esa fecha.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Ranking del período (acumulado del rango de fechas elegido). Solo tiene
# sentido cuando se están viendo todas las tiendas — si ya se filtró por
# una tienda puntual, este ranking quedaría con una sola fila, así que se
# oculta y se deja solo la info de los pickers.
# ---------------------------------------------------------------------

if filtro_tienda == "Todas":
    st.markdown(
        '<div class="section">🏬 Top 10 tiendas — mejor rendimiento</div>'
        '<div class="section-desc">Acumulado de todo el historial disponible, '
        'sumando todos los Reportes diarios subidos.</div>',
        unsafe_allow_html=True
    )

    if log_filtrado is not None and len(log_filtrado):
        _base_tiendas = log_filtrado[~log_filtrado["Deposito"].apply(norm_txt).isin(DEPOSITO_INVALIDO)]
        tiendas_periodo = _base_tiendas.groupby("Deposito", as_index=False).agg(
            Pickers=("Picker", "nunique"),
            Dias=("Fecha", "nunique"),
            Pedidos=("Pedidos", "sum"),
            Unidades=("Unidades", "sum"),
            Rendimiento=("Rendimiento", "mean"),
        ).sort_values("Rendimiento", ascending=False)
        tiendas_periodo = tiendas_periodo.rename(columns={"Deposito": "Tienda", "Dias": "Días"})

        ttop = tiendas_periodo.head(10).copy()
        ttop["Rendimiento"] = ttop["Rendimiento"].apply(num1)
        ttop["Pedidos"] = ttop["Pedidos"].apply(num0)
        ttop["Unidades"] = ttop["Unidades"].apply(num0)
        st.write(table_html(ttop), unsafe_allow_html=True)

        if len(tiendas_periodo) > 10:
            with st.expander(f"Ver las {len(tiendas_periodo)} tiendas del período"):
                with st.container(height=420):
                    tfull = tiendas_periodo.copy()
                    tfull["Rendimiento"] = tfull["Rendimiento"].apply(num1)
                    tfull["Pedidos"] = tfull["Pedidos"].apply(num0)
                    tfull["Unidades"] = tfull["Unidades"].apply(num0)
                    st.write(table_html(tfull), unsafe_allow_html=True)
    elif log_df is None:
        st.markdown(
            '<div class="empty-box">Todavía no hay historial conectado — se activa solo la próxima vez '
            'que subas un Reporte diario con la hoja "Data Picker" en Operativo.</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="empty-box">Sin datos acumulados.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Productividad del picker en un rango de fechas elegido
# ---------------------------------------------------------------------

st.markdown('<div class="section">🧑‍💼 Productividad del picker</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Elegí un rango de fechas para ver el rendimiento de cada picker '
    'en ese período (respeta el filtro de tienda de arriba).</div>',
    unsafe_allow_html=True
)

if log_filtrado is not None and len(log_filtrado) and log_filtrado["FechaDt"].notna().any():
    _min_date = log_filtrado["FechaDt"].min().date()
    _max_date = log_filtrado["FechaDt"].max().date()

    fp1, fp2 = st.columns(2)
    with fp1:
        st.markdown('<div class="field-label">Desde</div>', unsafe_allow_html=True)
        picker_desde = st.date_input(
            "Desde", value=_min_date, min_value=_min_date, max_value=_max_date,
            key="picker_prod_desde", label_visibility="collapsed"
        )
    with fp2:
        st.markdown('<div class="field-label">Hasta</div>', unsafe_allow_html=True)
        picker_hasta = st.date_input(
            "Hasta", value=_max_date, min_value=_min_date, max_value=_max_date,
            key="picker_prod_hasta", label_visibility="collapsed"
        )

    if picker_desde > picker_hasta:
        st.warning("La fecha 'Desde' es posterior a 'Hasta' — invertí las fechas para ver resultados.")
        picker_rango = log_filtrado.iloc[0:0]
    else:
        picker_rango = log_filtrado[
            (log_filtrado["FechaDt"].dt.date >= picker_desde) & (log_filtrado["FechaDt"].dt.date <= picker_hasta)
        ]

    if len(picker_rango):
        productividad = picker_rango.groupby("Picker", as_index=False).agg(
            Tienda=("Tienda", "first"),
            Dias=("Fecha", "nunique"),
            Pedidos=("Pedidos", "sum"),
            Unidades=("Unidades", "sum"),
            Rendimiento=("Rendimiento", "mean"),
        ).sort_values("Unidades", ascending=False)
        productividad = productividad.rename(columns={"Dias": "Días"})

        ptop = productividad.head(20).copy()
        ptop["Rendimiento"] = ptop["Rendimiento"].apply(num1)
        ptop["Pedidos"] = ptop["Pedidos"].apply(num0)
        ptop["Unidades"] = ptop["Unidades"].apply(num0)
        st.write(table_html(ptop), unsafe_allow_html=True)

        if len(productividad) > 20:
            with st.expander(f"Ver los {len(productividad)} pickers del período"):
                with st.container(height=420):
                    pfull = productividad.copy()
                    pfull["Rendimiento"] = pfull["Rendimiento"].apply(num1)
                    pfull["Pedidos"] = pfull["Pedidos"].apply(num0)
                    pfull["Unidades"] = pfull["Unidades"].apply(num0)
                    st.write(table_html(pfull), unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="empty-box">Sin datos de pickers para ese rango de fechas.</div>',
            unsafe_allow_html=True
        )
elif log_df is None:
    st.markdown(
        '<div class="empty-box">Todavía no hay historial conectado — se activa solo la próxima vez '
        'que subas un Reporte diario con la hoja "Data Picker" en Operativo.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown('<div class="empty-box">Sin datos acumulados para esta tienda.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Evolución día a día (historial acumulado en Google Sheets)
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">📈 Evolución día a día</div>'
    '<div class="section-desc">Se arma solo, con cada Reporte diario que se suba en Operativo '
    '(una fila por picker, por día). Respeta el filtro de tienda de arriba.</div>',
    unsafe_allow_html=True
)

if log_df is None:
    _debug_msg = _gsheets_debug_box().get("msg")
    _debug_html = (
        f'<div style="font-size:11px;color:#b0413e;margin-top:8px;font-family:monospace;">{_debug_msg}</div>'
        if _debug_msg else ""
    )
    st.markdown(
        '<div class="empty-box">Todavía no hay historial conectado — se activa solo la próxima vez '
        'que subas un Reporte diario con la hoja "Data Picker" en Operativo.' + _debug_html + '</div>',
        unsafe_allow_html=True
    )
elif not len(log_df):
    st.markdown(
        '<div class="empty-box">Todavía no hay historial acumulado. Se va a empezar a llenar '
        'con cada Reporte diario que subas de acá en adelante.</div>',
        unsafe_allow_html=True
    )
elif log_filtrado is None or not len(log_filtrado):
    st.markdown('<div class="empty-box">Sin datos para esta tienda.</div>', unsafe_allow_html=True)
else:
    diario = log_filtrado.groupby("Fecha", as_index=False).agg(
        FechaDt=("FechaDt", "first"),
        Pickers=("Picker", "nunique"),
        Pedidos=("Pedidos", "sum"),
        Unidades=("Unidades", "sum"),
        Rendimiento=("Rendimiento", "mean"),
    ).sort_values("FechaDt")

    tabla = diario[["Fecha", "Pickers", "Pedidos", "Unidades", "Rendimiento"]].copy()
    tabla["Pedidos"] = tabla["Pedidos"].apply(num0)
    tabla["Unidades"] = tabla["Unidades"].apply(num0)
    tabla["Rendimiento"] = tabla["Rendimiento"].apply(pct1)
    tabla = tabla.rename(columns={"Rendimiento": "Rendimiento prom."})
    st.write(table_html(tabla.iloc[::-1]), unsafe_allow_html=True)

    with st.expander(f"Ver historial completo por picker ({len(log_filtrado)} filas)"):
        with st.container(height=380):
            st.write(
                table_html(
                    log_filtrado.sort_values("FechaDt", ascending=False)
                    [["Fecha", "Picker", "Tienda", "Pedidos", "Unidades", "Rendimiento", "FoundRate", "FillRate"]]
                ),
                unsafe_allow_html=True
            )

    csv_bytes = (
        log_filtrado.sort_values("FechaDt")
        [["Fecha", "Picker", "Tienda", "Pedidos", "Unidades", "Rendimiento", "RendimientoPicking", "FoundRate", "FillRate"]]
        .to_csv(index=False).encode("utf-8-sig")
    )
    st.download_button(
        "⬇️ Descargar historial filtrado (CSV)",
        data=csv_bytes,
        file_name="pickers_historial.csv",
        mime="text/csv",
        key="dl_pickers_historial",
    )

st.markdown(
    '<div style="color:#6b7280;font-size:11.5px;text-align:center;margin-top:18px;">'
    'Productividad Pickers · datos de la hoja "Data Picker" del Reporte diario · '
    'no tiene uploader propio: se actualiza sola con lo que subas en Operativo.</div>',
    unsafe_allow_html=True
)
