import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import calendar

st.set_page_config(page_title="MásOnline | Ecommerce", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background: #f5f7fa; }
    .block-container { max-width: 1500px; padding-top: 1.2rem; }
    .title { foimportnt-size: 34px; font-weight: 800; color: #20252b; margin-bottom: 0; }
    .subtitle { color: #6b7280; font-size: 15px; margin-bottom: 22px; }
    .card {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        min-height: 125px; border: 1px solid #e8ebef;
    }
    .label { color: #6b7280; font-size: 14px; font-weight: 600; }
    .value { color: #20252b; font-size: 30px; font-weight: 800; margin-top: 7px; }
    .small { color: #6b7280; font-size: 13px; margin-top: 5px; }
    .section { font-size: 20px; font-weight: 800; color: #20252b; margin: 28px 0 12px; }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

# Read the CSV directly. No cache, so a new data.csv is picked up after redeploy/refresh.
try:
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

# Current period: September 2026. The source column is intentionally not used
# because the uploaded report labels all rows with the same source text.
current = df[
    (df["date"].dt.year == 2026) &
    (df["date"].dt.month == 9)
].copy().sort_values("date")

if current.empty:
    st.error("No hay datos de septiembre 2026.")
    st.stop()

latest = current.iloc[-1]
prev = current.iloc[-2] if len(current) > 1 else None
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
    if prev is not None and prev["ecommerce_tax"] else 0
)

# Like-for-like comparisons: same number of elapsed days.
# We use dates, not the source label, so the report's source text can change safely.
n = days_elapsed
aug = df[
    (df["date"].dt.year == 2026) &
    (df["date"].dt.month == 8) &
    (df["date"].dt.day <= n)
].sort_values("date")
sep25 = df[
    (df["date"].dt.year == 2025) &
    (df["date"].dt.month == 9) &
    (df["date"].dt.day <= n)
].sort_values("date")

aug_acc = aug["ecommerce_tax"].sum()
sep25_acc = sep25["ecommerce_tax"].sum()
vs_aug = (acc_ecom / aug_acc - 1) if aug_acc else None
vs_25 = (acc_ecom / sep25_acc - 1) if sep25_acc else None

def money(v):
    return f"${v/1_000_000:,.2f} MM".replace(",", "X").replace(".", ",").replace("X", ".")

def pct(v):
    return f"{v*100:.2f}%".replace(".", ",")

def pct_change(v):
    return f"{v:+.2%}".replace(".", ",")

st.markdown('<div class="title">MásOnline | Dashboard Ecommerce</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtitle">Septiembre 2026 · Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card">
      <div class="label">PARTICIPACIÓN E-COMMERCE</div>
      <div class="value">{pct(share)}</div>
      <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
      <div class="label">VENTA DÍA ANTERIOR</div>
      <div class="value">{money(latest["ecommerce_tax"])}</div>
      <div class="small">Vs día previo: {pct_change(day_change)}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
      <div class="label">MES EN CURSO</div>
      <div class="value">{money(acc_ecom)}</div>
      <div class="small">{int(acc_orders):,} pedidos · {int(acc_units):,} unidades</div>
    </div>""".replace(",", "."), unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card">
      <div class="label">PROYECCIÓN DE CIERRE</div>
      <div class="value">{money(projection)}</div>
      <div class="small">Promedio diario × {days_month} días</div>
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="section">Avance de participación</div>', unsafe_allow_html=True)
st.progress(min(share / target, 1.0))
st.caption(f"Participación actual: {pct(share)} · Objetivo: {pct(target)}")

st.markdown('<div class="section">Evolución diaria</div>', unsafe_allow_html=True)
chart = px.line(
    current, x="date", y="ecommerce_tax", markers=True,
    labels={"date": "Fecha", "ecommerce_tax": "Venta ecommerce"}
)
chart.update_layout(
    height=430, margin=dict(l=10, r=10, t=20, b=10),
    yaxis_tickprefix="$", yaxis_tickformat=",.0f",
    hovermode="x unified"
)
st.plotly_chart(chart, use_container_width=True)

st.markdown('<div class="section">Comparaciones — misma cantidad de días</div>', unsafe_allow_html=True)
a, b, c = st.columns(3)

def comparison_card(title, value, base_text):
    sign = "+" if value >= 0 else ""
    return f"""
    <div class="card">
      <div class="label">{title}</div>
      <div class="value">{sign}{value*100:.1f}%</div>
      <div class="small">{base_text}</div>
    </div>"""

with a:
    if vs_aug is not None:
        st.markdown(comparison_card("VS MES ANTERIOR", vs_aug, f"Sep 1–{n} vs Ago 1–{n}"), unsafe_allow_html=True)
    else:
        st.markdown(comparison_card("VS MES ANTERIOR", 0, "Sin base disponible"), unsafe_allow_html=True)

with b:
    if vs_25 is not None:
        st.markdown(comparison_card("VS 2025", vs_25, f"Sep 1–{n} 2026 vs Sep 1–{n} 2025"), unsafe_allow_html=True)
    else:
        st.markdown(comparison_card("VS 2025", 0, "Sin base disponible"), unsafe_allow_html=True)

with c:
    st.markdown(f"""
    <div class="card">
      <div class="label">AVANCE AL OBJETIVO</div>
      <div class="value">{share/target:.1%}</div>
      <div class="small">Objetivo de participación: 3,00%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Fuente: venta con impuesto de MicroStrategy. Comparaciones históricas calculadas sobre la misma cantidad de días transcurridos.")
