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
    page_title="MásOnline | Operativo",
    page_icon="🚨",
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
    .section .count-pill {
        font-size: 15px; font-weight: 800; background:#fdeee5; color:#ff5a1f;
        border-radius: 999px; padding: 3px 15px; box-shadow: 0 1px 5px rgba(255,90,31,.22);
    }
    .section-desc { color:#6b7280; font-size:12.5px; margin: -2px 0 10px; }

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
    table.dashtable tbody tr.total-row {
        background: #d7ecfc; font-weight: 800; color:#0f3a5c;
        border-top: 2px solid #7fb8e8;
    }
    table.dashtable tbody tr.total-row td { padding: 10px 12px; font-size: 13.5px; }
    table.dashtable tbody tr.total-row:hover { background: #d7ecfc; }

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
"""

st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def norm_cols(df):
    df = df.copy()
    df.columns = [str(c).replace("\xa0", " ").strip() for c in df.columns]
    return df

def norm_txt(v):
    if pd.isna(v):
        return ""
    return str(v).replace("\xa0", " ").strip()

TIENDA_ALIASES = {
    "grafa": "Constituyentes",
}

def strip_sucursal(v):
    """Quita el prefijo 'Sucursal ' y normaliza espacios, para poder unificar
    nombres de tienda que vienen distinto de una hoja a otra. También aplica
    alias manuales para tiendas que figuran con un nombre distinto en una
    planilla puntual (ej. 'Grafa' en Faltantes = 'Constituyentes' en el resto
    de los reportes)."""
    s = norm_txt(v)
    s = re.sub(r"(?i)^sucursal\s+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    alias = TIENDA_ALIASES.get(s.lower())
    if alias:
        return alias
    return s

def fold_tienda_key(s):
    """Clave sin acentos/mayúsculas para agrupar nombres de tienda equivalentes
    aunque vengan escritos distinto entre hojas (ej. 'Cordoba Oeste' vs 'Córdoba Oeste')."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()

# Mapa Tienda -> Auditor, armado a partir de "tiendas por formato.xlsx". La
# clave es fold_tienda_key(nombre de la tienda tal como aparece en los
# reportes), para que funcione sin importar acentos/mayúsculas. Pendiente de
# confirmar con Emi: "Comodoro Rivadavia" / "Comodoro Rivadavia Norte" (hay
# más de una tienda "Comodoro" en los reportes y no se pudo saber cuál es
# cuál) y "R.S. Peña, Chaco" (aparece con dos ortografías distintas en los
# reportes: "Roque Saenz Peña" y "Sáenz Peña. Chaco"). Esas tiendas, hasta
# aclararlo, no muestran auditor.
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
    """Unifica nombres de tienda entre hojas (mayúsculas/minúsculas, acentos, prefijo
    'Sucursal', espacios) usando la ortografía más frecuente como canónica."""
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
    """Parse an Argentine-formatted number that may come as a plain value
    or as a string like '9.473 ▼ 12.6%vs MA' / '1.565' / '$464K'."""
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
    """Parsea un porcentaje que puede venir como número (0.977 o 97.7) o como
    texto con '%' en notación estándar (punto decimal, ej. '97.7%', '50.0%').
    A diferencia de ar_number, acá el '.' siempre es punto decimal y nunca
    separador de miles (los porcentajes no lo necesitan)."""
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
    """Return the (sheet_name, df) whose normalized columns cover required_cols."""
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
    """Abre un archivo subido como pd.ExcelFile, mostrando un error prolijo si falla."""
    if uploaded_file is None:
        return None
    try:
        return pd.ExcelFile(uploaded_file)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return None

# ---------------------------------------------------------------------
# Guardado compartido: para que los auditores (o cualquiera con el link)
# vean el último reporte que subiste sin tener que subir nada ellos. Se
# guarda una copia del archivo en el disco donde corre la app; mientras la
# app siga "despierta", todos los que entren ven esa misma copia. Si
# Streamlit la reinicia por inactividad, o subís un cambio nuevo a GitHub,
# esa copia se borra y hace falta volver a subir el reporte una vez para
# que se vuelva a compartir con todos.
# ---------------------------------------------------------------------

SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_DIR.mkdir(parents=True, exist_ok=True)
SHARED_REPORTE_PATH = SHARED_DIR / "reporte_diario.xlsx"
SHARED_FALTANTES_PATH = SHARED_DIR / "faltantes.xlsx"

def get_shared_bytes(uploaded_file, shared_path):
    """Si en ESTA sesión alguien subió un archivo, lo usa y lo guarda para
    compartirlo con quien entre después. Si nadie subió nada en esta
    sesión, usa el último que haya quedado guardado (subido antes por
    cualquier otra persona). Devuelve (bytes o None, es_subida_nueva)."""
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
            return None, False
    return None, False

def load_section_from_xl(xl, required_cols):
    """Busca, dentro de un pd.ExcelFile ya abierto, la hoja cuyas columnas
    cubren required_cols. Permite reusar el mismo Excel para varias secciones
    sin tener que volver a leerlo del disco."""
    if xl is None:
        return None
    name, df = find_sheet(xl, required_cols)
    if df is None:
        st.error(
            "No encontré una hoja con las columnas esperadas "
            f"({', '.join(required_cols)}) en el archivo subido."
        )
        return None
    return df

def load_section(uploaded_file, required_cols):
    """Load an uploaded file (single-sheet export OR the full Reporte diario.xlsx)
    and return the dataframe matching required_cols, or None."""
    return load_section_from_xl(safe_open_excel(uploaded_file), required_cols)

def _fr_read_positional(xl, sheet_name):
    """Lee una hoja de Fill Rate por POSICIÓN (6 columnas: Tienda, Unidades,
    No entregado, Reemplazo, Monto, FR%) en vez de por nombre de columna,
    porque el nombre de esas columnas cambia de un día a otro en el export
    (a veces 'Tienda/FR/Limpio', a veces 'Tienda/unidades pedidas/.../fill
    rate', a veces directamente sin fila de encabezado). Si la primera fila
    es un encabezado (columna 1 dice 'Tienda'), la descartamos; si no, ya es
    un dato y la dejamos."""
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
    """Último recurso cuando ninguna hoja se llama '...Fr...': hoja de 6+
    columnas donde alguna fila arranca con 'TOTAL' y la última columna tiene
    pinta de porcentaje (para no confundirla con otra hoja que también
    tenga una fila de totales, ej. On Time)."""
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
    """Carga Fill Rate. Primero probamos la hoja con encabezado 'de toda la
    vida' (Tienda/FR/Limpio). Si no está, buscamos la hoja cuyo nombre
    contiene 'fr' (ej. 'Data Fr') y la leemos por posición, sin importar
    cómo se llamen sus columnas ese día. Como último recurso, entre todas
    las hojas buscamos una con pinta de Fill Rate (fila 'TOTAL' + última
    columna con '%')."""
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

def load_cancelados_from_xl(xl):
    """Carga Pedidos cancelados. Cuando la hoja no trae la columna 'Total $'
    (pasa algunos días), tiene exactamente las mismas columnas base que
    'Data +72hs' (Pedido/Tienda/Fecha/Estado/Monto) — así que primero
    probamos identificarla por el NOMBRE de la hoja (contiene 'cancel') para
    no terminar leyendo por error los datos de +72hs."""
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
    st.error(
        "No encontré una hoja con las columnas esperadas "
        "(Pedido, Tienda, Fecha, Estado, Total $) en el archivo subido."
    )
    return None

def load_reclamos_from_xl(xl):
    """Carga Reclamos desde la hoja ya traducida ('Data Reclamos': Reclamo/Pedido/
    Tienda/Tipo/Estado/Fecha) o desde el export crudo del sistema de reclamos
    (ej. 'claim-page-1.xlsx': displayId/typeName/orderCommerceSequentialId/
    storeName/statusName/dateCreated). En el export crudo, sólo se toman las
    filas cuyo typeName contiene la palabra 'reclamo'."""
    if xl is None:
        return None

    # Formato ya traducido (hoja "Data Reclamos" del Reporte diario)
    name, df = find_sheet(xl, ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha"])
    if df is not None:
        return df

    # Formato crudo del sistema de reclamos
    raw_cols = ["displayId", "typeName", "orderCommerceSequentialId", "storeName", "statusName", "dateCreated"]
    name, raw = find_sheet(xl, raw_cols)
    if raw is None:
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
        "Pedido": raw["orderCommerceSequentialId"].apply(
            lambda v: "" if pd.isna(v) else str(int(v))
        ),
        "Tienda": raw["storeName"].apply(norm_txt),
        "Tipo": raw["typeName"].apply(norm_txt),
        "Estado": raw["statusName"].apply(norm_txt),
        "Fecha": pd.to_datetime(raw["dateCreated"], format="%d/%m/%Y %H:%M:%S", errors="coerce"),
    })

def load_reclamos(uploaded_file):
    return load_reclamos_from_xl(safe_open_excel(uploaded_file))

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

def badge(level, label):
    icons = {"good": "●", "warning": "▲", "serious": "▲", "critical": "✕", "neutral": "●"}
    return f'<span class="badge {level}">{icons.get(level,"●")} {label}</span>'

def table_html(df):
    """Tabla de detalle, con el estilo .dashtable en vez del default de pandas."""
    return df.to_html(escape=False, index=False, classes="dashtable", border=0)

def kpi_card(label, value, sub, cls=""):
    return f"""
    <div class="kpi {cls}">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div class="sub">{sub}</div>
    </div>
    """

def resumen_table_html(agg, label_col, col_formatters, total_label="Total general"):
    """Tabla resumen tipo tabla dinámica de Excel: una fila por tienda + una fila
    de 'Total general' resaltada al pie. col_formatters: {columna: función de formato}."""
    cols = list(col_formatters.keys())
    thead = "".join(f"<th>{c}</th>" for c in [label_col] + cols)
    body_rows = []
    for _, r in agg.iterrows():
        tds = f"<td>{r[label_col]}</td>" + "".join(
            f"<td>{col_formatters[c](r[c])}</td>" for c in cols
        )
        body_rows.append(f"<tr>{tds}</tr>")
    total_tds = f"<td>{total_label}</td>" + "".join(
        f"<td>{col_formatters[c](agg[c].sum())}</td>" for c in cols
    )
    body_rows.append(f'<tr class="total-row">{total_tds}</tr>')
    return (
        '<table class="dashtable"><thead><tr>' + thead + '</tr></thead>'
        '<tbody>' + "".join(body_rows) + '</tbody></table>'
    )

def export_section_html(section_title, section_desc, body_html):
    """Arma un HTML standalone (con el mismo look del panel) para descargar una sección sola."""
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
    {brand_html}
    <div class="hero-sub">ALERTAS OPERATIVAS</div>
  </div>
  {corte_html}
</div>
<div class="wrap">
<div class="section">{section_title}</div>
<div class="section-desc">{section_desc}</div>
{body_html}
</div>
</body>
</html>"""

def section_download_button(html_doc, filename, key):
    st.download_button(
        "⬇️ Descargar esta sección (HTML)",
        data=html_doc.encode("utf-8"),
        file_name=filename,
        mime="text/html",
        key=key,
    )

# ---- severity rules (same thresholds as el Pulso Operativo VMont) ----

def sev_pedido_72h(dias):
    if dias >= 10:
        return "critical", "Crítico"
    if dias >= 6:
        return "serious", "Grave"
    return "warning", "Atención"

def sev_reclamo(horas, estado):
    if estado in ("Cerrado", "No aplica-Anulado"):
        return "neutral", estado
    if horas > 72:
        return "critical", ">72h sin acción"
    if horas >= 24:
        return "warning", "24–72h"
    return "good", "<24h"

def sev_ontime(pct):
    if pct >= 95:
        return "good", "OK"
    if pct >= 90:
        return "warning", "Atención"
    if pct >= 80:
        return "serious", "Grave"
    return "critical", "Crítico"

def sev_fr(pct, unidades):
    if not unidades:
        return "neutral", "Sin actividad"
    if pct >= 97:
        return "good", "OK"
    if pct >= 93:
        return "warning", "Atención"
    if pct >= 85:
        return "serious", "Grave"
    return "critical", "Crítico"

def sev_faltante(alta_rotacion):
    if alta_rotacion:
        return "critical", "Alta rotación"
    return "warning", "Faltante"

# ---------------------------------------------------------------------
# HTML de cada sección, generado antes que las tarjetas KPI para poder
# linkearlas directo (clickear la tarjeta baja el HTML de esa sección).
# ---------------------------------------------------------------------

def _body_pedidos(pedidos_f):
    if pedidos_f is None or not len(pedidos_f):
        return None
    show = pedidos_f.copy().sort_values("Dias", ascending=False)
    show["Días"] = show["Dias"].round(1)
    show["Monto"] = show["MontoNum"].apply(money)
    show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Pedido", "Tienda", "Estado", "Fecha", "Días", "Monto", "Urgencia"]
    agg = pedidos_f.groupby("Tienda").agg(
        Cantidad=("Pedido", "count")
    ).reset_index().sort_values("Cantidad", ascending=False)
    resumen_html = resumen_table_html(agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}"})
    return (
        '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )

def html_doc_pedidos(pedidos_f):
    body = _body_pedidos(pedidos_f)
    if body is None:
        return None
    return export_section_html(
        "📦 Pedidos sin movimiento +72hs",
        "Pedidos que llevan más de 3 días en el mismo estado sin avanzar.",
        body
    )

def _body_reclamos(reclamos_f):
    if reclamos_f is None or not len(reclamos_f):
        return None
    abiertos = reclamos_f[reclamos_f["Estado"].isin(["Nuevo", "En proceso"])]
    if not len(abiertos):
        return None
    show = abiertos.copy().sort_values("Horas", ascending=False)
    show["Horas"] = show["Horas"].round(1)
    show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha", "Horas", "Urgencia"]
    agg = abiertos.groupby("Tienda").apply(lambda g: pd.Series({
        "Cantidad": len(g),
        ">72h": int((g["Horas"] > 72).sum()),
        "24–72h": int(((g["Horas"] >= 24) & (g["Horas"] <= 72)).sum()),
    })).reset_index().sort_values("Cantidad", ascending=False)
    resumen_html = resumen_table_html(
        agg, "Tienda",
        {"Cantidad": lambda v: f"{int(v)}", ">72h": lambda v: f"{int(v)}", "24–72h": lambda v: f"{int(v)}"}
    )
    agg_tipo = abiertos.groupby("Tipo").agg(
        Cantidad=("Pedido", "count")
    ).reset_index().sort_values("Cantidad", ascending=False)
    resumen_tipo_html = resumen_table_html(agg_tipo, "Tipo", {"Cantidad": lambda v: f"{int(v)}"})
    return (
        '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
        '<div style="flex:1;min-width:260px;">'
        '<div class="resumen-title">Resumen por tienda (abiertos)</div>' + resumen_html + '</div>'
        '<div style="flex:1;min-width:260px;">'
        '<div class="resumen-title">Resumen por tipo (abiertos)</div>' + resumen_tipo_html + '</div>'
        '</div>'
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )

def html_doc_reclamos(reclamos_f):
    body = _body_reclamos(reclamos_f)
    if body is None:
        return None
    return export_section_html(
        "🗣️ Reclamos operativos",
        "Franjas de alerta: 24hs y 72hs sin acción.",
        body
    )

def prepa_bundle(prepa_f):
    """Arma todo lo que necesita On Time Preparación: detalle, totales y el
    Top 5 de tiendas con peor % on time (por debajo del 95%)."""
    if prepa_f is None or not len(prepa_f):
        return None
    show = prepa_f.copy().sort_values("OntimePct")
    show["Ontime %"] = show["OntimePct"].apply(pct1)
    show["Estado"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    show["Pedidos"] = show["Pedidos"].astype(int)
    show["Fuera de horario"] = show["Fuera"].astype(int)
    detail_cols = ["Tienda", "Formato", "Pedidos", "Fuera de horario", "Ontime %", "Estado"]

    ped_tot = int(prepa_f["Pedidos"].sum())
    fuera_tot = int(prepa_f["Fuera"].sum())
    ot_pct_tot = 100 * (1 - fuera_tot / ped_tot) if ped_tot else 0

    peores = show[show["OntimePct"] < 95].head(5)
    if len(peores):
        top5_html = table_html(peores[detail_cols])
    else:
        top5_html = '<div class="empty-box">Ninguna tienda por debajo del 95% 🎉</div>'

    body = (
        f'<div class="resumen-title">Total — {ped_tot} pedidos · {fuera_tot} fuera de horario · '
        f'{pct1(ot_pct_tot)} on time</div>'
        '<div class="resumen-title" style="margin-top:18px;">Top 5 tiendas con % on time &lt; 95%</div>'
        + top5_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )
    html_doc = export_section_html(
        "⏱️ On Time Preparación",
        "Porcentaje de pedidos preparados en horario, por tienda.",
        body
    )
    return {
        "show": show, "detail_cols": detail_cols, "ped_tot": ped_tot, "fuera_tot": fuera_tot,
        "ot_pct_tot": ot_pct_tot, "top5_html": top5_html, "html_doc": html_doc, "body": body,
    }

def html_doc_prepa(prepa_f):
    b = prepa_bundle(prepa_f)
    return b["html_doc"] if b else None

FR_OBJETIVO = 98

def _body_fr(fr_f):
    if fr_f is None or not len(fr_f):
        return None
    show = fr_f[(fr_f["Unidades"] > 0) & (fr_f["FRPct"] < FR_OBJETIVO)].copy().sort_values("FRPct")
    if not len(show):
        return '<div class="empty-box">Todas las tiendas con venta llegan al objetivo (98%) 🎉</div>'
    show["Unidades"] = show["Unidades"].astype(int)
    show["Sin sustituto"] = show["SinSustituto"].astype(int)
    show["Con sustituto"] = show["ConSustituto"].astype(int)
    show["Monto faltante"] = show["MontoFaltante"].apply(money)
    show["FR %"] = show["FRPct"].apply(pct1)
    show["Estado"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Tienda", "Unidades", "Sin sustituto", "Con sustituto", "Monto faltante", "FR %", "Estado"]
    return table_html(show[detail_cols])

def html_doc_fr(fr_f):
    body = _body_fr(fr_f)
    if body is None:
        return None
    return export_section_html(
        "🧩 Fill Rate — con y sin sustituto",
        "Unidades faltantes por tienda: cubiertas con reemplazo vs. no entregadas.",
        body
    )

def _body_delivery(deliv_f):
    if deliv_f is None or not len(deliv_f):
        return None
    tot_retiro = deliv_f["Retiro"].sum()
    tot_pickup = deliv_f["Pickup"].sum()
    tot_delivery = deliv_f["Delivery"].sum()
    tot_fuera = deliv_f["Fuera"].sum()
    resumen = ""
    for label, val in [("Retiro", tot_retiro), ("Pickup", tot_pickup), ("Delivery", tot_delivery)]:
        share = (val / tot_fuera * 100) if tot_fuera else 0
        resumen += f'<div class="resumen-title" style="margin-top:0;">{label}: {int(val)} ({pct1(share)} del total fuera)</div>'
    show = deliv_f.copy().sort_values("Fuera", ascending=False)
    for c in ["Pedidos", "Retiro", "Pickup", "Delivery", "Fuera"]:
        show[c] = show[c].astype(int)
    show["% Retiro"] = show["% Retiro"].apply(pct1)
    show["% Pickup"] = show["% Pickup"].apply(pct1)
    show["% Delivery"] = show["% Delivery"].apply(pct1)
    detail_cols = ["Tienda", "Formato", "Pedidos", "Fuera", "Retiro", "% Retiro", "Pickup", "% Pickup", "Delivery", "% Delivery"]
    return resumen + table_html(show[detail_cols])

def cancelados_bundle(can_f):
    """Arma el Top 10 de tiendas con más cancelados, el resumen completo por
    tienda y el detalle pedido a pedido, para la sección y para el HTML."""
    if can_f is None or not len(can_f):
        return None
    agg = can_f.groupby("Tienda").agg(
        Cancelados=("Pedido", "count"), Monto=("Total $", "sum")
    ).reset_index().sort_values("Cancelados", ascending=False)

    top10 = agg.head(10)[["Tienda", "Cancelados"]]
    top10_html = resumen_table_html(
        top10, "Tienda", {"Cancelados": lambda v: f"{int(v)}"}, total_label="Total (top 10)"
    )

    resumen_html = resumen_table_html(agg, "Tienda", {"Cancelados": lambda v: f"{int(v)}", "Monto": money})

    det = can_f.copy().sort_values("Fecha", ascending=False)
    det["Total $"] = det["Total $"].apply(money)
    detail_cols = ["Pedido", "Tienda", "Fecha", "Total $"]

    body = (
        '<div class="resumen-title">Top 10 tiendas con más cancelados</div>' + top10_html +
        '<div class="resumen-title" style="margin-top:18px;">Resumen completo por tienda</div>' + resumen_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(det[detail_cols])
    )
    html_doc = export_section_html(
        "🚫 Pedidos cancelados",
        "Cancelaciones por tienda en el período del reporte.",
        body
    )
    return {
        "agg": agg, "top10_html": top10_html, "resumen_html": resumen_html,
        "det": det, "detail_cols": detail_cols, "html_doc": html_doc, "body": body,
    }

def html_doc_cancelados(can_f):
    b = cancelados_bundle(can_f)
    return b["html_doc"] if b else None

def _body_faltantes(falt_f):
    if falt_f is None or not len(falt_f):
        return None
    show = falt_f.copy().sort_values(["Tienda", "Producto"])
    show["SKU"] = show["Producto"]
    show["Código Principal"] = show["CodigoPrincipal"]
    detail_cols = ["Tienda", "Departamento", "SKU", "Código Principal"]
    agg = falt_f.groupby("Tienda").agg(
        Cantidad=("Producto", "count")
    ).reset_index().sort_values("Cantidad", ascending=False)
    resumen_html = resumen_table_html(
        agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}"}
    )
    return (
        '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )

def html_doc_faltantes(falt_f):
    body = _body_faltantes(falt_f)
    if body is None:
        return None
    return export_section_html(
        "📉 Faltantes ECOM",
        "SKUs marcados como faltante para e-commerce, por tienda.",
        body
    )

def export_full_report_html(pedidos_f, reclamos_f, prepa_f, deliv_f, fr_f, can_f, falt_f, filtro_activo=False):
    """Arma un único HTML con las tarjetas KPI de arriba + todas las secciones
    que tengan datos cargados, para bajar de un solo golpe y mandarlo
    (ej. por WhatsApp/mail al jefe)."""
    prepa_b = prepa_bundle(prepa_f)
    can_b = cancelados_bundle(can_f)
    sections = [
        ("📦 Pedidos sin movimiento +72hs", "Pedidos que llevan más de 3 días en el mismo estado sin avanzar.", _body_pedidos(pedidos_f)),
        ("🗣️ Reclamos operativos", "Franjas de alerta: 24hs y 72hs sin acción.", _body_reclamos(reclamos_f)),
        ("⏱️ On Time Preparación", "Porcentaje de pedidos preparados en horario, por tienda.", prepa_b["body"] if prepa_b else None),
        ("🚚 On Time Delivery — por método", "De los pedidos fuera de horario, cuántos correspondieron a cada método de entrega.", _body_delivery(deliv_f)),
        ("🧩 Fill Rate — con y sin sustituto", "Unidades faltantes por tienda: cubiertas con reemplazo vs. no entregadas.", _body_fr(fr_f)),
        ("🚫 Pedidos cancelados", "Cancelaciones por tienda en el período del reporte.", can_b["body"] if can_b else None),
        ("📉 Faltantes ECOM", "SKUs marcados como faltante para e-commerce, por tienda.", _body_faltantes(falt_f)),
    ]
    sections = [(title, desc, body) for title, desc, body in sections if body]
    if not sections:
        return None

    kpis = build_kpis(pedidos_f, reclamos_f, prepa_f, fr_f, can_f, falt_f, filtro_activo=filtro_activo)
    kpi_row_html = f'<div class="kpi-row">{"".join(kpis)}</div>' if kpis else ""

    corte_html = ""
    if now_ref is not None:
        corte_html = (
            '<div class="hero-date">Corte del reporte<br>'
            f'<small>{now_ref.strftime("%d/%m/%Y %H:%M")}</small></div>'
        )
    blocks_html = "".join(
        f'<div class="section">{title}</div><div class="section-desc">{desc}</div>{body}'
        f'<div style="height:26px;"></div>'
        for title, desc, body in sections
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>MásOnline · Reporte Operativo Completo</title>
<style>
{APP_CSS}
body {{ margin:0; background:#fafaf8; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }}
.wrap {{ max-width: 1400px; margin: 0 auto; padding: 0 20px 28px; }}
</style>
</head>
<body>
<div class="hero">
  <div>
    {brand_html}
    <div class="hero-sub">ALERTAS OPERATIVAS — REPORTE COMPLETO</div>
  </div>
  {corte_html}
</div>
<div class="wrap">
{kpi_row_html}
{blocks_html}
</div>
</body>
</html>"""

def kpi_link_wrap(inner_html, html_doc, filename):
    """Envuelve una tarjeta KPI en un link que descarga el HTML de esa sección al clickearla."""
    if not html_doc:
        return inner_html
    b64 = base64.b64encode(html_doc.encode("utf-8")).decode("utf-8")
    return (
        f'<a class="kpi-link" href="data:text/html;base64,{b64}" download="{filename}" '
        'title="Descargar esta sección como HTML">' + inner_html + '</a>'
    )

def build_kpis(pedidos_f, reclamos_f, prepa_f, fr_f, can_f, falt_f, filtro_activo=False):
    """Arma las tarjetas KPI de arriba de todo (clickeables para bajar el HTML
    de esa sección). Se usa tanto para la fila en pantalla como para incluirlas
    arriba del HTML combinado."""
    kpis = []
    if pedidos_f is not None:
        card = kpi_card(
            "Pedidos +72h sin mover", f"{len(pedidos_f)}",
            f"{money(pedidos_f['MontoNum'].sum())} en pedidos",
            "crit" if len(pedidos_f) > 0 else "good"
        )
        kpis.append(kpi_link_wrap(card, html_doc_pedidos(pedidos_f), "operativo_pedidos_72h.html"))
    if reclamos_f is not None:
        abiertos = reclamos_f[reclamos_f["Estado"].isin(["Nuevo", "En proceso"])]
        r72 = (abiertos["Horas"] > 72).sum()
        r24 = ((abiertos["Horas"] >= 24) & (abiertos["Horas"] <= 72)).sum()
        card = kpi_card(
            "Reclamos abiertos", f"{len(abiertos)}",
            f"{r72} &gt;72h · {r24} 24–72h",
            "crit" if r72 > 0 else ("warn" if r24 > 0 else "good")
        )
        kpis.append(kpi_link_wrap(card, html_doc_reclamos(reclamos_f), "operativo_reclamos.html"))
    if prepa_f is not None and len(prepa_f):
        ped_tot = prepa_f["Pedidos"].sum()
        fuera_tot = prepa_f["Fuera"].sum()
        ot_pct = 100 * (1 - fuera_tot / ped_tot) if ped_tot else 0
        card = kpi_card(
            "On time preparación", pct1(ot_pct),
            f"Total: {int(ped_tot)} pedidos · {int(fuera_tot)} fuera de horario",
            "good" if ot_pct >= 95 else ("warn" if ot_pct >= 90 else "crit")
        )
        kpis.append(kpi_link_wrap(card, html_doc_prepa(prepa_f), "operativo_ontime_preparacion.html"))
    if fr_f is not None and len(fr_f):
        if fr_total_declared is not None and not filtro_activo:
            # Usamos el % de FR que ya viene calculado en la fila "TOTAL" de la
            # planilla (coincide siempre con lo que ve Emi ahí), en vez de
            # recalcularlo nosotros sumando tienda por tienda. Solo vale para
            # el total SIN filtrar — con un filtro de Tienda/Auditor activo,
            # ese "TOTAL" de la planilla ya no representa lo que se está
            # mostrando.
            sin_tot = fr_total_declared["sin"]
            fr_pct_tot = fr_total_declared["fr_pct"]
        elif len(fr_f) == 1:
            # Una sola tienda: usamos el % que ya trae esa fila de la planilla
            # (mismo criterio que para el TOTAL general), en vez de
            # recalcularlo — así también coincide siempre con lo que ve Emi.
            sin_tot = fr_f["SinSustituto"].iloc[0]
            fr_pct_tot = fr_f["FRPct"].iloc[0]
        else:
            # Varias tiendas juntas (ej. las de un auditor): no hay una fila
            # de "TOTAL" de ese subconjunto en la planilla, así que estimamos
            # ponderando por unidades. Puede no coincidir 100% con un cálculo
            # manual de ese grupo en la planilla.
            unid_tot = fr_f["Unidades"].sum()
            sin_tot = fr_f["SinSustituto"].sum()
            con_tot = fr_f["ConSustituto"].sum()
            fr_pct_tot = 100 * (1 - (sin_tot + con_tot) / unid_tot) if unid_tot else 0
        card = kpi_card(
            "Fill rate (con+sin sust.)", pct1(fr_pct_tot),
            f"{int(sin_tot)} unid. sin sustituto",
            "good" if fr_pct_tot >= 97 else ("warn" if fr_pct_tot >= 93 else "crit")
        )
        kpis.append(kpi_link_wrap(card, html_doc_fr(fr_f), "operativo_fill_rate.html"))
    if can_f is not None:
        card = kpi_card(
            "Pedidos cancelados", f"{len(can_f)}",
            f"{money(can_f['Total $'].sum())} totales"
        )
        kpis.append(kpi_link_wrap(card, html_doc_cancelados(can_f), "operativo_cancelados.html"))
    if falt_f is not None:
        card = kpi_card(
            "SKUs faltantes ECOM", f"{len(falt_f)}",
            "",
            "warn" if len(falt_f) > 0 else "good"
        )
        kpis.append(kpi_link_wrap(card, html_doc_faltantes(falt_f), "operativo_faltantes.html"))
    return kpis

# ---------------------------------------------------------------------
# Header + uploaders
# ---------------------------------------------------------------------

# El logo vive en la raíz del repo; esta página está un nivel adentro (pages/).
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"
if LOGO_FILE.exists():
    logo_b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode("utf-8")
    brand_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        'style="height:48px;max-width:280px;object-fit:contain;">'
    )
else:
    brand_html = '<div class="hero-brand">🚨 Operativo</div>'

st.markdown(f"""
<div class="hero">
  <div>
    {brand_html}
    <div class="hero-sub">ALERTAS OPERATIVAS</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin-bottom:14px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    CARGAR REPORTES
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí el "Reporte diario.xlsx" completo una sola vez: detecto solas todas las hojas
    (Pedidos +72h, Reclamos, On Time, Fill Rate, Cancelados) por sus columnas y armo
    todas las secciones de abajo. Faltantes viene siempre en un archivo aparte.
  </div>
</div>
""", unsafe_allow_html=True)

def upload_box(col, title, help_text, key):
    with col:
        st.markdown(f"""
        <div class="upload-box">
          <div class="upload-title">{title}</div>
          <div class="upload-text">{help_text}</div>
        </div>
        """, unsafe_allow_html=True)
        return st.file_uploader(title, type=["xlsx", "xls"], key=key, label_visibility="collapsed")

u1, u2 = st.columns([3, 1])
f_reporte = upload_box(
    u1, "REPORTE DIARIO COMPLETO",
    "El Reporte diario.xlsx de siempre, con todas las hojas: Pedidos +72h, Reclamos, On Time y Fill Rate.",
    "f_reporte"
)
f_faltantes = upload_box(u2, "FALTANTES", "SKUs marcados como faltante ECOM por tienda.", "f_faltantes")

reporte_bytes, reporte_es_nuevo = get_shared_bytes(f_reporte, SHARED_REPORTE_PATH)
faltantes_bytes, faltantes_es_nuevo = get_shared_bytes(f_faltantes, SHARED_FALTANTES_PATH)

if (reporte_bytes is not None and not reporte_es_nuevo) or (faltantes_bytes is not None and not faltantes_es_nuevo):
    st.markdown(
        '<div style="font-size:11.5px;color:#0ca30c;font-weight:700;margin:-2px 0 2px;">'
        '● Mostrando el último reporte que subieron — no hace falta que subas nada para verlo actualizado.</div>',
        unsafe_allow_html=True
    )

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Parse each section
# ---------------------------------------------------------------------

now_ref = None  # se calcula como el máximo timestamp visto en los archivos cargados

xl_reporte = safe_open_excel(io.BytesIO(reporte_bytes)) if reporte_bytes is not None else None
df_72h_raw = load_section_from_xl(xl_reporte, ["Pedido", "Tienda", "Fecha", "Estado", "Monto"])
df_reclamos_raw = load_reclamos_from_xl(xl_reporte)
df_ontime_raw = load_section_from_xl(xl_reporte, ["Tienda", "Pedifod", "Fuera", "ONTIME"])
df_fr_raw = load_fr_from_xl(xl_reporte)
df_cancelados_raw = load_cancelados_from_xl(xl_reporte)
xl_faltantes = safe_open_excel(io.BytesIO(faltantes_bytes)) if faltantes_bytes is not None else None
df_faltantes_raw = load_section_from_xl(
    xl_faltantes,
    ["Tienda@DESC", "SKU@DESC", "Etiqueta_Stock", "Dias sin venta"]
)

candidate_times = []

pedidos_72h = None
if df_72h_raw is not None:
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
if df_cancelados_raw is not None:
    d = df_cancelados_raw.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    cancelados = d

if candidate_times:
    now_ref = max([t for t in candidate_times if pd.notna(t)])
else:
    now_ref = pd.Timestamp(datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None))

# ---- Pedidos +72h ----
if pedidos_72h is not None:
    pedidos_72h["Dias"] = (now_ref - pedidos_72h["Fecha"]).dt.total_seconds() / 86400
    pedidos_72h = pedidos_72h[pedidos_72h["Dias"] >= 3].copy()
    pedidos_72h["MontoNum"] = pedidos_72h["Monto"].apply(ar_number)
    pedidos_72h["Tienda"] = pedidos_72h["Tienda"].apply(norm_txt)
    pedidos_72h[["Sev", "SevLabel"]] = pedidos_72h["Dias"].apply(
        lambda d: pd.Series(sev_pedido_72h(d))
    )

# ---- Reclamos ----
if reclamos is not None:
    reclamos["Horas"] = (now_ref - reclamos["Fecha"]).dt.total_seconds() / 3600
    reclamos["Tienda"] = reclamos["Tienda"].apply(norm_txt)
    reclamos["Estado"] = reclamos["Estado"].apply(norm_txt)
    reclamos["Tipo"] = reclamos["Tipo"].apply(norm_txt)
    reclamos[["Sev", "SevLabel"]] = reclamos.apply(
        lambda r: pd.Series(sev_reclamo(r["Horas"], r["Estado"])), axis=1
    )

# ---- On Time (Preparación directo + Delivery por método) ----
ontime_prepa = None
ontime_delivery = None
if df_ontime_raw is not None:
    d = df_ontime_raw.copy()
    for c in ["Pedifod", "Retiro", "Pickup", "Delivery", "Fuera"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
        else:
            d[c] = 0
    d["Tienda"] = d["Tienda"].apply(norm_txt)
    d = d[~d["Tienda"].str.upper().isin(["TOTAL", "TOTA"])]
    d = d.rename(columns={"Pedifod": "Pedidos"})

    # ONTIME puede venir como número (fracción 0-1 o ya en %) o como texto con
    # '%' en notación estándar (ej. "50.0%") — algunos días el export cambia
    # el formato, así que probamos ambas lecturas con ar_pct.
    if "ONTIME" in d.columns:
        ontime_parsed = d["ONTIME"].apply(ar_pct)
    else:
        ontime_parsed = pd.Series([None] * len(d), index=d.index)
    ontime_raw = ontime_parsed.astype(float).fillna(0.0)
    valid_max = ontime_parsed.dropna().max() if ontime_parsed.notna().any() else 0
    d["OntimePct"] = ontime_raw * 100 if (pd.notna(valid_max) and valid_max <= 1.5) else ontime_raw

    # Preparación: % on time directo, por tienda
    prepa = d[["Tienda", "Formato", "Pedidos", "Fuera", "OntimePct"]].copy()
    prepa[["Sev", "SevLabel"]] = prepa["OntimePct"].apply(lambda p: pd.Series(sev_ontime(p)))
    ontime_prepa = prepa

    # Delivery: pedidos fuera de horario, discriminados por método de entrega
    deliv = d[["Tienda", "Formato", "Pedidos", "Retiro", "Pickup", "Delivery", "Fuera"]].copy()
    deliv["% Retiro"] = np.where(deliv["Fuera"] > 0, deliv["Retiro"] / deliv["Fuera"] * 100, 0)
    deliv["% Pickup"] = np.where(deliv["Fuera"] > 0, deliv["Pickup"] / deliv["Fuera"] * 100, 0)
    deliv["% Delivery"] = np.where(deliv["Fuera"] > 0, deliv["Delivery"] / deliv["Fuera"] * 100, 0)
    ontime_delivery = deliv

# ---- Fill Rate ----
fill_rate = None
fr_total_declared = None
if df_fr_raw is not None:
    d = df_fr_raw.copy()
    fr_cols = list(d.columns)
    unidades_plus_col = "Unidades +" if "Unidades +" in d.columns else None
    no_entregado_plus_col = "No entregado +" if "No entregado +" in d.columns else None
    reemplazo_plus_col = "Reemplazo +" if "Reemplazo +" in d.columns else None

    # Algunos exports del día vienen "compactados": las columnas limpias
    # (Reemplazo/Monto/FR/Limpio) llegan vacías y los datos reales quedan
    # corridos hacia las primeras 6 columnas del archivo (Tienda+, Unidades+,
    # No entregado+, Reemplazo+, Monto N/E+, FR+), aunque el encabezado siga
    # teniendo las 13 columnas de siempre. Si detectamos eso, leemos por
    # posición en vez de por nombre de columna para no mezclar los valores.
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
                _fr_tot = ar_pct(vals.iloc[5])
                if _fr_tot is not None:
                    fr_total_declared = {
                        "unidades": ar_number(vals.iloc[1]),
                        "sin": ar_number(vals.iloc[2]),
                        "con": ar_number(vals.iloc[3]),
                        "fr_pct": _fr_tot,
                    }
                continue
            unidades = ar_number(vals.iloc[1])
            sin_sustituto = ar_number(vals.iloc[2])
            con_sustituto = ar_number(vals.iloc[3])
            monto_faltante = ar_number(vals.iloc[4])
            fr_pct = ar_pct(vals.iloc[5])
            fr_pct = fr_pct if fr_pct is not None else 0.0
        else:
            tienda = norm_txt(r.get("Tienda"))
            if tienda.strip().upper() in ("TOTAL", "TOTA"):
                _limpio_tot = r.get("Limpio")
                if pd.notna(_limpio_tot):
                    _fr_tot = float(_limpio_tot) * 100
                else:
                    _fr_tot = ar_pct(r.get("FR"))
                if _fr_tot is not None:
                    _unid_tot_row = ar_number(r.get(unidades_plus_col)) if unidades_plus_col else ar_number(r.get("Unidades"))
                    _sin_tot_row = ar_number(r.get(no_entregado_plus_col)) if no_entregado_plus_col else ar_number(r.get("no entregado"))
                    _con_tot_row = ar_number(r.get(reemplazo_plus_col)) if reemplazo_plus_col else ar_number(r.get("Reemplazo"))
                    fr_total_declared = {
                        "unidades": _unid_tot_row, "sin": _sin_tot_row,
                        "con": _con_tot_row, "fr_pct": _fr_tot,
                    }
                continue
            unidades = ar_number(r.get(unidades_plus_col)) if unidades_plus_col else ar_number(r.get("Unidades"))
            sin_sustituto = ar_number(r.get(no_entregado_plus_col)) if no_entregado_plus_col else ar_number(r.get("no entregado"))
            con_sustituto = ar_number(r.get(reemplazo_plus_col)) if reemplazo_plus_col else ar_number(r.get("Reemplazo"))
            monto_faltante = r.get("Monto")
            monto_faltante = float(monto_faltante) if pd.notna(monto_faltante) and isinstance(monto_faltante, (int, float, np.integer, np.floating)) else ar_number(r.get("Monto N/E +"))
            limpio = r.get("Limpio")
            if pd.notna(limpio):
                fr_pct = float(limpio) * 100
            else:
                fr_pct = ar_pct(r.get("FR"))
                fr_pct = fr_pct if fr_pct is not None else 0.0
        rows.append({
            "Tienda": tienda, "Unidades": unidades, "SinSustituto": sin_sustituto,
            "ConSustituto": con_sustituto, "MontoFaltante": monto_faltante, "FRPct": fr_pct
        })
    fr_df = pd.DataFrame(rows)
    fr_df[["Sev", "SevLabel"]] = fr_df.apply(
        lambda r: pd.Series(sev_fr(r["FRPct"], r["Unidades"])), axis=1
    )
    fill_rate = fr_df

# ---- Cancelados ----
if cancelados is not None:
    cancelados["Tienda"] = cancelados["Tienda"].apply(norm_txt)
    # "Total $" no siempre viene en el export (algunos días la hoja no trae esa
    # columna, o la trae vacía) — en ese caso usamos "Monto" (ej. "$330K"),
    # que es la que sí viene siempre con el importe.
    if "Total $" in cancelados.columns:
        _total_num = pd.to_numeric(cancelados["Total $"], errors="coerce")
    else:
        _total_num = pd.Series([np.nan] * len(cancelados), index=cancelados.index)
    _monto_num = cancelados.get("Monto", pd.Series([np.nan] * len(cancelados), index=cancelados.index)).apply(ar_number)
    cancelados["Total $"] = _total_num.fillna(_monto_num).fillna(0)

# ---- Faltantes ----
faltantes = None
if df_faltantes_raw is not None:
    d = df_faltantes_raw.copy()
    d["Tienda"] = d["Tienda@DESC"].apply(norm_txt)
    d["Producto"] = d["SKU@DESC"].apply(norm_txt) if "SKU@DESC" in d.columns else ""
    d["Categoria"] = d["Clase@DESC"].apply(norm_txt) if "Clase@DESC" in d.columns else ""
    d["Departamento"] = d["Departamento@DESC"].apply(norm_txt) if "Departamento@DESC" in d.columns else ""
    _cod_col = next(
        (c for c in ["Codigo Principal", "Código Principal", "CodigoPrincipal", "Codigo_Principal"] if c in d.columns),
        None
    )
    d["CodigoPrincipal"] = d[_cod_col].apply(norm_txt) if _cod_col else ""
    d["DiasSinVenta"] = pd.to_numeric(d.get("Dias sin venta"), errors="coerce")
    d["VentaProm"] = pd.to_numeric(d.get("Venta Promedio Semanal"), errors="coerce").fillna(0)
    alta_col = "ALTA_ROTACION" if "ALTA_ROTACION" in d.columns else "Alerta_Alta_Rotacion"
    d["AltaRotacion"] = d.get(alta_col, "No").apply(lambda v: norm_txt(v).lower() in ("si", "sí", "yes", "true", "1"))
    d["Etiqueta"] = d.get("Etiqueta_Stock", "").apply(norm_txt)
    d = d[d["Etiqueta"] != ""]
    d[["Sev", "SevLabel"]] = d["AltaRotacion"].apply(lambda a: pd.Series(sev_faltante(a)))
    faltantes = d

# ---------------------------------------------------------------------
# Unificar nombres de tienda entre hojas (mayúsc/minúsc, prefijo "Sucursal")
# y armar el filtro de tienda
# ---------------------------------------------------------------------

_canon_map = build_tienda_canon_map(
    [pedidos_72h, reclamos, ontime_prepa, ontime_delivery, fill_rate, cancelados, faltantes]
)
pedidos_72h = apply_tienda_canon(pedidos_72h, _canon_map)
reclamos = apply_tienda_canon(reclamos, _canon_map)
ontime_prepa = apply_tienda_canon(ontime_prepa, _canon_map)
ontime_delivery = apply_tienda_canon(ontime_delivery, _canon_map)
fill_rate = apply_tienda_canon(fill_rate, _canon_map)
cancelados = apply_tienda_canon(cancelados, _canon_map)
faltantes = apply_tienda_canon(faltantes, _canon_map)

all_stores = set()
for d in [pedidos_72h, reclamos, ontime_prepa, fill_rate, cancelados, faltantes]:
    if d is not None and "Tienda" in d.columns:
        all_stores.update([s for s in d["Tienda"].unique() if s])

any_data_loaded = len(all_stores) > 0

if any_data_loaded:
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
      <div style="font-size:12px;color:#6b7280;">
        Corte del reporte: <b style="color:#20252b;">{now_ref.strftime('%d/%m/%Y %H:%M')}</b>
      </div>
    </div>
    """, unsafe_allow_html=True)

    auditores = sorted({a for a in (get_auditor(s) for s in all_stores) if a})
    col_aud, col_tda = st.columns([1, 2])
    with col_aud:
        auditor_sel = st.selectbox("Auditor", ["Todos los auditores"] + auditores)
    filtro_auditor = None if auditor_sel == "Todos los auditores" else auditor_sel

    # Si hay un auditor elegido, el desplegable de Tienda se acota a sus tiendas.
    stores_disponibles = (
        {s for s in all_stores if get_auditor(s) == filtro_auditor}
        if filtro_auditor else all_stores
    )
    with col_tda:
        tienda_sel = st.selectbox("Tienda", ["Todas las tiendas"] + sorted(stores_disponibles))
    filtro_tienda = None if tienda_sel == "Todas las tiendas" else tienda_sel

    def ftr(d):
        if d is None:
            return d
        if filtro_tienda is not None:
            return d[d["Tienda"] == filtro_tienda]
        if filtro_auditor is not None:
            return d[d["Tienda"].apply(get_auditor) == filtro_auditor]
        return d

    pedidos_f = ftr(pedidos_72h)
    reclamos_f = ftr(reclamos)
    prepa_f = ftr(ontime_prepa)
    deliv_f = ftr(ontime_delivery)
    fr_f = ftr(fill_rate)
    can_f = ftr(cancelados)
    falt_f = ftr(faltantes)

    filtro_activo = filtro_tienda is not None or filtro_auditor is not None

    # ---- KPI row ----
    kpis = build_kpis(pedidos_f, reclamos_f, prepa_f, fr_f, can_f, falt_f, filtro_activo=filtro_activo)

    if kpis:
        st.markdown(f'<div class="kpi-row">{"".join(kpis)}</div>', unsafe_allow_html=True)

    # ---- Descargar todo junto (para mandar al jefe) ----
    _full_report_html = export_full_report_html(
        pedidos_f, reclamos_f, prepa_f, deliv_f, fr_f, can_f, falt_f, filtro_activo=filtro_activo
    )
    if _full_report_html:
        st.download_button(
            "📋 Descargar TODO en un solo HTML (para mandar/capturar)",
            data=_full_report_html.encode("utf-8"),
            file_name="operativo_reporte_completo.html",
            mime="text/html",
            key="dl_full_report",
            use_container_width=True,
        )

    # ---- Pedidos +72h ----
    st.markdown(
        '<div class="section">📦 Pedidos sin movimiento +72hs</div>'
        '<div class="section-desc">Pedidos que llevan más de 3 días en el mismo estado sin avanzar.</div>',
        unsafe_allow_html=True
    )
    if pedidos_f is not None:
        if len(pedidos_f):
            show = pedidos_f.copy().sort_values("Dias", ascending=False)
            show["Días"] = show["Dias"].round(1)
            show["Monto"] = show["MontoNum"].apply(money)
            show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
            detail_cols = ["Pedido", "Tienda", "Estado", "Fecha", "Días", "Monto", "Urgencia"]

            agg = pedidos_f.groupby("Tienda").agg(
                Cantidad=("Pedido", "count")
            ).reset_index().sort_values("Cantidad", ascending=False)

            st.markdown('<div class="resumen-title">Resumen por tienda</div>', unsafe_allow_html=True)
            resumen_html = resumen_table_html(
                agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}"}
            )
            st.write(resumen_html, unsafe_allow_html=True)

            with st.expander(f"Ver detalle de pedidos ({len(show)})"):
                with st.container(height=380):
                    st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

            export_body = (
                '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
                '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
                + table_html(show[detail_cols])
            )
            html_doc = export_section_html(
                "📦 Pedidos sin movimiento +72hs",
                "Pedidos que llevan más de 3 días en el mismo estado sin avanzar.",
                export_body
            )
            section_download_button(html_doc, "operativo_pedidos_72h.html", "dl_72h")
        else:
            st.markdown('<div class="empty-box">Sin pedidos estancados para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Pedidos +72hs para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Reclamos ----
    st.markdown(
        f'<div class="section">🗣️ Reclamos operativos '
        f'<span class="count-pill">{len(reclamos_f) if reclamos_f is not None else 0}</span></div>'
        '<div class="section-desc">Franjas de alerta: 24hs y 72hs sin acción.</div>',
        unsafe_allow_html=True
    )
    if reclamos_f is not None:
        solo_abiertos = st.checkbox("Mostrar solo abiertos (Nuevo / En proceso)", value=True, key="chk_reclamos")
        show = reclamos_f.copy()
        if solo_abiertos:
            show = show[show["Estado"].isin(["Nuevo", "En proceso"])]
        if len(show):
            show = show.sort_values("Horas", ascending=False)
            show["Horas"] = show["Horas"].round(1)
            show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
            detail_cols = ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha", "Horas", "Urgencia"]

            base = reclamos_f.copy()
            if solo_abiertos:
                base = base[base["Estado"].isin(["Nuevo", "En proceso"])]
            agg = base.groupby("Tienda").apply(lambda g: pd.Series({
                "Cantidad": len(g),
                ">72h": int((g["Horas"] > 72).sum()),
                "24–72h": int(((g["Horas"] >= 24) & (g["Horas"] <= 72)).sum()),
            })).reset_index().sort_values("Cantidad", ascending=False)
            agg_tipo = base.groupby("Tipo").agg(
                Cantidad=("Pedido", "count")
            ).reset_index().sort_values("Cantidad", ascending=False)

            resumen_html = resumen_table_html(
                agg, "Tienda",
                {"Cantidad": lambda v: f"{int(v)}", ">72h": lambda v: f"{int(v)}", "24–72h": lambda v: f"{int(v)}"}
            )
            resumen_tipo_html = resumen_table_html(agg_tipo, "Tipo", {"Cantidad": lambda v: f"{int(v)}"})
            resumen_side_by_side = (
                '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Resumen por tienda</div>' + resumen_html + '</div>'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Resumen por tipo</div>' + resumen_tipo_html + '</div>'
                '</div>'
            )
            export_body = (
                resumen_side_by_side +
                '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
                + table_html(show[detail_cols])
            )
            html_doc = export_section_html(
                "🗣️ Reclamos operativos",
                "Franjas de alerta: 24hs y 72hs sin acción.",
                export_body
            )

            r72_tot = int((base["Horas"] > 72).sum())
            r24_tot = int(((base["Horas"] >= 24) & (base["Horas"] <= 72)).sum())
            mini_card = kpi_card(
                "Reclamos abiertos" if solo_abiertos else "Reclamos (todos)", f"{len(show)}",
                f"{r72_tot} &gt;72h · {r24_tot} 24–72h — clickeá para bajar el HTML",
                "crit" if r72_tot > 0 else ("warn" if r24_tot > 0 else "good")
            )
            st.markdown(
                f'<div class="kpi-row" style="margin:4px 0 14px; grid-template-columns: minmax(230px, 340px);">'
                f'{kpi_link_wrap(mini_card, html_doc, "operativo_reclamos.html")}</div>',
                unsafe_allow_html=True
            )

            col_tienda, col_tipo = st.columns(2)
            with col_tienda:
                st.markdown('<div class="resumen-title">Resumen por tienda</div>', unsafe_allow_html=True)
                st.write(resumen_html, unsafe_allow_html=True)
            with col_tipo:
                st.markdown('<div class="resumen-title">Resumen por tipo</div>', unsafe_allow_html=True)
                st.write(resumen_tipo_html, unsafe_allow_html=True)

            with st.expander(f"Ver detalle de reclamos ({len(show)})"):
                with st.container(height=380):
                    st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

            section_download_button(html_doc, "operativo_reclamos.html", "dl_reclamos")
        else:
            st.markdown('<div class="empty-box">Sin reclamos para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Reclamos para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- On Time Preparación ----
    st.markdown(
        f'<div class="section">⏱️ On Time Preparación '
        f'<span class="count-pill">{len(prepa_f) if prepa_f is not None else 0}</span></div>'
        '<div class="section-desc">Porcentaje de pedidos preparados en horario, por tienda.</div>',
        unsafe_allow_html=True
    )
    if prepa_f is not None and len(prepa_f):
        b = prepa_bundle(prepa_f)
        show, detail_cols, html_doc = b["show"], b["detail_cols"], b["html_doc"]

        mini_card = kpi_card(
            "On time preparación", pct1(b["ot_pct_tot"]),
            f"Total: {b['ped_tot']} pedidos · {b['fuera_tot']} fuera de horario — clickeá para bajar el HTML",
            "good" if b["ot_pct_tot"] >= 95 else ("warn" if b["ot_pct_tot"] >= 90 else "crit")
        )
        st.markdown(
            f'<div class="kpi-row" style="margin:4px 0 14px; grid-template-columns: minmax(230px, 340px);">'
            f'{kpi_link_wrap(mini_card, html_doc, "operativo_ontime_preparacion.html")}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="resumen-title">Top 5 tiendas con % on time &lt; 95%</div>',
            unsafe_allow_html=True
        )
        st.write(b["top5_html"], unsafe_allow_html=True)

        st.markdown('<div class="resumen-title" style="margin-top:14px;">Detalle completo</div>', unsafe_allow_html=True)
        with st.container(height=380):
            st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

        section_download_button(html_doc, "operativo_ontime_preparacion.html", "dl_prepa")
    else:
        st.markdown('<div class="empty-box">Subí el archivo de On Time para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- On Time Delivery (por método) ----
    st.markdown(
        f'<div class="section">🚚 On Time Delivery — por método '
        f'<span class="count-pill">{len(deliv_f) if deliv_f is not None else 0}</span></div>'
        '<div class="section-desc">De los pedidos fuera de horario, cuántos correspondieron a cada método de entrega.</div>',
        unsafe_allow_html=True
    )
    if deliv_f is not None and len(deliv_f):
        tot_retiro = deliv_f["Retiro"].sum()
        tot_pickup = deliv_f["Pickup"].sum()
        tot_delivery = deliv_f["Delivery"].sum()
        tot_fuera = deliv_f["Fuera"].sum()
        c1, c2, c3 = st.columns(3)
        for col, label, val in zip(
            [c1, c2, c3],
            ["Retiro", "Pickup", "Delivery"],
            [tot_retiro, tot_pickup, tot_delivery]
        ):
            share = (val / tot_fuera * 100) if tot_fuera else 0
            with col:
                st.markdown(kpi_card(f"FUERA DE HORARIO · {label.upper()}", f"{int(val)}", f"{pct1(share)} del total fuera"), unsafe_allow_html=True)
        show = deliv_f.copy().sort_values("Fuera", ascending=False)
        for c in ["Pedidos", "Retiro", "Pickup", "Delivery", "Fuera"]:
            show[c] = show[c].astype(int)
        show["% Retiro"] = show["% Retiro"].apply(pct1)
        show["% Pickup"] = show["% Pickup"].apply(pct1)
        show["% Delivery"] = show["% Delivery"].apply(pct1)
        detail_cols = ["Tienda", "Formato", "Pedidos", "Fuera", "Retiro", "% Retiro", "Pickup", "% Pickup", "Delivery", "% Delivery"]
        with st.container(height=380):
            st.write(table_html(show[detail_cols]), unsafe_allow_html=True)
        html_doc = export_section_html(
            "🚚 On Time Delivery — por método",
            "De los pedidos fuera de horario, cuántos correspondieron a cada método de entrega.",
            table_html(show[detail_cols])
        )
        section_download_button(html_doc, "operativo_ontime_delivery.html", "dl_delivery")
    else:
        st.markdown('<div class="empty-box">Subí el archivo de On Time para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Fill Rate ----
    fr_below = fr_f[(fr_f["Unidades"] > 0) & (fr_f["FRPct"] < FR_OBJETIVO)] if fr_f is not None else None
    st.markdown(
        f'<div class="section">🧩 Fill Rate — con y sin sustituto '
        f'<span class="count-pill">{len(fr_below) if fr_below is not None else 0}</span></div>'
        f'<div class="section-desc">Tiendas con venta que no llegan al objetivo ({FR_OBJETIVO}%). '
        'Unidades faltantes: cubiertas con reemplazo vs. no entregadas.</div>',
        unsafe_allow_html=True
    )
    if fr_f is not None and len(fr_f):
        if len(fr_below):
            show = fr_below.copy().sort_values("FRPct")
            show["Unidades"] = show["Unidades"].astype(int)
            show["Sin sustituto"] = show["SinSustituto"].astype(int)
            show["Con sustituto"] = show["ConSustituto"].astype(int)
            show["Monto faltante"] = show["MontoFaltante"].apply(money)
            show["FR %"] = show["FRPct"].apply(pct1)
            show["Estado"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
            detail_cols = ["Tienda", "Unidades", "Sin sustituto", "Con sustituto", "Monto faltante", "FR %", "Estado"]
            with st.container(height=380):
                st.write(table_html(show[detail_cols]), unsafe_allow_html=True)
            html_doc = export_section_html(
                "🧩 Fill Rate — con y sin sustituto",
                f"Tiendas con venta que no llegan al objetivo ({FR_OBJETIVO}%).",
                table_html(show[detail_cols])
            )
            section_download_button(html_doc, "operativo_fill_rate.html", "dl_fr")
        else:
            st.markdown('<div class="empty-box">Todas las tiendas con venta llegan al objetivo (98%) 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Fill Rate para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Cancelados ----
    st.markdown(
        f'<div class="section">🚫 Pedidos cancelados '
        f'<span class="count-pill">{len(can_f) if can_f is not None else 0}</span></div>'
        '<div class="section-desc">Cancelaciones por tienda en el período del reporte.</div>',
        unsafe_allow_html=True
    )
    if can_f is not None:
        if len(can_f):
            b = cancelados_bundle(can_f)

            st.markdown('<div class="resumen-title">Top 10 tiendas con más cancelados</div>', unsafe_allow_html=True)
            st.write(b["top10_html"], unsafe_allow_html=True)

            with st.expander(f"Ver resumen completo por tienda ({len(b['agg'])} tiendas)"):
                st.write(b["resumen_html"], unsafe_allow_html=True)

            with st.expander(f"Ver detalle de pedidos cancelados ({len(b['det'])})"):
                with st.container(height=380):
                    st.write(table_html(b["det"][b["detail_cols"]]), unsafe_allow_html=True)

            section_download_button(b["html_doc"], "operativo_cancelados.html", "dl_cancelados")
        else:
            st.markdown('<div class="empty-box">Sin cancelaciones para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Cancelados para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Faltantes ----
    st.markdown(
        f'<div class="section">📉 Faltantes ECOM '
        f'<span class="count-pill">{len(falt_f) if falt_f is not None else 0}</span></div>'
        '<div class="section-desc">SKUs marcados como faltante para e-commerce, por tienda.</div>',
        unsafe_allow_html=True
    )
    if falt_f is not None:
        if len(falt_f):
            show = falt_f.copy().sort_values(["Tienda", "Producto"])
            show["SKU"] = show["Producto"]
            show["Código Principal"] = show["CodigoPrincipal"]
            detail_cols = ["Tienda", "Departamento", "SKU", "Código Principal"]

            agg = falt_f.groupby("Tienda").agg(
                Cantidad=("Producto", "count")
            ).reset_index()
            agg = agg.sort_values("Cantidad", ascending=False)

            st.markdown('<div class="resumen-title">Resumen por tienda</div>', unsafe_allow_html=True)
            resumen_html = resumen_table_html(
                agg, "Tienda",
                {"Cantidad": lambda v: f"{int(v)}"}
            )
            st.write(resumen_html, unsafe_allow_html=True)

            with st.expander(f"Ver detalle de faltantes ({len(show)})"):
                with st.container(height=380):
                    st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

            export_body = (
                '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
                '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
                + table_html(show[detail_cols])
            )
            html_doc = export_section_html(
                "📉 Faltantes ECOM",
                "SKUs marcados como faltante para e-commerce, por tienda.",
                export_body
            )
            section_download_button(html_doc, "operativo_faltantes.html", "dl_faltantes")
        else:
            st.markdown('<div class="empty-box">Sin faltantes para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Faltantes para ver esta sección.</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="color:#6b7280;font-size:11.5px;text-align:center;margin-top:18px;">'
        'Operativo · datos del Reporte diario · esta página no guarda historial: volvé a subir los archivos '
        'actualizados para regenerar el panel.</div>',
        unsafe_allow_html=True
    )

else:
    st.markdown(
        '<div class="empty-box" style="margin-top:20px;">'
        'Subí al menos un archivo arriba para ver el panel operativo.</div>',
        unsafe_allow_html=True
    )
