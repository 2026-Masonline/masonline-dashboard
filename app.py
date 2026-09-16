import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import html

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
    .progress-target small {
        display: block; color: #6b7280; font-size: 12px;
        font-weight: 400; margin-top: 5px;
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

DATA_FILE = Path(__file__).resolve().parent / "data.csv"
LOGO_FILE = Path(__file__).resolve().parent / "masonline_logo.png"

try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin-bottom:14px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    ACTUALIZAR DATOS
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí el Excel "Venta Con y sin Impuesto" y el dashboard calculará los indicadores con ese archivo.
  </div>
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
        raise ValueError(
            "No encontré las columnas Fecha, Facturacion y Venta - Ecommerce en el archivo."
        )

    d = pd.read_excel(file, sheet_name=0, header=header_row)

    required = [
        "Fecha",
        "Facturacion",
        "Venta - Ecommerce",
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

        # GUARDAR LOS DATOS EN GITHUB
        try:
            import urllib.request
            import urllib.error
            import json
            import base64
            from datetime import datetime
            from zoneinfo import ZoneInfo

            token = st.secrets.get("GITHUB_TOKEN")

            if token:
                repo = "2026-Masonline/masonline-dashboard"
                path = "data.csv"
                branch = "main"

                url = f"https://api.github.com/repos/{repo}/contents/{path}"

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "Masonline-Dashboard"
                }

                # Obtener SHA actual de data.csv
                request_get = urllib.request.Request(
                    f"{url}?ref={branch}",
                    headers=headers,
                    method="GET"
                )

                with urllib.request.urlopen(request_get, timeout=30) as response:
                    github_file = json.loads(response.read().decode("utf-8"))

                sha = github_file["sha"]

                # No guardar el día actual si todavía está en curso
                arg_today = datetime.now(
                    ZoneInfo("America/Argentina/Buenos_Aires")
                ).date()

                save_df = df[
                    df["date"].dt.date < arg_today
                ].copy()

                save_df = save_df.sort_values("date")

                csv_text = save_df.to_csv(
                    index=False,
                    date_format="%Y-%m-%d"
                )

                content_b64 = base64.b64encode(
                    csv_text.encode("utf-8")
                ).decode("utf-8")

                payload = {
                    "message": f"Actualizar datos ecommerce - {label}",
                    "content": content_b64,
                    "sha": sha,
                    "branch": branch
                }

                request_put = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        **headers,
                        "Content-Type": "application/json"
                    },
                    method="PUT"
                )

                with urllib.request.urlopen(
                    request_put,
                    timeout=30
                ) as response:
                    response.read()

                st.success(
                    f"{label}: datos cargados y guardados correctamente."
                )

            else:
                st.warning(
                    "Los datos se cargaron para esta sesión, "
                    "pero GITHUB_TOKEN no está configurado."
                )

        except Exception as github_error:
            st.error(
                f"Los datos se cargaron, pero no se pudieron guardar en GitHub: "
                f"{github_error}"
            )

    except Exception as e:
        st.error(f"{label}: error al procesar el archivo: {e}")

        st.success(f"{label}: {len(incoming)} días cargados correctamente.")

    except Exception as e:
        st.error(f"{label}: no pude procesar el Excel: {e}")

replace_period(upload_current, 2026, 9, "Mes en curso")
replace_period(upload_prev, 2026, 8, "Mes anterior")
replace_period(upload_ly, 2025, 9, "Mismo período año pasado")

# Siempre mostramos el último día cerrado en Argentina.
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"]).copy()

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df = df[df["date"].dt.date < arg_today].copy()

current = df[
    (df["date"].dt.year == 2026) &
    (df["date"].dt.month == 9)
].copy().sort_values("date")

if current.empty:
    st.error("No hay datos de septiembre 2026.")
    st.stop()

latest = current.iloc[-1]
prev = current.iloc[-2] if len(current) > 1 else None
is_monday = arg_today.weekday() == 0

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

# Fin de semana = Viernes + Sábado (no se suma el Domingo)
weekend = friday_sales + saturday_sales
weekend_units = friday_units + saturday_units

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
  </div>
</div>

<div class="kpis">

<div class="card">
  <div class="label">PARTICIPACIÓN E-COMMERCE</div>
  <div class="value">{html.escape(pct(share))}</div>
  <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
</div>

<div class="card">
<div class="label">{sales_label}</div>
<div class="value">{html.escape(money(sales_value))}</div>
  <div class="small">Vs día previo: {html.escape(pct_change(day_change))}</div>
</div>

<div class="card">
  <div class="label">MES EN CURSO</div>
  <div class="value">{html.escape(money(acc_ecom))}</div>
  <div class="small">{int(acc_orders):,} pedidos · {int(acc_units):,} unidades</div>
</div>

<div class="card">
  <div class="label">PROYECCIÓN DE CIERRE</div>
  <div class="value">{html.escape(money(projection))}</div>
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

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card">
      <div class="label">PARTICIPACIÓN E-COMMERCE</div>
      <div class="value">{pct(share)}</div>
      <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
      <div class="label">{sales_label}</div>
<div class="value">{money(sales_value)}</div>
      <div class="small">Vs día previo: {pct_change(day_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
      <div class="label">MES EN CURSO</div>
      <div class="value">{money(acc_ecom)}</div>
      <div class="small">{int(acc_orders):,} pedidos · {int(acc_units):,} unidades</div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card">
      <div class="label">PROYECCIÓN DE CIERRE</div>
      <div class="value">{money(projection)}</div>
      <div class="small">Promedio diario × {days_month} días</div>
    </div>
    """, unsafe_allow_html=True)

progress = min(share / target, 1.0) * 100

st.markdown(f"""
<div class="progress-wrap">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div style="flex:1;">
      <div class="progress-track">
        <div class="progress-fill" style="width:{progress:.1f}%;"></div>
      </div>
      <div class="progress-row">
        <span>Participación actual: {pct(share)}</span>
        <span>Objetivo: {pct(target)}</span>
      </div>
    </div>
    <div style="width:150px;">
      <div class="progress-target">
        {share/target:.0%}
        <small>del objetivo</small>
      </div>
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

st.markdown('<div class="section">Evolución diaria</div>', unsafe_allow_html=True)
st.markdown('<div class="chart-card">', unsafe_allow_html=True)

chart = px.line(
    current,
    x="date",
    y="ecommerce_tax",
    markers=True,
    labels={"date": "Fecha", "ecommerce_tax": "Venta ecommerce"}
)

chart.update_layout(
    height=430,
    margin=dict(l=10, r=10, t=20, b=10),
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    hovermode="x unified"
)

st.plotly_chart(chart, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="footer">'
    '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
    '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
    '</div>',
    unsafe_allow_html=True
)
