import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import base64
import calendar

st.set_page_config(page_title="MásOnline | Ecommerce", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background: #f5f7fa; }
    .block-container { max-width: 1500px; padding: 0 1.2rem 1.2rem; }

    .hero {
        background: #171b20;
        margin: -1rem -1.2rem 1.2rem;
        padding: 22px 28px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 4px solid #20252b;
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
    .small { color: #6b7280; font-size: 13px; margin-top: 7px; }

    .section {
        font-size: 20px; font-weight: 800; color: #20252b;
        margin: 26px 0 12px;
    }

    .progress-wrap {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        border: 1px solid #e8ebef;
    }
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
        color: #208653; font-size: 30px; font-weight: 800;
        text-align: right; line-height: 1;
    }
    .progress-target small { display: block; color: #6b7280; font-size: 12px; font-weight: 400; margin-top: 5px; }

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

DATA_FILE = Path(__file__).resolve().parent / "data.csv"

# Carga base: data.csv. El archivo subido en la app puede reemplazarlo para esta sesión.
try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

# Carga opcional del reporte original de "Venta Con y sin Impuesto".
st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;padding:12px 16px;margin-bottom:14px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">ACTUALIZAR DATOS</div>
  <div style="font-size:12px;color:#6b7280;">Subí el Excel "Venta Con y sin Impuesto" y el dashboard calculará los indicadores con ese archivo.</div>
</div>
""", unsafe_allow_html=True)

u1, u2, u3 = st.columns(3)

with u1:
    st.markdown("""
    <div class="upload-box upload-current">
      <div class="upload-title">MES EN CURSO</div>
      <div class="upload-text">Subí el Excel de Septiembre 2026</div>
    </div>
    """, unsafe_allow_html=True)
    upload_current = st.file_uploader(
        "Archivo mes en curso",
        type=["xlsx", "xls"],
        key="upload_current",
        label_visibility="collapsed",
        help="Reporte Venta Con y sin Impuesto del mes en curso."
    )

with u2:
    st.markdown("""
    <div class="upload-box upload-prev">
      <div class="upload-title">MES ANTERIOR</div>
      <div class="upload-text">Subí el Excel de Agosto 2026</div>
    </div>
    """, unsafe_allow_html=True)
    upload_prev = st.file_uploader(
        "Archivo mes anterior",
        type=["xlsx", "xls"],
        key="upload_prev",
        label_visibility="collapsed",
        help="Reporte Venta Con y sin Impuesto del mes anterior."
    )

with u3:
    st.markdown("""
    <div class="upload-box upload-ly">
      <div class="upload-title">MISMO PERÍODO AÑO PASADO</div>
      <div class="upload-text">Subí el Excel de Septiembre 2025</div>
    </div>
    """, unsafe_allow_html=True)
    upload_ly = st.file_uploader(
        "Archivo año pasado",
        type=["xlsx", "xls"],
        key="upload_ly",
        label_visibility="collapsed",
        help="Reporte Venta Con y sin Impuesto del mismo mes del año pasado."
    )

def normalize_uploaded_excel(file):
    raw = pd.read_excel(file, sheet_name=0, header=None)
    header_row = None
    for i in range(min(10, len(raw))):
        vals = raw.iloc[i].astype(str).str.strip().tolist()
        if "Fecha" in vals and "Facturacion" in vals and "Venta - Ecommerce" in vals:
            header_row = i
            break
    if header_row is None:
        raise ValueError("No encontré las columnas Fecha, Facturacion y Venta - Ecommerce en el archivo.")

    d = pd.read_excel(file, sheet_name=0, header=header_row)
    required = [
        "Fecha", "Facturacion", "Venta - Ecommerce",
        "Cantidad Venta Operativa - Ecommerce",
        "Pedidos Facturados con Venta Operativa - Ecommerce"
    ]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError("Faltan columnas: " + ", ".join(missing))

    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    for c in required[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d = d.dropna(subset=["Fecha"])

    out = d.groupby("Fecha", as_index=False).agg(
        company_tax=("Facturacion", "sum"),
        ecommerce_tax=("Venta - Ecommerce", "sum"),
        orders=("Pedidos Facturados con Venta Operativa - Ecommerce", "sum"),
        units=("Cantidad Venta Operativa - Ecommerce", "sum")
    )
    out = out.rename(columns={"Fecha": "date"})
    out["source"] = "Reporte subido"
    return out

# Cada botón reemplaza únicamente el período que corresponde.
# Si no se sube un archivo, se usa la base histórica de data.csv.
df = base_df.copy()

def replace_period(uploaded_file, year, month, label):
    global df
    if uploaded_file is None:
        return
    try:
        incoming = normalize_uploaded_excel(uploaded_file)
        incoming = incoming[
            (incoming["date"].dt.year == year) &
            (incoming["date"].dt.month == month)
        ].copy()

        if incoming.empty:
            st.error(f"{label}: no encontré datos de {month:02d}/{year} en el archivo.")
            return

        df = df[
            ~(
                (df["date"].dt.year == year) &
                (df["date"].dt.month == month)
            )
        ].copy()

        df = pd.concat([df, incoming], ignore_index=True)
        df = (
            df.sort_values("date")
              .drop_duplicates(subset=["date"], keep="last")
              .reset_index(drop=True)
        )

        st.success(f"{label}: {len(incoming)} días cargados correctamente.")
    except Exception as e:
        st.error(f"{label}: no pude procesar el Excel: {e}")

replace_period(upload_current, 2026, 9, "Mes en curso")
replace_period(upload_prev, 2026, 8, "Mes anterior")
replace_period(upload_ly, 2025, 9, "Mismo período año pasado")

# El reporte puede traer el día actual todavía abierto. Para el dashboard usamos
# siempre el último día cerrado: excluimos la fecha de hoy de Argentina.
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"]).copy()

from datetime import datetime
from zoneinfo import ZoneInfo
arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df = df[df["date"].dt.date < arg_today].copy()

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

logo_file = Path(__file__).resolve().parent / "masonline_logo.png"
if logo_file.exists():
    import base64
    logo_b64 = base64.b64encode(logo_file.read_bytes()).decode("utf-8")
    brand_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:58px;max-width:330px;object-fit:contain;">'
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
  </div>
</div>
""", unsafe_allow_html=True)
html_descarga = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>MásOnline - Dashboard Ecommerce</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f5f7fa;
    margin: 0;
    padding: 40px;
    color: #252a31;
}}
.header {{
    background: #171b20;
    padding: 25px 35px;
    color: white;
    margin-bottom: 25px;
}}
h1 {{ margin: 0; }}
.grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
}}
.card {{
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,.08);
}}
.label {{
    font-size: 14px;
    font-weight: bold;
    color: #697386;
}}
.value {{
    font-size: 30px;
    font-weight: bold;
    margin-top: 15px;
}}
small {{ color: #697386; }}
</style>
</head>
<body>

<div class="header">
    <h1>MásOnline</h1>
    <div>E-COMMERCE · Septiembre 2026</div>
</div>

<div class="grid">

<div class="card">
    <div class="label">PARTICIPACIÓN E-COMMERCE</div>
    <div class="value">{pct(share)}</div>
    <small>Objetivo: 3,00%</small>
</div>

<div class="card">
    <div class="label">VENTA DÍA ANTERIOR</div>
    <div class="value">{money(latest["ecommerce_tax"])}</div>
    <small>Último día cerrado</small>
</div>

<div class="card">
    <div class="label">MES EN CURSO</div>
    <div class="value">{money(mtd_ecommerce)}</div>
    <small>Datos acumulados</small>
</div>

<div class="card">
    <div class="label">PROYECCIÓN DE CIERRE</div>
    <div class="value">{money(projection)}</div>
    <small>Proyección mensual</small>
</div>

</div>

</body>
</html>
"""

st.download_button(
    "⬇️ Descargar dashboard HTML",
    data=html_descarga,
    file_name="dashboard_masonline.html",
    mime="text/html",
    use_container_width=True
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
progress = min(share / target, 1.0) * 100
st.markdown(f"""
<div class="progress-wrap">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div style="flex:1;">
      <div class="progress-track"><div class="progress-fill" style="width:{progress:.1f}%;"></div></div>
      <div class="progress-row">
        <span>Participación actual: {pct(share)}</span>
        <span>Objetivo: {pct(target)}</span>
      </div>
    </div>
    <div style="width:150px;">
      <div class="progress-target">{share/target:.0%}<small>del objetivo</small></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section">Evolución diaria</div>', unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section">Comparaciones</div>', unsafe_allow_html=True)
st.markdown('<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">Variación de ventas e-commerce sobre la misma cantidad de días</div>', unsafe_allow_html=True)

a, b = st.columns(2)

def compare_box(title, value, base_text):
    cls = "positive" if value >= 0 else "negative"
    arrow = "↑" if value >= 0 else "↓"
    return f"""
    <div class="compare-card">
      <div class="compare-title">{title}</div>
      <div class="compare-base">{base_text}</div>
      <div class="compare-value {cls}">{arrow}&nbsp;&nbsp;{value:+.1%}</div>
    </div>"""

with a:
    if vs_aug is not None:
        st.markdown(compare_box("VS MES ANTERIOR", vs_aug, f"Sep 1–{n} 2026 vs Ago 1–{n} 2026"), unsafe_allow_html=True)
    else:
        st.markdown(compare_box("VS MES ANTERIOR", 0, "Sin base disponible"), unsafe_allow_html=True)

with b:
    if vs_25 is not None:
        st.markdown(compare_box("VS MISMO MES AÑO ANTERIOR", vs_25, f"Sep 1–{n} 2026 vs Sep 1–{n} 2025"), unsafe_allow_html=True)
    else:
        st.markdown(compare_box("VS MISMO MES AÑO ANTERIOR", 0, "Sin base disponible"), unsafe_allow_html=True)

st.markdown('<div class="footer"><span>Fuente: venta con impuesto de MicroStrategy.</span><span>MásOnline &nbsp;|&nbsp; E-commerce</span></div>', unsafe_allow_html=True)
