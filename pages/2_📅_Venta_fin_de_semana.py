import streamlit as st
import pandas as pd
import calendar
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64

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

acc_ecom = current["ecommerce_tax"].sum()
acc_company = current["company_tax"].sum()
acc_orders = current["orders"].sum()
acc_units = current["units"].sum()
share = acc_ecom / acc_company if acc_company else 0

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

st.markdown('<div class="section">Fin de semana vs. acumulado</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
    'Fin de semana = Viernes + Sábado + Domingo.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(f"""
<div style="display:flex;gap:16px;">
  <div style="flex:1;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
    <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
      FIN DE SEMANA &nbsp;|&nbsp; {weekend_full_label}
    </div>
    <div style="padding:18px 16px;">
      <div style="display:flex;">
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
      <div style="display:flex;">
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
      <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(weekend_full_share)}</span>
    </div>
  </div>

  <div style="flex:1;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
    <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
      MENSUAL &nbsp;SEPTIEMBRE 2026
    </div>
    <div style="padding:18px 16px;">
      <div style="display:flex;">
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
      <div style="display:flex;">
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
        finde_rows_html += f"""
        <tr style="border-top:1px solid #eee;">
          <td style="padding:10px 14px;color:#20252b;">{r['rango']}</td>
          <td style="padding:10px 14px;font-weight:700;color:#e8432c;">{money(r['venta'])}</td>
          <td style="padding:10px 14px;color:#20252b;">{intfmt(r['pedidos'])}</td>
          <td style="padding:10px 14px;color:#20252b;">{intfmt(r['unidades'])}</td>
          <td style="padding:10px 14px;color:#20252b;">{pct(r['participacion'])}</td>
        </tr>
        """

    st.markdown(f"""
    <div style="background:white;border:1px solid #e8ebef;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.06);">
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
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
