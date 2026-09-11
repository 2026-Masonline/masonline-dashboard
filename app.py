
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="MásOnline | Venta",
    page_icon="📊",
    layout="wide"
)

# ---------- ESTILO ----------
st.markdown("""
<style>
    .main {background-color:#f5f6f7;}
    .block-container {padding-top:2rem; padding-bottom:2rem;}
    .kpi {
        background:white;
        border-radius:16px;
        padding:20px;
        box-shadow:0 2px 10px rgba(0,0,0,.06);
        min-height:145px;
    }
    .kpi-title {
        font-size:13px;
        font-weight:700;
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
        margin-top:5px;
    }
    .section {
        font-size:20px;
        font-weight:800;
        color:#20242a;
        margin:12px 0 8px;
    }
    .source {
        color:#777;
        font-size:12px;
        margin-top:20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- CARGA ----------
FILE = "Dashboard Mas-Online.xlsx"

@st.cache_data
def cargar_datos():
    df = pd.read_excel(FILE, sheet_name="Dashboard")

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

try:
    df = cargar_datos()
except Exception as e:
    st.error("No pude leer el Excel. Verificá que 'Dashboard Mas-Online.xlsx' esté en la misma carpeta que app.py.")
    st.stop()

# ---------- FILTRO SEPTIEMBRE 2026 ----------
df = df[(df["Fecha"].dt.year == 2026) & (df["Fecha"].dt.month == 9)].copy()
df = df.sort_values("Fecha")

if df.empty:
    st.warning("No hay datos de septiembre 2026.")
    st.stop()

# ---------- CALCULOS ----------
dias = len(df)
dias_mes = df["Fecha"].dt.days_in_month.iloc[0]

venta_ecom = df["Venta_Ecommerce"].sum()
venta_compania = df["Facturacion_Compañia"].sum()
share = venta_ecom / venta_compania if venta_compania else 0

objetivo = 0.03
avance_objetivo = share / objetivo if objetivo else 0

ultimo = df.iloc[-1]
venta_ultimo = ultimo["Venta_Ecommerce"]

if len(df) >= 2:
    venta_anterior = df.iloc[-2]["Venta_Ecommerce"]
    vs_dia_anterior = venta_ultimo / venta_anterior - 1 if venta_anterior else 0
else:
    vs_dia_anterior = 0

promedio_diario = venta_ecom / dias
proyeccion = promedio_diario * dias_mes

# Vs mes: agosto completo vs septiembre acumulado
# Si luego cargamos el histórico mensual en otra hoja, lo hacemos dinámico.
# Por ahora se calcula desde la hoja Agosto 2026.
try:
    agosto = pd.read_excel(FILE, sheet_name="Agosto 2026")
    # Busca una columna que contenga "ecommerce"
    col_ecom = next((c for c in agosto.columns if "ecommerce" in str(c).lower()), None)
    if col_ecom:
        agosto_val = pd.to_numeric(agosto[col_ecom], errors="coerce").sum()
        vs_mes = venta_ecom / agosto_val - 1 if agosto_val else None
    else:
        vs_mes = None
except:
    vs_mes = None

# Vs 2025
try:
    sep25 = pd.read_excel(FILE, sheet_name="Septiembre 2025")
    col_ecom25 = next((c for c in sep25.columns if "ecommerce" in str(c).lower()), None)
    if col_ecom25:
        val25 = pd.to_numeric(sep25[col_ecom25], errors="coerce").sum()
        vs_2025 = venta_ecom / val25 - 1 if val25 else None
    else:
        vs_2025 = None
except:
    vs_2025 = None

# ---------- HEADER ----------
c1, c2 = st.columns([3,1])
with c1:
    st.title("Venta e-commerce")
    st.caption(f"MásOnline · Septiembre 2026 · Último cierre: {ultimo['Fecha'].strftime('%d/%m/%Y')}")
with c2:
    st.markdown(
        "<div style='text-align:right;font-size:28px;font-weight:800;'>MÁS<span style='font-weight:400;'>ONLINE</span></div>",
        unsafe_allow_html=True
    )

# ---------- KPIs ----------
cols = st.columns(4)

with cols[0]:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Share</div>
        <div class="kpi-value">{share:.2%}</div>
        <div class="kpi-sub">Objetivo: 3,00%</div>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    color = "#d66c00" if vs_dia_anterior < 0 else "#4b9b63"
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Cierre {ultimo['Fecha'].strftime('%d/%m')}</div>
        <div class="kpi-value">${venta_ultimo/1e6:,.2f} MM</div>
        <div class="kpi-sub" style="color:{color};font-weight:700;">
            Vs día anterior: {vs_dia_anterior:+.1%}
        </div>
    </div>
    """.replace(",", "X").replace(".", ",").replace("X","."), unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Venta acumulada</div>
        <div class="kpi-value">${venta_ecom/1e6:,.2f} MM</div>
        <div class="kpi-sub">{dias} días cargados · Promedio ${promedio_diario/1e6:,.2f} MM/día</div>
    </div>
    """.replace(",", "X").replace(".", ",").replace("X","."), unsafe_allow_html=True)

with cols[3]:
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-title">Proyección de cierre</div>
        <div class="kpi-value">${proyeccion/1e6:,.2f} MM</div>
        <div class="kpi-sub">Run-rate actual · {dias_mes} días</div>
    </div>
    """.replace(",", "X").replace(".", ",").replace("X","."), unsafe_allow_html=True)

# ---------- OBJETIVO ----------
st.markdown('<div class="section">Avance hacia el objetivo de 3%</div>', unsafe_allow_html=True)
st.progress(min(avance_objetivo, 1.0))
st.caption(f"Avance: {avance_objetivo:.1%} · Brecha actual: {(objetivo-share)*100:.2f} puntos porcentuales")

# ---------- GRAFICO ----------
st.markdown('<div class="section">Evolución diaria de venta e-commerce</div>', unsafe_allow_html=True)

chart = df[["Fecha", "Venta_Ecommerce"]].copy()
chart["Venta MM"] = chart["Venta_Ecommerce"] / 1e6

fig = px.line(
    chart,
    x="Fecha",
    y="Venta MM",
    markers=True,
    labels={"Fecha":"", "Venta MM":"Venta ($ MM)"}
)
fig.update_layout(
    height=400,
    margin=dict(l=10,r=10,t=10,b=10),
    plot_bgcolor="white",
    paper_bgcolor="white"
)
st.plotly_chart(fig, use_container_width=True)

# ---------- COMPARATIVOS ----------
st.markdown('<div class="section">Comparativos</div>', unsafe_allow_html=True)
a,b = st.columns(2)

with a:
    valor = "—" if vs_mes is None else f"{vs_mes:+.1%}"
    st.metric("Variación Vs Mes Anterior", valor)

with b:
    valor = "—" if vs_2025 is None else f"{vs_2025:+.1%}"
    st.metric("Variación Vs 2025", valor)

st.markdown(
    '<div class="source">Fuente: venta con impuesto extraída de MicroStrategy · Datos cargados desde el Excel de MásOnline.</div>',
    unsafe_allow_html=True
)
