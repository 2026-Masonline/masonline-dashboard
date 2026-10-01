import streamlit as st
import pandas as pd
import io
import tempfile
from pathlib import Path
import base64
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="MásOnline | Comparativo",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #ffffff; }
    .block-container { max-width: 1300px; padding: 0 1.2rem 1.2rem; }

    .hero {
        background: #ffffff;
        margin: -1rem -1.2rem 1.2rem;
        padding: 22px 28px;
        color: #000000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 4px solid #ff5a1f;
    }
    .hero-brand { font-size: 26px; font-weight: 800; letter-spacing: -.5px; }
    .hero-brand span { font-weight: 400; }
    .hero-sub { font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }
    .periodo-badge {
        background: #fafaf8; border: 1px solid #e8ebef; border-radius: 12px;
        padding: 10px 16px; text-align: right;
    }
    .periodo-badge .lbl { color: #000000; font-size: 11px; font-weight: 700; letter-spacing:.03em; }
    .periodo-badge .val { color: #000000; font-size: 16px; font-weight: 800; margin-top: 2px; }
    .periodo-badge small { display:block; color:#000000; font-size:11px; margin-top:3px; }

    .section { font-size: 20px; font-weight: 800; color: #000000; margin: 26px 0 2px; }
    .section-desc { color: #000000; font-size: 13px; margin: 0 0 14px; }

    .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }
    .kpi-card {
        background: white; border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06); border: 1px solid #e8ebef;
    }
    .kpi-icon {
        width: 36px; height: 36px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 17px; margin-bottom: 10px;
    }
    .kpi-icon.blue { background: #e7f0fd; }
    .kpi-icon.red { background: #fde9e9; }
    .kpi-icon.green { background: #e6f5ea; }
    .kpi-icon.orange { background: #fdf0e0; }
    .kpi-label { color: #000000; font-size: 13px; font-weight: 700; }
    .kpi-value { color: #000000; font-size: 26px; font-weight: 800; margin-top: 4px; }
    .kpi-delta { font-size: 13px; font-weight: 700; margin-top: 8px; }
    .kpi-delta .sub { color: #000000; font-weight: 400; }
    .positive { color: #208653; }
    .negative { color: #d64545; }
    .neutral { color: #000000; font-weight: 400; }

    .cmp-table-wrap {
        background: white; border-radius: 14px; overflow: hidden;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.06);
    }
    table.cmp-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    table.cmp-table thead th {
        background: #20252b; color: #ffffff; font-weight: 700;
        padding: 12px 16px; text-align: left; white-space: nowrap;
    }
    table.cmp-table thead th:not(:first-child) { text-align: center; }
    table.cmp-table td {
        padding: 13px 16px; border-top: 1px solid #f1f3f5; color: #000000;
    }
    table.cmp-table td:not(:first-child) { text-align: center; font-weight: 700; }
    table.cmp-table td:first-child { display:flex; align-items:center; gap:8px; font-weight:700; }

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero img { max-width: 170px !important; height: 40px !important; }
        .periodo-badge { text-align: left; }
        .section { font-size: 17px; }
        .kpi-value { font-size: 22px; }
    }
</style>
""", unsafe_allow_html=True)

LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

# Esta pestaña no tiene uploader propio: el archivo "Vs de ventas" se sube en
# la pestaña "app" (tarjeta "COMPARATIVO") y queda guardado en una carpeta
# compartida en el servidor, igual que Pedidos/Reclamos/Pickers/etc. en
# Operativo — acá solo se lee la última copia que haya quedado ahí.
SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_VSVENTAS_PATH = SHARED_DIR / "vsventas.xlsx"

def get_shared_bytes(shared_path):
    if shared_path.exists():
        try:
            return shared_path.read_bytes()
        except Exception:
            return None
    return None

vsventas_bytes = get_shared_bytes(SHARED_VSVENTAS_PATH)

if vsventas_bytes is None:
    st.markdown("""
    <div style="background:white;border:1px solid #e8ebef;border-radius:12px;
    padding:12px 16px;margin-bottom:14px;">
      <div style="font-size:13px;font-weight:800;color:#000000;margin-bottom:5px;">
        TODAVÍA NO HAY ARCHIVO CARGADO
      </div>
      <div style="font-size:12px;color:#000000;">
        Subí el Excel "Vs de ventas" (con una hoja por año, ej. "2025" y "2026")
        en la pestaña <b>app</b> (menú de la izquierda), tarjeta "COMPARATIVO".
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(
    '<div style="color:#000000;font-size:12px;margin:-6px 0 14px;">'
    'Los datos se cargan desde la pestaña <b>app</b> (menú de la izquierda) — subí '
    'ahí el Excel "Vs de ventas" cuando quieras actualizarlos.'
    '</div>',
    unsafe_allow_html=True
)

# El archivo trae una hoja por año (ej. "2025", "2026"), una fila por
# tienda y por día. Juntamos todas las hojas y sumamos las 4 columnas que
# necesitamos, por día (across todas las tiendas) — así no importa cómo se
# llamen las hojas ni cuántos años tenga, ni si el mes cargado cambia.
COL_VENTA = "Venta - Ecommerce"
COL_PEDIDOS = "Pedidos Facturados con Venta Operativa - Ecommerce"
COL_UNIDADES = "Cantidad Venta Operativa - Ecommerce"
COL_FACTURACION = "Facturacion"

try:
    xl = pd.ExcelFile(io.BytesIO(vsventas_bytes))
    frames = []
    for sheet in xl.sheet_names:
        d = xl.parse(sheet)
        d.columns = [str(c).strip() for c in d.columns]
        if "Fecha" not in d.columns:
            continue
        d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
        d = d.dropna(subset=["Fecha"])
        if len(d):
            frames.append(d)
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
except Exception as e:
    st.error(f"No se pudo leer el archivo 'Vs de ventas': {e}")
    st.stop()

if raw.empty:
    st.error("No encontré filas con fecha válida en el archivo 'Vs de ventas'.")
    st.stop()

for col in [COL_VENTA, COL_PEDIDOS, COL_UNIDADES, COL_FACTURACION]:
    if col not in raw.columns:
        raw[col] = 0
    raw[col] = pd.to_numeric(raw[col], errors="coerce").fillna(0)

raw["date"] = raw["Fecha"].dt.normalize()
df = raw.groupby("date", as_index=False).agg({
    COL_VENTA: "sum", COL_PEDIDOS: "sum", COL_UNIDADES: "sum", COL_FACTURACION: "sum"
}).rename(columns={
    COL_VENTA: "ecommerce_tax", COL_PEDIDOS: "orders",
    COL_UNIDADES: "units", COL_FACTURACION: "company_tax"
})

# Siempre mostramos el último día cerrado en Argentina (igual que Venta diaria).
arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df = df[df["date"].dt.date < arg_today].copy()

if df.empty:
    st.error("Todavía no hay datos cargados para un día anterior a hoy.")
    st.stop()

# Período actual: el mes/año del último día con datos cargados — a diferencia
# de Venta diaria (que todavía tiene "septiembre 2026" fijo en el código),
# acá lo calculamos solo para que la pestaña siga funcionando sin tocar nada
# cuando cambie el mes.
last_date = df["date"].max()
cur_year, cur_month = last_date.year, last_date.month

current = df[
    (df["date"].dt.year == cur_year) & (df["date"].dt.month == cur_month)
].sort_values("date")
n = len(current)  # días con datos cargados este mes (acumulado al día n)

prev = df[
    (df["date"].dt.year == cur_year - 1) &
    (df["date"].dt.month == cur_month) &
    (df["date"].dt.day <= n)
]
hay_prev = len(prev) > 0

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}
mes_nombre = MESES_ES.get(cur_month, "").capitalize()

def money(v):
    """Mismo formato que el resto del dashboard: número completo debajo del
    millón (ej. $213.945), 'M' entre 1 millón y 999 millones, 'MM' de ahí
    en más."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "$0"
    av = abs(v)
    if av < 1_000_000:
        return f"${v:,.0f}".replace(",", ".")
    if av < 1_000_000_000 and round(av / 1_000_000, 3) < 1000:
        txt = f"${v/1_000_000:,.3f} M"
    else:
        txt = f"${v/1_000_000_000:,.3f} MM"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

def intfmt(v):
    return f"{int(round(v)):,}".replace(",", ".")

def delta_badge(v, is_money=False):
    if not hay_prev:
        return '<span class="kpi-delta neutral">Sin datos de ' + str(cur_year - 1) + ' para comparar</span>'
    cls = "positive" if v >= 0 else "negative"
    arrow = "▲" if v >= 0 else "▼"
    sign = "+" if v >= 0 else "−"
    body = money(abs(v))[1:] if is_money else intfmt(abs(v))
    return (
        f'<span class="kpi-delta {cls}">{arrow} {sign} {body}</span>'
        f'<div class="sub" style="margin-top:2px;">vs mismo período {cur_year - 1}</div>'
    )

#  El archivo "Vs de ventas" trae, en cada fila, el ACUMULADO del mes hasta
#  esa fecha (no el valor de ese día puntual) — por eso NO hay que sumar
#  todas las filas del mes (eso contaba el acumulado una y otra vez, de ahí
#  salía el 30.360 en vez de 2.086 pedidos). El total del mes-a-la-fecha es
#  directamente el valor de la última fila cargada.
last_row = current.sort_values("date").iloc[-1]
pedidos_cur = last_row["orders"]
venta_cur = last_row["ecommerce_tax"]
unidades_cur = last_row["units"]
ticket_cur = (venta_cur / pedidos_cur) if pedidos_cur else 0

if hay_prev:
    prev_last_row = prev.sort_values("date").iloc[-1]
    pedidos_prev = prev_last_row["orders"]
    venta_prev = prev_last_row["ecommerce_tax"]
    unidades_prev = prev_last_row["units"]
else:
    pedidos_prev = venta_prev = unidades_prev = 0
ticket_prev = (venta_prev / pedidos_prev) if pedidos_prev else 0

d_pedidos = pedidos_cur - pedidos_prev
d_venta = venta_cur - venta_prev
d_unidades = unidades_cur - unidades_prev
d_ticket = ticket_cur - ticket_prev

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

if LOGO_FILE.exists():
    logo_b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode("utf-8")
    brand_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        'style="height:50px;max-width:290px;object-fit:contain;">'
    )
else:
    brand_html = '<div class="hero-brand">Más<span>Online</span></div>'

st.markdown(f"""
<div class="hero">
  <div>
    {brand_html}
    <div class="hero-sub">ECOMMERCE · RESUMEN DE RESULTADOS</div>
  </div>
  <div class="periodo-badge">
    <div class="lbl">📅 PERÍODO</div>
    <div class="val">{mes_nombre} {cur_year}</div>
    <small>Datos acumulados al {last_date.strftime('%d/%m')}</small>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Resultados del período
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">Resultados del período</div>'
    '<div class="section-desc">Indicadores principales del canal ecommerce — '
    f'datos tomados al <b>{last_date.strftime("%d-%m-%Y")}</b>.</div>',
    unsafe_allow_html=True
)

kpis_html = f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-icon blue">🛒</div>
    <div class="kpi-label">Pedidos Facturados</div>
    <div class="kpi-value">{intfmt(pedidos_cur)}</div>
    <div>{delta_badge(d_pedidos, is_money=False)}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon red">💰</div>
    <div class="kpi-label">Venta Ecommerce (con impuesto)</div>
    <div class="kpi-value">{money(venta_cur)}</div>
    <div>{delta_badge(d_venta, is_money=True)}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon green">📦</div>
    <div class="kpi-label">Unidades</div>
    <div class="kpi-value">{intfmt(unidades_cur)}</div>
    <div>{delta_badge(d_unidades, is_money=False)}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon orange">🏷️</div>
    <div class="kpi-label">Ticket promedio</div>
    <div class="kpi-value">{money(ticket_cur)}</div>
    <div>{delta_badge(d_ticket, is_money=True)}</div>
  </div>
</div>
"""
st.markdown(kpis_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Comparativo vs año anterior
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section" style="margin-top:30px;">Comparativo vs año anterior</div>'
    f'<div class="section-desc">Datos acumulados al <b>{last_date.strftime("%d-%m-%Y")}</b>. '
    'Indicadores calculados con Venta Ecommerce (con impuesto) y Pedidos Facturados.</div>',
    unsafe_allow_html=True
)

col_prev_label = f"{mes_nombre} {cur_year - 1}" if hay_prev else f"{mes_nombre} {cur_year - 1} (sin datos)"
prev_pedidos_txt = intfmt(pedidos_prev) if hay_prev else "—"
prev_venta_txt = money(venta_prev) if hay_prev else "—"
prev_unidades_txt = intfmt(unidades_prev) if hay_prev else "—"
prev_ticket_txt = money(ticket_prev) if hay_prev else "—"

table_html = f"""
<div class="cmp-table-wrap">
<div class="table-scroll">
<table class="cmp-table">
  <thead>
    <tr>
      <th>Indicador</th>
      <th>{mes_nombre} {cur_year}</th>
      <th>{col_prev_label}</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>🛒 Pedidos facturados</td><td>{intfmt(pedidos_cur)}</td><td>{prev_pedidos_txt}</td></tr>
    <tr><td>💰 Venta Ecommerce (con impuesto)</td><td>{money(venta_cur)}</td><td>{prev_venta_txt}</td></tr>
    <tr><td>📦 Unidades</td><td>{intfmt(unidades_cur)}</td><td>{prev_unidades_txt}</td></tr>
    <tr><td>🏷️ Ticket promedio</td><td>{money(ticket_cur)}</td><td>{prev_ticket_txt}</td></tr>
  </tbody>
</table>
</div>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

st.markdown(
    '<div style="color:#000000;font-size:11px;margin-top:14px;">'
    f'"{mes_nombre} {cur_year - 1}" toma el acumulado hasta el mismo día {n} del mes '
    '(la misma cantidad de días que ya pasaron este mes), para que la comparación sea pareja.'
    '</div>',
    unsafe_allow_html=True
)
