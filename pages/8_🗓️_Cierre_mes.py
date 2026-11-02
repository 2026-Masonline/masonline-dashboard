import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import html
import tempfile
import io
import re
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="MásOnline | Cierre de mes",
    page_icon="🗓️",
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

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }

    .rank-table-card {
        background: white; border-radius: 14px; overflow: hidden;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.06);
    }
    table.rank-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    table.rank-table thead th {
        background: #e9f7ef; color: #208653; font-weight: 700;
        padding: 10px 14px; text-align: left; white-space: nowrap;
    }
    table.rank-table td {
        padding: 12px 14px; border-top: 1px solid #f1f3f5; color: #20252b;
    }
    .rank-badge {
        width: 28px; height: 28px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 13px;
    }

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
DATA_TIENDAS_FILE = Path(__file__).resolve().parent.parent / "data_tiendas.csv"
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"
_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
_RESUMEN_FONT_BOLD_PATH = _FONTS_DIR / "DejaVuSans-Bold.ttf"
_RESUMEN_FONT_REG_PATH = _FONTS_DIR / "DejaVuSans.ttf"

try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    # "company_tax_neto" (Venta Comercial Operativa, SIN impuesto) — mismo
    # criterio que Venta diaria: COMPAÑÍA en esta página también muestra la
    # venta SIN impuesto, con Facturación (con impuesto) como respaldo para
    # fechas sin ese dato todavía (data.csv viejo, o mes no resubido).
    if "company_tax_neto" not in base_df.columns:
        base_df["company_tax_neto"] = pd.NA
    base_df["company_tax_neto"] = pd.to_numeric(base_df["company_tax_neto"], errors="coerce")
    # Guardamos la Compañía CON impuesto aparte (antes de pisarla con la
    # versión sin impuesto) — la tarjeta COMPAÑÍA sigue mostrando sin
    # impuesto, pero el % SHARE compara impuesto contra impuesto (Ecommerce
    # con impuesto / Compañía con impuesto), a pedido de Emi.
    base_df["company_tax_con_impuesto"] = base_df["company_tax"]
    base_df["company_tax"] = base_df["company_tax_neto"].where(
        base_df["company_tax_neto"].notna(), base_df["company_tax"]
    )
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

TIENDAS_COLUMNS = ["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax", "orders", "units"]

def _empty_tiendas_df():
    empty = pd.DataFrame(columns=TIENDAS_COLUMNS)
    empty["date"] = pd.to_datetime(empty["date"])
    return empty

try:
    if DATA_TIENDAS_FILE.exists():
        base_df_tiendas = pd.read_csv(DATA_TIENDAS_FILE)
        base_df_tiendas["date"] = pd.to_datetime(base_df_tiendas["date"], errors="coerce")
        base_df_tiendas["Tienda"] = base_df_tiendas["Tienda"].astype(str)
        for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
            base_df_tiendas[col] = pd.to_numeric(base_df_tiendas[col], errors="coerce").fillna(0)
        base_df_tiendas = base_df_tiendas.dropna(subset=["date"])
    else:
        base_df_tiendas = _empty_tiendas_df()
except Exception:
    base_df_tiendas = _empty_tiendas_df()

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()
if len(df_tiendas):
    df_tiendas["date"] = pd.to_datetime(df_tiendas["date"], errors="coerce")
    df_tiendas = df_tiendas.dropna(subset=["date"]).copy()

# ---------------------------------------------------------------------
# Pedidos y Unidades: salen de "Vs de ventas" (el mismo archivo compartido
# que ya usan Venta diaria, Comparativo, Venta hoy, etc.), contados por
# fecha de CREACIÓN del pedido — mismo criterio que Venta diaria. La Venta
# $ (ecommerce_tax) sigue 100% de Facturación (data.csv), sin tocar.
# ---------------------------------------------------------------------
SHARED_DIR_PEDIDOS = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_VSVENTAS_PATH_PEDIDOS = SHARED_DIR_PEDIDOS / "vsventas.xlsx"


def _pedidos_github_headers():
    token = st.secrets.get("GITHUB_TOKEN") if hasattr(st, "secrets") else None
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Masonline-Dashboard",
    }


def _pedidos_fetch_from_github(shared_path):
    headers = _pedidos_github_headers()
    if not headers:
        return None
    import urllib.request
    repo = "2026-Masonline/masonline-dashboard"
    branch = "main"
    repo_path = f"shared_uploads/{shared_path.name}"
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}?ref={branch}"
    raw_headers = {**headers, "Accept": "application/vnd.github.raw+json"}
    try:
        req = urllib.request.Request(url, headers=raw_headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except Exception:
        return None


def _pedidos_get_shared_bytes(shared_path):
    if shared_path.exists():
        try:
            data = shared_path.read_bytes()
            if data:
                return data
        except Exception:
            pass
    content = _pedidos_fetch_from_github(shared_path)
    if content:
        try:
            shared_path.parent.mkdir(parents=True, exist_ok=True)
            shared_path.write_bytes(content)
        except Exception:
            pass
        return content
    return None


_PEDIDOS_RAW_COLS = {
    "commerceDateCreated", "deliveryFinishDate", "commerceId", "commerceSequentialId",
    "salesChannelPrefix", "totalAmount", "itemsPickedQuantity",
}
_COL_PEDIDOS_VIEJO = "Pedidos Facturados con Venta Operativa - Ecommerce"
_COL_UNIDADES_VIEJO = "Cantidad Venta Operativa - Ecommerce"


def _pedidos_norm_codigo(v):
    if pd.isna(v):
        return ""
    try:
        if isinstance(v, float) and v == int(v):
            return str(int(v))
        return str(int(float(v)))
    except (TypeError, ValueError):
        return str(v).strip()


def _pedidos_codigo_tienda(v, tienda_codes):
    s = _pedidos_norm_codigo(v)
    if s in tienda_codes:
        return s
    candidatos = re.findall(r"\d{3,6}", s)
    for c in candidatos:
        if c in tienda_codes:
            return c
    return candidatos[-1] if candidatos else s


def _pedidos_es_hoja_detalle(d):
    return _PEDIDOS_RAW_COLS.issubset(set(d.columns))


def _pedidos_adaptar_hoja_detalle(d, tienda_codes):
    d = d.copy()
    es_pm = d["salesChannelPrefix"].astype(str).str.strip().str.upper() == "PM"
    es_rma = d["commerceId"].astype(str).str.upper().str.contains("RMA", na=False)
    d = d[~es_pm & ~es_rma & d["commerceSequentialId"].notna()]
    d = d.drop_duplicates(subset=["commerceSequentialId"])
    if "shippingWarehouseReferenceId" in d.columns:
        tienda_col = d["shippingWarehouseReferenceId"].apply(
            lambda v: _pedidos_codigo_tienda(v, tienda_codes)
        )
    else:
        tienda_col = ""
    if "itemsPickedQuantity" in d.columns:
        unidades_col = pd.to_numeric(d["itemsPickedQuantity"], errors="coerce").fillna(0)
    else:
        unidades_col = 0
    out = pd.DataFrame({
        "Id": d["commerceSequentialId"].values,
        "date": pd.to_datetime(d["commerceDateCreated"], errors="coerce").dt.normalize(),
        "Tienda": tienda_col,
        "pedidos": 1,
        "unidades": unidades_col,
    })
    return out


def _pedidos_es_hoja_vieja(d):
    return {"Fecha", "Tienda", _COL_PEDIDOS_VIEJO}.issubset(set(d.columns))


def _pedidos_adaptar_hoja_vieja(d):
    d = d.copy()
    unidades_viejo = (
        pd.to_numeric(d[_COL_UNIDADES_VIEJO], errors="coerce").fillna(0)
        if _COL_UNIDADES_VIEJO in d.columns else 0
    )
    out = pd.DataFrame({
        "Id": pd.Series([pd.NA] * len(d)),
        "date": pd.to_datetime(d["Fecha"], errors="coerce").dt.normalize(),
        "Tienda": d["Tienda"].apply(_pedidos_norm_codigo),
        "pedidos": pd.to_numeric(d[_COL_PEDIDOS_VIEJO], errors="coerce").fillna(0),
        "unidades": unidades_viejo,
    })
    return out


@st.cache_data(ttl=180, show_spinner=False)
def _cargar_pedidos_vsventas(vsventas_bytes, tienda_codes_tuple):
    cols_dia = ["date", "orders_vsventas", "unidades_vsventas"]
    cols_tienda = ["date", "Tienda", "orders_vsventas"]
    vacio = (pd.DataFrame(columns=cols_dia), pd.DataFrame(columns=cols_tienda))
    if not vsventas_bytes:
        return vacio
    tienda_codes = set(tienda_codes_tuple)
    try:
        xl = pd.ExcelFile(io.BytesIO(vsventas_bytes))
        partes = []
        for sheet in xl.sheet_names:
            d = xl.parse(sheet)
            d.columns = [str(c).strip() for c in d.columns]
            if _pedidos_es_hoja_detalle(d):
                partes.append(_pedidos_adaptar_hoja_detalle(d, tienda_codes))
            elif _pedidos_es_hoja_vieja(d):
                partes.append(_pedidos_adaptar_hoja_vieja(d))
        if not partes:
            return vacio
        todo = pd.concat(partes, ignore_index=True, sort=False)
        con_id = todo["Id"].notna()
        todo = pd.concat(
            [todo[con_id].drop_duplicates(subset=["Id"]), todo[~con_id]],
            ignore_index=True, sort=False,
        )
    except Exception:
        return vacio

    base = todo.dropna(subset=["date"])
    pedidos_tienda = (
        base.groupby(["date", "Tienda"], as_index=False)["pedidos"].sum()
        .rename(columns={"pedidos": "orders_vsventas"})
    )
    pedidos_dia = (
        base.groupby("date", as_index=False)
        .agg(pedidos=("pedidos", "sum"), unidades=("unidades", "sum"))
        .rename(columns={"pedidos": "orders_vsventas", "unidades": "unidades_vsventas"})
    )
    return pedidos_dia, pedidos_tienda


_tienda_codes_conocidos = tuple(sorted(set(df_tiendas["Tienda"].astype(str)))) if len(df_tiendas) else tuple()
_vsventas_bytes_pedidos = _pedidos_get_shared_bytes(SHARED_VSVENTAS_PATH_PEDIDOS)
_pedidos_dia_vs, _pedidos_tienda_vs = _cargar_pedidos_vsventas(_vsventas_bytes_pedidos, _tienda_codes_conocidos)

df = df.rename(columns={"orders": "orders_facturados", "units": "units_facturacion"})
df = df.merge(_pedidos_dia_vs, on="date", how="left")
df["orders"] = df["orders_vsventas"].where(df["orders_vsventas"].notna(), df["orders_facturados"])
df["units"] = df["unidades_vsventas"].where(df["unidades_vsventas"].notna(), df["units_facturacion"])
df = df.drop(columns=["orders_vsventas", "unidades_vsventas"])

if len(df_tiendas):
    df_tiendas = df_tiendas.rename(columns={"orders": "orders_facturados"})
    df_tiendas = df_tiendas.merge(_pedidos_tienda_vs, on=["date", "Tienda"], how="left")
    df_tiendas["orders"] = df_tiendas["orders_vsventas"].where(
        df_tiendas["orders_vsventas"].notna(), df_tiendas["orders_facturados"]
    )
    df_tiendas = df_tiendas.drop(columns=["orders_vsventas"])
# ---------------------------------------------------------------------

_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()

# El mes CERRADO siempre es el calendario anterior al actual (no el mes en
# curso, que ya muestra Venta diaria) — a pedido de Emi, automático, sin
# selector.
if arg_today.month == 1:
    REF_YEAR, REF_MONTH = arg_today.year - 1, 12
else:
    REF_YEAR, REF_MONTH = arg_today.year, arg_today.month - 1

MES_NOMBRE = _MESES_ES[REF_MONTH - 1].capitalize()
MES_LABEL = f"{MES_NOMBRE} {REF_YEAR}"

current = df[
    (df["date"].dt.year == REF_YEAR) &
    (df["date"].dt.month == REF_MONTH)
].copy().sort_values("date")

if current.empty:
    st.error(
        f"Todavía no hay datos de {MES_NOMBRE.lower()} {REF_YEAR} cargados. "
        'Subí el Excel "Venta Con y sin Impuesto" de ese mes desde la pestaña "app".'
    )
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

def pct(v):
    return f"{v*100:.2f}%".replace(".", ",")

def intfmt(v):
    return f"{int(v):,}".replace(",", ".")


acc_ecom = current["ecommerce_tax"].sum()
acc_company = current["company_tax"].sum()
# Para el % SHARE (no para la tarjeta de $ COMPAÑÍA, que sigue sin
# impuesto): comparación impuesto contra impuesto, a pedido de Emi.
acc_company_con_imp = current["company_tax_con_impuesto"].sum()
acc_orders = current["orders"].sum()
acc_units = current["units"].sum()
share = acc_ecom / acc_company_con_imp if acc_company_con_imp else 0
target = 0.03
gap = target - share

# ---- Top 5 tiendas del mes cerrado ----
current_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)
if len(df_tiendas):
    current_tiendas = df_tiendas[
        (df_tiendas["date"].dt.year == REF_YEAR) &
        (df_tiendas["date"].dt.month == REF_MONTH)
    ].copy()

tiendas_resumen = pd.DataFrame(columns=["Tienda", "Nombre", "ecommerce_tax", "orders"])
if len(current_tiendas):
    tiendas_resumen = (
        current_tiendas.groupby(["Tienda", "Nombre"], as_index=False)
        .agg(ecommerce_tax=("ecommerce_tax", "sum"), orders=("orders", "sum"))
    )

top_venta_mes = (
    tiendas_resumen.sort_values("ecommerce_tax", ascending=False).head(5).reset_index(drop=True)
    if len(tiendas_resumen) else tiendas_resumen.copy()
)

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
    <div class="hero-sub">E-COMMERCE · CIERRE DE MES</div>
  </div>
  <div class="hero-date">
    {MES_LABEL}
    <small>Mes cerrado — {intfmt(len(current))} días con datos</small>
  </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #f5a623;">
      <div class="label" style="color:#f5a623;">PARTICIPACIÓN E-COMMERCE</div>
      <div class="value">{pct(share)}</div>
      <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #3b82c4;">
      <div class="label" style="color:#2566a0;">COMPAÑÍA</div>
      <div class="value">{money(acc_company)}</div>
      <div class="small">Venta del mes (sin impuesto)</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #e8432c;">
      <div class="label" style="color:#e8432c;">ECOMMERCE</div>
      <div class="value" style="color:#e8432c;">{money(acc_ecom)}</div>
      <div class="small">Venta del mes (con impuesto)</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #59636e;">
      <div class="label">PEDIDOS Y UNIDADES</div>
      <div class="value">{intfmt(acc_orders)}</div>
      <div class="small">{intfmt(acc_units)} unidades</div>
    </div>
    """, unsafe_allow_html=True)

progress = min(share / target, 1.0) * 100 if target else 0
st.markdown('<div class="section">Avance de participación</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="progress-wrap">
  <div class="progress-layout">
    <div class="progress-main">
      <div class="progress-track">
        <div class="progress-fill" style="width:{progress:.1f}%;"></div>
      </div>
      <div class="progress-row">
        <span>Participación del mes: {pct(share)}</span>
        <span>Objetivo: {pct(target)}</span>
      </div>
    </div>
    <div class="progress-target">
      {f"{share/target:.0%}" if target else "0%"}
      <small>del objetivo</small>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section">Resumen para GDN</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
    'Capturá esta card y enviala directo — sin tocar el resto del dashboard.'
    '</div>',
    unsafe_allow_html=True
)
st.markdown(f"""
<div style="max-width:420px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
  <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
    CIERRE DE MES &nbsp;{MES_NOMBRE.upper()} {REF_YEAR}
  </div>
  <div style="padding:18px 16px;">
    <div style="display:flex;gap:12px;">
      <div style="flex:1;">
        <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
        <div style="font-size:11px;color:#9ca3af;">VENTA DEL MES</div>
        <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(acc_company)}</div>
      </div>
      <div style="flex:1;">
        <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
        <div style="font-size:11px;color:#9ca3af;">VENTA DEL MES</div>
        <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(acc_ecom)}</div>
      </div>
    </div>
    <div style="border-top:1px solid #eee;margin:14px 0;"></div>
    <div style="display:flex;gap:12px;">
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
    <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE DEL MES</span>
    <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share)}</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section">Top 5 tiendas eCommerce</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">'
    'Ranking por venta ecommerce del mes cerrado, con pedidos de cada tienda.'
    '</div>',
    unsafe_allow_html=True
)

def tienda_rank_table_html(rows_df, titulo):
    header = (
        '<div style="background:#2f9e66;color:#fff;font-weight:800;'
        'font-size:15px;padding:13px 20px;display:flex;align-items:center;gap:10px;">'
        f'<span>🏆</span><span>{titulo}</span>'
        '</div>'
    )
    empty_msg = (
        'Todavía no hay datos por tienda para este mes. Se completa '
        'automáticamente la próxima vez que se suba el Excel desde "app" '
        '(si trae las columnas Tienda y Nombre).'
    )
    if not len(rows_df):
        return (
            f'<div class="rank-table-card">{header}'
            f'<div style="padding:20px;color:#9ca3af;font-size:13px;">{empty_msg}</div>'
            '</div>'
        )
    rows_html = ""
    for i, r in enumerate(rows_df.itertuples(), start=1):
        nombre = str(r.Nombre) if r.Nombre else ""
        tienda_label = f"{r.Tienda} - {nombre}" if nombre else str(r.Tienda)
        rows_html += (
            '<tr>'
            '<td><span class="rank-badge" style="background:#2f9e66;color:#fff;">'
            f'{i}</span></td>'
            f'<td>{html.escape(tienda_label)}</td>'
            f'<td style="text-align:center;">{intfmt(r.orders)}</td>'
            f'<td style="text-align:right;font-weight:800;color:#208653;">{money(r.ecommerce_tax)}</td>'
            '</tr>'
        )
    return (
        f'<div class="rank-table-card">{header}'
        '<div class="table-scroll">'
        '<table class="rank-table"><thead><tr>'
        '<th></th><th>Tienda</th>'
        '<th style="text-align:center;">Pedidos eCommerce</th>'
        '<th style="text-align:right;">Venta eCommerce (con impuesto)</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>'
        '</div></div>'
    )

st.markdown(
    tienda_rank_table_html(top_venta_mes, f"TOP 5 · {MES_NOMBRE.upper()} {REF_YEAR}"),
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------
# RESUMEN EN IMAGEN (PNG): una sola card de cierre de mes, lista para
# compartir (WhatsApp, redes) — mismo estilo que el resumen de Venta
# diaria, pero con un solo panel (no hay "día" en esta página).
# ---------------------------------------------------------------------

def _resumen_font(bold, size):
    candidatos = (
        [_RESUMEN_FONT_BOLD_PATH, _RESUMEN_FONT_REG_PATH]
        if bold else [_RESUMEN_FONT_REG_PATH, _RESUMEN_FONT_BOLD_PATH]
    )
    candidatos += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidatos:
        try:
            return ImageFont.truetype(str(c), size)
        except Exception:
            continue
    return ImageFont.load_default()


def _resumen_text_w(draw, txt, f):
    bbox = draw.textbbox((0, 0), txt, font=f)
    return bbox[2] - bbox[0]


def _resumen_text_center(draw, cx, y, txt, f, fill):
    w = _resumen_text_w(draw, txt, f)
    draw.text((cx - w / 2, y), txt, font=f, fill=fill)


def _resumen_rr(draw, box, radius, fill, corners=None):
    try:
        if corners is not None:
            draw.rounded_rectangle(box, radius=radius, fill=fill, corners=corners)
            return
    except TypeError:
        pass
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _resumen_shade(hexcolor, factor):
    hexcolor = hexcolor.lstrip("#")
    r0, g0, b0 = int(hexcolor[0:2], 16), int(hexcolor[2:4], 16), int(hexcolor[4:6], 16)
    r1 = int(r0 + (255 - r0) * factor) if factor > 0 else int(r0 * (1 + factor))
    g1 = int(g0 + (255 - g0) * factor) if factor > 0 else int(g0 * (1 + factor))
    b1 = int(b0 + (255 - b0) * factor) if factor > 0 else int(b0 * (1 + factor))
    return (max(0, min(255, r1)), max(0, min(255, g1)), max(0, min(255, b1)))


def _resumen_icon_cube(draw, cx, cy, size, color):
    s = size * 0.56
    top_pt = (cx, cy - s)
    right_pt = (cx + s * 0.92, cy - s * 0.46)
    left_pt = (cx - s * 0.92, cy - s * 0.46)
    center_pt = (cx, cy)
    bot_left_pt = (cx - s * 0.92, cy + s * 0.5)
    bot_right_pt = (cx + s * 0.92, cy + s * 0.5)
    bottom_pt = (cx, cy + s * 1.0)
    draw.polygon([top_pt, right_pt, center_pt, left_pt], fill=_resumen_shade(color, 0.42))
    draw.polygon([left_pt, center_pt, bottom_pt, bot_left_pt], fill=_resumen_shade(color, 0.12))
    draw.polygon([right_pt, bot_right_pt, bottom_pt, center_pt], fill=_resumen_shade(color, -0.18))


def _resumen_icon_bag(draw, cx, cy, size, color):
    bw = size * 0.95
    bh = size * 0.85
    top = cy - bh * 0.42
    bot = cy + bh * 0.58
    left = cx - bw * 0.5
    right = cx + bw * 0.5
    draw.rounded_rectangle([left, top, right, bot], radius=max(2, bw * 0.12), fill=color)
    handle_box = [cx - bw * 0.3, top - bw * 0.42, cx + bw * 0.3, top + bw * 0.22]
    draw.arc(handle_box, 185, 355, fill=color, width=max(3, int(size * 0.12)))
    fold_y = top + bh * 0.26
    draw.line([left + bw * 0.14, fold_y, right - bw * 0.14, fold_y], fill="white", width=2)


def _resumen_icon_percent(draw, cx, cy, size, color):
    r = size * 0.5
    draw.line([cx - r * 0.55, cy + r * 0.55, cx + r * 0.55, cy - r * 0.55], fill=color, width=5)
    sr = size * 0.16
    draw.ellipse([cx - r * 0.55 - sr, cy - r * 0.55 - sr, cx - r * 0.55 + sr, cy - r * 0.55 + sr], fill=color)
    draw.ellipse([cx + r * 0.55 - sr, cy + r * 0.55 - sr, cx + r * 0.55 + sr, cy + r * 0.55 + sr], fill=color)


def generar_resumen_imagen_mes(mes_label, company, ecom, orders, units, share_v):
    W, H = 900, 616
    C_BG = "#ffffff"
    C_BORDER = "#cfe0f2"
    C_TEXT_DARK = "#1b2430"
    C_GRAY = "#6b7280"
    C_BLUE = "#1f5fae"
    C_RED = "#e8432c"
    C_ORANGE = "#f5a623"
    C_PINK_BG = "#fdeceb"
    C_BLUELIGHT_BG = "#eaf2fb"
    C_CREAM_BG = "#fef6e7"
    C_CARD_BORDER = "#e8ebef"

    img = Image.new("RGB", (W, H), C_BG)
    d = ImageDraw.Draw(img)

    f_title = _resumen_font(True, 27)
    f_subtitle = _resumen_font(True, 17)
    f_panel_header = _resumen_font(True, 22)
    f_col_label = _resumen_font(True, 15)
    f_col_value = _resumen_font(True, 27)
    f_mini_label = _resumen_font(False, 13)
    f_mini_value = _resumen_font(True, 21)
    f_share_label = _resumen_font(True, 15)
    f_share_value = _resumen_font(True, 24)
    f_footer = _resumen_font(True, 14)
    f_footer_reg = _resumen_font(False, 14)

    d.rounded_rectangle([6, 6, W - 6, H - 6], radius=26, outline=C_BORDER, width=4)

    logo_img = None
    if LOGO_FILE.exists():
        try:
            logo_img = Image.open(LOGO_FILE).convert("RGBA")
        except Exception:
            logo_img = None

    # Logo arriba en su propia fila, título y subtítulo centrados debajo
    # (no al costado, como en el resumen de Venta diaria) — así nunca se
    # superponen sin importar qué tan ancho sea el logo real.
    if logo_img is not None:
        lw, lh = logo_img.size
        target_h = 46
        target_w = int(lw * target_h / lh)
        logo_resized = logo_img.resize((target_w, target_h))
        img.paste(logo_resized, (int(W / 2 - target_w / 2), 34), logo_resized)
    else:
        _resumen_text_center(d, W / 2, 38, "MásOnline", _resumen_font(True, 28), C_TEXT_DARK)

    _resumen_text_center(d, W / 2, 98, "VENTAS COMPAÑÍA VS ECOMMERCE", f_title, C_TEXT_DARK)
    _resumen_text_center(d, W / 2, 134, f"CIERRE DE MES · {mes_label}", f_subtitle, C_BLUE)

    d.line([40, 174, W - 40, 174], fill=C_CARD_BORDER, width=2)

    panel_x0, panel_y0, panel_x1, panel_y1 = 40, 200, W - 40, H - 70
    _resumen_rr(d, [panel_x0, panel_y0, panel_x1, panel_y1], 16, "#ffffff")
    d.rounded_rectangle([panel_x0, panel_y0, panel_x1, panel_y1], radius=16, outline=C_CARD_BORDER, width=2)

    header_h = 60
    bottom_h = 60
    _resumen_rr(d, [panel_x0, panel_y0, panel_x1, panel_y0 + header_h], 16, C_ORANGE, corners=(True, True, False, False))
    _resumen_text_center(d, (panel_x0 + panel_x1) / 2, panel_y0 + 17, "VENTA DEL MES", f_panel_header, C_TEXT_DARK)

    _resumen_rr(d, [panel_x0, panel_y1 - bottom_h, panel_x1, panel_y1], 16, C_CREAM_BG, corners=(False, False, True, True))

    body_top = panel_y0 + header_h
    pad = 44
    col_w = (panel_x1 - panel_x0 - pad * 2 - 24) / 2
    colA_x = panel_x0 + pad
    colB_x = panel_x0 + pad + col_w + 24
    row1_y = body_top + 22

    d.text((colA_x, row1_y), "COMPAÑÍA", font=f_col_label, fill=C_GRAY)
    d.text((colB_x, row1_y), "ECOMMERCE", font=f_col_label, fill=C_RED)

    pill_y0 = row1_y + 26
    pill_h = 56
    _resumen_rr(d, [colA_x, pill_y0, colA_x + col_w, pill_y0 + pill_h], 12, C_BLUELIGHT_BG)
    _resumen_rr(d, [colB_x, pill_y0, colB_x + col_w, pill_y0 + pill_h], 12, C_PINK_BG)
    d.text((colA_x + 16, pill_y0 + 13), money(company), font=f_col_value, fill=C_TEXT_DARK)
    d.text((colB_x + 16, pill_y0 + 13), money(ecom), font=f_col_value, fill=C_RED)

    divider_y = pill_y0 + pill_h + 22
    d.line([panel_x0 + pad, divider_y, panel_x1 - pad, divider_y], fill=C_CARD_BORDER, width=2)

    row2_y = divider_y + 18
    icon_r = 24
    icon_cx_a = colA_x + icon_r
    icon_cx_b = colB_x + icon_r
    icon_cy = row2_y + icon_r

    d.ellipse([icon_cx_a - icon_r, icon_cy - icon_r, icon_cx_a + icon_r, icon_cy + icon_r], fill=C_PINK_BG)
    _resumen_icon_bag(d, icon_cx_a, icon_cy, icon_r * 0.9, C_RED)
    d.ellipse([icon_cx_b - icon_r, icon_cy - icon_r, icon_cx_b + icon_r, icon_cy + icon_r], fill=C_CREAM_BG)
    _resumen_icon_cube(d, icon_cx_b, icon_cy, icon_r * 0.95, C_ORANGE)

    text_x_a = icon_cx_a + icon_r + 14
    text_x_b = icon_cx_b + icon_r + 14
    d.text((text_x_a, row2_y - 2), "PEDIDOS ECOMMERCE", font=f_mini_label, fill=C_GRAY)
    d.text((text_x_a, row2_y + 16), intfmt(orders), font=f_mini_value, fill=C_TEXT_DARK)
    d.text((text_x_b, row2_y - 2), "UNIDADES ECOMMERCE", font=f_mini_label, fill=C_GRAY)
    d.text((text_x_b, row2_y + 16), intfmt(units), font=f_mini_value, fill=C_TEXT_DARK)

    share_cy = panel_y1 - bottom_h / 2
    _resumen_icon_percent(d, panel_x0 + pad + 10, share_cy, 24, C_RED)
    d.text((panel_x0 + pad + 32, share_cy - 10), "SHARE ECOMMERCE DEL MES", font=f_share_label, fill=C_GRAY)
    val_txt = pct(share_v)
    vw = _resumen_text_w(d, val_txt, f_share_value)
    d.text((panel_x1 - pad - vw, share_cy - 12), val_txt, font=f_share_value, fill=C_RED)

    footer_y = H - 44
    if logo_img is not None:
        lw, lh = logo_img.size
        th = 20
        tw = int(lw * th / lh)
        small_logo = logo_img.resize((tw, th))
        img.paste(small_logo, (40, footer_y - 1), small_logo)
        fx = 40 + tw + 12
    else:
        d.text((40, footer_y), "MásOnline", font=_resumen_font(True, 16), fill=C_TEXT_DARK)
        fx = 40 + 100
    d.line([fx - 6, footer_y, fx - 6, footer_y + 18], fill=C_CARD_BORDER, width=2)
    d.text((fx + 6, footer_y), "OPERACIONES ECOMMERCE", font=f_footer, fill=C_GRAY)

    foot_right = f"Datos con impuesto. Período: {mes_label}."
    fw = _resumen_text_w(d, foot_right, f_footer_reg)
    d.text((W - 40 - fw, footer_y), foot_right, font=f_footer_reg, fill=C_GRAY)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


try:
    _resumen_png_bytes = generar_resumen_imagen_mes(
        mes_label=f"{MES_NOMBRE.upper()} {REF_YEAR}",
        company=acc_company, ecom=acc_ecom, orders=acc_orders, units=acc_units,
        share_v=share,
    )
    st.download_button(
        "🖼️ Descargar resumen (imagen)",
        data=_resumen_png_bytes,
        file_name=f"cierre_mes_{REF_YEAR}{REF_MONTH:02d}.png",
        mime="image/png",
    )
except Exception as _e:
    st.caption(f"No pude armar la imagen de resumen ({_e}).")

st.markdown(
    '<div class="footer">'
    '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
    '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
    '</div>',
    unsafe_allow_html=True
)
