import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import calendar
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import html

# Historial de Faltantes (Google Sheet "HistorialFaltantes"): mismo mecanismo
# que usa la pestaña "Operativo" para acumular, mes a mes, los SKUs marcados
# como faltante. Acá lo reusamos solo para armar el ranking de qué tiendas
# tuvieron más faltantes. El import va "blindado": si la librería no está
# instalada, esta página funciona igual y esa sección simplemente muestra un
# aviso de "todavía no conectado".
try:
    import gspread
    from google.oauth2.service_account import Credentials as _GCreds
    _GSHEETS_LIB_OK = True
except Exception:
    _GSHEETS_LIB_OK = False

st.set_page_config(
    page_title="MásOnline | Ecommerce",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
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
    .hero-brand { font-size: 30px; font-weight: 800; letter-spacing: -.5px; }
    .hero-brand span { font-weight: 400; }
    .hero-sub { font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }
    .hero-date { text-align: right; font-size: 19px; font-weight: 800; }
    .hero-date small { display: block; font-size: 12px; font-weight: 400; margin-top: 4px; opacity: .8; }

    .card {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        min-height: 125px; border: 1px solid #e8ebef;
    }
    .label { color: #6b7280; font-size: 14px; font-weight: 700; }
    .value { color: #20252b; font-size: 30px; font-weight: 800; margin-top: 7px; }
    .small { color: #20252b; font-size: 13px; font-weight: 700; margin-top: 7px; }

    .section {
        font-size: 20px; font-weight: 800; color: #20252b;
        margin: 26px 0 12px;
    }

    .progress-wrap {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        border: 1px solid #e8ebef;
    }
    .progress-layout { display: flex; align-items: center; gap: 28px; }
    .progress-main { flex: 1; }
    .progress-track {
        height: 16px; background: #e6e9ed; border-radius: 20px;
        overflow: hidden; margin: 10px 0 8px;
    }
    .progress-fill { height: 100%; background: #2f9e66; border-radius: 20px; }
    .progress-row {
        display: flex; justify-content: space-between; color: #6b7280;
        font-size: 13px;
    }
    .progress-target {
        width: 150px; color: #208653; font-size: 30px; font-weight: 800;
        text-align: right; line-height: 1;
    }
    .progress-target small {
        display: block; color: #6b7280; font-size: 12px;
        font-weight: 400; margin-top: 5px;
    }

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }

    .rank-table-card {
        background: white; border-radius: 14px; overflow: hidden;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.06);
    }
    table.rank-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    table.rank-table thead th {
        background: #e9f7ef; color: #208653; font-weight: 700;
        padding: 10px 14px; text-align: left; white-space: nowrap;
    }
    table.rank-table td {
        padding: 12px 14px; border-top: 1px solid #f1f3f5; color: #20252b;
    }
    .rank-badge {
        width: 28px; height: 28px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 13px;
    }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero img { max-width: 170px !important; height: 40px !important; }
        .hero-brand { font-size: 22px; }
        .hero-date { text-align: left; }
        .section { font-size: 17px; margin: 20px 0 8px; }
        .value { font-size: 24px; }
        .compare-value { font-size: 24px; }
        .progress-layout { flex-direction: column; align-items: stretch; gap: 14px; }
        .progress-target { width: auto; text-align: left; }
        table { font-size: 12px; }
    }

    .chart-card {
        background: white; border-radius: 14px; padding: 12px 16px 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        border: 1px solid #e8ebef;
    }

    .compare-card {
        background: white; border-radius: 14px; padding: 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        border: 1px solid #e8ebef; min-height: 125px;
    }
    .compare-title { color: #20252b; font-size: 16px; font-weight: 800; }
    .compare-base { color: #6b7280; font-size: 13px; margin-top: 5px; }
    .compare-value { font-size: 31px; font-weight: 800; margin-top: 14px; }
    .negative { color: #d64545; }
    .positive { color: #208653; }

    .upload-box {
        background: white; border-radius: 14px; padding: 16px 18px 8px;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.05);
        margin-bottom: 6px; min-height: 82px;
    }
    .upload-current { border-top: 4px solid #ff5a1f; }
    .upload-prev { border-top: 4px solid #2f9e66; }
    .upload-ly { border-top: 4px solid #59636e; }

    .upload-title { color:#20252b; font-size:14px; font-weight:800; }
    .upload-text { color:#6b7280; font-size:12px; margin-top:5px; }

    .footer {
        display: flex; justify-content: space-between; color: #6b7280;
        font-size: 12px; margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).resolve().parent.parent / "data.csv"
DATA_TIENDAS_FILE = Path(__file__).resolve().parent.parent / "data_tiendas.csv"
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

TIENDAS_COLUMNS = ["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax", "orders", "units"]

try:
    if DATA_TIENDAS_FILE.exists():
        base_df_tiendas = pd.read_csv(DATA_TIENDAS_FILE)
        base_df_tiendas["date"] = pd.to_datetime(base_df_tiendas["date"], errors="coerce")
        base_df_tiendas["Tienda"] = base_df_tiendas["Tienda"].astype(str)
        for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
            base_df_tiendas[col] = pd.to_numeric(base_df_tiendas[col], errors="coerce").fillna(0)
        base_df_tiendas = base_df_tiendas.dropna(subset=["date"])
    else:
        base_df_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)
except Exception:
    base_df_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)

# ---------------------------------------------------------------------
# Historial de Faltantes (Google Sheet "HistorialFaltantes") — mismas
# credenciales que ya están cargadas en Secrets para "Operativo". Acá solo
# se usa para armar el ranking de tiendas con más faltantes del mes.
# ---------------------------------------------------------------------

FALTANTES_LOG_HEADERS = ["Fecha", "Tienda", "Departamento", "SKU", "CodigoPrincipal", "Etiqueta"]

@st.cache_resource(show_spinner=False)
def _gsheets_client():
    if not _GSHEETS_LIB_OK:
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
        return gspread.authorize(creds)
    except Exception:
        return None

def _faltantes_log_ws():
    client = _gsheets_client()
    if client is None:
        return None
    sheet_id = st.secrets.get("FALTANTES_SHEET_ID")
    if not sheet_id:
        return None
    try:
        sh = client.open_by_key(sheet_id)
        return sh.worksheet("HistorialFaltantes")
    except Exception:
        return None

@st.cache_data(ttl=180, show_spinner=False)
def load_faltantes_log():
    """None = todavía no conectado. DataFrame vacío = conectado pero sin
    filas cargadas aún."""
    ws = _faltantes_log_ws()
    if ws is None:
        return None
    try:
        records = ws.get_all_records()
    except Exception:
        return None
    df = pd.DataFrame(records) if records else pd.DataFrame(columns=FALTANTES_LOG_HEADERS)
    if "Fecha" in df.columns:
        df["FechaDt"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    return df

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin-bottom:14px;">
  <div style="font-size:12px;color:#6b7280;">
    Los datos se actualizan desde la página principal ("app"). Esta página muestra
    siempre la última información cargada ahí.
  </div>
</div>
""", unsafe_allow_html=True)

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"]).copy()

# Siempre mostramos el último día cerrado en Argentina (no el día en curso,
# que todavía puede estar sumando ventas).
arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df_mostrar = df[df["date"].dt.date < arg_today].copy()

if len(df_tiendas):
    df_tiendas["date"] = pd.to_datetime(df_tiendas["date"], errors="coerce")
    df_tiendas = df_tiendas.dropna(subset=["date"]).copy()

current = df_mostrar[
    (df_mostrar["date"].dt.year == 2026) &
    (df_mostrar["date"].dt.month == 9)
].copy().sort_values("date")

if current.empty:
    st.error("No hay datos de septiembre 2026.")
    st.stop()

latest = current.iloc[-1]
prev = current.iloc[-2] if len(current) > 1 else None
is_monday = arg_today.weekday() == 0
share_daily = (latest["ecommerce_tax"] / latest["company_tax"]) if latest["company_tax"] else 0

# Buscamos el Sábado más reciente con datos cargados (y el Viernes anterior),
# sin asumir que "hoy" es Lunes: así funciona sin importar qué día se abra el dashboard.
last_data_date = current["date"].max()
days_since_saturday = (last_data_date.weekday() - 5) % 7  # Monday=0 ... Saturday=5, Sunday=6
last_saturday = last_data_date - pd.Timedelta(days=days_since_saturday)
last_friday = last_saturday - pd.Timedelta(days=1)
last_sunday = last_saturday + pd.Timedelta(days=1)

friday_sales = current[current["date"] == last_friday]["ecommerce_tax"].sum()
saturday_sales = current[current["date"] == last_saturday]["ecommerce_tax"].sum()
sunday_sales = current[current["date"] == last_sunday]["ecommerce_tax"].sum()

friday_units = current[current["date"] == last_friday]["units"].sum()
saturday_units = current[current["date"] == last_saturday]["units"].sum()
sunday_units = current[current["date"] == last_sunday]["units"].sum()

friday_orders = current[current["date"] == last_friday]["orders"].sum()
saturday_orders = current[current["date"] == last_saturday]["orders"].sum()
sunday_orders = current[current["date"] == last_sunday]["orders"].sum()

friday_company = current[current["date"] == last_friday]["company_tax"].sum()
saturday_company = current[current["date"] == last_saturday]["company_tax"].sum()
sunday_company = current[current["date"] == last_sunday]["company_tax"].sum()

# Fin de semana = Viernes + Sábado (no se suma el Domingo) — se usa en la card
# "VENTA DÍA ANTERIOR" de los lunes.
weekend = friday_sales + saturday_sales
weekend_units = friday_units + saturday_units

# Fin de semana completo (Viernes + Sábado + Domingo), para la pestaña
# "Venta fin de semana".
weekend_full_ecom = friday_sales + saturday_sales + sunday_sales
weekend_full_units = friday_units + saturday_units + sunday_units
weekend_full_orders = friday_orders + saturday_orders + sunday_orders
weekend_full_company = friday_company + saturday_company + sunday_company
weekend_full_share = (weekend_full_ecom / weekend_full_company) if weekend_full_company else 0
weekend_full_label = f"{last_friday.strftime('%d-%m')} al {last_sunday.strftime('%d-%m')}"

sales_label = "VENTA DÍA ANTERIOR"
if is_monday:
    # Los lunes no tomamos el domingo como "día anterior": usamos el sábado.
    sales_value = saturday_sales
else:
    sales_value = latest["ecommerce_tax"]
days_elapsed = len(current)
days_month = calendar.monthrange(2026, 9)[1]

acc_ecom = current["ecommerce_tax"].sum()
acc_company = current["company_tax"].sum()
acc_orders = current["orders"].sum()
acc_units = current["units"].sum()

share = acc_ecom / acc_company if acc_company else 0
target = 0.03
gap = target - share

projection = acc_ecom / days_elapsed * days_month if days_elapsed else 0

day_change = (
    (latest["ecommerce_tax"] / prev["ecommerce_tax"]) - 1
    if prev is not None and prev["ecommerce_tax"]
    else 0
)

n = days_elapsed

aug = df_mostrar[
    (df_mostrar["date"].dt.year == 2026) &
    (df_mostrar["date"].dt.month == 8) &
    (df_mostrar["date"].dt.day <= n)
].sort_values("date")

sep25 = df_mostrar[
    (df_mostrar["date"].dt.year == 2025) &
    (df_mostrar["date"].dt.month == 9) &
    (df_mostrar["date"].dt.day <= n)
].sort_values("date")

aug_acc = aug["ecommerce_tax"].sum()
sep25_acc = sep25["ecommerce_tax"].sum()

vs_aug = (acc_ecom / aug_acc - 1) if aug_acc else None
vs_25 = (acc_ecom / sep25_acc - 1) if sep25_acc else None

# ---- Mejores y peores tiendas del mes en curso (venta y pedidos) ----
current_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)
if len(df_tiendas):
    current_tiendas = df_tiendas[
        (df_tiendas["date"].dt.year == 2026) &
        (df_tiendas["date"].dt.month == 9)
    ].copy()

tiendas_resumen = pd.DataFrame(columns=["Tienda", "Nombre", "ecommerce_tax", "orders"])
if len(current_tiendas):
    tiendas_resumen = (
        current_tiendas.groupby(["Tienda", "Nombre"], as_index=False)
        .agg(ecommerce_tax=("ecommerce_tax", "sum"), orders=("orders", "sum"))
    )

# Mismo "último día cerrado" que usa el resto del dashboard (variable `latest`,
# calculada más arriba a partir de `current`), para que el cuadro "venta
# diaria" siempre muestre el día más reciente con datos, no el día en curso.
latest_tienda_date = latest["date"]
tiendas_dia = pd.DataFrame(columns=["Tienda", "Nombre", "ecommerce_tax", "orders"])
if len(df_tiendas):
    filas_dia = df_tiendas[df_tiendas["date"] == latest_tienda_date]
    if len(filas_dia):
        tiendas_dia = (
            filas_dia.groupby(["Tienda", "Nombre"], as_index=False)
            .agg(ecommerce_tax=("ecommerce_tax", "sum"), orders=("orders", "sum"))
        )

def top_tiendas(df_in, metric, n=5):
    if not len(df_in):
        return df_in.copy()
    return df_in.sort_values(metric, ascending=False).head(n).reset_index(drop=True)

top_venta_dia = top_tiendas(tiendas_dia, "ecommerce_tax", n=5)
top_venta_mes = top_tiendas(tiendas_resumen, "ecommerce_tax", n=5)

# ---- Tiendas con más faltantes del mes (historial de "Operativo") ----
faltantes_log = load_faltantes_log()
faltantes_rank = pd.DataFrame(columns=["Tienda", "Faltantes", "Dias"])
log_mes_falt = pd.DataFrame(columns=["Fecha", "Tienda", "Departamento", "SKU", "CodigoPrincipal", "Etiqueta", "FechaDt"])
if faltantes_log is not None and len(faltantes_log):
    mes_inicio_falt = pd.Timestamp(year=2026, month=9, day=1)
    log_mes_falt = faltantes_log[faltantes_log["FechaDt"] >= mes_inicio_falt].copy()
    if len(log_mes_falt):
        faltantes_rank = (
            log_mes_falt.groupby("Tienda", as_index=False)
            .agg(Faltantes=("SKU", "count"), Dias=("FechaDt", "nunique"))
            .sort_values("Faltantes", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )

# Fechas del mes con al menos un reporte de Faltantes subido, para el filtro
# "ver por fecha" (más reciente primero).
faltantes_fechas_disponibles = []
if len(log_mes_falt):
    faltantes_fechas_disponibles = sorted(
        log_mes_falt["FechaDt"].dropna().dt.normalize().unique(), reverse=True
    )

# ---- Venta por fin de semana del mes en curso ----
# Para la pestaña "Venta fin de semana": Fin de semana = Viernes + Sábado +
# Domingo (los tres días).
finde_rows = current[current["date"].dt.weekday.isin([4, 5, 6])].copy()
finde_rows["finde_inicio"] = finde_rows["date"] - pd.to_timedelta(
    (finde_rows["date"].dt.weekday - 4) % 7, unit="D"
)
finde_tabla = (
    finde_rows.groupby("finde_inicio", as_index=False)
    .agg(
        venta=("ecommerce_tax", "sum"),
        pedidos=("orders", "sum"),
        unidades=("units", "sum"),
    )
    .sort_values("finde_inicio")
    .reset_index(drop=True)
)
finde_tabla["rango"] = finde_tabla["finde_inicio"].apply(
    lambda d: f"Vie {d.strftime('%d/%m')} – Dom {(d + pd.Timedelta(days=2)).strftime('%d/%m')}"
)
finde_tabla["participacion"] = (
    finde_tabla["venta"] / acc_ecom if acc_ecom else 0
)

# ---- Comparación entre findes (pestaña "findesema") ----
# Usamos TODO el historial cargado (no solo el mes en curso) para poder
# comparar el finde más reciente contra el anterior aunque estemos al
# principio del mes y todavía no haya un segundo finde en septiembre.
findesema_rows = df_mostrar[df_mostrar["date"].dt.weekday.isin([4, 5, 6])].copy()
findesema_rows["finde_inicio"] = findesema_rows["date"] - pd.to_timedelta(
    (findesema_rows["date"].dt.weekday - 4) % 7, unit="D"
)
findesema_tabla = (
    findesema_rows.groupby("finde_inicio", as_index=False)
    .agg(
        venta=("ecommerce_tax", "sum"),
        company=("company_tax", "sum"),
        pedidos=("orders", "sum"),
        unidades=("units", "sum"),
    )
    .sort_values("finde_inicio")
    .reset_index(drop=True)
)

def _finde_rango(inicio):
    return f"{inicio.strftime('%d-%m')} al {(inicio + pd.Timedelta(days=2)).strftime('%d-%m')}"

if len(findesema_tabla) >= 1:
    finde_actual = findesema_tabla.iloc[-1]
    finde_actual_rango = _finde_rango(finde_actual["finde_inicio"])
else:
    finde_actual = None
    finde_actual_rango = ""

if len(findesema_tabla) >= 2:
    finde_anterior = findesema_tabla.iloc[-2]
    finde_anterior_rango = _finde_rango(finde_anterior["finde_inicio"])
    finde_vs_anterior = (
        (finde_actual["venta"] / finde_anterior["venta"]) - 1
        if finde_anterior["venta"] else None
    )
else:
    finde_anterior = None
    finde_anterior_rango = ""
    finde_vs_anterior = None

def money(v):
    return (
       f"${v/1_000_000:,.2f} M"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

def pct(v):
    return f"{v*100:.2f}%".replace(".", ",")

def pct_change(v):
    return f"{v:+.2%}".replace(".", ",")

def intfmt(v):
    return f"{int(v):,}".replace(",", ".")

if LOGO_FILE.exists():
    logo_b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode("utf-8")
    brand_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        'style="height:58px;max-width:330px;object-fit:contain;">'
    )
else:
    brand_html = '<div class="hero-brand">Más<span>Online</span></div>'

st.markdown(f"""
<div class="hero">
  <div>
    {brand_html}
    <div class="hero-sub">E-COMMERCE</div>
  </div>
  <div class="hero-date">
    Septiembre 2026
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
    <div style="font-weight:800;font-size:16px;margin-top:6px;color:#20252b;">
      Participación del día: <span style="color:#2f9e66;">{pct(share_daily)}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# HTML DESCARGABLE: copia independiente del dashboard, sin Streamlit.
# ---------------------------------------------------------------------

def build_standalone_html():
    # Logo embebido para que el archivo sea realmente independiente.
    if LOGO_FILE.exists():
        html_logo = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            'style="height:58px;max-width:330px;object-fit:contain;">'
        )
    else:
        html_logo = '<div class="brand">Más<span>Online</span></div>'

    # Datos para el gráfico.
    chart_w = 1120
    chart_h = 400
    left = 72
    right = 24
    top = 30
    bottom = 58
    plot_w = chart_w - left - right
    plot_h = chart_h - top - bottom

    vals = current["ecommerce_tax"].astype(float).tolist()
    dates = current["date"].dt.strftime("%d/%m").tolist()

    vmax = max(vals) if vals else 1
    vmin = min(vals) if vals else 0
    if vmax == vmin:
        vmax = vmin + 1

    points = []
    for i, value in enumerate(vals):
        x = left + (plot_w * i / max(len(vals) - 1, 1))
        y = top + plot_h - ((value - vmin) / (vmax - vmin)) * plot_h
        points.append((x, y))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    circles = ""
    for i, ((x, y), value) in enumerate(zip(points, vals)):
        circles += (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#2f9e66"/>'
            f'<text x="{x:.1f}" y="{y-12:.1f}" text-anchor="middle" '
            f'font-size="11" fill="#59636e">{money(value)}</text>'
        )

    xlabels = ""
    for i, date_text in enumerate(dates):
        x = left + (plot_w * i / max(len(dates) - 1, 1))
        xlabels += (
            f'<text x="{x:.1f}" y="{chart_h-22}" text-anchor="middle" '
            f'font-size="11" fill="#697386">{html.escape(date_text)}</text>'
        )

    # Cuadrícula horizontal.
    grid = ""
    for j in range(5):
        y = top + plot_h * j / 4
        value = vmax - (vmax - vmin) * j / 4
        grid += (
            f'<line x1="{left}" y1="{y:.1f}" x2="{chart_w-right}" y2="{y:.1f}" '
            'stroke="#e8ebef" stroke-width="1"/>'
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#697386">{html.escape(money(value))}</text>'
        )

    svg = f"""
    <svg viewBox="0 0 {chart_w} {chart_h}" width="100%" height="400"
         xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="white"/>
      {grid}
      <polyline points="{polyline}" fill="none" stroke="#2f9e66"
                stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      {circles}
      {xlabels}
    </svg>
    """

    progress = min(share / target, 1.0) * 100
    progress_label = f"{share/target:.0%}"

    def standalone_compare(title, value, base_text):
        if value is None:
            return f"""
            <div class="compare-card">
              <div class="compare-title">{html.escape(title)}</div>
              <div class="compare-base">Sin base disponible</div>
            </div>
            """
        cls = "positive" if value >= 0 else "negative"
        arrow = "↑" if value >= 0 else "↓"
        return f"""
        <div class="compare-card">
          <div class="compare-title">{html.escape(title)}</div>
          <div class="compare-base">{html.escape(base_text)}</div>
          <div class="compare-value {cls}">
            {arrow}&nbsp;&nbsp;{value:+.1%}
          </div>
        </div>
        """

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MásOnline | Dashboard Ecommerce</title>
<style>
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 34px 42px 42px;
    background: #ffffff;
    color: #20252b;
    font-family: Arial, Helvetica, sans-serif;
}}
.container {{ max-width: 1500px; margin: 0 auto; }}
.hero {{
    background: #ffffff;
    color: #20252b;
    padding: 22px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 112px;
    border-bottom: 4px solid #ff5a1f;
}}
.hero-sub {{
    font-size: 11px;
    letter-spacing: 3px;
    margin-top: 3px;
    opacity: .85;
}}
.hero-date {{
    text-align: right;
    font-size: 19px;
    font-weight: 800;
}}
.hero-date small {{
    display: block;
    font-size: 12px;
    font-weight: 400;
    margin-top: 4px;
    opacity: .8;
}}
.kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-top: 16px;
}}
.card, .progress-wrap, .chart-card, .compare-card {{
    background: white;
    border: 1px solid #e8ebef;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
}}
.card {{
    padding: 20px 22px;
    min-height: 125px;
}}
.label {{
    color: #6b7280;
    font-size: 14px;
    font-weight: 700;
}}
.value {{
    color: #20252b;
    font-size: 30px;
    font-weight: 800;
    margin-top: 7px;
}}
.small {{
    color: #20252b;
    font-size: 13px;
    font-weight: 700;
    margin-top: 7px;
}}
.section {{
    font-size: 20px;
    font-weight: 800;
    margin: 26px 0 12px;
}}
.progress-wrap {{ padding: 20px 22px; }}
.progress-layout {{
    display: flex;
    align-items: center;
    gap: 28px;
}}
.progress-main {{ flex: 1; }}
.progress-track {{
    height: 16px;
    background: #e6e9ed;
    border-radius: 20px;
    overflow: hidden;
    margin: 10px 0 8px;
}}
.progress-fill {{
    height: 100%;
    width: {progress:.1f}%;
    background: #2f9e66;
    border-radius: 20px;
}}
.progress-row {{
    display: flex;
    justify-content: space-between;
    color: #6b7280;
    font-size: 13px;
}}
.progress-target {{
    width: 150px;
    color: #208653;
    font-size: 30px;
    font-weight: 800;
    text-align: right;
    line-height: 1;
}}
.progress-target small {{
    display: block;
    color: #6b7280;
    font-size: 12px;
    font-weight: 400;
    margin-top: 5px;
}}
.chart-card {{ padding: 12px 16px 4px; overflow: hidden; }}
.comparisons {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}}
.compare-card {{ padding: 22px; min-height: 125px; }}
.compare-title {{
    color: #20252b;
    font-size: 16px;
    font-weight: 800;
}}
.compare-base {{
    color: #6b7280;
    font-size: 13px;
    margin-top: 5px;
}}
.compare-value {{
    font-size: 31px;
    font-weight: 800;
    margin-top: 14px;
}}
.negative {{ color: #d64545; }}
.positive {{ color: #208653; }}
.footer {{
    display: flex;
    justify-content: space-between;
    color: #6b7280;
    font-size: 12px;
    margin-top: 14px;
}}
@media (max-width: 900px) {{
    body {{ padding: 18px; }}
    .kpis {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 600px) {{
    .hero {{ flex-direction: column; align-items: flex-start; gap: 15px; }}
    .hero-date {{ text-align: left; }}
    .kpis, .comparisons {{ grid-template-columns: 1fr; }}
    .progress-layout {{ flex-direction: column; align-items: stretch; }}
    .progress-target {{ width: auto; text-align: left; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="hero">
  <div>
    {html_logo}
    <div class="hero-sub">E-COMMERCE</div>
  </div>
  <div class="hero-date">
    Septiembre 2026
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
    <div style="font-weight:800;font-size:16px;margin-top:6px;color:#20252b;">
      Participación del día: <span style="color:#2f9e66;">{pct(share_daily)}</span>
    </div>
  </div>
</div>

<div class="kpis">

<div class="card" style="border-top:4px solid #f5a623;">
  <div class="label" style="color:#f5a623;">PARTICIPACIÓN E-COMMERCE</div>
  <div class="value">{html.escape(pct(share))}</div>
  <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
</div>

<div class="card" style="border-top:4px solid #e8432c;">
<div class="label" style="color:#e8432c;">{sales_label}</div>
<div class="value" style="color:#e8432c;">{html.escape(money(sales_value))}</div>
  <div class="small">Vs día previo: {html.escape(pct_change(day_change))}</div>
</div>

<div class="card" style="border-top:4px solid #59636e;">
  <div class="label">MES EN CURSO</div>
  <div class="value">{html.escape(money(acc_ecom))}</div>
  <div class="small">{int(acc_orders):,} pedidos · {int(acc_units):,} unidades</div>
</div>

<div class="card" style="border-top:4px solid #2f9e66;">
  <div class="label" style="color:#208653;">PROYECCIÓN DE CIERRE</div>
  <div class="value" style="color:#208653;">{html.escape(money(projection))}</div>
  <div class="small">Promedio diario × {days_month} días</div>
</div>

</div>
        </div>

        </div>

<div class="section">Avance de participación</div>
<div class="progress-wrap">
  <div class="progress-layout">
    <div class="progress-main">
      <div class="progress-track">
        <div class="progress-fill"></div>
      </div>
      <div class="progress-row">
        <span>Participación actual: {html.escape(pct(share))}</span>
        <span>Objetivo: 3,00%</span>
      </div>
    </div>
    <div class="progress-target">
      {progress_label}
      <small>del objetivo</small>
    </div>
  </div>
</div>

<div class="section">Comparaciones</div>
<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">
Variación de ventas e-commerce sobre la misma cantidad de días
</div>

<div class="comparisons">
{standalone_compare(
    "VS MES ANTERIOR",
    vs_aug,
    f"Sep 1–{n} 2026 vs Ago 1–{n} 2026"
)}
{standalone_compare(
    "VS MISMO MES AÑO ANTERIOR",
    vs_25,
    f"Sep 1–{n} 2026 vs Sep 1–{n} 2025"
)}
</div>

<div class="section">Evolución diaria</div>
<div class="chart-card">
{svg}
</div>

<div class="footer">
  <span>Fuente: venta con impuesto de MicroStrategy.</span>
  <span>MásOnline | E-commerce</span>
</div>

</div>
</body>
</html>
"""
    return html_doc

html_dashboard = build_standalone_html()

st.download_button(
    "⬇️ Descargar dashboard HTML",
    data=html_dashboard,
    file_name="dashboard_masonline.html",
    mime="text/html",
    use_container_width=True
)

# ---------------------------------------------------------------------
# Dashboard principal
# ---------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard completo",
    "📤 Resumen para GDN",
    "📅 Venta fin de semana",
    "findesema",
])

with tab1:
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #f5a623;">
          <div class="label" style="color:#f5a623;">PARTICIPACIÓN E-COMMERCE</div>
          <div class="value">{pct(share)}</div>
          <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #e8432c;">
          <div class="label" style="color:#e8432c;">{sales_label}</div>
    <div class="value" style="color:#e8432c;">{money(sales_value)}</div>
          <div class="small">Vs día previo: {pct_change(day_change)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #59636e;">
          <div class="label">MES EN CURSO</div>
          <div class="value">{money(acc_ecom)}</div>
          <div class="small">{intfmt(acc_orders)} pedidos · {intfmt(acc_units)} unidades</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #2f9e66;">
          <div class="label" style="color:#208653;">PROYECCIÓN DE CIERRE</div>
          <div class="value" style="color:#208653;">{money(projection)}</div>
          <div class="small">Promedio diario × {days_month} días</div>
        </div>
        """, unsafe_allow_html=True)

    progress = min(share / target, 1.0) * 100

    st.markdown(f"""
    <div class="progress-wrap">
      <div class="progress-layout">
        <div class="progress-main">
          <div class="progress-track">
            <div class="progress-fill" style="width:{progress:.1f}%;"></div>
          </div>
          <div class="progress-row">
            <span>Participación actual: {pct(share)}</span>
            <span>Objetivo: {pct(target)}</span>
          </div>
        </div>
        <div class="progress-target">
          {share/target:.0%}
          <small>del objetivo</small>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Resumen visual: Compañía vs Ecommerce (Diario / Mensual) ----
    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;margin-top:20px;">
      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
          DIARIO &nbsp;|&nbsp; {latest["date"].strftime("%d-%m")}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(latest["company_tax"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(latest["ecommerce_tax"])}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["orders"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["units"])}</div>
            </div>
          </div>
        </div>
        <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE DIARIO</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_daily)}</span>
        </div>
      </div>

      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
          MENSUAL &nbsp;SEPTIEMBRE 2026
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA MENSUAL</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(acc_company)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA MENSUAL</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(acc_ecom)}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_orders)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_units)}</div>
            </div>
          </div>
        </div>
        <div style="background:#fef6e7;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE MENSUAL</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share)}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section">Comparaciones</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">'
        'Variación de ventas e-commerce sobre la misma cantidad de días'
        '</div>',
        unsafe_allow_html=True
    )

    a, b = st.columns(2)

    def compare_box(title, value, base_text):
        cls = "positive" if value >= 0 else "negative"
        arrow = "↑" if value >= 0 else "↓"

        return f"""
        <div class="compare-card">
          <div class="compare-title">{title}</div>
          <div class="compare-base">{base_text}</div>
          <div class="compare-value {cls}">{arrow}&nbsp;&nbsp;{value:+.1%}</div>
        </div>
        """

    with a:
        if vs_aug is not None:
            st.markdown(
                compare_box(
                    "VS MES ANTERIOR",
                    vs_aug,
                    f"Sep 1–{n} 2026 vs Ago 1–{n} 2026"
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                compare_box("VS MES ANTERIOR", 0, "Sin base disponible"),
                unsafe_allow_html=True
            )

    with b:
        if vs_25 is not None:
            st.markdown(
                compare_box(
                    "VS MISMO MES AÑO ANTERIOR",
                    vs_25,
                    f"Sep 1–{n} 2026 vs Sep 1–{n} 2025"
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                compare_box("VS MISMO MES AÑO ANTERIOR", 0, "Sin base disponible"),
                unsafe_allow_html=True
            )

    def tienda_rank_table_html(rows_df, titulo, empty_msg=None):
        # Nota: el HTML se arma en una sola línea por elemento (sin saltos de
        # línea indentados) porque Streamlit interpreta texto indentado con
        # 4+ espacios después de un salto de línea como bloque de código, y
        # lo muestra como texto plano en vez de renderizarlo.
        header = (
            '<div style="background:#2f9e66;color:#fff;font-weight:800;'
            'font-size:15px;padding:13px 20px;display:flex;align-items:center;gap:10px;">'
            f'<span>🏆</span><span>{titulo}</span>'
            '</div>'
        )
        if empty_msg is None:
            empty_msg = (
                'Todavía no hay datos por tienda para este período. Se completa '
                'automáticamente la próxima vez que se suba el Excel desde "app" '
                '(si trae las columnas Tienda y Nombre).'
            )
        if not len(rows_df):
            return (
                f'<div class="rank-table-card">{header}'
                f'<div style="padding:20px;color:#9ca3af;font-size:13px;">{empty_msg}</div>'
                '</div>'
            )

        rows_html = ""
        for i, r in enumerate(rows_df.itertuples(), start=1):
            nombre = str(r.Nombre) if r.Nombre else ""
            tienda_label = f"{r.Tienda} - {nombre}" if nombre else str(r.Tienda)
            rows_html += (
                '<tr>'
                '<td><span class="rank-badge" style="background:#2f9e66;color:#fff;">'
                f'{i}</span></td>'
                f'<td>{html.escape(tienda_label)}</td>'
                f'<td style="text-align:center;">{intfmt(r.orders)}</td>'
                f'<td style="text-align:right;font-weight:800;color:#208653;">{money(r.ecommerce_tax)}</td>'
                '</tr>'
            )

        return (
            f'<div class="rank-table-card">{header}'
            '<div class="table-scroll">'
            '<table class="rank-table"><thead><tr>'
            '<th></th><th>Tienda</th>'
            '<th style="text-align:center;">Pedidos eCommerce</th>'
            '<th style="text-align:right;">Venta eCommerce (con impuesto)</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table>'
            '</div></div>'
        )

    def faltantes_rank_table_html(rows_df, titulo, show_dias=False, empty_msg=None):
        header = (
            '<div style="background:#ff5a1f;color:#fff;font-weight:800;'
            'font-size:15px;padding:13px 20px;display:flex;align-items:center;gap:10px;">'
            f'<span>🚨</span><span>{titulo}</span>'
            '</div>'
        )
        if faltantes_log is None:
            return (
                f'<div class="rank-table-card">{header}'
                '<div style="padding:20px;color:#9ca3af;font-size:13px;">'
                'Este ranking todavía no está conectado — hace falta activar el '
                'historial de Faltantes en Google Sheets (misma configuración que '
                'ya usa la pestaña "Operativo").'
                '</div></div>'
            )
        if empty_msg is None:
            empty_msg = (
                'Todavía no hay faltantes cargados este mes. Se completa automáticamente '
                'cada vez que se sube un archivo de Faltantes desde "Operativo".'
            )
        if not len(rows_df):
            return (
                f'<div class="rank-table-card">{header}'
                f'<div style="padding:20px;color:#9ca3af;font-size:13px;">{empty_msg}</div>'
                '</div>'
            )

        th_style = 'background:#fdeee5;color:#c9481a;font-weight:700;padding:10px 14px;'
        rows_html = ""
        for i, r in enumerate(rows_df.itertuples(), start=1):
            dias_td = ""
            if show_dias:
                dias_td = f'<td style="text-align:center;">{intfmt(r.Dias)}</td>'
            rows_html += (
                '<tr>'
                '<td><span class="rank-badge" style="background:#ff5a1f;color:#fff;">'
                f'{i}</span></td>'
                f'<td>{html.escape(str(r.Tienda))}</td>'
                f'<td style="text-align:right;font-weight:800;color:#c9481a;">{intfmt(r.Faltantes)}</td>'
                f'{dias_td}'
                '</tr>'
            )

        dias_th = f'<th style="{th_style}text-align:center;">Días con faltantes</th>' if show_dias else ""
        thead = (
            '<tr>'
            f'<th style="{th_style}text-align:left;"></th>'
            f'<th style="{th_style}text-align:left;">Tienda</th>'
            f'<th style="{th_style}text-align:right;">Faltantes (SKUs)</th>'
            f'{dias_th}'
            '</tr>'
        )
        return (
            f'<div class="rank-table-card">{header}'
            '<div class="table-scroll">'
            f'<table class="rank-table"><thead>{thead}</thead><tbody>{rows_html}</tbody></table>'
            '</div></div>'
        )

    _total_faltantes_mes = int(faltantes_rank["Faltantes"].sum()) if len(faltantes_rank) else 0
    _tiendas_con_faltantes = len(faltantes_rank)
    st.markdown('<div class="section">Faltantes</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #ff5a1f;max-width:340px;">
      <div class="label" style="color:#ff5a1f;">FALTANTES · ACUMULADO DEL MES</div>
      <div class="value">{intfmt(_total_faltantes_mes)}</div>
      <div class="small">{intfmt(_tiendas_con_faltantes)} tiendas con faltantes este mes</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section">Top 5 tiendas eCommerce</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">'
        'Ranking por venta ecommerce, con pedidos de cada tienda.'
        '</div>',
        unsafe_allow_html=True
    )

    td1, td2 = st.columns(2)
    with td1:
        st.markdown(
            tienda_rank_table_html(
                top_venta_dia,
                f"VENTA DIARIA · TOP 5 ({latest_tienda_date.strftime('%d/%m')})",
                empty_msg=(
                    'Todavía no hay datos por tienda para el último día cargado. '
                    'Se completa automáticamente la próxima vez que se suba el Excel '
                    'desde "app" (si trae las columnas Tienda y Nombre).'
                ),
            ),
            unsafe_allow_html=True
        )
    with td2:
        st.markdown(
            tienda_rank_table_html(
                top_venta_mes,
                "VENTA MENSUAL · TOP 5",
                empty_msg=(
                    'Todavía no hay datos por tienda para el mes en curso. '
                    'Se completa automáticamente la próxima vez que se suba el Excel '
                    'desde "app" (si trae las columnas Tienda y Nombre).'
                ),
            ),
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="footer">'
        '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
        '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
        '</div>',
        unsafe_allow_html=True
    )

with tab2:
    st.markdown('<div class="section">Resumen para GDN</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
        'Capturá esta card y enviala directo — sin tocar el resto del dashboard.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;">
      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
          DIARIO &nbsp;|&nbsp; {latest["date"].strftime("%d-%m")}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(latest["company_tax"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(latest["ecommerce_tax"])}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["orders"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["units"])}</div>
            </div>
          </div>
        </div>
        <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE DIARIO</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_daily)}</span>
        </div>
      </div>

      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
          MENSUAL &nbsp;SEPTIEMBRE 2026
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA MENSUAL</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(acc_company)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA MENSUAL</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(acc_ecom)}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_orders)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_units)}</div>
            </div>
          </div>
        </div>
        <div style="background:#fef6e7;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE MENSUAL</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share)}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="section">Fin de semana vs. acumulado</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
        'Fin de semana = Viernes + Sábado + Domingo.'
        '</div>',
        unsafe_allow_html=True
    )

    share_weekend_daily_style = weekend_full_share

    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;">
      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
          FIN DE SEMANA &nbsp;|&nbsp; {weekend_full_label}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(weekend_full_company)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(weekend_full_ecom)}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(weekend_full_orders)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(weekend_full_units)}</div>
            </div>
          </div>
        </div>
        <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE FIN DE SEMANA</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_weekend_daily_style)}</span>
        </div>
      </div>

      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
          MENSUAL &nbsp;SEPTIEMBRE 2026
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA MENSUAL</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(acc_company)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA MENSUAL</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(acc_ecom)}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_orders)}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_units)}</div>
            </div>
          </div>
        </div>
        <div style="background:#fef6e7;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE MENSUAL</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share)}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section">Venta por fin de semana del mes</div>', unsafe_allow_html=True)

    if len(finde_tabla):
        finde_rows_html = ""
        for _, r in finde_tabla.iterrows():
            finde_rows_html += (
                '<tr style="border-top:1px solid #eee;">'
                f'<td style="padding:10px 14px;color:#20252b;">{r["rango"]}</td>'
                f'<td style="padding:10px 14px;font-weight:700;color:#e8432c;">{money(r["venta"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{intfmt(r["pedidos"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{intfmt(r["unidades"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{pct(r["participacion"])}</td>'
                '</tr>'
            )

        st.markdown(f"""
        <div class="table-scroll" style="background:white;border:1px solid #e8ebef;border-radius:14px;overflow-x:auto;box-shadow:0 2px 10px rgba(0,0,0,.06);">
          <table style="width:100%;border-collapse:collapse;font-size:13px;min-width:520px;">
            <thead>
              <tr style="background:#20252b;color:white;text-align:left;">
                <th style="padding:10px 14px;">FIN DE SEMANA</th>
                <th style="padding:10px 14px;">VENTA ECOMMERCE</th>
                <th style="padding:10px 14px;">PEDIDOS</th>
                <th style="padding:10px 14px;">UNIDADES</th>
                <th style="padding:10px 14px;">% DEL MES</th>
              </tr>
            </thead>
            <tbody>
              {finde_rows_html}
            </tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="upload-box"><div class="upload-text">'
            'Todavía no hay ningún fin de semana (viernes, sábado y domingo) cargado este mes.'
            '</div></div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="footer">'
        '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
        '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
        '</div>',
        unsafe_allow_html=True
    )

with tab4:
    st.markdown('<div class="section">Comparación entre fines de semana</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
        'Fin de semana = Viernes + Sábado + Domingo. Se compara el finde más reciente '
        'contra el finde anterior.'
        '</div>',
        unsafe_allow_html=True
    )

    if finde_actual is None:
        st.markdown(
            '<div class="upload-box"><div class="upload-text">'
            'Todavía no hay ningún fin de semana cargado.'
            '</div></div>',
            unsafe_allow_html=True
        )
    else:
        share_finde_actual = (
            (finde_actual["venta"] / finde_actual["company"])
            if finde_actual["company"] else 0
        )

        if finde_anterior is not None:
            share_finde_anterior = (
                (finde_anterior["venta"] / finde_anterior["company"])
                if finde_anterior["company"] else 0
            )
            card_anterior_html = f"""
              <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
                <div style="background:#59636e;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
                  FIN DE SEMANA ANTERIOR &nbsp;|&nbsp; {finde_anterior_rango}
                </div>
                <div style="padding:18px 16px;">
                  <div style="display:flex;gap:12px;">
                    <div style="flex:1;">
                      <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
                      <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                      <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(finde_anterior["company"])}</div>
                    </div>
                    <div style="flex:1;">
                      <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
                      <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                      <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(finde_anterior["venta"])}</div>
                    </div>
                  </div>
                  <div style="border-top:1px solid #eee;margin:14px 0;"></div>
                  <div style="display:flex;gap:12px;">
                    <div style="flex:1;">
                      <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
                      <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_anterior["pedidos"])}</div>
                    </div>
                    <div style="flex:1;">
                      <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
                      <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_anterior["unidades"])}</div>
                    </div>
                  </div>
                </div>
                <div style="background:#eef0f2;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE</span>
                  <span style="font-size:20px;font-weight:800;color:#59636e;">{pct(share_finde_anterior)}</span>
                </div>
              </div>
            """
        else:
            card_anterior_html = """
              <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);display:flex;align-items:center;justify-content:center;padding:20px;">
                <div style="color:#9ca3af;font-size:13px;text-align:center;">Sin fin de semana anterior cargado todavía.</div>
              </div>
            """

        st.markdown(f"""
        <div style="display:flex;flex-wrap:wrap;gap:16px;">
          <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
            <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
              FIN DE SEMANA ACTUAL &nbsp;|&nbsp; {finde_actual_rango}
            </div>
            <div style="padding:18px 16px;">
              <div style="display:flex;gap:12px;">
                <div style="flex:1;">
                  <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
                  <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                  <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(finde_actual["company"])}</div>
                </div>
                <div style="flex:1;">
                  <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
                  <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                  <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(finde_actual["venta"])}</div>
                </div>
              </div>
              <div style="border-top:1px solid #eee;margin:14px 0;"></div>
              <div style="display:flex;gap:12px;">
                <div style="flex:1;">
                  <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
                  <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_actual["pedidos"])}</div>
                </div>
                <div style="flex:1;">
                  <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
                  <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_actual["unidades"])}</div>
                </div>
              </div>
            </div>
            <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE</span>
              <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_finde_actual)}</span>
            </div>
          </div>

          {card_anterior_html}
        </div>
        """, unsafe_allow_html=True)

        if finde_vs_anterior is not None:
            st.markdown('<div class="section">Variación vs. finde anterior</div>', unsafe_allow_html=True)
            st.markdown(
                compare_box(
                    "VENTA ECOMMERCE FIN DE SEMANA",
                    finde_vs_anterior,
                    f"{finde_actual_rango} vs {finde_anterior_rango}"
                ),
                unsafe_allow_html=True
            )

    st.markdown(
        '<div class="footer">'
        '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
        '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
        '</div>',
        unsafe_allow_html=True
    )
