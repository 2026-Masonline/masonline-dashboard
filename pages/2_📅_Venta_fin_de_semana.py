import streamlit as st
import pandas as pd
import calendar
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import html

st.set_page_config(
    page_title="MásOnline | Venta fin de semana",
    page_icon="📅",
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

    .section {
        font-size: 20px; font-weight: 800; color: #20252b;
        margin: 26px 0 12px;
    }

    .card {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        min-height: 125px; border: 1px solid #e8ebef;
    }
    .label { color: #6b7280; font-size: 14px; font-weight: 700; }
    .value { color: #20252b; font-size: 30px; font-weight: 800; margin-top: 7px; }
    .small { color: #20252b; font-size: 13px; font-weight: 700; margin-top: 7px; }

    .progress-wrap {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        border: 1px solid #e8ebef; margin-top: 16px;
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

    .upload-box {
        background: white; border-radius: 14px; padding: 16px 18px 8px;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.05);
        margin-bottom: 6px; min-height: 82px;
    }
    .upload-text { color:#6b7280; font-size:12px; margin-top:5px; }

    .footer {
        display: flex; justify-content: space-between; color: #6b7280;
        font-size: 12px; margin-top: 12px;
    }

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero img { max-width: 170px !important; height: 40px !important; }
        .hero-brand { font-size: 22px; }
        .hero-date { text-align: left; }
        .section { font-size: 17px; margin: 20px 0 8px; }
        .value { font-size: 24px; }
        .progress-layout { flex-direction: column; align-items: stretch; gap: 14px; }
        .progress-target { width: auto; text-align: left; }
        table { font-size: 12px; }
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).resolve().parent.parent / "data.csv"
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

try:
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

# Esta página muestra la misma info de fin de semana que ya está en la
# pestaña "Venta fin de semana" del Dashboard de Ventas. Los datos se
# actualizan subiendo los Excels ahí — acá solo se leen y se muestran.

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df = df[df["date"].dt.date < arg_today].copy()

current = df[
    (df["date"].dt.year == 2026) &
    (df["date"].dt.month == 9)
].copy().sort_values("date")

if current.empty:
    st.error("No hay datos de septiembre 2026 todavía. Subilos desde la página del Dashboard de Ventas.")
    st.stop()

latest = current.iloc[-1]
days_month = calendar.monthrange(2026, 9)[1]
days_elapsed = len(current)

acc_ecom = current["ecommerce_tax"].sum()
acc_company = current["company_tax"].sum()
acc_orders = current["orders"].sum()
acc_units = current["units"].sum()
projection = acc_ecom / days_elapsed * days_month if days_elapsed else 0

target = 0.03
share = acc_ecom / acc_company if acc_company else 0
progress = min(share / target, 1.0) * 100 if target else 0

# Buscamos el Sábado más reciente con datos cargados (y el Viernes/Domingo
# alrededor), sin asumir que "hoy" es un día en particular.
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

# Fin de semana = Viernes + Sábado + Domingo (los tres días).
weekend_full_ecom = friday_sales + saturday_sales + sunday_sales
weekend_full_units = friday_units + saturday_units + sunday_units
weekend_full_orders = friday_orders + saturday_orders + sunday_orders
weekend_full_company = friday_company + saturday_company + sunday_company
weekend_full_share = (weekend_full_ecom / weekend_full_company) if weekend_full_company else 0
weekend_full_label = f"{last_friday.strftime('%d-%m')} al {last_sunday.strftime('%d-%m')}"

# ---- Venta por fin de semana del mes en curso ----
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

def money(v):
    return (
       f"${v/1_000_000:,.2f} M"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

def pct(v):
    return f"{v*100:.2f}%".replace(".", ",")

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
    <div class="hero-sub">VENTA FIN DE SEMANA</div>
  </div>
  <div class="hero-date">
    Septiembre 2026
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# HTML DESCARGABLE: copia independiente de esta página, sin Streamlit.
# ---------------------------------------------------------------------

def build_standalone_html():
    if LOGO_FILE.exists():
        html_logo = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            'style="height:58px;max-width:330px;object-fit:contain;">'
        )
    else:
        html_logo = '<div class="brand">Más<span>Online</span></div>'

    if len(finde_tabla):
        finde_rows_html_static = ""
        for _, r in finde_tabla.iterrows():
            finde_rows_html_static += (
                '<tr style="border-top:1px solid #eee;">'
                f'<td style="padding:10px 14px;color:#20252b;">{r["rango"]}</td>'
                f'<td style="padding:10px 14px;font-weight:700;color:#e8432c;">{money(r["venta"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{intfmt(r["pedidos"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{intfmt(r["unidades"])}</td>'
                '</tr>'
            )
        tabla_html = f"""
        <div style="background:white;border:1px solid #e8ebef;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.06);">
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="background:#20252b;color:white;text-align:left;">
                <th style="padding:10px 14px;">FIN DE SEMANA</th>
                <th style="padding:10px 14px;">VENTA ECOMMERCE</th>
                <th style="padding:10px 14px;">PEDIDOS</th>
                <th style="padding:10px 14px;">UNIDADES</th>
              </tr>
            </thead>
            <tbody>{finde_rows_html_static}</tbody>
          </table>
        </div>
        """
    else:
        tabla_html = (
            '<div class="upload-box"><div class="upload-text">'
            'Todavía no hay ningún fin de semana (viernes, sábado y domingo) cargado este mes.'
            '</div></div>'
        )

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MásOnline | Venta fin de semana</title>
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
.hero-sub {{ font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }}
.hero-date {{ text-align: right; font-size: 19px; font-weight: 800; }}
.hero-date small {{ display: block; font-size: 12px; font-weight: 400; margin-top: 4px; opacity: .8; }}
.section {{ font-size: 20px; font-weight: 800; margin: 26px 0 12px; }}
.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 16px; }}
.card, .progress-wrap {{
    background: white; border: 1px solid #e8ebef; border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
}}
.card {{ padding: 20px 22px; min-height: 125px; }}
.label {{ color: #6b7280; font-size: 14px; font-weight: 700; }}
.value {{ color: #20252b; font-size: 30px; font-weight: 800; margin-top: 7px; }}
.small {{ color: #20252b; font-size: 13px; font-weight: 700; margin-top: 7px; }}
.progress-wrap {{ padding: 20px 22px; margin-top: 20px; }}
.progress-layout {{ display: flex; align-items: center; gap: 28px; }}
.progress-main {{ flex: 1; }}
.progress-track {{
    height: 16px; background: #e6e9ed; border-radius: 20px;
    overflow: hidden; margin: 10px 0 8px;
}}
.progress-fill {{ height: 100%; width: {progress:.1f}%; background: #2f9e66; border-radius: 20px; }}
.progress-row {{ display: flex; justify-content: space-between; color: #6b7280; font-size: 13px; }}
.progress-target {{
    width: 150px; color: #208653; font-size: 30px; font-weight: 800;
    text-align: right; line-height: 1;
}}
.progress-target small {{
    display: block; color: #6b7280; font-size: 12px; font-weight: 400; margin-top: 5px;
}}
.footer {{ display: flex; justify-content: space-between; color: #6b7280; font-size: 12px; margin-top: 14px; }}
.upload-box {{
    background: white; border-radius: 14px; padding: 16px 18px; border: 1px solid #e8ebef;
}}
.upload-text {{ color:#6b7280; font-size:12px; }}
@media (max-width: 900px) {{
    body {{ padding: 18px; }}
    .kpis {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 600px) {{
    .hero {{ flex-direction: column; align-items: flex-start; gap: 15px; }}
    .hero-date {{ text-align: left; }}
    .kpis {{ grid-template-columns: 1fr; }}
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
    <div class="hero-sub">VENTA FIN DE SEMANA</div>
  </div>
  <div class="hero-date">
    Septiembre 2026
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
  </div>
</div>

<div class="section">Fin de semana vs. acumulado</div>
<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">Fin de semana = Viernes + Sábado + Domingo.</div>

<div class="kpis">

<div class="card" style="border-top:4px solid #e8432c;">
  <div class="label" style="color:#e8432c;">VENTA FIN DE SEMANA</div>
  <div class="value" style="color:#e8432c;">{html.escape(money(weekend_full_ecom))}</div>
  <div class="small">{html.escape(weekend_full_label)} · Cía: {html.escape(money(weekend_full_company))}</div>
</div>

<div class="card" style="border-top:4px solid #f5a623;">
  <div class="label" style="color:#f5a623;">SHARE ECOMMERCE</div>
  <div class="value">{html.escape(pct(share))}</div>
  <div class="small">Objetivo: {html.escape(pct(target))}</div>
</div>

<div class="card" style="border-top:4px solid #2f9e66;">
  <div class="label" style="color:#208653;">PROYECCIÓN DE CIERRE</div>
  <div class="value" style="color:#208653;">{html.escape(money(projection))}</div>
  <div class="small">Promedio diario × {days_month} días</div>
</div>

<div class="card" style="border-top:4px solid #59636e;">
  <div class="label">ACUMULADO</div>
  <div class="value">{html.escape(money(acc_ecom))}</div>
  <div class="small">{intfmt(acc_orders)} pedidos · {intfmt(acc_units)} unidades</div>
</div>

</div>

<div class="progress-wrap">
  <div class="progress-layout">
    <div class="progress-main">
      <div class="progress-track">
        <div class="progress-fill"></div>
      </div>
      <div class="progress-row">
        <span>Participación actual: {html.escape(pct(share))}</span>
        <span>Objetivo: {html.escape(pct(target))}</span>
      </div>
    </div>
    <div class="progress-target">
      {share/target:.0%}
      <small>del objetivo</small>
    </div>
  </div>
</div>

<div class="section">Venta por fin de semana del mes</div>
{tabla_html}

<div class="footer">
  <span>Fuente: venta con impuesto de MicroStrategy.</span>
  <span>MásOnline | E-commerce</span>
</div>

</div>
</body>
</html>
"""
    return html_doc

html_dashboard_finde = build_standalone_html()

st.download_button(
    "⬇️ Descargar esta página en HTML",
    data=html_dashboard_finde,
    file_name="venta_fin_de_semana.html",
    mime="text/html",
    use_container_width=True
)

st.markdown('<div class="section">Fin de semana vs. acumulado</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
    'Fin de semana = Viernes + Sábado + Domingo.'
    '</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #e8432c;">
      <div class="label" style="color:#e8432c;">VENTA FIN DE SEMANA</div>
      <div class="value" style="color:#e8432c;">{money(weekend_full_ecom)}</div>
      <div class="small">{weekend_full_label} · Cía: {money(weekend_full_company)}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #f5a623;">
      <div class="label" style="color:#f5a623;">SHARE ECOMMERCE</div>
      <div class="value">{pct(share)}</div>
      <div class="small">Objetivo: {pct(target)}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #2f9e66;">
      <div class="label" style="color:#208653;">PROYECCIÓN DE CIERRE</div>
      <div class="value" style="color:#208653;">{money(projection)}</div>
      <div class="small">Promedio diario × {days_month} días</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #59636e;">
      <div class="label">ACUMULADO</div>
      <div class="value">{money(acc_ecom)}</div>
      <div class="small">{intfmt(acc_orders)} pedidos · {intfmt(acc_units)} unidades</div>
    </div>
    """, unsafe_allow_html=True)

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
            '</tr>'
        )

    st.markdown(f"""
    <div class="table-scroll" style="background:white;border:1px solid #e8ebef;border-radius:14px;overflow-x:auto;box-shadow:0 2px 10px rgba(0,0,0,.06);">
      <table style="width:100%;border-collapse:collapse;font-size:13px;min-width:420px;">
        <thead>
          <tr style="background:#20252b;color:white;text-align:left;">
            <th style="padding:10px 14px;">FIN DE SEMANA</th>
            <th style="padding:10px 14px;">VENTA ECOMMERCE</th>
            <th style="padding:10px 14px;">PEDIDOS</th>
            <th style="padding:10px 14px;">UNIDADES</th>
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
