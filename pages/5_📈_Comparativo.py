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
    el servidor se reinició y la copia local temporal ya no está)."""
    headers = _github_headers()
    if not headers:
        return None
    import urllib.request
    import json
    import base64
    repo = "2026-Masonline/masonline-dashboard"
    branch = "main"
    repo_path = f"shared_uploads/{shared_path.name}"
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}?ref={branch}"
    try:
        request_get = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request_get, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return base64.b64decode(data["content"])
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

# Filtro de fecha: por default se muestra el último día cerrado cargado,
# pero se puede elegir cualquier otro día del archivo para ver el acumulado
# "a esa fecha" (el archivo trae un acumulado del mes por cada fila/día).
available_dates = sorted(df["date"].unique(), reverse=True)
date_labels = [pd.Timestamp(d).strftime("%d-%m-%Y") for d in available_dates]
label_to_date = {lbl: pd.Timestamp(d) for lbl, d in zip(date_labels, available_dates)}

st.markdown('<div class="filtro-row">', unsafe_allow_html=True)
selected_label = st.selectbox(
    "📅 Fecha de corte (acumulado hasta ese día)",
    date_labels,
    index=0,
    key="comparativo_fecha_corte",
)
st.markdown('</div>', unsafe_allow_html=True)

last_date = label_to_date[selected_label]
cur_year, cur_month = last_date.year, last_date.month
n = last_date.day  # día del mes al que se corta (p.ej. 30 = acumulado al 30)

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
        return (
            '<div class="kpi-delta-line neutral">'
            f'<span class="kpi-delta">Sin datos de {cur_year - 1} para comparar</span>'
            '</div>'
        )
    cls = "positive" if v >= 0 else "negative"
    arrow = "▲" if v >= 0 else "▼"
    sign = "+" if v >= 0 else "−"
    body = money(abs(v))[1:] if is_money else intfmt(abs(v))
    return (
        f'<div class="kpi-delta-line {cls}">'
        f'<span class="kpi-delta">{arrow} {sign} {body}</span>'
        f'<div class="sub">vs mismo período {cur_year - 1}</div>'
        '</div>'
    )

#  El archivo "Vs de ventas" trae, en cada fila, el ACUMULADO del mes hasta
#  esa fecha (no el valor de ese día puntual) — por eso NO hay que sumar
#  varias filas del mes (eso contaba el acumulado una y otra vez, de ahí
#  salía el 30.360 en vez de 2.086 pedidos). El total del mes-a-la-fecha es
#  directamente el valor de la fila de la fecha elegida en el filtro.
last_row = df[df["date"] == last_date].iloc[0]
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

col_prev_label = f"{mes_nombre} {cur_year - 1}" if hay_prev else f"{mes_nombre} {cur_year - 1} (sin datos)"
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

footnote_html = (
    '<div style="color:#000000;font-size:11px;margin-top:14px;">'
    f'"{mes_nombre} {cur_year - 1}" toma el acumulado hasta el mismo día {n} del mes '
    '(la misma cantidad de días que ya pasaron este mes), para que la comparación sea pareja.'
    '</div>'
)

# ---------------------------------------------------------------------
# Primer fin de semana del mes: Viernes + Sábado + Domingo de la primera
# semana completa del mes, comparado con el mismo fin de semana (primer
# finde de ese mismo mes) del año anterior. El archivo trae el ACUMULADO
# del mes por día, no el valor de cada día suelto — así que para aislar
# solo esos 3 días hay que restar: acumulado del domingo menos acumulado
# del día anterior al viernes (0 si el viernes es el día 1 del mes, porque
# ahí el acumulado recién arranca).
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
    semana de ese mes/año, aislados del acumulado — o None si los datos
    cargados todavía no llegan a esa fecha."""
    friday, saturday, sunday = primer_finde_fechas(year, month)
    fila_domingo = df[df["date"] == sunday]
    if fila_domingo.empty:
        return None
    cum_sunday = fila_domingo.iloc[0]
    day_before = friday - pd.Timedelta(days=1)
    fila_antes = df[df["date"] == day_before] if day_before.month == month else pd.DataFrame()
    cum_before = fila_antes.iloc[0] if len(fila_antes) else None
    totales = {}
    for col in ["ecommerce_tax", "orders", "units", "company_tax"]:
        v_before = cum_before[col] if cum_before is not None else 0
        totales[col] = cum_sunday[col] - v_before
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
# Día a día: misma fecha del mes (día 1, 2, 3...) de este año vs el mismo
# día del mes del año anterior. El archivo trae el ACUMULADO del mes por
# fila, así que para aislar el valor de CADA día individual hay que restar
# el acumulado de ese día menos el del día anterior (el primer día del mes
# no se resta nada, el acumulado de ese día ES el valor del día).
# ---------------------------------------------------------------------

def dia_a_dia(year, month):
    sub = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)].sort_values("date").copy()
    if sub.empty:
        return sub
    sub["dia"] = sub["date"].dt.day
    for col in ["ecommerce_tax", "orders", "units", "company_tax"]:
        valores = sub[col].to_numpy().copy()
        if len(valores) > 1:
            valores[1:] = valores[1:] - valores[:-1]
        sub[col] = valores
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
    <div class="val">{mes_nombre} {cur_year}</div>
    <small>Datos acumulados al {last_date.strftime('%d/%m')}</small>
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
    <div class="val">{mes_nombre} {cur_year}</div>
    <small>Datos acumulados al {last_date.strftime('%d/%m')}</small>
  </div>
</div>

<div class="section">Resultados del período</div>
<div class="section-desc">Indicadores principales del canal ecommerce — datos tomados al <b>{last_date.strftime('%d-%m-%Y')}</b>.</div>
{kpis_html}

<div class="section" style="margin-top:30px;">Comparativo vs año anterior</div>
<div class="section-desc">Datos acumulados al <b>{last_date.strftime('%d-%m-%Y')}</b>. Indicadores calculados con Venta Ecommerce (con impuesto) y Pedidos Facturados.</div>
{table_html}
{footnote_html}
{finde_section_html}
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
    f'datos tomados al <b>{last_date.strftime("%d-%m-%Y")}</b>.</div>',
    unsafe_allow_html=True
)
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
st.markdown(table_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Primer fin de semana del mes
# ---------------------------------------------------------------------

st.markdown(finde_section_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Día a día vs año anterior
# ---------------------------------------------------------------------

st.markdown(dia_section_html, unsafe_allow_html=True)

st.markdown(footnote_html, unsafe_allow_html=True)
