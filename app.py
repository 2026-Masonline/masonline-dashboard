import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import requests
import io

st.set_page_config(
    page_title="MásOnline | Venta",
    page_icon="📊",
    layout="wide"
)

# ---------- ESTILO ----------
st.markdown("""
<style>
    .main {background-color:#f5f6f7;}
    .block-container {padding-top:1.5rem; padding-bottom:1.5rem; max-width:1500px;}
    .kpi {
        background:white;
        border-radius:16px;
        padding:20px 22px;
        box-shadow:0 2px 10px rgba(0,0,0,.06);
        min-height:145px;
    }
    .kpi-title {
        font-size:13px;
        font-weight:800;
        text-transform:uppercase;
        color:#777;
        letter-spacing:.05em;
    }
    .kpi-value {
        font-size:30px;
        font-weight:800;
        color:#20242a;
        margin-top:8px;
    }
    .kpi-sub {
        font-size:13px;
        color:#777;
        margin-top:6px;
    }
    .section {
        font-size:20px;
        font-weight:800;
        color:#20242a;
        margin:22px 0 10px;
    }
    .compare-card {
        background:white;
        border-radius:16px;
        padding:18px 20px;
        box-shadow:0 2px 10px rgba(0,0,0,.06);
        min-height:125px;
    }
    .compare-title {
        font-size:13px;
        font-weight:800;
        text-transform:uppercase;
        color:#777;
        letter-spacing:.04em;
    }
    .compare-value {
        font-size:28px;
        font-weight:800;
        color:#20242a;
        margin-top:8px;
    }
    .compare-detail {
        font-size:12px;
        color:#777;
        margin-top:5px;
    }
    .source {
        color:#777;
        font-size:12px;
        margin-top:22px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- HELPERS ----------
LOCAL_FILE = Path(__file__).resolve().parent / "Dashboard Mas-Online.xlsx"
EXCEL_URL = "https://github.com/2026-Masonline/masonline-dashboard/raw/refs/heads/main/Dashboard%20Mas-Online.xlsx"

def moneda_mm(valor):
    return f"${valor/1e6:,.2f} MM".replace(",", "X").replace(".", ",").replace("X", ".")

def porcentaje(valor):
    return f"{valor:+.1%}"

@st.cache_data
def cargar_dashboard():
    if LOCAL_FILE.exists():
        df = pd.read_excel(LOCAL_FILE, sheet_name="Dashboard", engine="openpyxl")
    else:
        response = requests.get(EXCEL_URL, timeout=60)
        response.raise_for_status()
        df = pd.read_excel(io.BytesIO(response.content), sheet_name="Dashboard", engine="openpyxl")

    fechas = pd.to_datetime(df.iloc[:, 8], errors="coerce")
    compania = pd.to_numeric(df.iloc[:, 9], errors="coerce")
    ecommerce = pd.to_numeric(df.iloc[:, 10], errors="coerce")
    pedidos = pd.to_numeric(df.iloc[:, 11], errors="coerce")
    unidades = pd.to_numeric(df.iloc[:, 12], errors="coerce")

    datos = pd.DataFrame({
        "Fecha": fechas,
        "Facturacion_Compañia": compania,
        "Venta_Ecommerce": ecommerce,
        "Pedidos": pedidos,
        "Unidades": unidades
    }).dropna(subset=["Fecha", "Facturacion_Compañia", "Venta_Ecommerce"])

    return datos

@st.cache_data
def cargar_ecommerce_historico(sheet_name):
    if LOCAL_FILE.exists():
        d = pd.read_excel(LOCAL_FILE, sheet_name=sheet_name, engine="openpyxl")
    else:
        response = requests.get(EXCEL_URL, timeout=60)
        response.raise_for_status()
        d = pd.read_excel(io.BytesIO(response.content), sheet_name=sheet_name, engine="openpyxl")
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d["Venta - Ecommerce"] = pd.to_numeric(
        d["Venta - Ecommerce"], errors="coerce"
    ).fillna(0)

    d = d.dropna(subset=["Fecha"])
    return d

# ---------- CARGA ----------
try:
    df = cargar_dashboard()
except Exception as e:
    st.error(
        f"No pude leer el Excel. Error: {type(e).__name__}: {e}"
    )
    st.stop()

# ---------- SEPTIEMBRE 2026 ----------
df = df[
    (df["Fecha"].dt.year == 2026) &
    (df["Fecha"].dt.month == 9)
].copy()

df = df.sort_values("Fecha")

if df.empty:
    st.warning("No hay datos de septiembre 2026.")
    st.stop()

# ---------- CALCULOS PRINCIPALES ----------
dias_cargados = len(df)
ultimo = df.iloc[-1]
dia_corte = int(ultimo["Fecha"].day)
dias_mes = int(ultimo["Fecha"].days_in_month)

venta_ecom = df["Venta_Ecommerce"].sum()
venta_compania = df["Facturacion_Compañia"].sum()
share = venta_ecom / venta_compania if venta_compania else 0

objetivo = 0.03
avance_objetivo = share / objetivo if objetivo else 0

venta_ultimo = ultimo["Venta_Ecommerce"]

if len(df) >= 2:
    venta_anterior = df.iloc[-2]["Venta_Ecommerce"]
    vs_dia_anterior = (
        venta_ultimo / venta_anterior - 1
        if venta_anterior else 0
    )
else:
    vs_dia_anterior = 0

promedio_diario = venta_ecom / dias_cargados
proyeccion = promedio_diario * dias_mes

# ---------- COMPARATIVOS LIKE-FOR-LIKE ----------
# Se compara el mismo número de días cargados:
# Sep-2026 1..N vs Ago-2026 1..N
# Sep-2026 1..N vs Sep-2025 1..N
try:
    agosto = cargar_ecommerce_historico("Agosto 2026")
    agosto_mismo_periodo = agosto[
        agosto["Fecha"].dt.day <= dia_corte
    ]["Venta - Ecommerce"].sum()
    vs_mes_anterior = (
        venta_ecom / agosto_mismo_periodo - 1
        if agosto_mismo_periodo else None
    )
except Exception:
    agosto_mismo_periodo = None
    vs_mes_anterior = None

try:
    sep25 = cargar_ecommerce_historico("Septiembre 2025")
    sep25_mismo_periodo = sep25[
        sep25["Fecha"].dt.day <= dia_corte
    ]["Venta - Ecommerce"].sum()
    vs_2025 = (
        venta_ecom / sep25_mismo_periodo - 1
        if sep25_mismo_periodo else None
    )
except Exception:
    sep25_mismo_periodo = None
    vs_2025 = None

# ---------- HEADER ----------
c1, c2 = st.columns([3, 1])

with c1:
    st.title("Venta e-commerce")
    st.caption(
        f"MásOnline · Septiembre 2026 · "
        f"Último cierre: {ultimo['Fecha'].strftime('%d/%m/%Y')}"
    )

with c2:
    st.markdown(
        "<div style='text-align:right;font-size:28px;font-weight:800;'>"
        "MÁS<span style='font-weight:400;'>ONLINE</span></div>",
        unsafe_allow_html=True
    )

# ---------- KPIs PRINCIPALES ----------
cols = st.columns(4)

with cols[0]:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Share e-commerce</div>
        <div class="kpi-value">{share:.2%}</div>
        <div class="kpi-sub">Objetivo: 3,00%</div>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    color = "#d66c00" if vs_dia_anterior < 0 else "#4b9b63"
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Venta día anterior</div>
        <div class="kpi-value">{moneda_mm(venta_ultimo)}</div>
        <div class="kpi-sub" style="color:#777;">
            Cierre {ultimo['Fecha'].strftime('%d/%m')}
        </div>
        <div class="kpi-sub" style="color:{color};font-weight:800;">
            Vs día anterior: {porcentaje(vs_dia_anterior)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Mes en curso</div>
        <div class="kpi-value">{moneda_mm(venta_ecom)}</div>
        <div class="kpi-sub">
            {dias_cargados} días cargados · Promedio {moneda_mm(promedio_diario)}/día
        </div>
    </div>
    """, unsafe_allow_html=True)

with cols[3]:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Proyección de cierre</div>
        <div class="kpi-value">{moneda_mm(proyeccion)}</div>
        <div class="kpi-sub">
            Run-rate actual · {dias_mes} días
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- OBJETIVO ----------
st.markdown(
    '<div class="section">Avance hacia el objetivo de 3%</div>',
    unsafe_allow_html=True
)

st.progress(min(max(avance_objetivo, 0), 1.0))
st.caption(
    f"Avance: {avance_objetivo:.1%} · "
    f"Brecha actual: {(objetivo-share)*100:.2f} puntos porcentuales"
)

# ---------- GRAFICO ----------
st.markdown(
    '<div class="section">Evolución diaria de venta e-commerce</div>',
    unsafe_allow_html=True
)

chart = df[["Fecha", "Venta_Ecommerce"]].copy()
chart["Venta MM"] = chart["Venta_Ecommerce"] / 1e6

fig = px.line(
    chart,
    x="Fecha",
    y="Venta MM",
    markers=True,
    labels={"Fecha": "", "Venta MM": "Venta ($ MM)"}
)

fig.update_layout(
    height=390,
    margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

# ---------- COMPARATIVOS ----------
st.markdown(
    '<div class="section">Evolución vs períodos comparables</div>',
    unsafe_allow_html=True
)

a, b, c = st.columns(3)

with a:
    valor = "—" if vs_mes_anterior is None else porcentaje(vs_mes_anterior)
    detalle = (
        f"Sep 2026 1–{dia_corte}: {moneda_mm(venta_ecom)}"
        + (
            f" · Ago 2026 1–{dia_corte}: {moneda_mm(agosto_mismo_periodo)}"
            if agosto_mismo_periodo is not None else ""
        )
    )
    st.markdown(f"""
    <div class="compare-card">
        <div class="compare-title">Vs mes anterior</div>
        <div class="compare-value">{valor}</div>
        <div class="compare-detail">{detalle}</div>
    </div>
    """, unsafe_allow_html=True)

with b:
    valor = "—" if vs_2025 is None else porcentaje(vs_2025)
    detalle = (
        f"Sep 2026 1–{dia_corte}: {moneda_mm(venta_ecom)}"
        + (
            f" · Sep 2025 1–{dia_corte}: {moneda_mm(sep25_mismo_periodo)}"
            if sep25_mismo_periodo is not None else ""
        )
    )
    st.markdown(f"""
    <div class="compare-card">
        <div class="compare-title">Vs 2025</div>
        <div class="compare-value">{valor}</div>
        <div class="compare-detail">{detalle}</div>
    </div>
    """, unsafe_allow_html=True)

with c:
    st.markdown(f"""
    <div class="compare-card">
        <div class="compare-title">Avance al objetivo</div>
        <div class="compare-value">{avance_objetivo:.1%}</div>
        <div class="compare-detail">
            Share actual {share:.2%} · Objetivo 3,00%
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- FUENTE ----------
st.markdown(
    '<div class="source">'
    'Fuente: venta con impuesto extraída de MicroStrategy · '
    'Datos cargados desde el Excel de MásOnline. '
    'Las comparaciones contra mes anterior y 2025 utilizan el mismo '
    'número de días cargados del mes en curso.'
    '</div>',
    unsafe_allow_html=True
)

