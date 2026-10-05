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

CSS_TEXT = """
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
    .periodo-badge small { display:block; color:#000000; font-size:11px; font-weight:700; margin-top:3px; }

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
    .kpi-delta-line { margin-top: 8px; }
    .kpi-delta-line .kpi-delta { font-size: 13px; font-weight: 700; }
    .kpi-delta-line .sub { font-size: 13px; font-weight: 700; margin-top: 2px; }
    .kpi-delta-line.positive, .kpi-delta-line.positive .kpi-delta, .kpi-delta-line.positive .sub { color: #208653; }
    .kpi-delta-line.negative, .kpi-delta-line.negative .kpi-delta, .kpi-delta-line.negative .sub { color: #d64545; }
    .kpi-delta-line.neutral, .kpi-delta-line.neutral .kpi-delta, .kpi-delta-line.neutral .sub { color: #000000; font-weight: 700; }

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

    .filtro-row {
        display: flex; align-items: flex-end; gap: 14px; flex-wrap: wrap;
        margin: -4px 0 4px;
    }
    .filtro-row > div[data-testid="stSelectbox"] { min-width: 220px; }
"""
st.markdown(f"<style>{CSS_TEXT}</style>", unsafe_allow_html=True)

LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

# Esta pestaña no tiene uploader propio: el archivo "Vs de ventas" se sube en
# la pestaña "app" (tarjeta "COMPARATIVO") y queda guardado en una carpeta
# compartida en el servidor, igual que Pedidos/Reclamos/Pickers/etc. en
# Operativo — acá solo se lee la última copia que haya quedado ahí.
SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_VSVENTAS_PATH = SHARED_DIR / "vsventas.xlsx"

def _github_headers():
    token = st.secrets.get("GITHUB_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Masonline-Dashboard",
    }

def fetch_shared_from_github(shared_path):
    """Trae de GitHub la última copia guardada de este reporte (para cuando
    el servidor se reinició y la copia local temporal ya no está).

    Pide el archivo en formato "raw" (Accept: vnd.github.raw+json) en vez
    del formato normal (JSON + contenido en base64): el formato normal solo
    trae el contenido completo para archivos de hasta 1 MB — con uno más
    pesado, GitHub devuelve el contenido vacío sin avisar, y acá terminaba
    leyéndose como un Excel de 0 bytes ("no pude determinar el formato del
    archivo"). El formato "raw" no tiene ese límite (soporta hasta 100 MB)."""
    headers = _github_headers()
    if not headers:
        return None
    import urllib.request
    repo = "2026-Masonline/masonline-dashboard"
    branch = "main"
    repo_path = f"shared_uploads/{shared_path.name}"
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}?ref={branch}"
    raw_headers = {**headers, "Accept": "application/vnd.github.raw+json"}
    try:
        request_get = urllib.request.Request(url, headers=raw_headers, method="GET")
        with urllib.request.urlopen(request_get, timeout=30) as response:
            return response.read()
    except Exception:
        return None

def get_shared_bytes(shared_path):
    """Primero intenta la copia local (rápida); si el servidor se reinició y
    la copia local se perdió, la trae de GitHub (donde queda guardada para
    siempre) y la vuelve a dejar en local para la próxima."""
    if shared_path.exists():
        try:
            return shared_path.read_bytes()
        except Exception:
            pass
    content = fetch_shared_from_github(shared_path)
    if content is not None:
        try:
            shared_path.write_bytes(content)
        except Exception:
            pass
        return content
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

# Siempre se muestra el acumulado hasta el último día cerrado cargado (no
# hay selector manual de fecha de corte); las tarjetas de "Resultados del
# período" suman el rango Desde/Hasta que se elija acá abajo (por default,
# del 1 del mes en curso hasta el último día cargado).
available_dates = sorted(df["date"].unique(), reverse=True)
_min_fecha = df["date"].min().date()
_max_fecha = df["date"].max().date()
_default_desde = _max_fecha.replace(day=1)

col_desde, col_hasta = st.columns(2)
with col_desde:
    rango_desde = st.date_input(
        "**Desde**", value=_default_desde, min_value=_min_fecha, max_value=_max_fecha,
        key="comparativo_rango_desde",
    )
with col_hasta:
    rango_hasta = st.date_input(
        "**Hasta**", value=_max_fecha, min_value=_min_fecha, max_value=_max_fecha,
        key="comparativo_rango_hasta",
    )
if rango_desde > rango_hasta:
    rango_desde, rango_hasta = rango_hasta, rango_desde

last_date = pd.Timestamp(available_dates[0])
cur_year, cur_month = last_date.year, last_date.month
n = last_date.day  # día del mes al que se corta (p.ej. 30 = acumulado al 30); lo usa "Día a día"

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

#  El archivo "Vs de ventas" trae una fila por DÍA y por TIENDA, con el
#  valor de ESE día puntual (no acumulado) — más arriba ya sumamos todas
#  las tiendas por fecha (el "df" de acá es uno-fila-por-día). Por eso para
#  sumar un rango de fechas alcanza con filtrar esas filas y sumarlas
#  directo, sin restar nada.

def suma_rango(desde_ts, hasta_ts):
    sub = df[(df["date"] >= desde_ts) & (df["date"] <= hasta_ts)]
    if sub.empty:
        return None
    return {
        "orders": sub["orders"].sum(),
        "ecommerce_tax": sub["ecommerce_tax"].sum(),
        "units": sub["units"].sum(),
        "company_tax": sub["company_tax"].sum(),
    }

def _mismo_dia_año_pasado(ts):
    try:
        return ts.replace(year=ts.year - 1)
    except ValueError:
        # 29 de febrero sin equivalente el año anterior
        return ts.replace(year=ts.year - 1, day=28)

rango_desde_ts = pd.Timestamp(rango_desde)
rango_hasta_ts = pd.Timestamp(rango_hasta)
tot_rango_cur = suma_rango(rango_desde_ts, rango_hasta_ts) or {
    "orders": 0, "ecommerce_tax": 0, "units": 0, "company_tax": 0
}
pedidos_cur = tot_rango_cur["orders"]
venta_cur = tot_rango_cur["ecommerce_tax"]
unidades_cur = tot_rango_cur["units"]
ticket_cur = (venta_cur / pedidos_cur) if pedidos_cur else 0

rango_desde_prev_ts = _mismo_dia_año_pasado(rango_desde_ts)
rango_hasta_prev_ts = _mismo_dia_año_pasado(rango_hasta_ts)
tot_rango_prev = suma_rango(rango_desde_prev_ts, rango_hasta_prev_ts)
hay_prev = tot_rango_prev is not None
if hay_prev:
    pedidos_prev = tot_rango_prev["orders"]
    venta_prev = tot_rango_prev["ecommerce_tax"]
    unidades_prev = tot_rango_prev["units"]
else:
    pedidos_prev = venta_prev = unidades_prev = 0
ticket_prev = (venta_prev / pedidos_prev) if pedidos_prev else 0

rango_label_cur = f"{rango_desde_ts.strftime('%d/%m/%Y')} al {rango_hasta_ts.strftime('%d/%m/%Y')}"
rango_label_prev = f"{rango_desde_prev_ts.strftime('%d/%m/%Y')} al {rango_hasta_prev_ts.strftime('%d/%m/%Y')}"
col_cur_label = rango_label_cur
col_prev_label = rango_label_prev if hay_prev else f"{rango_label_prev} (sin datos)"
comparar_vs_year = f"{rango_desde_prev_ts.year}"
comparar_vs_sub = f"mismo rango {rango_desde_prev_ts.year}"
periodo_val_label = "Rango acumulado"
periodo_small_label = f"Datos acumulados del {rango_desde_ts.strftime('%d/%m')} al {rango_hasta_ts.strftime('%d/%m')}"

def delta_badge(v, is_money=False):
    if not hay_prev:
        return (
            '<div class="kpi-delta-line neutral">'
            f'<span class="kpi-delta">Sin datos de {comparar_vs_year} para comparar</span>'
            '</div>'
        )
    cls = "positive" if v >= 0 else "negative"
    arrow = "▲" if v >= 0 else "▼"
    sign = "+" if v >= 0 else "−"
    body = money(abs(v))[1:] if is_money else intfmt(abs(v))
    return (
        f'<div class="kpi-delta-line {cls}">'
        f'<span class="kpi-delta">{arrow} {sign} {body}</span>'
        f'<div class="sub">vs {comparar_vs_sub}</div>'
        '</div>'
    )

d_pedidos = pedidos_cur - pedidos_prev
d_venta = venta_cur - venta_prev
d_unidades = unidades_cur - unidades_prev
d_ticket = ticket_cur - ticket_prev

prev_pedidos_txt = intfmt(pedidos_prev) if hay_prev else "—"
prev_venta_txt = money(venta_prev) if hay_prev else "—"
prev_unidades_txt = intfmt(unidades_prev) if hay_prev else "—"
prev_ticket_txt = money(ticket_prev) if hay_prev else "—"

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

table_html = f"""
<div class="cmp-table-wrap">
<div class="table-scroll">
<table class="cmp-table">
  <thead>
    <tr>
      <th>Indicador</th>
      <th>{col_cur_label}</th>
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

footnote_html = (
    '<div style="color:#000000;font-size:11px;margin-top:14px;">'
    f'"{col_prev_label}" toma el mismo rango de fechas (día y mes) un año antes, '
    'para que la comparación sea pareja.'
    '</div>'
)

# ---------------------------------------------------------------------
# Primer fin de semana del mes: Viernes + Sábado + Domingo de la primera
# semana completa del mes, comparado con el mismo fin de semana (primer
# finde de ese mismo mes) del año anterior. El archivo trae el valor de
# CADA día puntual (no acumulado), así que alcanza con sumar esos 3 días.
# ---------------------------------------------------------------------

def primer_finde_fechas(year, month):
    d1 = pd.Timestamp(year=year, month=month, day=1)
    offset = (4 - d1.weekday()) % 7  # 4 = viernes
    friday = d1 + pd.Timedelta(days=offset)
    saturday = friday + pd.Timedelta(days=1)
    sunday = friday + pd.Timedelta(days=2)
    return friday, saturday, sunday

def finde_acumulado(year, month):
    """Totales (venta, pedidos, unidades, facturación) del primer fin de
    semana de ese mes/año — o None si los datos cargados todavía no
    llegan a esa fecha (no hay fila para el domingo)."""
    friday, saturday, sunday = primer_finde_fechas(year, month)
    if df[df["date"] == sunday].empty:
        return None
    sub = df[df["date"].isin([friday, saturday, sunday])]
    totales = {col: sub[col].sum() for col in ["ecommerce_tax", "orders", "units", "company_tax"]}
    return friday, sunday, totales

finde_cur = finde_acumulado(cur_year, cur_month)
finde_prev = finde_acumulado(cur_year - 1, cur_month)

if finde_cur is None:
    _friday_cur, _, _ = primer_finde_fechas(cur_year, cur_month)
    finde_section_html = f"""
<div class="section" style="margin-top:30px;">Primer fin de semana de {mes_nombre}</div>
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;padding:12px 16px;color:#000000;font-size:13px;">
  Todavía no llegamos al primer fin de semana de {mes_nombre} {cur_year}
  (arranca el viernes {_friday_cur.strftime('%d/%m')}).
</div>
"""
else:
    friday_cur, sunday_cur, tot_cur = finde_cur
    label_finde_cur = f"{friday_cur.strftime('%d/%m')} al {sunday_cur.strftime('%d/%m')}"
    ticket_finde_cur = (tot_cur["ecommerce_tax"] / tot_cur["orders"]) if tot_cur["orders"] else 0

    if finde_prev is not None:
        friday_prev, sunday_prev, tot_prev = finde_prev
        label_finde_prev = f"{friday_prev.strftime('%d/%m')} al {sunday_prev.strftime('%d/%m')} ({cur_year - 1})"
        ticket_finde_prev = (tot_prev["ecommerce_tax"] / tot_prev["orders"]) if tot_prev["orders"] else 0
        prev_pedidos_finde_txt = intfmt(tot_prev["orders"])
        prev_venta_finde_txt = money(tot_prev["ecommerce_tax"])
        prev_unidades_finde_txt = intfmt(tot_prev["units"])
        prev_ticket_finde_txt = money(ticket_finde_prev)
    else:
        label_finde_prev = f"Primer finde {mes_nombre} {cur_year - 1} (sin datos)"
        prev_pedidos_finde_txt = prev_venta_finde_txt = prev_unidades_finde_txt = prev_ticket_finde_txt = "—"

    finde_table_html = f"""
<div class="cmp-table-wrap">
<div class="table-scroll">
<table class="cmp-table">
  <thead>
    <tr>
      <th>Indicador</th>
      <th>{label_finde_cur}</th>
      <th>{label_finde_prev}</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>🛒 Pedidos facturados</td><td>{intfmt(tot_cur["orders"])}</td><td>{prev_pedidos_finde_txt}</td></tr>
    <tr><td>💰 Venta Ecommerce (con impuesto)</td><td>{money(tot_cur["ecommerce_tax"])}</td><td>{prev_venta_finde_txt}</td></tr>
    <tr><td>📦 Unidades</td><td>{intfmt(tot_cur["units"])}</td><td>{prev_unidades_finde_txt}</td></tr>
    <tr><td>🏷️ Ticket promedio</td><td>{money(ticket_finde_cur)}</td><td>{prev_ticket_finde_txt}</td></tr>
  </tbody>
</table>
</div>
</div>
"""
    finde_section_html = f"""
<div class="section" style="margin-top:30px;">Primer fin de semana de {mes_nombre}</div>
<div class="section-desc">Viernes + sábado + domingo de la primera semana completa del mes, comparado con el mismo fin de semana de {cur_year - 1}.</div>
{finde_table_html}
"""

# ---------------------------------------------------------------------
# Último fin de semana cerrado (el más reciente con datos cargados, no
# necesariamente el primero del mes) comparado con el mismo fin de semana
# —el mismo número de fin de semana dentro del mes— del año anterior.
# El archivo trae el valor de cada día puntual, así que alcanza con sumar.
# ---------------------------------------------------------------------

def finde_totales(friday, saturday, sunday):
    """Totales de un viernes/sábado/domingo puntuales — o None si ninguno
    de los tres tiene datos cargados."""
    sub = df[df["date"].isin([friday, saturday, sunday])]
    if sub.empty:
        return None
    return {col: sub[col].sum() for col in ["ecommerce_tax", "orders", "units", "company_tax"]}

def nth_finde_fechas(year, month, n):
    friday1, _, _ = primer_finde_fechas(year, month)
    friday = friday1 + pd.Timedelta(weeks=n - 1)
    return friday, friday + pd.Timedelta(days=1), friday + pd.Timedelta(days=2)

_ultima_fecha_cargada = df["date"].max()
_dias_desde_sabado = (_ultima_fecha_cargada.weekday() - 5) % 7  # Monday=0 ... Saturday=5, Sunday=6
ultimo_sabado = _ultima_fecha_cargada - pd.Timedelta(days=_dias_desde_sabado)
ultimo_viernes = ultimo_sabado - pd.Timedelta(days=1)
ultimo_domingo = ultimo_sabado + pd.Timedelta(days=1)

_primer_viernes_ese_mes, _, _ = primer_finde_fechas(ultimo_viernes.year, ultimo_viernes.month)
n_ultimo_finde = int(round((ultimo_viernes - _primer_viernes_ese_mes).days / 7)) + 1
mes_ultimo_finde = MESES_ES.get(ultimo_viernes.month, "").capitalize()

friday_up, saturday_up, sunday_up = nth_finde_fechas(
    ultimo_viernes.year - 1, ultimo_viernes.month, n_ultimo_finde
)

tot_ultimo = finde_totales(ultimo_viernes, ultimo_sabado, ultimo_domingo)
tot_ultimo_prev = finde_totales(friday_up, saturday_up, sunday_up)

label_ultimo = f"{ultimo_viernes.strftime('%d/%m')} al {ultimo_domingo.strftime('%d/%m')}"
ticket_ultimo = (tot_ultimo["ecommerce_tax"] / tot_ultimo["orders"]) if tot_ultimo["orders"] else 0

if tot_ultimo_prev is not None:
    label_ultimo_prev = f"{friday_up.strftime('%d/%m')} al {sunday_up.strftime('%d/%m')} ({ultimo_viernes.year - 1})"
    ticket_ultimo_prev = (tot_ultimo_prev["ecommerce_tax"] / tot_ultimo_prev["orders"]) if tot_ultimo_prev["orders"] else 0
    prev_pedidos_ultimo_txt = intfmt(tot_ultimo_prev["orders"])
    prev_venta_ultimo_txt = money(tot_ultimo_prev["ecommerce_tax"])
    prev_unidades_ultimo_txt = intfmt(tot_ultimo_prev["units"])
    prev_ticket_ultimo_txt = money(ticket_ultimo_prev)
else:
    label_ultimo_prev = f"Mismo finde {ultimo_viernes.year - 1} (sin datos)"
    prev_pedidos_ultimo_txt = prev_venta_ultimo_txt = prev_unidades_ultimo_txt = prev_ticket_ultimo_txt = "—"

ultimo_finde_table_html = f"""
<div class="cmp-table-wrap">
<div class="table-scroll">
<table class="cmp-table">
  <thead>
    <tr>
      <th>Indicador</th>
      <th>{label_ultimo}</th>
      <th>{label_ultimo_prev}</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>🛒 Pedidos facturados</td><td>{intfmt(tot_ultimo["orders"])}</td><td>{prev_pedidos_ultimo_txt}</td></tr>
    <tr><td>💰 Venta Ecommerce (con impuesto)</td><td>{money(tot_ultimo["ecommerce_tax"])}</td><td>{prev_venta_ultimo_txt}</td></tr>
    <tr><td>📦 Unidades</td><td>{intfmt(tot_ultimo["units"])}</td><td>{prev_unidades_ultimo_txt}</td></tr>
    <tr><td>🏷️ Ticket promedio</td><td>{money(ticket_ultimo)}</td><td>{prev_ticket_ultimo_txt}</td></tr>
  </tbody>
</table>
</div>
</div>
"""
ultimo_finde_section_html = f"""
<div class="section" style="margin-top:30px;">Último fin de semana</div>
<div class="section-desc">Viernes + sábado + domingo del fin de semana más reciente ya cerrado, comparado con ese mismo fin de semana (el fin de semana n.º {n_ultimo_finde} del mes) de {mes_ultimo_finde} {ultimo_viernes.year - 1}.</div>
{ultimo_finde_table_html}
"""

# ---------------------------------------------------------------------
# Día a día: misma fecha del mes (día 1, 2, 3...) de este año vs el mismo
# día del mes del año anterior. El archivo ya trae el valor de CADA día
# puntual (no acumulado), así que se usa directo, sin restar nada.
# ---------------------------------------------------------------------

def dia_a_dia(year, month):
    sub = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)].sort_values("date").copy()
    if sub.empty:
        return sub
    sub["dia"] = sub["date"].dt.day
    return sub[["dia", "ecommerce_tax", "orders", "units", "company_tax"]]

dia_cur = dia_a_dia(cur_year, cur_month)
dia_cur = dia_cur[dia_cur["dia"] <= n]
dia_prev = dia_a_dia(cur_year - 1, cur_month)

dia_cmp = dia_cur.merge(dia_prev, on="dia", how="left", suffixes=("", "_prev"))

def variacion_html(v):
    if v is None:
        return '<span style="color:#6b7280;">—</span>'
    cls = "#208653" if v >= 0 else "#d64545"
    arrow = "▲" if v >= 0 else "▼"
    sign = "+" if v >= 0 else "−"
    return f'<span style="color:{cls};font-weight:700;">{arrow} {sign}{abs(v) * 100:.1f}%</span>'

dia_rows_html = ""
for _, r in dia_cmp.iterrows():
    hay_prev_dia = pd.notna(r.get("ecommerce_tax_prev"))
    venta_prev_txt = money(r["ecommerce_tax_prev"]) if hay_prev_dia else "—"
    variacion = (
        (r["ecommerce_tax"] / r["ecommerce_tax_prev"] - 1)
        if hay_prev_dia and r["ecommerce_tax_prev"] else None
    )
    dia_rows_html += (
        '<tr style="border-top:1px solid #f1f3f5;">'
        f'<td style="padding:10px 16px;color:#000000;font-weight:700;">{int(r["dia"])}</td>'
        f'<td style="padding:10px 16px;color:#000000;text-align:center;">{money(r["ecommerce_tax"])}</td>'
        f'<td style="padding:10px 16px;color:#000000;text-align:center;">{venta_prev_txt}</td>'
        f'<td style="padding:10px 16px;text-align:center;">{variacion_html(variacion)}</td>'
        '</tr>'
    )

if dia_rows_html:
    dia_table_html = f"""
<div class="cmp-table-wrap">
<div class="table-scroll">
<table class="cmp-table">
  <thead>
    <tr>
      <th>Día</th>
      <th>{mes_nombre} {cur_year}</th>
      <th>{mes_nombre} {cur_year - 1}</th>
      <th>Variación</th>
    </tr>
  </thead>
  <tbody>{dia_rows_html}</tbody>
</table>
</div>
</div>
"""
else:
    dia_table_html = (
        '<div style="background:white;border:1px solid #e8ebef;border-radius:12px;'
        'padding:12px 16px;color:#000000;font-size:13px;">Todavía no hay días cargados para comparar.</div>'
    )

dia_section_html = f"""
<div class="section" style="margin-top:30px;">Día a día vs {cur_year - 1}</div>
<div class="section-desc">Venta Ecommerce (con impuesto) de cada día del mes, comparada con el mismo día de {mes_nombre} {cur_year - 1} (no el mismo día de la semana, el mismo número de día).</div>
{dia_table_html}
"""

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
    <div class="val">{periodo_val_label}</div>
    <small>{periodo_small_label}</small>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# HTML descargable: copia independiente de esta pestaña (fecha elegida),
# sin depender de Streamlit — se puede abrir en cualquier navegador o
# mandar por mail/WhatsApp.
# ---------------------------------------------------------------------

def build_standalone_html():
    if LOGO_FILE.exists():
        html_logo = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            'style="height:50px;max-width:290px;object-fit:contain;">'
        )
    else:
        html_logo = '<div class="hero-brand">Más<span>Online</span></div>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MásOnline | Comparativo</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:0; background:#ffffff; font-family: Arial, Helvetica, sans-serif; }}
.block-container {{ max-width:1300px; margin:0 auto; padding:24px 20px 40px; }}
{CSS_TEXT}
</style>
</head>
<body>
<div class="block-container">

<div class="hero">
  <div>
    {html_logo}
    <div class="hero-sub">ECOMMERCE · RESUMEN DE RESULTADOS</div>
  </div>
  <div class="periodo-badge">
    <div class="lbl">📅 PERÍODO</div>
    <div class="val">{periodo_val_label}</div>
    <small>{periodo_small_label}</small>
  </div>
</div>

<div class="section">Resultados del período</div>
<div class="section-desc">Indicadores principales del canal ecommerce — <b>{periodo_small_label}</b>.</div>
{kpis_html}

<div class="section" style="margin-top:30px;">Comparativo vs año anterior</div>
<div class="section-desc"><b>{periodo_small_label}</b>. Indicadores calculados con Venta Ecommerce (con impuesto) y Pedidos Facturados.</div>
{table_html}
{footnote_html}
{finde_section_html}
{ultimo_finde_section_html}
{dia_section_html}

</div>
</body>
</html>
"""

st.download_button(
    "⬇️ Descargar comparativo HTML",
    data=build_standalone_html(),
    file_name=f"comparativo_masonline_{last_date.strftime('%Y-%m-%d')}.html",
    mime="text/html",
    use_container_width=False,
)

# ---------------------------------------------------------------------
# Resultados del período
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">Resultados del período</div>'
    '<div class="section-desc">Indicadores principales del canal ecommerce — '
    f'<b>{periodo_small_label}</b>.</div>',
    unsafe_allow_html=True
)
st.markdown(kpis_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Comparativo vs año anterior
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section" style="margin-top:30px;">Comparativo vs año anterior</div>'
    f'<div class="section-desc"><b>{periodo_small_label}</b>. '
    'Indicadores calculados con Venta Ecommerce (con impuesto) y Pedidos Facturados.</div>',
    unsafe_allow_html=True
)
st.markdown(table_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Primer fin de semana del mes
# ---------------------------------------------------------------------

st.markdown(finde_section_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Último fin de semana
# ---------------------------------------------------------------------

st.markdown(ultimo_finde_section_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Día a día vs año anterior
# ---------------------------------------------------------------------

st.markdown(dia_section_html, unsafe_allow_html=True)

st.markdown(footnote_html, unsafe_allow_html=True)
