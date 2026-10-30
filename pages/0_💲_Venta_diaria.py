import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import html
import tempfile
import io
import re
from PIL import Image, ImageDraw, ImageFont

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
        .compare-value { font-size: 24px; }
        .progress-layout { flex-direction: column; align-items: stretch; gap: 14px; }
        .progress-target { width: auto; text-align: left; }
        table { font-size: 12px; }
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

DATA_FILE = Path(__file__).resolve().parent.parent / "data.csv"
DATA_TIENDAS_FILE = Path(__file__).resolve().parent.parent / "data_tiendas.csv"
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    # "company_tax_neto" (Venta Comercial Operativa, SIN impuesto) es
    # columna nueva que arma la pestaña "app" — un data.csv viejo, o un mes
    # todavía no vuelto a subir con el Excel actualizado, puede no tenerla
    # (o tenerla en NaN para esas fechas); en ese caso se usa como respaldo
    # "company_tax" (con impuesto), más abajo.
    if "company_tax_neto" not in base_df.columns:
        base_df["company_tax_neto"] = pd.NA
    base_df["company_tax_neto"] = pd.to_numeric(base_df["company_tax_neto"], errors="coerce")
    # A pedido de Emi, en esta página (Venta diaria) "COMPAÑÍA" muestra la
    # venta SIN impuesto ("Venta Comercial Operativa"), no "Facturacion"
    # (con impuesto) — el resto del dashboard (Operativo, Resumen, Venta
    # hoy) sigue usando Facturación para este mismo dato, sin cambios ahí.
    base_df["company_tax_con_impuesto"] = base_df["company_tax"]
    base_df["company_tax"] = base_df["company_tax_neto"].where(
        base_df["company_tax_neto"].notna(), base_df["company_tax"]
    )
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

# Desglose por tienda ("Top 5 tiendas eCommerce" más abajo). Es un archivo
# aparte, "data_tiendas.csv", que lo arma y actualiza la pestaña "app" cada
# vez que se sube el Excel — puede no existir todavía la primera vez.
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

st.markdown(
    '<div style="color:#6b7280;font-size:12px;margin:-6px 0 14px;">'
    'Los datos se cargan desde la pestaña <b>app</b> (menú de la izquierda) — subí '
    'ahí el Excel "Venta Con y sin Impuesto" cuando quieras actualizarlos.'
    '</div>',
    unsafe_allow_html=True
)

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df[df["date"].dt.date < arg_today].copy()

if len(df_tiendas):
    df_tiendas["date"] = pd.to_datetime(df_tiendas["date"], errors="coerce")
    df_tiendas = df_tiendas.dropna(subset=["date"]).copy()

# ---------------------------------------------------------------------
# Pedidos: de acá en más salen siempre de "Vs de ventas" (el mismo archivo
# que usan Comparativo y Finde largo), no de "Pedidos Facturados" de Venta
# Con y sin Impuesto. Motivo: "Pedidos Facturados" se sigue completando
# varios días después de cargado el archivo (un mismo día puede pasar de
# 709 a 1.151 pedidos recién días más tarde), y eso hacía que la Venta
# diaria y el Excel de Emi no coincidieran según cuándo se había actualizado
# cada uno. Acá contamos por fecha de CREACIÓN del pedido (commerceDateCreated),
# que no se corrige de la misma manera, y además coincide con la base de la
# venta $ (que también es por fecha de facturación/creación, no de entrega).
# Nota: esto es distinto de Comparativo y Finde largo, que cuentan por fecha
# de ENTREGA (deliveryFinishDate) — ahí se dejó así a propósito, no se tocó.
# La venta ($) y la participación NO cambian: siguen saliendo de "Venta Con
# y sin Impuesto" (data.csv), sin ningún cambio. Esto solo reemplaza la
# columna "orders" (pedidos), tanto el total por día como el desglose por
# tienda, en todas las pestañas de esta página.
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
_COL_VENTA_VIEJO = "Venta - Ecommerce"
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
    """El código de depósito de 'Vs de ventas' (shippingWarehouseReferenceId)
    a veces viene con prefijos del sistema (ej. 'Inv-Full-1017', 'wm-1012',
    'RT-STS-PP-1044') en vez del código pelado. Probamos primero tal cual, y
    si no matchea, buscamos entre los números que trae el string cuál es un
    código de tienda ya conocido (de data_tiendas.csv)."""
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
    """Devuelve una fila por pedido con AMBAS fechas (creación y entrega) ya
    calculadas, para poder armar los dos criterios (creación/entrega) leyendo
    y filtrando el archivo una sola vez, en vez de dos. Incluye el Id del
    pedido (commerceSequentialId) para poder dedupear también ENTRE hojas
    (el archivo puede traer varias solapas/sheets, por ejemplo una por
    semana, con pedidos repetidos de una hoja a otra)."""
    d = d.copy()
    es_pm = d["salesChannelPrefix"].astype(str).str.strip().str.upper() == "PM"
    es_rma = d["commerceId"].astype(str).str.upper().str.contains("RMA", na=False)
    d = d[~es_pm & ~es_rma & d["commerceSequentialId"].notna()]
    # El archivo a veces trae el mismo pedido repetido dentro de una misma
    # hoja (filas idénticas, más de una vez de punta a punta) — nos quedamos
    # con un solo registro por pedido (commerceSequentialId) para no
    # duplicar el conteo. El dedupe ENTRE hojas se hace después, en
    # _cargar_pedidos_vsventas, una vez juntadas todas las hojas.
    d = d.drop_duplicates(subset=["commerceSequentialId"])
    if "shippingWarehouseReferenceId" in d.columns:
        tienda_col = d["shippingWarehouseReferenceId"].apply(
            lambda v: _pedidos_codigo_tienda(v, tienda_codes)
        )
    else:
        tienda_col = ""
    # Monto ($) y Unidades del pedido — mismo criterio que usa Comparativo
    # (totalAmount para $, itemsPickedQuantity para unidades, no
    # itemsQuantity): a pedido de Emi, la Venta $ y las Unidades de esta
    # página también salen de acá en vez de depender solo de Facturación
    # (ver más abajo, armado de "ecommerce_tax"/"units" con respaldo).
    monto_col = pd.to_numeric(
        d["totalAmount"].astype(str)
        .str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    ).fillna(0)
    if "itemsPickedQuantity" in d.columns:
        unidades_col = pd.to_numeric(d["itemsPickedQuantity"], errors="coerce").fillna(0)
    else:
        unidades_col = 0
    out = pd.DataFrame({
        "Id": d["commerceSequentialId"].values,
        "date_creacion": pd.to_datetime(d["commerceDateCreated"], errors="coerce").dt.normalize(),
        "date_entrega": pd.to_datetime(d["deliveryFinishDate"], errors="coerce").dt.normalize(),
        "Tienda": tienda_col,
        "pedidos": 1,
        "monto": monto_col,
        "unidades": unidades_col,
    })
    return out


def _pedidos_es_hoja_vieja(d):
    return {"Fecha", "Tienda", _COL_PEDIDOS_VIEJO}.issubset(set(d.columns))


def _pedidos_adaptar_hoja_vieja(d):
    # La hoja vieja (formato agregado, años anteriores) solo trae una fecha
    # por fila — se usa esa misma fecha para los dos criterios. A diferencia
    # del detalle de pedidos, esta hoja sí trae Venta $ y Unidades ya
    # agregadas por tienda-día (mismas columnas que usa Comparativo), así
    # que se toman directo en vez de quedar en 0.
    d = d.copy()
    fecha = pd.to_datetime(d["Fecha"], errors="coerce").dt.normalize()
    monto_viejo = (
        pd.to_numeric(d[_COL_VENTA_VIEJO], errors="coerce").fillna(0)
        if _COL_VENTA_VIEJO in d.columns else 0
    )
    unidades_viejo = (
        pd.to_numeric(d[_COL_UNIDADES_VIEJO], errors="coerce").fillna(0)
        if _COL_UNIDADES_VIEJO in d.columns else 0
    )
    out = pd.DataFrame({
        "Id": pd.Series([pd.NA] * len(d)),
        "date_creacion": fecha,
        "date_entrega": fecha,
        "Tienda": d["Tienda"].apply(_pedidos_norm_codigo),
        "pedidos": pd.to_numeric(d[_COL_PEDIDOS_VIEJO], errors="coerce").fillna(0),
        "monto": monto_viejo,
        "unidades": unidades_viejo,
    })
    return out


@st.cache_data(ttl=180, show_spinner=False)
def _cargar_pedidos_vsventas(vsventas_bytes, tienda_codes_tuple):
    """Lee 'Vs de ventas' UNA sola vez y arma los dos criterios de pedidos
    (fecha de creación y fecha de entrega) juntos, para no tener que abrir y
    filtrar el archivo (que puede ser grande) dos veces."""
    cols_dia = ["date", "orders_vsventas", "monto_vsventas", "unidades_vsventas"]
    cols_tienda = ["date", "Tienda", "orders_vsventas"]
    vacio_dia = pd.DataFrame(columns=cols_dia)
    vacio_tienda = pd.DataFrame(columns=cols_tienda)
    vacio = (vacio_dia, vacio_tienda, vacio_dia, vacio_tienda)
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
        # El archivo puede traer varias hojas (por ejemplo, una por semana) y
        # un mismo pedido puede repetirse de una hoja a otra. El dedupe de
        # _pedidos_adaptar_hoja_detalle solo saca duplicados DENTRO de cada
        # hoja; acá sacamos los que quedan repetidos ENTRE hojas, por Id
        # (commerceSequentialId) — así no se cuenta el mismo pedido varias
        # veces en el total del mes. Las filas de la hoja vieja (formato
        # agregado, sin Id) no se tocan: ya vienen una por fila/fecha.
        con_id = todo["Id"].notna()
        todo = pd.concat(
            [todo[con_id].drop_duplicates(subset=["Id"]), todo[~con_id]],
            ignore_index=True, sort=False,
        )
    except Exception:
        return vacio

    def _agg(date_col):
        base = todo.dropna(subset=[date_col]).rename(columns={date_col: "date"})
        pedidos_tienda = (
            base.groupby(["date", "Tienda"], as_index=False)["pedidos"].sum()
            .rename(columns={"pedidos": "orders_vsventas"})
        )
        # A nivel día (no por tienda) también sumamos monto $ y unidades —
        # a pedido de Emi, la Venta $ y las Unidades de esta página también
        # salen de acá (mismo criterio que Comparativo), con Facturación
        # como respaldo solo para fechas sin datos acá (ver más abajo).
        pedidos_dia = (
            base.groupby("date", as_index=False)
            .agg(pedidos=("pedidos", "sum"), monto=("monto", "sum"), unidades=("unidades", "sum"))
            .rename(columns={
                "pedidos": "orders_vsventas", "monto": "monto_vsventas", "unidades": "unidades_vsventas",
            })
        )
        return pedidos_dia, pedidos_tienda

    pedidos_dia_creacion, pedidos_tienda_creacion = _agg("date_creacion")
    pedidos_dia_entrega, pedidos_tienda_entrega = _agg("date_entrega")
    return pedidos_dia_creacion, pedidos_tienda_creacion, pedidos_dia_entrega, pedidos_tienda_entrega


_tienda_codes_conocidos = tuple(sorted(set(df_tiendas["Tienda"].astype(str)))) if len(df_tiendas) else tuple()
_vsventas_bytes_pedidos = _pedidos_get_shared_bytes(SHARED_VSVENTAS_PATH_PEDIDOS)
(
    _pedidos_dia_vs, _pedidos_tienda_vs,
    _pedidos_dia_vs_entrega, _pedidos_tienda_vs_entrega,
) = _cargar_pedidos_vsventas(_vsventas_bytes_pedidos, _tienda_codes_conocidos)

# Reemplazo con respaldo: si para una fecha puntual "Vs de ventas" todavía
# no tiene datos (por ejemplo, no se subió una versión más nueva), se usa
# como respaldo el valor de Facturación ("Venta Con y sin Impuesto"), para
# que la página no se quede sin número ese día. A pedido de Emi, Pedidos,
# Venta $ y Unidades de toda esta página salen de "Vs de ventas" (mismo
# criterio que Comparativo); Facturación queda solo como respaldo para
# fechas sin datos en "Vs de ventas".
df = df.rename(columns={
    "orders": "orders_facturados",
    "ecommerce_tax": "ecommerce_tax_facturacion",
    "units": "units_facturacion",
})
df = df.merge(_pedidos_dia_vs, on="date", how="left")
df["orders"] = df["orders_vsventas"].where(df["orders_vsventas"].notna(), df["orders_facturados"])
df["ecommerce_tax"] = df["monto_vsventas"].where(
    df["monto_vsventas"].notna(), df["ecommerce_tax_facturacion"]
)
df["units"] = df["unidades_vsventas"].where(
    df["unidades_vsventas"].notna(), df["units_facturacion"]
)
# "orders_entrega"/"orders_entrega_real": antes salían de un segundo conteo
# por fecha de ENTREGA (deliveryFinishDate); ahora, a pedido de Emi, el
# Pedidos de toda esta página sale por fecha de CREACIÓN del pedido
# (commerceDateCreated) — el mismo criterio que ya usa Comparativo — así
# que estos dos quedan como alias de "orders"/el dato sin respaldo. Se
# mantienen estos nombres para no tener que tocar cada lugar de la página
# donde ya se usan (tarjeta DIARIO, MES EN CURSO, Top 5 del día, Resumen
# para GDN, imagen descargable).
df["orders_entrega"] = df["orders"]
df["orders_entrega_real"] = df["orders_vsventas"].fillna(0)
df = df.drop(columns=["orders_vsventas", "monto_vsventas", "unidades_vsventas"])

if len(df_tiendas):
    df_tiendas = df_tiendas.rename(columns={"orders": "orders_facturados"})
    df_tiendas = df_tiendas.merge(_pedidos_tienda_vs, on=["date", "Tienda"], how="left")
    df_tiendas["orders"] = df_tiendas["orders_vsventas"].where(
        df_tiendas["orders_vsventas"].notna(), df_tiendas["orders_facturados"]
    )
    df_tiendas["orders_entrega"] = df_tiendas["orders"]
    df_tiendas = df_tiendas.drop(columns=["orders_vsventas"])
# ---------------------------------------------------------------------

_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
_MESES_ABREV_ES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul",
    "Ago", "Sep", "Oct", "Nov", "Dic"
]

# Selector de mes: por defecto abre en el mes en curso (calculado solo, sin
# quedar fijo en el código), pero se puede elegir cualquier otro mes que ya
# tenga datos cargados, para mirar un mes cerrado sin tener que esperar a
# que vuelva a ser el mes actual.
_periodos_disponibles = sorted(
    {(d.year, d.month) for d in df["date"].dt.date},
    reverse=True
)

def _etiqueta_periodo(p):
    y, m = p
    return f"{_MESES_ES[m - 1].capitalize()} {y}"

if _periodos_disponibles:
    _periodo_hoy = (arg_today.year, arg_today.month)
    _default_idx = (
        _periodos_disponibles.index(_periodo_hoy)
        if _periodo_hoy in _periodos_disponibles else 0
    )
    REF_YEAR, REF_MONTH = st.selectbox(
        "Mes a mostrar",
        _periodos_disponibles,
        index=_default_idx,
        format_func=_etiqueta_periodo,
        key="venta_diaria_mes_sel",
    )
else:
    REF_YEAR, REF_MONTH = arg_today.year, arg_today.month

# Año/mes "anterior" y "mismo mes año pasado", calculados a partir del mes
# elegido arriba (el en curso por defecto).
if REF_MONTH == 1:
    PREV_YEAR, PREV_MONTH = REF_YEAR - 1, 12
else:
    PREV_YEAR, PREV_MONTH = REF_YEAR, REF_MONTH - 1
LY_YEAR = REF_YEAR - 1

MES_ACTUAL_NOMBRE = _MESES_ES[REF_MONTH - 1].capitalize()
MES_ACTUAL_LABEL = f"{MES_ACTUAL_NOMBRE} {REF_YEAR}"
MES_ACTUAL_ABREV = _MESES_ABREV_ES[REF_MONTH - 1]
MES_ANTERIOR_ABREV = _MESES_ABREV_ES[PREV_MONTH - 1]

current = df[
    (df["date"].dt.year == REF_YEAR) &
    (df["date"].dt.month == REF_MONTH)
].copy().sort_values("date")

if current.empty:
    st.error(f"No hay datos de {MES_ACTUAL_NOMBRE.lower()} {REF_YEAR}.")
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
sunday_units = current[current["date"] == last_sunday]["units"].sum()

friday_orders = current[current["date"] == last_friday]["orders"].sum()
saturday_orders = current[current["date"] == last_saturday]["orders"].sum()
sunday_orders = current[current["date"] == last_sunday]["orders"].sum()

friday_company = current[current["date"] == last_friday]["company_tax"].sum()
saturday_company = current[current["date"] == last_saturday]["company_tax"].sum()
sunday_company = current[current["date"] == last_sunday]["company_tax"].sum()

# Fin de semana = Viernes + Sábado (no se suma el Domingo) — se usa en la card
# "VENTA DÍA ANTERIOR" de los lunes.
weekend = friday_sales + saturday_sales
weekend_units = friday_units + saturday_units

# Fin de semana completo (Viernes + Sábado + Domingo), para la pestaña
# "Venta fin de semana".
weekend_full_ecom = friday_sales + saturday_sales + sunday_sales
weekend_full_units = friday_units + saturday_units + sunday_units
weekend_full_orders = friday_orders + saturday_orders + sunday_orders
weekend_full_company = friday_company + saturday_company + sunday_company
weekend_full_share = (weekend_full_ecom / weekend_full_company) if weekend_full_company else 0
weekend_full_label = f"{last_friday.strftime('%d-%m')} al {last_sunday.strftime('%d-%m')}"

sales_label = "VENTA DÍA ANTERIOR"
if is_monday:
    # Los lunes no tomamos el domingo como "día anterior": usamos el sábado.
    sales_value = saturday_sales
else:
    sales_value = latest["ecommerce_tax"]
days_elapsed = len(current)
days_month = calendar.monthrange(REF_YEAR, REF_MONTH)[1]

acc_ecom = current["ecommerce_tax"].sum()
acc_company = current["company_tax"].sum()
acc_orders = current["orders"].sum()
acc_orders_entrega = current["orders_entrega_real"].sum()
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
    (df["date"].dt.year == PREV_YEAR) &
    (df["date"].dt.month == PREV_MONTH) &
    (df["date"].dt.day <= n)
].sort_values("date")

sep25 = df[
    (df["date"].dt.year == LY_YEAR) &
    (df["date"].dt.month == REF_MONTH) &
    (df["date"].dt.day <= n)
].sort_values("date")

aug_acc = aug["ecommerce_tax"].sum()
sep25_acc = sep25["ecommerce_tax"].sum()

vs_aug = (acc_ecom / aug_acc - 1) if aug_acc else None
vs_25 = (acc_ecom / sep25_acc - 1) if sep25_acc else None

# ---- Tiendas con más ventas del mes en curso (venta y pedidos) ----
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

# Mismo día que usa el resto del dashboard (variable `latest`, calculada más
# arriba a partir de `current`: el más reciente con datos, hoy incluido si
# ya está cargado), para que el cuadro "venta diaria" quede consistente.
latest_tienda_date = latest["date"]
tiendas_dia = pd.DataFrame(columns=["Tienda", "Nombre", "ecommerce_tax", "orders"])
if len(df_tiendas):
    filas_dia = df_tiendas[df_tiendas["date"] == latest_tienda_date]
    if len(filas_dia):
        # "Pedidos" en el Top 5 del DÍA usa "orders_entrega", que a su vez es
        # alias de "orders" — ambos por fecha de CREACIÓN del pedido, igual
        # que el Top 5 del MES (tiendas_resumen, más abajo) y que Comparativo.
        tiendas_dia = (
            filas_dia.groupby(["Tienda", "Nombre"], as_index=False)
            .agg(ecommerce_tax=("ecommerce_tax", "sum"), orders=("orders_entrega", "sum"))
        )

def top_tiendas(df_in, metric, n=5):
    if not len(df_in):
        return df_in.copy()
    return df_in.sort_values(metric, ascending=False).head(n).reset_index(drop=True)

top_venta_dia = top_tiendas(tiendas_dia, "ecommerce_tax", n=5)
top_venta_mes = top_tiendas(tiendas_resumen, "ecommerce_tax", n=5)

# ---- Venta por fin de semana del mes en curso ----
# Para la pestaña "Venta fin de semana": Fin de semana = Viernes + Sábado +
# Domingo (los tres días).
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

# ---- Comparación entre findes (pestaña "findesema") ----
# Usamos TODO el historial cargado (no solo el mes en curso) para poder
# comparar el finde más reciente contra el anterior aunque estemos al
# principio del mes y todavía no haya un segundo finde en septiembre.
findesema_rows = df[df["date"].dt.weekday.isin([4, 5, 6])].copy()
findesema_rows["finde_inicio"] = findesema_rows["date"] - pd.to_timedelta(
    (findesema_rows["date"].dt.weekday - 4) % 7, unit="D"
)
findesema_tabla = (
    findesema_rows.groupby("finde_inicio", as_index=False)
    .agg(
        venta=("ecommerce_tax", "sum"),
        company=("company_tax", "sum"),
        pedidos=("orders", "sum"),
        unidades=("units", "sum"),
    )
    .sort_values("finde_inicio")
    .reset_index(drop=True)
)

def _finde_rango(inicio):
    return f"{inicio.strftime('%d-%m')} al {(inicio + pd.Timedelta(days=2)).strftime('%d-%m')}"

if len(findesema_tabla) >= 1:
    finde_actual = findesema_tabla.iloc[-1]
    finde_actual_rango = _finde_rango(finde_actual["finde_inicio"])
else:
    finde_actual = None
    finde_actual_rango = ""

if len(findesema_tabla) >= 2:
    finde_anterior = findesema_tabla.iloc[-2]
    finde_anterior_rango = _finde_rango(finde_anterior["finde_inicio"])
    finde_vs_anterior = (
        (finde_actual["venta"] / finde_anterior["venta"]) - 1
        if finde_anterior["venta"] else None
    )
else:
    finde_anterior = None
    finde_anterior_rango = ""
    finde_vs_anterior = None

def money(v):
    """Número completo mientras esté por debajo del millón (ej. $213.945).
    De ahí en más, redondea y abrevia: 'M' (millones) entre 1 millón y
    999 millones, 'MM' (miles de millones) a partir de los mil millones.
    Así no queda ni un número gigante sin abreviar, ni una fracción de
    millón rara como '$0,21 M'."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "$0"
    av = abs(v)
    if av < 1_000_000:
        return f"${v:,.0f}".replace(",", ".")
    # Si al redondear a "M" el número llega a 1.000, mejor mostrarlo ya
    # como "MM" (ej. 999.999.999 -> "$1.000,00 M" se ve raro; "$1,00 MM" no).
    if av < 1_000_000_000 and round(av / 1_000_000, 3) < 1000:
        txt = f"${v/1_000_000:,.3f} M"
    else:
        txt = f"${v/1_000_000_000:,.3f} MM"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

def pct(v):
    return f"{v*100:.2f}%".replace(".", ",")

def pct_change(v):
    return f"{v:+.2%}".replace(".", ",")

def intfmt(v):
    return f"{int(v):,}".replace(",", ".")

share_daily = (latest["ecommerce_tax"] / latest["company_tax"]) if latest["company_tax"] else 0

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
    {MES_ACTUAL_LABEL}
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
    <div style="font-weight:800;font-size:16px;margin-top:6px;color:#20252b;">
      Participación del día: <span style="color:#2f9e66;">{pct(share_daily)}</span>
    </div>
    <div style="font-weight:800;font-size:16px;margin-top:4px;color:#20252b;">
      Pedidos del día: <span style="color:#e8432c;">{intfmt(latest["orders_entrega"])}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# RESUMEN EN IMAGEN (PNG): una tarjeta lista para compartir (WhatsApp,
# redes), con el resumen diario y mensual de Compañía vs eCommerce.
# Se dibuja con Pillow (no depende de un navegador), así que es liviana
# en memoria para Streamlit Cloud.
# ---------------------------------------------------------------------
_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
_RESUMEN_FONT_BOLD_PATH = _FONTS_DIR / "DejaVuSans-Bold.ttf"
_RESUMEN_FONT_REG_PATH = _FONTS_DIR / "DejaVuSans.ttf"


def _resumen_font(bold, size):
    candidatos = (
        [_RESUMEN_FONT_BOLD_PATH, _RESUMEN_FONT_REG_PATH]
        if bold else [_RESUMEN_FONT_REG_PATH, _RESUMEN_FONT_BOLD_PATH]
    )
    # Si no están los archivos en /fonts del repo, probamos rutas típicas
    # del sistema (pueden existir igual en el servidor), y si no, el font
    # genérico de Pillow para que la función nunca rompa la página.
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


def _resumen_icon_calendar(draw, cx, cy, size, color):
    r = size / 2
    box = [cx - r, cy - r * 0.85, cx + r, cy + r * 0.95]
    draw.rounded_rectangle(box, radius=4, outline=color, width=3)
    draw.line([box[0] + 3, box[1] + size * 0.28, box[2] - 3, box[1] + size * 0.28], fill=color, width=3)
    draw.line([cx - r * 0.5, box[1] - size * 0.12, cx - r * 0.5, box[1] + size * 0.12], fill=color, width=3)
    draw.line([cx + r * 0.5, box[1] - size * 0.12, cx + r * 0.5, box[1] + size * 0.12], fill=color, width=3)


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


def _resumen_icon_percent(draw, cx, cy, size, color):
    r = size * 0.5
    draw.line([cx - r * 0.55, cy + r * 0.55, cx + r * 0.55, cy - r * 0.55], fill=color, width=5)
    sr = size * 0.16
    draw.ellipse([cx - r * 0.55 - sr, cy - r * 0.55 - sr, cx - r * 0.55 + sr, cy - r * 0.55 + sr], fill=color)
    draw.ellipse([cx + r * 0.55 - sr, cy + r * 0.55 - sr, cx + r * 0.55 + sr, cy + r * 0.55 + sr], fill=color)


def generar_resumen_imagen(
    fecha_diaria_label, mes_label,
    daily_company, daily_ecom, daily_orders, daily_units, share_daily_v,
    mes_company, mes_ecom, mes_orders, mes_units, share_mes_v,
):
    W, H = 1600, 650
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

    f_title = _resumen_font(True, 30)
    f_subtitle = _resumen_font(True, 19)
    f_badge_label = _resumen_font(True, 15)
    f_badge_value = _resumen_font(True, 32)
    f_panel_header = _resumen_font(True, 21)
    f_panel_subheader = _resumen_font(True, 15)
    f_col_label = _resumen_font(True, 15)
    f_col_value = _resumen_font(True, 26)
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

    if logo_img is not None:
        lw, lh = logo_img.size
        target_h = 56
        target_w = int(lw * target_h / lh)
        logo_resized = logo_img.resize((target_w, target_h))
        img.paste(logo_resized, (48, 48), logo_resized)
    else:
        d.text((48, 58), "MásOnline", font=_resumen_font(True, 34), fill=C_TEXT_DARK)

    _resumen_text_center(d, W / 2 + 20, 48, "VENTAS COMPAÑÍA VS ECOMMERCE", f_title, C_TEXT_DARK)
    _resumen_text_center(d, W / 2 + 20, 86, "RESUMEN DE VENTAS", f_subtitle, C_BLUE)

    badge_box = [W - 310, 40, W - 48, 150]
    _resumen_rr(d, badge_box, 18, C_PINK_BG)
    _resumen_icon_calendar(d, badge_box[0] + 44, (badge_box[1] + badge_box[3]) / 2, 34, C_RED)
    _resumen_text_center(d, (badge_box[0] + badge_box[2]) / 2 + 24, badge_box[1] + 20, "DIARIO", f_badge_label, C_BLUE)
    _resumen_text_center(d, (badge_box[0] + badge_box[2]) / 2 + 24, badge_box[1] + 42, fecha_diaria_label, f_badge_value, C_TEXT_DARK)

    d.line([48, 172, W - 48, 172], fill=C_CARD_BORDER, width=2)

    panel_y0 = 200
    panel_y1 = 568
    gap = 24
    panel_w = (W - 48 * 2 - gap) / 2
    panels = [
        dict(
            x0=48, header_color=C_RED, header_lines=["VENTA DIARIA"],
            company=daily_company, ecom=daily_ecom, orders=daily_orders, units=daily_units,
            share=share_daily_v, share_label="SHARE ECOMMERCE DIARIO", bottom_bg=C_PINK_BG,
        ),
        dict(
            x0=48 + panel_w + gap, header_color=C_ORANGE, header_lines=["VENTA MENSUAL", mes_label],
            company=mes_company, ecom=mes_ecom, orders=mes_orders, units=mes_units,
            share=share_mes_v, share_label="SHARE ECOMMERCE MENSUAL", bottom_bg=C_CREAM_BG,
        ),
    ]

    header_h = 78
    bottom_h = 64

    for p in panels:
        x0 = p["x0"]
        x1 = x0 + panel_w

        _resumen_rr(d, [x0, panel_y0, x1, panel_y1], 16, "#ffffff")
        d.rounded_rectangle([x0, panel_y0, x1, panel_y1], radius=16, outline=C_CARD_BORDER, width=2)

        _resumen_rr(d, [x0, panel_y0, x1, panel_y0 + header_h], 16, p["header_color"], corners=(True, True, False, False))
        header_text_color = "#ffffff" if p["header_color"] == C_RED else C_TEXT_DARK
        cx = (x0 + x1) / 2
        if len(p["header_lines"]) == 1:
            _resumen_text_center(d, cx, panel_y0 + 24, p["header_lines"][0], f_panel_header, header_text_color)
        else:
            _resumen_text_center(d, cx, panel_y0 + 14, p["header_lines"][0], f_panel_header, header_text_color)
            _resumen_text_center(d, cx, panel_y0 + 44, p["header_lines"][1], f_panel_subheader, header_text_color)

        _resumen_rr(d, [x0, panel_y1 - bottom_h, x1, panel_y1], 16, p["bottom_bg"], corners=(False, False, True, True))

        body_top = panel_y0 + header_h
        pad = 34

        col_w = (panel_w - pad * 2 - 20) / 2
        colA_x = x0 + pad
        colB_x = x0 + pad + col_w + 20
        row1_y = body_top + 24

        d.text((colA_x, row1_y), "COMPAÑÍA", font=f_col_label, fill=C_GRAY)
        d.text((colB_x, row1_y), "ECOMMERCE", font=f_col_label, fill=C_RED)

        pill_y0 = row1_y + 26
        pill_h = 58
        _resumen_rr(d, [colA_x, pill_y0, colA_x + col_w, pill_y0 + pill_h], 12, C_BLUELIGHT_BG)
        _resumen_rr(d, [colB_x, pill_y0, colB_x + col_w, pill_y0 + pill_h], 12, C_PINK_BG)
        d.text((colA_x + 16, pill_y0 + 14), money(p["company"]), font=f_col_value, fill=C_TEXT_DARK)
        d.text((colB_x + 16, pill_y0 + 14), money(p["ecom"]), font=f_col_value, fill=C_RED)

        divider_y = pill_y0 + pill_h + 26
        d.line([x0 + pad, divider_y, x1 - pad, divider_y], fill=C_CARD_BORDER, width=2)

        row2_y = divider_y + 20
        icon_r = 26
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
        d.text((text_x_a, row2_y + 16), intfmt(p["orders"]), font=f_mini_value, fill=C_TEXT_DARK)
        d.text((text_x_b, row2_y - 2), "UNIDADES ECOMMERCE", font=f_mini_label, fill=C_GRAY)
        d.text((text_x_b, row2_y + 16), intfmt(p["units"]), font=f_mini_value, fill=C_TEXT_DARK)

        share_cy = panel_y1 - bottom_h / 2
        _resumen_icon_percent(d, x0 + pad + 10, share_cy, 26, C_RED)
        d.text((x0 + pad + 34, share_cy - 10), p["share_label"], font=f_share_label, fill=C_GRAY)
        val_txt = pct(p["share"])
        vw = _resumen_text_w(d, val_txt, f_share_value)
        d.text((x1 - pad - vw, share_cy - 13), val_txt, font=f_share_value, fill=C_RED)

    footer_y = 598
    if logo_img is not None:
        lw, lh = logo_img.size
        th = 22
        tw = int(lw * th / lh)
        small_logo = logo_img.resize((tw, th))
        img.paste(small_logo, (48, footer_y - 2), small_logo)
        fx = 48 + tw + 12
    else:
        d.text((48, footer_y), "MásOnline", font=_resumen_font(True, 18), fill=C_TEXT_DARK)
        fx = 48 + 110
    d.line([fx - 6, footer_y, fx - 6, footer_y + 20], fill=C_CARD_BORDER, width=2)
    d.text((fx + 6, footer_y + 2), "OPERACIONES ECOMMERCE", font=f_footer, fill=C_GRAY)

    foot_right = f"Datos con impuesto. Período: {mes_label.title()}."
    fw = _resumen_text_w(d, foot_right, f_footer_reg)
    d.text((W - 48 - fw, footer_y + 2), foot_right, font=f_footer_reg, fill=C_GRAY)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


try:
    _resumen_png_bytes = generar_resumen_imagen(
        fecha_diaria_label=latest["date"].strftime("%d-%m"),
        mes_label=f"{MES_ACTUAL_NOMBRE.upper()} {REF_YEAR}",
        daily_company=latest["company_tax"], daily_ecom=latest["ecommerce_tax"],
        daily_orders=latest["orders_entrega"], daily_units=latest["units"], share_daily_v=share_daily,
        mes_company=acc_company, mes_ecom=acc_ecom, mes_orders=acc_orders_entrega, mes_units=acc_units,
        share_mes_v=share,
    )
    st.download_button(
        "🖼️ Descargar resumen (imagen)",
        data=_resumen_png_bytes,
        file_name=f"resumen_ventas_{latest['date'].strftime('%Y%m%d')}.png",
        mime="image/png",
    )
except Exception as _e:
    st.caption(f"No pude armar la imagen de resumen ({_e}).")

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

    progress = min(share / target, 1.0) * 100

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

    def standalone_tienda_table(rows_df, titulo):
        header = f'<div class="rank-table-header">🏆 {html.escape(titulo)}</div>'
        if not len(rows_df):
            return (
                f'<div class="rank-table-card">{header}'
                '<div style="padding:20px;color:#9ca3af;font-size:13px;">'
                'Todavía no hay datos por tienda para este período.</div></div>'
            )
        rows_html = ""
        for i, r in enumerate(rows_df.itertuples(), start=1):
            nombre = str(r.Nombre) if r.Nombre else ""
            tienda_label = f"{r.Tienda} - {nombre}" if nombre else str(r.Tienda)
            rows_html += (
                '<tr>'
                f'<td><span class="rank-badge">{i}</span></td>'
                f'<td>{html.escape(tienda_label)}</td>'
                f'<td style="text-align:center;">{intfmt(r.orders)}</td>'
                f'<td style="text-align:right;font-weight:800;color:#208653;">{html.escape(money(r.ecommerce_tax))}</td>'
                '</tr>'
            )
        return (
            f'<div class="rank-table-card">{header}'
            '<table class="rank-table"><thead><tr>'
            '<th></th><th>Tienda</th>'
            '<th style="text-align:center;">Pedidos eCommerce</th>'
            '<th style="text-align:right;">Venta eCommerce (con impuesto)</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table></div>'
        )

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
.rank-tables {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}}
.rank-table-card {{
    background: white;
    border: 1px solid #e8ebef;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
}}
.rank-table-header {{
    background: #2f9e66;
    color: #fff;
    font-weight: 800;
    font-size: 15px;
    padding: 13px 20px;
}}
table.rank-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
table.rank-table thead th {{
    text-align: left;
    padding: 9px 12px;
    color: #6b7280;
    font-size: 11.5px;
    text-transform: uppercase;
    border-bottom: 1px solid #e8ebef;
}}
table.rank-table td {{ padding: 8px 12px; border-bottom: 1px solid #eef0ef; }}
.rank-badge {{
    display: inline-block;
    min-width: 20px;
    text-align: center;
    background: #2f9e66;
    color: #fff;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    padding: 2px 6px;
}}
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
    .kpis, .comparisons, .rank-tables {{ grid-template-columns: 1fr; }}
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
    {MES_ACTUAL_LABEL}
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
    <div style="font-weight:800;font-size:16px;margin-top:6px;color:#20252b;">
      Participación del día: <span style="color:#2f9e66;">{html.escape(pct(share_daily))}</span>
    </div>
    <div style="font-weight:800;font-size:16px;margin-top:4px;color:#20252b;">
      Pedidos del día: <span style="color:#e8432c;">{html.escape(intfmt(latest["orders_entrega"]))}</span>
    </div>
  </div>
</div>

<div class="kpis">

<div class="card" style="border-top:4px solid #f5a623;">
  <div class="label" style="color:#f5a623;">PARTICIPACIÓN E-COMMERCE</div>
  <div class="value">{html.escape(pct(share))}</div>
  <div class="small">Objetivo: 3,00% · Brecha: {gap*100:.2f} pp</div>
</div>

<div class="card" style="border-top:4px solid #e8432c;">
<div class="label" style="color:#e8432c;">{sales_label}</div>
<div class="value" style="color:#e8432c;">{html.escape(money(sales_value))}</div>
  <div class="small">Vs día previo: {html.escape(pct_change(day_change))}</div>
</div>

<div class="card" style="border-top:4px solid #59636e;">
  <div class="label">MES EN CURSO</div>
  <div class="value">{html.escape(money(acc_ecom))}</div>
  <div class="small">{int(acc_orders_entrega):,} pedidos · {int(acc_units):,} unidades</div>
</div>

<div class="card" style="border-top:4px solid #2f9e66;">
  <div class="label" style="color:#208653;">PROYECCIÓN DE CIERRE</div>
  <div class="value" style="color:#208653;">{html.escape(money(projection))}</div>
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
      {html.escape(f"{share/target:.0%}")}
      <small>del objetivo</small>
    </div>
  </div>
</div>

<div class="section">Top 5 tiendas eCommerce</div>
<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">
Ranking por venta ecommerce, con pedidos de cada tienda.
</div>
<div class="rank-tables">
{standalone_tienda_table(top_venta_dia, f"VENTA DIARIA · TOP 5 ({latest_tienda_date.strftime('%d/%m')})")}
{standalone_tienda_table(top_venta_mes, "VENTA MENSUAL · TOP 5")}
</div>

<div class="section">Comparaciones</div>
<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">
Variación de ventas e-commerce sobre la misma cantidad de días
</div>

<div class="comparisons">
{standalone_compare(
    "VS MES ANTERIOR",
    vs_aug,
    f"{MES_ACTUAL_ABREV} 1–{n} {REF_YEAR} vs {MES_ANTERIOR_ABREV} 1–{n} {PREV_YEAR}"
)}
{standalone_compare(
    "VS MISMO MES AÑO ANTERIOR",
    vs_25,
    f"{MES_ACTUAL_ABREV} 1–{n} {REF_YEAR} vs {MES_ACTUAL_ABREV} 1–{n} {LY_YEAR}"
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard completo",
    "📤 Resumen para GDN",
    "📅 Venta fin de semana",
    "findesema",
])

with tab1:
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
        <div class="card" style="border-top:4px solid #e8432c;">
          <div class="label" style="color:#e8432c;">{sales_label}</div>
    <div class="value" style="color:#e8432c;">{money(sales_value)}</div>
          <div class="small">Vs día previo: {pct_change(day_change)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #59636e;">
          <div class="label">MES EN CURSO</div>
          <div class="value">{money(acc_ecom)}</div>
          <div class="small">{intfmt(acc_orders_entrega)} pedidos · {intfmt(acc_units)} unidades</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #2f9e66;">
          <div class="label" style="color:#208653;">PROYECCIÓN DE CIERRE</div>
          <div class="value" style="color:#208653;">{money(projection)}</div>
          <div class="small">Promedio diario × {days_month} días</div>
        </div>
        """, unsafe_allow_html=True)

    progress = min(share / target, 1.0) * 100

    st.markdown('<div class="section">Avance de participación</div>', unsafe_allow_html=True)
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
          {f"{share/target:.0%}"}
          <small>del objetivo</small>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Resumen visual: Compañía vs Ecommerce (Diario / Mensual) ----
    share_daily = (latest["ecommerce_tax"] / latest["company_tax"]) if latest["company_tax"] else 0

    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;margin-top:20px;">
      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
          DIARIO &nbsp;|&nbsp; {latest["date"].strftime("%d-%m")}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(latest["company_tax"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(latest["ecommerce_tax"])}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["orders_entrega"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["units"])}</div>
            </div>
          </div>
        </div>
        <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE DIARIO</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_daily)}</span>
        </div>
      </div>

      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
          MENSUAL &nbsp;{MES_ACTUAL_NOMBRE.upper()} {REF_YEAR}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
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
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_orders_entrega)}</div>
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

    def tienda_rank_table_html(rows_df, titulo, empty_msg=None):
        # Nota: el HTML se arma en una sola línea por elemento (sin saltos de
        # línea indentados) porque Streamlit interpreta texto indentado con
        # 4+ espacios después de un salto de línea como bloque de código, y
        # lo muestra como texto plano en vez de renderizarlo.
        header = (
            '<div style="background:#2f9e66;color:#fff;font-weight:800;'
            'font-size:15px;padding:13px 20px;display:flex;align-items:center;gap:10px;">'
            f'<span>🏆</span><span>{titulo}</span>'
            '</div>'
        )
        if empty_msg is None:
            empty_msg = (
                'Todavía no hay datos por tienda para este período. Se completa '
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

    st.markdown('<div class="section">Top 5 tiendas eCommerce</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">'
        'Ranking por venta ecommerce, con pedidos de cada tienda.'
        '</div>',
        unsafe_allow_html=True
    )

    td1, td2 = st.columns(2)
    with td1:
        st.markdown(
            tienda_rank_table_html(
                top_venta_dia,
                f"VENTA DIARIA · TOP 5 ({latest_tienda_date.strftime('%d/%m')})",
                empty_msg=(
                    'Todavía no hay datos por tienda para el último día cargado. '
                    'Se completa automáticamente la próxima vez que se suba el Excel '
                    'desde "app" (si trae las columnas Tienda y Nombre).'
                ),
            ),
            unsafe_allow_html=True
        )
    with td2:
        st.markdown(
            tienda_rank_table_html(
                top_venta_mes,
                "VENTA MENSUAL · TOP 5",
                empty_msg=(
                    'Todavía no hay datos por tienda para el mes en curso. '
                    'Se completa automáticamente la próxima vez que se suba el Excel '
                    'desde "app" (si trae las columnas Tienda y Nombre).'
                ),
            ),
            unsafe_allow_html=True
        )

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
                    f"{MES_ACTUAL_ABREV} 1–{n} {REF_YEAR} vs {MES_ANTERIOR_ABREV} 1–{n} {PREV_YEAR}"
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
                    f"{MES_ACTUAL_ABREV} 1–{n} {REF_YEAR} vs {MES_ACTUAL_ABREV} 1–{n} {LY_YEAR}"
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

with tab2:
    st.markdown('<div class="section">Resumen para GDN</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
        'Capturá esta card y enviala directo — sin tocar el resto del dashboard.'
        '</div>',
        unsafe_allow_html=True
    )

    share_daily_gdn = (latest["ecommerce_tax"] / latest["company_tax"]) if latest["company_tax"] else 0

    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;">
      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
          DIARIO &nbsp;|&nbsp; {latest["date"].strftime("%d-%m")}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(latest["company_tax"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
              <div style="font-size:11px;color:#9ca3af;">VENTA DIARIA</div>
              <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(latest["ecommerce_tax"])}</div>
            </div>
          </div>
          <div style="border-top:1px solid #eee;margin:14px 0;"></div>
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["orders_entrega"])}</div>
            </div>
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(latest["units"])}</div>
            </div>
          </div>
        </div>
        <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE DIARIO</span>
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_daily_gdn)}</span>
        </div>
      </div>

      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
          MENSUAL &nbsp;{MES_ACTUAL_NOMBRE.upper()} {REF_YEAR}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
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
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_orders_entrega)}</div>
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


with tab3:
    st.markdown('<div class="section">Fin de semana vs. acumulado</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
        'Fin de semana = Viernes + Sábado + Domingo.'
        '</div>',
        unsafe_allow_html=True
    )

    share_weekend_daily_style = weekend_full_share

    st.markdown(f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;">
      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
          FIN DE SEMANA &nbsp;|&nbsp; {weekend_full_label}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
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
          <div style="display:flex;gap:12px;">
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
          <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_weekend_daily_style)}</span>
        </div>
      </div>

      <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
        <div style="background:#f5a623;color:#20252b;font-weight:800;font-size:15px;padding:12px 16px;">
          MENSUAL &nbsp;{MES_ACTUAL_NOMBRE.upper()} {REF_YEAR}
        </div>
        <div style="padding:18px 16px;">
          <div style="display:flex;gap:12px;">
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
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
              <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(acc_orders_entrega)}</div>
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
            finde_rows_html += (
                '<tr style="border-top:1px solid #eee;">'
                f'<td style="padding:10px 14px;color:#20252b;">{r["rango"]}</td>'
                f'<td style="padding:10px 14px;font-weight:700;color:#e8432c;">{money(r["venta"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{intfmt(r["pedidos"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{intfmt(r["unidades"])}</td>'
                f'<td style="padding:10px 14px;color:#20252b;">{pct(r["participacion"])}</td>'
                '</tr>'
            )

        st.markdown(f"""
        <div class="table-scroll" style="background:white;border:1px solid #e8ebef;border-radius:14px;overflow-x:auto;box-shadow:0 2px 10px rgba(0,0,0,.06);">
          <table style="width:100%;border-collapse:collapse;font-size:13px;min-width:520px;">
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

with tab4:
    st.markdown('<div class="section">Comparación entre fines de semana</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
        'Fin de semana = Viernes + Sábado + Domingo. Se compara el finde más reciente '
        'contra el finde anterior.'
        '</div>',
        unsafe_allow_html=True
    )

    if finde_actual is None:
        st.markdown(
            '<div class="upload-box"><div class="upload-text">'
            'Todavía no hay ningún fin de semana cargado.'
            '</div></div>',
            unsafe_allow_html=True
        )
    else:
        share_finde_actual = (
            (finde_actual["venta"] / finde_actual["company"])
            if finde_actual["company"] else 0
        )

        if finde_anterior is not None:
            share_finde_anterior = (
                (finde_anterior["venta"] / finde_anterior["company"])
                if finde_anterior["company"] else 0
            )
            card_anterior_html = f"""
              <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
                <div style="background:#59636e;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
                  FIN DE SEMANA ANTERIOR &nbsp;|&nbsp; {finde_anterior_rango}
                </div>
                <div style="padding:18px 16px;">
                  <div style="display:flex;gap:12px;">
                    <div style="flex:1;">
                      <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
                      <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                      <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(finde_anterior["company"])}</div>
                    </div>
                    <div style="flex:1;">
                      <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
                      <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                      <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(finde_anterior["venta"])}</div>
                    </div>
                  </div>
                  <div style="border-top:1px solid #eee;margin:14px 0;"></div>
                  <div style="display:flex;gap:12px;">
                    <div style="flex:1;">
                      <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
                      <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_anterior["pedidos"])}</div>
                    </div>
                    <div style="flex:1;">
                      <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
                      <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_anterior["unidades"])}</div>
                    </div>
                  </div>
                </div>
                <div style="background:#eef0f2;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE</span>
                  <span style="font-size:20px;font-weight:800;color:#59636e;">{pct(share_finde_anterior)}</span>
                </div>
              </div>
            """
        else:
            card_anterior_html = """
              <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);display:flex;align-items:center;justify-content:center;padding:20px;">
                <div style="color:#9ca3af;font-size:13px;text-align:center;">Sin fin de semana anterior cargado todavía.</div>
              </div>
            """

        st.markdown(f"""
        <div style="display:flex;flex-wrap:wrap;gap:16px;">
          <div style="flex:1;min-width:260px;background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e8ebef;box-shadow:0 2px 10px rgba(0,0,0,.06);">
            <div style="background:#e8432c;color:#fff;font-weight:800;font-size:15px;padding:12px 16px;">
              FIN DE SEMANA ACTUAL &nbsp;|&nbsp; {finde_actual_rango}
            </div>
            <div style="padding:18px 16px;">
              <div style="display:flex;gap:12px;">
                <div style="flex:1;">
                  <div style="font-size:12px;font-weight:700;color:#6b7280;">COMPAÑÍA</div>
                  <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                  <div style="font-size:22px;font-weight:800;color:#20252b;margin-top:2px;">{money(finde_actual["company"])}</div>
                </div>
                <div style="flex:1;">
                  <div style="font-size:12px;font-weight:700;color:#e8432c;">ECOMMERCE</div>
                  <div style="font-size:11px;color:#9ca3af;">VENTA FIN DE SEMANA</div>
                  <div style="font-size:22px;font-weight:800;color:#e8432c;margin-top:2px;">{money(finde_actual["venta"])}</div>
                </div>
              </div>
              <div style="border-top:1px solid #eee;margin:14px 0;"></div>
              <div style="display:flex;gap:12px;">
                <div style="flex:1;">
                  <div style="font-size:11px;color:#9ca3af;">PEDIDOS</div>
                  <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_actual["pedidos"])}</div>
                </div>
                <div style="flex:1;">
                  <div style="font-size:11px;color:#9ca3af;">UNIDADES</div>
                  <div style="font-size:18px;font-weight:700;color:#20252b;">{intfmt(finde_actual["unidades"])}</div>
                </div>
              </div>
            </div>
            <div style="background:#fdeceb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:12px;font-weight:700;color:#6b7280;">SHARE ECOMMERCE</span>
              <span style="font-size:20px;font-weight:800;color:#e8432c;">{pct(share_finde_actual)}</span>
            </div>
          </div>

          {card_anterior_html}
        </div>
        """, unsafe_allow_html=True)

        if finde_vs_anterior is not None:
            st.markdown('<div class="section">Variación vs. finde anterior</div>', unsafe_allow_html=True)
            st.markdown(
                compare_box(
                    "VENTA ECOMMERCE FIN DE SEMANA",
                    finde_vs_anterior,
                    f"{finde_actual_rango} vs {finde_anterior_rango}"
                ),
                unsafe_allow_html=True
            )

    st.markdown(
        '<div class="footer">'
        '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
        '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
        '</div>',
        unsafe_allow_html=True
    )
