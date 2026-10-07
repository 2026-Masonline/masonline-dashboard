import io
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="MásOnline | Pedidos STS",
    page_icon="🧾",
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

    .kpi-row { display:flex; gap:14px; margin-top:6px; flex-wrap:wrap; }
    .kpi {
        background:#fafaf8; border:1px solid #eef0ef; border-radius:12px;
        padding:14px 18px; flex:1; min-width:150px;
    }
    .kpi .label { color:#6b7280; font-size:11.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
    .kpi .value { color:#ff5a1f; font-size:26px; font-weight:800; margin-top:6px; }

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

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; max-height: 640px; overflow-y: auto; }

    div[data-testid="stDownloadButton"] button {
        background: #ffffff; color: #ff5a1f; border: 1.5px solid #ff5a1f;
        border-radius: 8px; font-size: 12.5px; font-weight: 700; padding: 4px 14px;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: #ff5a1f; color: #ffffff; border-color: #ff5a1f;
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

def norm_codigo(v):
    """Como norm_txt, pero evita que un código (commerceSequentialId,
    shippingWarehouseReferenceId) quede como '2998.0' por venir de una
    columna numérica del Excel."""
    if pd.isna(v):
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return norm_txt(v)

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

def safe_open_excel(file_bytes):
    if file_bytes is None:
        return None
    try:
        return pd.ExcelFile(io.BytesIO(file_bytes))
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return None

def table_html(df):
    inner = df.to_html(escape=False, index=False, classes="dashtable", border=0)
    return f'<div class="table-scroll">{inner}</div>'

def kpi_card(label, value):
    return (
        '<div class="kpi">'
        '<div class="label">' + str(label) + '</div>'
        '<div class="value">' + str(value) + '</div>'
        '</div>'
    )

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

def mes_label(ts):
    if pd.isna(ts):
        return ""
    return f"{MESES_ES.get(ts.month, ts.month).capitalize()} {ts.year}"

# Código de tienda (shippingWarehouseReferenceId) -> nombre. Mismo listado
# que usan Productividad Pickers y la pestaña app.
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
    return TIENDA_MAP.get(norm_txt(codigo), norm_txt(codigo))

# ---------------------------------------------------------------------
# Archivo compartido: esta pestaña NO tiene uploader propio. Usa el mismo
# archivo de Pedidos (export "order-operation") que se sube en la pestaña
# app, tarjeta "PEDIDOS +72H" — la misma carpeta compartida que usan
# Operativo, Resumen, Pickers y Comparativo.
# ---------------------------------------------------------------------

SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_DIR.mkdir(parents=True, exist_ok=True)
SHARED_PEDIDOS_STS_PATH = SHARED_DIR / "pedidos_sts.xlsx"
SHARED_PEDIDOS_PATH = SHARED_DIR / "pedidos.xlsx"
SHARED_REPORTE_PATH = SHARED_DIR / "reporte_diario.xlsx"

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
    el servidor se reinició y la copia local temporal ya no está). Pide el
    archivo en formato "raw" (soporta hasta 100 MB) en vez del formato
    normal (que para archivos de más de 1 MB devuelve contenido vacío sin
    avisar)."""
    headers = _github_headers()
    if not headers:
        return None
    import urllib.request
    repo = "2026-Masonline/masonline-dashboard"
    branch = "main"
    repo_path = f"shared_uploads/{shared_path.name}"
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}?ref={branch}"
    raw_headers = {**headers, "Accept": "application/vnd.github.raw+json"}
    try:
        request_get = urllib.request.Request(url, headers=raw_headers, method="GET")
        with urllib.request.urlopen(request_get, timeout=30) as response:
            return response.read()
    except Exception:
        return None

def get_shared_bytes(shared_path):
    """Primero intenta la copia local (rápida); si no está, la trae de
    GitHub y la vuelve a dejar en local para la próxima. Si la copia local
    está vacía (0 bytes) la descarta y va directo a GitHub."""
    if shared_path.exists():
        try:
            data = shared_path.read_bytes()
            if data:
                return data
        except Exception:
            pass
    content = fetch_shared_from_github(shared_path)
    if content:
        try:
            shared_path.write_bytes(content)
        except Exception:
            pass
        return content
    return None

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.markdown("""
<div class="hero">
  <div>
    <div class="hero-brand">🧾 Pedidos STS</div>
    <div class="hero-sub">MES · NÚMERO DE PEDIDO · NÚMERO DE TIENDA</div>
  </div>
</div>
""", unsafe_allow_html=True)

pedidos_sts_bytes = get_shared_bytes(SHARED_PEDIDOS_STS_PATH)
pedidos_bytes = get_shared_bytes(SHARED_PEDIDOS_PATH)
reporte_bytes = get_shared_bytes(SHARED_REPORTE_PATH)
src_bytes = pedidos_sts_bytes if pedidos_sts_bytes is not None else (
    pedidos_bytes if pedidos_bytes is not None else reporte_bytes
)

if pedidos_sts_bytes is not None:
    st.markdown(
        '<div style="font-size:11.5px;color:#0ca30c;font-weight:700;margin:-2px 0 10px;">'
        '● Mostrando el archivo subido en la pestaña app, tarjeta "PEDIDOS STS".</div>',
        unsafe_allow_html=True
    )
elif src_bytes is not None:
    st.markdown(
        '<div style="font-size:11.5px;color:#0ca30c;font-weight:700;margin:-2px 0 10px;">'
        '● Todavía no subiste nada en la tarjeta "PEDIDOS STS" — mostrando el archivo '
        'de "PEDIDOS +72H" en su lugar.</div>',
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
        Subí el archivo de Pedidos (export "order-operation") en la pestaña <b>app</b>,
        tarjeta "PEDIDOS STS". Esta página va a mostrar el listado automáticamente.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------
# Armar las 3 columnas pedidas: Mes (de deliveryFinishDate), Número de
# pedido (commerceSequentialId) y Número de tienda
# (shippingWarehouseReferenceId). Se descartan las filas sin
# commerceSequentialId (Pick&Mix / devoluciones RMA), que no tienen un
# "número de pedido" real para este listado.
# ---------------------------------------------------------------------

REQUIRED_COLS = ["commerceSequentialId", "shippingWarehouseReferenceId", "deliveryFinishDate"]

def find_all_sheets(xl, required_cols):
    """Como find_sheet, pero junta TODAS las hojas que tengan las columnas
    necesarias (no solo la primera) — por si el archivo trae una hoja por
    mes/período en vez de todo en una sola, como pasa con 'Vs de ventas'.
    Devuelve también qué hojas usó y cuáles descartó, para poder mostrar un
    detalle técnico en pantalla si algo no cierra (por ejemplo, si el
    archivo tiene más meses de los que se terminan mostrando)."""
    required = {c.lower() for c in required_cols}
    frames = []
    hojas_usadas = []
    hojas_descartadas = []
    for name in xl.sheet_names:
        try:
            df = xl.parse(name)
        except Exception as e:
            hojas_descartadas.append(f"{name} (no se pudo leer: {e})")
            continue
        df = norm_cols(df)
        cols = {c.lower() for c in df.columns}
        if required.issubset(cols):
            frames.append(df)
            hojas_usadas.append(f"{name} ({len(df):,} filas)".replace(",", "."))
        else:
            faltantes = required - cols
            hojas_descartadas.append(f"{name} (sin columnas: {', '.join(sorted(faltantes))})")
    if not frames:
        return None, hojas_usadas, hojas_descartadas
    return pd.concat(frames, ignore_index=True), hojas_usadas, hojas_descartadas

xl = safe_open_excel(src_bytes)
df_raw = None
hojas_usadas, hojas_descartadas = [], []
if xl is not None:
    df_raw, hojas_usadas, hojas_descartadas = find_all_sheets(xl, REQUIRED_COLS)

if df_raw is None:
    st.markdown("""
    <div style="background:white;border:1px solid #e8ebef;border-radius:12px;
    padding:12px 16px;margin-bottom:14px;">
      <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
        NO ENCONTRÉ LAS COLUMNAS NECESARIAS
      </div>
      <div style="font-size:12px;color:#6b7280;">
        El archivo de Pedidos cargado no tiene las columnas
        <b>commerceSequentialId</b>, <b>shippingWarehouseReferenceId</b> y
        <b>deliveryFinishDate</b> — volvé a subir el export "order-operation"
        en la pestaña <b>app</b>.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

d = df_raw.copy()
filas_antes = len(d)
d["_fecha_raw"] = pd.to_datetime(d["deliveryFinishDate"], errors="coerce")
sin_fecha_valida = d["_fecha_raw"].isna().sum()
d["_fecha"] = d["_fecha_raw"]
d = d.dropna(subset=["commerceSequentialId", "_fecha"]).copy()
d["Mes"] = d["_fecha"].apply(mes_label)
d["_mes_ord"] = d["_fecha"].dt.to_period("M")
d["Numero de pedido"] = d["commerceSequentialId"].apply(norm_codigo)
d["Numero de tienda"] = d["shippingWarehouseReferenceId"].apply(norm_codigo)

tabla = d[["Mes", "Numero de pedido", "Numero de tienda", "_mes_ord"]].sort_values(
    ["_mes_ord", "Numero de pedido"], ascending=[False, True]
)

with st.expander("Ver detalle técnico (para diagnosticar si falta algún mes)"):
    st.markdown(
        f"**Hojas usadas** ({len(hojas_usadas)}): " + (", ".join(hojas_usadas) if hojas_usadas else "ninguna")
    )
    if hojas_descartadas:
        st.markdown(f"**Hojas descartadas** ({len(hojas_descartadas)}): " + ", ".join(hojas_descartadas))
    st.markdown(f"**Filas leídas en total:** {filas_antes:,}".replace(",", "."))
    st.markdown(
        f"**Filas sin deliveryFinishDate válido (se descartan):** {sin_fecha_valida:,}".replace(",", ".")
    )
    if not tabla.empty:
        mes_min = tabla["_mes_ord"].min()
        mes_max = tabla["_mes_ord"].max()
        st.markdown(f"**Rango de meses cargados:** {mes_min} a {mes_max}")
        st.markdown(f"**Pedidos finales (sin PM/RMA, con fecha válida):** {len(tabla):,}".replace(",", "."))

# ---------------------------------------------------------------------
# Filtro de Mes
# ---------------------------------------------------------------------

meses_disponibles = (
    tabla[["_mes_ord", "Mes"]].drop_duplicates().sort_values("_mes_ord", ascending=False)
)
opciones_mes = ["Todos los meses"] + meses_disponibles["Mes"].tolist()
mes_elegido = st.selectbox("**Mes**", opciones_mes)

if mes_elegido != "Todos los meses":
    tabla_f = tabla[tabla["Mes"] == mes_elegido]
else:
    tabla_f = tabla

tabla_f = tabla_f[["Mes", "Numero de pedido", "Numero de tienda"]].reset_index(drop=True)

st.markdown(
    f'<div class="kpi-row">{kpi_card("Pedidos listados", f"{len(tabla_f):,}".replace(",", "."))}'
    f'{kpi_card("Tiendas", tabla_f["Numero de tienda"].nunique())}</div>',
    unsafe_allow_html=True
)

csv_bytes = tabla_f.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇ Descargar CSV (todo lo filtrado)",
    data=csv_bytes,
    file_name="pedidos_sts.csv",
    mime="text/csv",
)

st.markdown('<div class="section">Listado por tienda</div>', unsafe_allow_html=True)

if tabla_f.empty:
    st.markdown(
        '<div style="background:#fafaf8;border:1px dashed #dfe2db;border-radius:12px;'
        'padding:22px;text-align:center;color:#868d8e;font-size:13px;margin-top:8px;">'
        'No hay pedidos para ese mes.</div>',
        unsafe_allow_html=True
    )
else:
    # Orden de tienda: numérico si el código lo permite, para que 998 no
    # quede antes que 1002 por orden de texto.
    tiendas_orden = sorted(
        tabla_f["Numero de tienda"].unique(),
        key=lambda t: (0, int(t)) if t.isdigit() else (1, t)
    )
    for tienda in tiendas_orden:
        sub = tabla_f[tabla_f["Numero de tienda"] == tienda][["Mes", "Numero de pedido"]]
        nombre = tienda_nombre(tienda)
        with st.expander(f"{nombre} ({tienda}) — {len(sub)} pedido(s)"):
            st.markdown(
                f'<div style="font-weight:800;font-size:15px;color:#20252b;margin-bottom:8px;">'
                f'{nombre} <span style="font-weight:400;color:#6b7280;font-size:12.5px;">(tienda {tienda})</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown(table_html(sub.reset_index(drop=True)), unsafe_allow_html=True)
