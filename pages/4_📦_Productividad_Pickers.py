import io
import json
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

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

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero-brand { font-size: 20px; }
        .section { font-size: 16px; margin: 20px 0 4px; }
        table.dashtable { font-size: 12px; }
        table.dashtable thead th, table.dashtable tbody td { padding: 7px 8px; }
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
        d["Depósito"] = d["warehouseRefId"].apply(norm_txt)
        d["Pedidos"] = pd.to_numeric(d["orders"], errors="coerce").fillna(0)
        d["Unidades"] = pd.to_numeric(d["items"], errors="coerce").fillna(0)
        d["Rendimiento"] = pd.to_numeric(d["performance"], errors="coerce")
        d["Rend. picking"] = pd.to_numeric(d.get("pickingPerformance"), errors="coerce")
        d["Found Rate"] = pd.to_numeric(d.get("foundRate"), errors="coerce")
        d["Fill Rate"] = pd.to_numeric(d.get("fillRate"), errors="coerce")
        d = d[d["Picker"] != ""]
        pickers_all = d[[
            "Picker", "Depósito", "Pedidos", "Unidades",
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
# Filtros: Tienda/Depósito y rango de fechas (desde/hasta). El de tienda
# se aplica al ranking de hoy y al historial; el de fechas solo tiene
# sentido en el historial (el ranking de hoy es siempre el último día).
# ---------------------------------------------------------------------

tiendas = set()
if pickers_all is not None:
    tiendas.update([t for t in pickers_all["Depósito"].unique() if t])
if log_df is not None and len(log_df) and "Deposito" in log_df.columns:
    tiendas.update([t for t in log_df["Deposito"].unique() if t])
tiendas = sorted(tiendas)

if log_df is not None and len(log_df) and log_df["FechaDt"].notna().any():
    min_date = log_df["FechaDt"].min().date()
    max_date = log_df["FechaDt"].max().date()
else:
    _hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    min_date = max_date = _hoy

f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    filtro_tienda = st.selectbox("Tienda / Depósito", ["Todas"] + tiendas, key="pickers_filtro_tienda")
with f2:
    filtro_desde = st.date_input("Desde", value=min_date, min_value=min_date, max_value=max_date, key="pickers_desde")
with f3:
    filtro_hasta = st.date_input("Hasta", value=max_date, min_value=min_date, max_value=max_date, key="pickers_hasta")

if filtro_desde > filtro_hasta:
    st.warning("La fecha 'Desde' es posterior a 'Hasta' — invertí las fechas para ver resultados.")

pickers = pickers_all
if pickers is not None and filtro_tienda != "Todas":
    pickers = pickers[pickers["Depósito"] == filtro_tienda]

log_filtrado = None
if log_df is not None and len(log_df):
    log_filtrado = log_df.copy()
    if filtro_tienda != "Todas":
        log_filtrado = log_filtrado[log_filtrado["Deposito"] == filtro_tienda]
    log_filtrado = log_filtrado[
        (log_filtrado["FechaDt"].dt.date >= filtro_desde) & (log_filtrado["FechaDt"].dt.date <= filtro_hasta)
    ]

# ---------------------------------------------------------------------
# Ranking de hoy
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">🏆 Ranking de pickers — hoy</div>'
    '<div class="section-desc">Ordenado por unidades pickeadas, de mayor a menor (siempre el último '
    'Reporte diario subido — el filtro de fechas no aplica acá, solo el de tienda). '
    '"Rendimiento" es la columna "performance" del export (unidades/hora estimadas) — en pickers con '
    'muy pocos pedidos ese número puede salir muy alto o muy bajo, así que conviene mirarlo junto a Pedidos/Unidades. '
    '"Depósito" es el código interno del depósito (no tenemos el nombre mapeado todavía).</div>',
    unsafe_allow_html=True
)

if pickers is not None and len(pickers):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pickers activos", num0(len(pickers)))
    c2.metric("Pedidos totales", num0(pickers["Pedidos"].sum()))
    c3.metric("Unidades totales", num0(pickers["Unidades"].sum()))
    c4.metric("Rendimiento promedio", num1(pickers["Rendimiento"].mean()))

    top = pickers.head(20).copy()
    for c in ["Rendimiento", "Rend. picking"]:
        top[c] = top[c].apply(num1)
    for c in ["Found Rate", "Fill Rate"]:
        top[c] = top[c].apply(pct1)
    top["Pedidos"] = top["Pedidos"].apply(num0)
    top["Unidades"] = top["Unidades"].apply(num0)
    st.write(table_html(top), unsafe_allow_html=True)

    if len(pickers) > 20:
        with st.expander(f"Ver los {len(pickers)} pickers"):
            with st.container(height=420):
                full = pickers.copy()
                for c in ["Rendimiento", "Rend. picking"]:
                    full[c] = full[c].apply(num1)
                for c in ["Found Rate", "Fill Rate"]:
                    full[c] = full[c].apply(pct1)
                full["Pedidos"] = full["Pedidos"].apply(num0)
                full["Unidades"] = full["Unidades"].apply(num0)
                st.write(table_html(full), unsafe_allow_html=True)
elif pickers_all is not None:
    st.markdown('<div class="empty-box">Sin pickers para esta tienda en el último reporte.</div>', unsafe_allow_html=True)
elif reporte_bytes is not None:
    st.markdown('<div class="empty-box">No encontré datos de pickers en el Reporte diario subido.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Ranking del período (acumulado del rango de fechas elegido)
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">📊 Ranking del período elegido</div>'
    f'<div class="section-desc">Acumulado entre el {filtro_desde.strftime("%d/%m/%Y")} y el '
    f'{filtro_hasta.strftime("%d/%m/%Y")}{"" if filtro_tienda == "Todas" else f" — tienda {filtro_tienda}"}, '
    'sumando todos los Reportes diarios subidos en ese rango.</div>',
    unsafe_allow_html=True
)

if log_filtrado is not None and len(log_filtrado):
    periodo = log_filtrado.groupby("Picker", as_index=False).agg(
        Deposito=("Deposito", "first"),
        Dias=("Fecha", "nunique"),
        Pedidos=("Pedidos", "sum"),
        Unidades=("Unidades", "sum"),
        Rendimiento=("Rendimiento", "mean"),
    ).sort_values("Unidades", ascending=False)
    periodo = periodo.rename(columns={"Deposito": "Depósito"})

    ptop = periodo.head(20).copy()
    ptop["Rendimiento"] = ptop["Rendimiento"].apply(num1)
    ptop["Pedidos"] = ptop["Pedidos"].apply(num0)
    ptop["Unidades"] = ptop["Unidades"].apply(num0)
    st.write(table_html(ptop), unsafe_allow_html=True)

    if len(periodo) > 20:
        with st.expander(f"Ver los {len(periodo)} pickers del período"):
            with st.container(height=420):
                pfull = periodo.copy()
                pfull["Rendimiento"] = pfull["Rendimiento"].apply(num1)
                pfull["Pedidos"] = pfull["Pedidos"].apply(num0)
                pfull["Unidades"] = pfull["Unidades"].apply(num0)
                st.write(table_html(pfull), unsafe_allow_html=True)
elif log_df is None:
    st.markdown(
        '<div class="empty-box">Todavía no hay historial conectado — se activa solo la próxima vez '
        'que subas un Reporte diario con la hoja "Data Picker" en Operativo.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown('<div class="empty-box">Sin datos acumulados para esta tienda y este rango de fechas.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Evolución día a día (historial acumulado en Google Sheets)
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">📈 Evolución día a día</div>'
    '<div class="section-desc">Se arma solo, con cada Reporte diario que se suba en Operativo '
    '(una fila por picker, por día). Respeta los filtros de tienda y fechas de arriba.</div>',
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
    st.markdown('<div class="empty-box">Sin datos para esta tienda y este rango de fechas.</div>', unsafe_allow_html=True)
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
    tabla["Rendimiento"] = tabla["Rendimiento"].apply(num1)
    tabla = tabla.rename(columns={"Rendimiento": "Rendimiento prom."})
    st.write(table_html(tabla.iloc[::-1]), unsafe_allow_html=True)

    if len(diario) >= 2:
        st.line_chart(diario.set_index("FechaDt")[["Unidades"]])

    with st.expander(f"Ver historial completo por picker ({len(log_filtrado)} filas)"):
        with st.container(height=380):
            st.write(
                table_html(
                    log_filtrado.sort_values("FechaDt", ascending=False)
                    [["Fecha", "Picker", "Deposito", "Pedidos", "Unidades", "Rendimiento", "FoundRate", "FillRate"]]
                ),
                unsafe_allow_html=True
            )

    csv_bytes = (
        log_filtrado.sort_values("FechaDt")
        [["Fecha", "Picker", "Deposito", "Pedidos", "Unidades", "Rendimiento", "RendimientoPicking", "FoundRate", "FillRate"]]
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
