import streamlit as st
import pandas as pd
import io
import tempfile
from pathlib import Path
import base64
import html
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="MásOnline | Finde largo",
    page_icon="🏖️",
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

    .upload-box {
        background: white; border-radius: 12px; padding: 12px 16px;
        border: 1px solid #e8ebef; margin-bottom: 14px;
    }
    .upload-text { color:#000000; font-size:12px; }

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
        margin: -4px 0 14px;
    }
    .filtro-row > div[data-testid="stSelectbox"] { min-width: 320px; }
"""
st.markdown(f"<style>{CSS_TEXT}</style>", unsafe_allow_html=True)

LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

# Esta pestaña no tiene uploader propio: usa el MISMO archivo "Vs de ventas"
# que ya se sube en la pestaña "app" (tarjeta "COMPARATIVO") para la pestaña
# Comparativo — acá se lee esa misma copia, para que el número de venta de
# este finde largo sea siempre el mismo que el de Comparativo (y no otro
# distinto, como pasaba cuando se mezclaban dos archivos de origen distinto).
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
    pesado, GitHub devuelve el contenido vacío sin avisar. El formato "raw"
    no tiene ese límite (soporta hasta 100 MB)."""
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
    siempre) y la vuelve a dejar en local para la próxima.

    Si la copia local está vacía (0 bytes) la descarta y va directo a
    GitHub — un bug viejo (ya arreglado) podía dejar guardada ahí una copia
    vacía/corrupta de un archivo pesado."""
    if shared_path.exists():
        try:
            data = shared_path.read_bytes()
            if data:
                return data
        except Exception:
            pass
    content = fetch_shared_from_github(shared_path)
    if content:
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
    'Los datos se cargan desde la pestaña <b>app</b> (menú de la izquierda), tarjeta '
    '"COMPARATIVO" — es el mismo archivo "Vs de ventas" que usa la pestaña Comparativo.'
    '</div>',
    unsafe_allow_html=True
)

# El archivo trae una hoja por año (ej. "2025", "2026"). Las hojas viejas
# traen los totales ya armados por tienda y por día; la hoja 2026 en
# cambio trae el detalle de pedidos sin armar (una fila por pedido) — se
# detecta por sus columnas y se arman acá las mismas 4 columnas, con el
# mismo criterio que usa Comparativo (sin PM ni RMA, día = fecha de
# entrega).
COL_VENTA = "Venta - Ecommerce"
COL_PEDIDOS = "Pedidos Facturados con Venta Operativa - Ecommerce"
COL_UNIDADES = "Cantidad Venta Operativa - Ecommerce"
COL_FACTURACION = "Facturacion"

RAW_ORDER_COLS = {
    "commerceDateCreated", "deliveryFinishDate", "commerceId", "commerceSequentialId",
    "salesChannelPrefix", "totalAmount", "itemsPickedQuantity",
}

def _es_hoja_detalle_pedidos(d):
    return RAW_ORDER_COLS.issubset(set(d.columns))

def _adaptar_hoja_detalle_pedidos(d):
    d = d.copy()
    es_pm = d["salesChannelPrefix"].astype(str).str.strip().str.upper() == "PM"
    es_rma = d["commerceId"].astype(str).str.upper().str.contains("RMA", na=False)
    d = d[~es_pm & ~es_rma & d["commerceSequentialId"].notna()]
    monto = pd.to_numeric(
        d["totalAmount"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce"
    ).fillna(0)
    out = pd.DataFrame({
        "Fecha": pd.to_datetime(d["deliveryFinishDate"], errors="coerce"),
        COL_VENTA: monto,
        COL_FACTURACION: monto,
        COL_UNIDADES: pd.to_numeric(d.get("itemsPickedQuantity"), errors="coerce").fillna(0),
        COL_PEDIDOS: 1,
    })
    return out

try:
    xl = pd.ExcelFile(io.BytesIO(vsventas_bytes))
    frames = []
    for sheet in xl.sheet_names:
        d = xl.parse(sheet)
        d.columns = [str(c).strip() for c in d.columns]
        if _es_hoja_detalle_pedidos(d):
            d = _adaptar_hoja_detalle_pedidos(d)
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

# Siempre se excluye el día de hoy (todavía no cerró).
arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df = df[df["date"].dt.date < arg_today].copy()

if df.empty:
    st.error("Todavía no hay datos cargados para un día anterior a hoy.")
    st.stop()

def money(v):
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

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}
DIA_NOMBRE = {4: "Viernes", 5: "Sábado", 6: "Domingo", 0: "Lunes"}

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

# ---------------------------------------------------------------------
# Elegís vos el fin de semana: el desplegable lista todos los viernes con
# datos cargados (de cualquier mes/año), del más reciente al más antiguo.
# El "finde largo" es ese viernes + los 3 días siguientes (sáb/dom/lun),
# estén o no todavía cargados los 4.
# ---------------------------------------------------------------------

viernes_disponibles = sorted(df[df["date"].dt.weekday == 4]["date"].unique(), reverse=True)

if not viernes_disponibles:
    st.error("Todavía no encontré ningún viernes cargado en el archivo 'Vs de ventas' para armar un finde largo.")
    st.stop()

def _opcion_label(viernes_ts):
    viernes_ts = pd.Timestamp(viernes_ts)
    lunes_ts = viernes_ts + pd.Timedelta(days=3)
    dias_presentes = df[(df["date"] >= viernes_ts) & (df["date"] <= lunes_ts)]["date"].nunique()
    mes_label = f"{MESES_ES.get(viernes_ts.month, '').capitalize()} {viernes_ts.year}"
    marca = "✓ 4/4 días" if dias_presentes == 4 else f"{dias_presentes}/4 días"
    return f"Viernes {viernes_ts.strftime('%d/%m')} – Lunes {lunes_ts.strftime('%d/%m')} ({mes_label}) · {marca}"

opciones = {_opcion_label(v): pd.Timestamp(v) for v in viernes_disponibles}

st.markdown('<div class="filtro-row">', unsafe_allow_html=True)
opcion_elegida = st.selectbox("**Elegí el finde largo**", list(opciones.keys()), index=0, key="finde_largo_select")
st.markdown('</div>', unsafe_allow_html=True)

viernes_sel = opciones[opcion_elegida]
sabado_sel = viernes_sel + pd.Timedelta(days=1)
domingo_sel = viernes_sel + pd.Timedelta(days=2)
lunes_sel = viernes_sel + pd.Timedelta(days=3)
dias_sel = [viernes_sel, sabado_sel, domingo_sel, lunes_sel]

viernes_prev = _mismo_dia_año_pasado(viernes_sel)
lunes_prev = _mismo_dia_año_pasado(lunes_sel)
dias_prev = [_mismo_dia_año_pasado(d) for d in dias_sel]

label_cur = f"{viernes_sel.strftime('%d/%m/%Y')} al {lunes_sel.strftime('%d/%m/%Y')}"
label_prev = f"{viernes_prev.strftime('%d/%m/%Y')} al {lunes_prev.strftime('%d/%m/%Y')}"

tot_cur = suma_rango(viernes_sel, lunes_sel) or {"orders": 0, "ecommerce_tax": 0, "units": 0, "company_tax": 0}
tot_prev = suma_rango(viernes_prev, lunes_prev)
hay_prev = tot_prev is not None
if not hay_prev:
    tot_prev = {"orders": 0, "ecommerce_tax": 0, "units": 0, "company_tax": 0}

pedidos_cur, venta_cur, unidades_cur = tot_cur["orders"], tot_cur["ecommerce_tax"], tot_cur["units"]
pedidos_prev, venta_prev, unidades_prev = tot_prev["orders"], tot_prev["ecommerce_tax"], tot_prev["units"]
ticket_cur = (venta_cur / pedidos_cur) if pedidos_cur else 0
ticket_prev = (venta_prev / pedidos_prev) if pedidos_prev else 0

d_pedidos = pedidos_cur - pedidos_prev
d_venta = venta_cur - venta_prev
d_unidades = unidades_cur - unidades_prev
d_ticket = ticket_cur - ticket_prev

def delta_badge(v, is_money=False):
    if not hay_prev:
        return (
            '<div class="kpi-delta-line neutral">'
            f'<span class="kpi-delta">Sin datos de {viernes_prev.year} para comparar</span>'
            '</div>'
        )
    cls = "positive" if v >= 0 else "negative"
    arrow = "▲" if v >= 0 else "▼"
    sign = "+" if v >= 0 else "−"
    body = money(abs(v))[1:] if is_money else intfmt(abs(v))
    return (
        f'<div class="kpi-delta-line {cls}">'
        f'<span class="kpi-delta">{arrow} {sign} {body}</span>'
        f'<div class="sub">vs mismo finde largo {viernes_prev.year}</div>'
        '</div>'
    )

prev_pedidos_txt = intfmt(pedidos_prev) if hay_prev else "—"
prev_venta_txt = money(venta_prev) if hay_prev else "—"
prev_unidades_txt = intfmt(unidades_prev) if hay_prev else "—"
prev_ticket_txt = money(ticket_prev) if hay_prev else "—"
col_prev_label = label_prev if hay_prev else f"{label_prev} (sin datos)"

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
      <th>{label_cur}</th>
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
    f'"{col_prev_label}" toma el mismo finde largo (viernes a lunes) un año antes, '
    'mismas fechas de calendario, para que la comparación sea pareja.'
    '</div>'
)

# ---------------------------------------------------------------------
# Día a día del finde largo elegido: viernes, sábado, domingo y lunes,
# cada uno comparado con el mismo día de calendario (no el mismo día de
# la semana) un año antes.
# ---------------------------------------------------------------------

def variacion_html(v):
    if v is None:
        return '<span style="color:#6b7280;">—</span>'
    cls = "#208653" if v >= 0 else "#d64545"
    arrow = "▲" if v >= 0 else "▼"
    sign = "+" if v >= 0 else "−"
    return f'<span style="color:{cls};font-weight:700;">{arrow} {sign}{abs(v) * 100:.1f}%</span>'

dia_rows_html = ""
for d_cur, d_prev in zip(dias_sel, dias_prev):
    nombre = DIA_NOMBRE.get(d_cur.weekday(), "")
    fila_cur = df[df["date"] == d_cur]
    fila_prev = df[df["date"] == d_prev]
    venta_dia_cur = fila_cur["ecommerce_tax"].sum() if len(fila_cur) else None
    pedidos_dia_cur = fila_cur["orders"].sum() if len(fila_cur) else None
    venta_dia_prev = fila_prev["ecommerce_tax"].sum() if len(fila_prev) else None
    pedidos_dia_prev = fila_prev["orders"].sum() if len(fila_prev) else None

    venta_cur_txt = money(venta_dia_cur) if venta_dia_cur is not None else "—"
    pedidos_cur_txt = intfmt(pedidos_dia_cur) if pedidos_dia_cur is not None else "—"
    venta_prev_txt = money(venta_dia_prev) if venta_dia_prev is not None else "—"
    pedidos_prev_txt = intfmt(pedidos_dia_prev) if pedidos_dia_prev is not None else "—"
    variacion = (
        (venta_dia_cur / venta_dia_prev - 1)
        if venta_dia_cur is not None and venta_dia_prev not in (None, 0) else None
    )
    dia_rows_html += (
        '<tr style="border-top:1px solid #f1f3f5;">'
        f'<td style="padding:10px 16px;color:#000000;font-weight:700;">{nombre} {d_cur.strftime("%d/%m")}</td>'
        f'<td style="padding:10px 16px;color:#000000;text-align:center;">{venta_cur_txt}</td>'
        f'<td style="padding:10px 16px;color:#000000;text-align:center;">{pedidos_cur_txt}</td>'
        f'<td style="padding:10px 16px;color:#000000;text-align:center;">{venta_prev_txt}</td>'
        f'<td style="padding:10px 16px;color:#000000;text-align:center;">{pedidos_prev_txt}</td>'
        f'<td style="padding:10px 16px;text-align:center;">{variacion_html(variacion)}</td>'
        '</tr>'
    )

dia_table_html = f"""
<div class="cmp-table-wrap">
<div class="table-scroll">
<table class="cmp-table">
  <thead>
    <tr>
      <th>Día</th>
      <th>Venta {viernes_sel.year}</th>
      <th>Pedidos {viernes_sel.year}</th>
      <th>Venta {viernes_prev.year}</th>
      <th>Pedidos {viernes_prev.year}</th>
      <th>Variación</th>
    </tr>
  </thead>
  <tbody>{dia_rows_html}</tbody>
</table>
</div>
</div>
"""

dia_section_html = f"""
<div class="section" style="margin-top:30px;">Día a día del finde largo</div>
<div class="section-desc">Viernes, sábado, domingo y lunes de {label_cur}, cada uno comparado con el mismo día de calendario de {viernes_prev.year}.</div>
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
    <div class="hero-sub">ECOMMERCE · FINDE LARGO</div>
  </div>
  <div class="periodo-badge">
    <div class="lbl">🏖️ FINDE LARGO</div>
    <div class="val">{viernes_sel.strftime('%d/%m')} al {lunes_sel.strftime('%d/%m')}</div>
    <small>vs. mismo finde largo {viernes_prev.year}</small>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# HTML descargable: copia independiente de esta pestaña (finde elegido),
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
<title>MásOnline | Finde largo</title>
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
    <div class="hero-sub">ECOMMERCE · FINDE LARGO</div>
  </div>
  <div class="periodo-badge">
    <div class="lbl">🏖️ FINDE LARGO</div>
    <div class="val">{html.escape(viernes_sel.strftime('%d/%m'))} al {html.escape(lunes_sel.strftime('%d/%m'))}</div>
    <small>vs. mismo finde largo {viernes_prev.year}</small>
  </div>
</div>

<div class="section">Resultados del finde largo</div>
<div class="section-desc">Indicadores del canal ecommerce — <b>{html.escape(label_cur)}</b> (viernes a lunes).</div>
{kpis_html}

<div class="section" style="margin-top:30px;">Comparativo vs año anterior</div>
<div class="section-desc"><b>{html.escape(label_cur)}</b> vs <b>{html.escape(label_prev)}</b>.</div>
{table_html}
{footnote_html}
{dia_section_html}

</div>
</body>
</html>
"""

st.download_button(
    "⬇️ Descargar finde largo HTML",
    data=build_standalone_html(),
    file_name=f"finde_largo_masonline_{viernes_sel.strftime('%Y-%m-%d')}.html",
    mime="text/html",
    use_container_width=False,
)

# ---------------------------------------------------------------------
# Resultados del finde largo
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section">Resultados del finde largo</div>'
    f'<div class="section-desc">Indicadores del canal ecommerce — <b>{label_cur}</b> (viernes a lunes).</div>',
    unsafe_allow_html=True
)
st.markdown(kpis_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Comparativo vs año anterior
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section" style="margin-top:30px;">Comparativo vs año anterior</div>'
    f'<div class="section-desc"><b>{label_cur}</b> vs <b>{label_prev}</b>.</div>',
    unsafe_allow_html=True
)
st.markdown(table_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Día a día
# ---------------------------------------------------------------------

st.markdown(dia_section_html, unsafe_allow_html=True)

st.markdown(footnote_html, unsafe_allow_html=True)
