import streamlit as st
import pandas as pd
import calendar
import tempfile
import io
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import html
from PIL import Image, ImageDraw, ImageFont

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
_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
_RESUMEN_FONT_BOLD_PATH = _FONTS_DIR / "DejaVuSans-Bold.ttf"
_RESUMEN_FONT_REG_PATH = _FONTS_DIR / "DejaVuSans.ttf"

try:
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

# ---------------------------------------------------------------------
# Pedidos: igual que en Venta diaria (Dashboard de Ventas), de acá en más
# salen de "Vs de ventas" contados por fecha de CREACIÓN (commerceDateCreated)
# en vez de la columna "orders" de data.csv ("Pedidos Facturados"). Esto es
# para que esta página coincida con el número de Venta diaria — "Pedidos
# Facturados" se sigue completando varios días después de cargado el
# archivo, así que sin este reemplazo los dos terminaban mostrando números
# distintos para el mismo mes. Si para alguna fecha puntual "Vs de ventas"
# todavía no tiene datos, se usa como respaldo el valor viejo de "orders",
# para no quedarse sin número ese día.
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


def _pedidos_es_hoja_detalle(d):
    return _PEDIDOS_RAW_COLS.issubset(set(d.columns))


def _pedidos_adaptar_hoja_detalle(d):
    d = d.copy()
    es_pm = d["salesChannelPrefix"].astype(str).str.strip().str.upper() == "PM"
    es_rma = d["commerceId"].astype(str).str.upper().str.contains("RMA", na=False)
    d = d[~es_pm & ~es_rma & d["commerceSequentialId"].notna()]
    # El archivo a veces trae el mismo pedido repetido (filas idénticas, más
    # de una vez de punta a punta) — nos quedamos con un solo registro por
    # pedido (commerceSequentialId) para no duplicar el conteo.
    d = d.drop_duplicates(subset=["commerceSequentialId"])
    out = pd.DataFrame({
        "date": pd.to_datetime(d["commerceDateCreated"], errors="coerce").dt.normalize(),
        "pedidos": 1,
    })
    return out


def _pedidos_es_hoja_vieja(d):
    return {"Fecha", "Tienda", _COL_PEDIDOS_VIEJO}.issubset(set(d.columns))


def _pedidos_adaptar_hoja_vieja(d):
    # La hoja vieja (formato agregado, años anteriores) solo trae una fecha
    # por fila (de creación y entrega, no se distinguen).
    d = d.copy()
    out = pd.DataFrame({
        "date": pd.to_datetime(d["Fecha"], errors="coerce").dt.normalize(),
        "pedidos": pd.to_numeric(d[_COL_PEDIDOS_VIEJO], errors="coerce").fillna(0),
    })
    return out


@st.cache_data(ttl=180, show_spinner=False)
def _cargar_pedidos_vsventas_dia(vsventas_bytes):
    """Lee 'Vs de ventas' y arma el total de pedidos por día, contados por
    fecha de CREACIÓN del pedido (igual que Venta diaria)."""
    vacio = pd.DataFrame(columns=["date", "orders_vsventas"])
    if not vsventas_bytes:
        return vacio
    try:
        xl = pd.ExcelFile(io.BytesIO(vsventas_bytes))
        partes = []
        for sheet in xl.sheet_names:
            d = xl.parse(sheet)
            d.columns = [str(c).strip() for c in d.columns]
            if _pedidos_es_hoja_detalle(d):
                partes.append(_pedidos_adaptar_hoja_detalle(d))
            elif _pedidos_es_hoja_vieja(d):
                partes.append(_pedidos_adaptar_hoja_vieja(d))
        if not partes:
            return vacio
        todo = pd.concat(partes, ignore_index=True, sort=False)
    except Exception:
        return vacio
    base = todo.dropna(subset=["date"])
    return (
        base.groupby("date", as_index=False)["pedidos"].sum()
        .rename(columns={"pedidos": "orders_vsventas"})
    )


_vsventas_bytes_pedidos = _pedidos_get_shared_bytes(SHARED_VSVENTAS_PATH_PEDIDOS)
_pedidos_dia_vs = _cargar_pedidos_vsventas_dia(_vsventas_bytes_pedidos)

df = df.rename(columns={"orders": "orders_facturados"})
df = df.merge(_pedidos_dia_vs, on="date", how="left")
df["orders"] = df["orders_vsventas"].where(df["orders_vsventas"].notna(), df["orders_facturados"])
df = df.drop(columns=["orders_vsventas"])
# ---------------------------------------------------------------------

# Esta página muestra la misma info de fin de semana que ya está en la
# pestaña "Venta fin de semana" del Dashboard de Ventas. Los datos se
# actualizan subiendo los Excels ahí — acá solo se leen y se muestran.
# Se excluye siempre el día de HOY: la venta de ese día todavía no cerró en
# tienda (sigue sumando durante el día), así que se muestra recién al otro
# día, cuando ya está cerrada y es un número final.

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
df = df[df["date"].dt.date < arg_today].copy()

REF_YEAR, REF_MONTH = arg_today.year, arg_today.month

_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MES_ACTUAL_NOMBRE = _MESES_ES[REF_MONTH - 1].capitalize()
MES_ACTUAL_LABEL = f"{MES_ACTUAL_NOMBRE} {REF_YEAR}"

current = df[
    (df["date"].dt.year == REF_YEAR) &
    (df["date"].dt.month == REF_MONTH)
].copy().sort_values("date")

if current.empty:
    st.error(f"No hay datos de {MES_ACTUAL_NOMBRE.lower()} {REF_YEAR} todavía. Subilos desde la página del Dashboard de Ventas.")
    st.stop()

latest = current.iloc[-1]
days_month = calendar.monthrange(REF_YEAR, REF_MONTH)[1]
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
# alrededor), sin asumir que "hoy" es un día en particular. La venta del
# domingo se suma a la del sábado (no se pierde), pero el domingo nunca se
# muestra como tal en ningún lado de la página — ni como fila propia, ni
# en los rangos de fecha, ni en ninguna etiqueta.
last_data_date = current["date"].max()
days_since_saturday = (last_data_date.weekday() - 5) % 7  # Monday=0 ... Saturday=5, Sunday=6
last_saturday = last_data_date - pd.Timedelta(days=days_since_saturday)
last_friday = last_saturday - pd.Timedelta(days=1)
last_sunday = last_saturday + pd.Timedelta(days=1)

friday_sales = current[current["date"] == last_friday]["ecommerce_tax"].sum()
saturday_sales = (
    current[current["date"].isin([last_saturday, last_sunday])]["ecommerce_tax"].sum()
)

friday_units = current[current["date"] == last_friday]["units"].sum()
saturday_units = (
    current[current["date"].isin([last_saturday, last_sunday])]["units"].sum()
)

friday_orders = current[current["date"] == last_friday]["orders"].sum()
saturday_orders = (
    current[current["date"].isin([last_saturday, last_sunday])]["orders"].sum()
)

friday_company = current[current["date"] == last_friday]["company_tax"].sum()
saturday_company = (
    current[current["date"].isin([last_saturday, last_sunday])]["company_tax"].sum()
)

# "Fin de semana" para esta página = Viernes + Sábado, pero el número del
# Sábado ya trae adentro lo que se vendió el domingo (sumado arriba).
weekend_full_ecom = friday_sales + saturday_sales
weekend_full_units = friday_units + saturday_units
weekend_full_orders = friday_orders + saturday_orders
weekend_full_company = friday_company + saturday_company
weekend_full_share = (weekend_full_ecom / weekend_full_company) if weekend_full_company else 0
weekend_full_label = f"{last_friday.strftime('%d-%m')} al {last_sunday.strftime('%d-%m')}"

# ---- Venta por fin de semana del mes en curso ----
# finde_rows incluye el domingo (weekday 6) para que su venta entre en la
# suma del fin de semana — pero el domingo se va a fusionar con el sábado
# más abajo, antes de mostrar nada, así que nunca aparece como fila propia.
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
    lambda d: f"Vie {d.strftime('%d/%m')} – Sáb {(d + pd.Timedelta(days=1)).strftime('%d/%m')}"
)
finde_tabla["participacion"] = (
    finde_tabla["venta"] / acc_ecom if acc_ecom else 0
)

# ---- Mismo período, abierto día por día (Viernes/Sábado) ----
# El domingo no se muestra como fila aparte: su venta se suma a la fila
# del sábado del mismo fin de semana, sin dejar rastro de que ese número
# incluye el domingo.
DIA_NOMBRE = {4: "Viernes", 5: "Sábado", 6: "Domingo"}
detalle_dia = finde_rows.copy().sort_values("date")
detalle_dia["dia_nombre"] = detalle_dia["date"].dt.weekday.map(DIA_NOMBRE)
detalle_dia["rango"] = detalle_dia["finde_inicio"].apply(
    lambda d: f"Vie {d.strftime('%d/%m')} – Sáb {(d + pd.Timedelta(days=1)).strftime('%d/%m')}"
)

_domingo_sums = (
    detalle_dia[detalle_dia["date"].dt.weekday == 6]
    .groupby("finde_inicio")[["ecommerce_tax", "orders", "units"]]
    .sum()
    .rename(columns=lambda c: f"{c}_dom")
)
detalle_dia = detalle_dia[detalle_dia["date"].dt.weekday != 6].merge(
    _domingo_sums, on="finde_inicio", how="left"
)
_es_sabado = detalle_dia["dia_nombre"] == "Sábado"
for _col in ["ecommerce_tax", "orders", "units"]:
    detalle_dia[_col] = detalle_dia[_col] + detalle_dia[f"{_col}_dom"].fillna(0) * _es_sabado
detalle_dia = detalle_dia.drop(columns=["ecommerce_tax_dom", "orders_dom", "units_dom"])

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

def intfmt(v):
    return f"{int(v):,}".replace(",", ".")

def render_finde_cards_html(finde_tabla, detalle_dia):
    """Una tarjeta por fin de semana: arriba el rango de fechas, abajo la
    info de Viernes y después Sábado (no se toma el domingo)."""
    if not len(finde_tabla):
        return (
            '<div class="upload-box"><div class="upload-text">'
            'Todavía no hay ningún fin de semana (viernes y sábado) cargado este mes.'
            '</div></div>'
        )
    orden_dia = {"Viernes": 0, "Sábado": 1}
    cards = ""
    for _, wknd in finde_tabla.iterrows():
        dias_finde = (
            detalle_dia[detalle_dia["rango"] == wknd["rango"]]
            .copy()
        )
        dias_finde["orden"] = dias_finde["dia_nombre"].map(orden_dia)
        dias_finde = dias_finde.sort_values("orden")

        filas_dias = ""
        for _, d in dias_finde.iterrows():
            filas_dias += (
                '<div style="display:flex;justify-content:space-between;align-items:baseline;'
                'padding:9px 0;border-top:1px solid #eef0ef;">'
                f'<span style="font-weight:700;color:#20252b;font-size:13.5px;">'
                f'{d["dia_nombre"]} <span style="font-weight:400;color:#6b7280;">{d["date"].strftime("%d/%m")}</span></span>'
                f'<span style="font-size:13px;color:#20252b;">'
                f'<b style="color:#e8432c;">{money(d["ecommerce_tax"])}</b>'
                f' · {intfmt(d["orders"])} pedidos · {intfmt(d["units"])} unidades</span>'
                '</div>'
            )
        cards += f"""
        <div class="card" style="border-top:4px solid #e8432c;margin-bottom:14px;min-height:0;">
          <div class="label" style="color:#e8432c;">{wknd["rango"].upper()}</div>
          <div style="margin-top:4px;">{filas_dias}</div>
        </div>
        """
    return cards

# ---------------------------------------------------------------------
# Resumen descargable como IMAGEN (PNG) — mismo estilo que el botón
# "Descargar resumen (imagen)" de Venta diaria, armado a mano con Pillow
# (sin depender de nada fuera de Streamlit). Acá en vez de Diario/Mensual
# muestra Fin de semana (Viernes + Sábado + Domingo) / Acumulado del mes.
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


def generar_resumen_imagen_finde(
    finde_label, mes_label,
    finde_company, finde_ecom, finde_orders, finde_units, share_finde_v,
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

    _resumen_text_center(d, W / 2 + 20, 48, "VENTA FIN DE SEMANA", f_title, C_TEXT_DARK)
    _resumen_text_center(d, W / 2 + 20, 86, "RESUMEN DE VENTAS", f_subtitle, C_BLUE)

    # El badge es más ancho que el de Venta diaria porque acá el valor es un
    # RANGO de fechas ("17-10 al 19-10", Viernes a Domingo) en vez de un solo
    # día — con el ancho de Venta diaria, ese texto más largo se superponía
    # con el ícono de calendario.
    badge_box = [W - 460, 40, W - 48, 150]
    _resumen_rr(d, badge_box, 18, C_PINK_BG)
    _resumen_icon_calendar(d, badge_box[0] + 44, (badge_box[1] + badge_box[3]) / 2, 34, C_RED)
    _resumen_text_center(d, (badge_box[0] + badge_box[2]) / 2 + 24, badge_box[1] + 20, "FIN DE SEMANA", f_badge_label, C_BLUE)
    _resumen_text_center(d, (badge_box[0] + badge_box[2]) / 2 + 24, badge_box[1] + 42, finde_label, f_badge_value, C_TEXT_DARK)

    d.line([48, 172, W - 48, 172], fill=C_CARD_BORDER, width=2)

    panel_y0 = 200
    panel_y1 = 568
    gap = 24
    panel_w = (W - 48 * 2 - gap) / 2
    panels = [
        dict(
            x0=48, header_color=C_RED, header_lines=["FIN DE SEMANA", finde_label],
            company=finde_company, ecom=finde_ecom, orders=finde_orders, units=finde_units,
            share=share_finde_v, share_label="PARTICIPACIÓN DEL FINDE", bottom_bg=C_PINK_BG,
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
    {MES_ACTUAL_LABEL}
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
    <div style="font-weight:800;font-size:16px;margin-top:6px;color:#20252b;">
      Participación del finde: <span style="color:#2f9e66;">{pct(weekend_full_share)}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

try:
    _resumen_png_bytes_finde = generar_resumen_imagen_finde(
        finde_label=weekend_full_label,
        mes_label=f"{MES_ACTUAL_NOMBRE.upper()} {REF_YEAR}",
        finde_company=weekend_full_company, finde_ecom=weekend_full_ecom,
        finde_orders=weekend_full_orders, finde_units=weekend_full_units, share_finde_v=weekend_full_share,
        mes_company=acc_company, mes_ecom=acc_ecom, mes_orders=acc_orders, mes_units=acc_units,
        share_mes_v=share,
    )
    st.download_button(
        "🖼️ Descargar resumen (imagen)",
        data=_resumen_png_bytes_finde,
        file_name=f"resumen_finde_{last_saturday.strftime('%Y%m%d')}.png",
        mime="image/png",
        use_container_width=True,
    )
except Exception as _e:
    st.caption(f"No pude armar la imagen de resumen ({_e}).")

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
            'Todavía no hay ningún fin de semana (viernes y sábado) cargado este mes.'
            '</div></div>'
        )

    detalle_tabla_html = render_finde_cards_html(finde_tabla, detalle_dia)

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
    {MES_ACTUAL_LABEL}
    <small>Datos acumulados al {latest["date"].strftime("%d/%m/%Y")}</small>
    <div style="font-weight:800;font-size:16px;margin-top:6px;color:#20252b;">
      Participación del finde: <span style="color:#2f9e66;">{pct(weekend_full_share)}</span>
    </div>
  </div>
</div>

<div class="section">Fin de semana vs. acumulado</div>
<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">Fin de semana = Viernes + Sábado + Domingo.</div>

<div class="kpis">

<div class="card" style="border-top:4px solid #e8432c;">
  <div class="label" style="color:#e8432c;">VENTA FIN DE SEMANA</div>
  <div class="value" style="color:#e8432c;">{html.escape(money(weekend_full_ecom))}</div>
  <div class="small">{html.escape(weekend_full_label)} · {intfmt(weekend_full_orders)} pedidos · Cía: {html.escape(money(weekend_full_company))}</div>
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

<div class="section">Detalle por día</div>
<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:12px;">Mismo período de arriba, abierto día por día (viernes y sábado de cada fin de semana).</div>
{detalle_tabla_html}

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
      <div class="small">{weekend_full_label} · {intfmt(weekend_full_orders)} pedidos · Cía: {money(weekend_full_company)}</div>
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
        'Todavía no hay ningún fin de semana (viernes y sábado) cargado este mes.'
        '</div></div>',
        unsafe_allow_html=True
    )

st.markdown('<div class="section">Detalle por día</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="color:#6b7280;font-size:13px;margin-top:-8px;margin-bottom:16px;">'
    'Mismo período de arriba, abierto día por día (viernes y sábado de cada fin de semana).'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(render_finde_cards_html(finde_tabla, detalle_dia), unsafe_allow_html=True)

st.markdown(
    '<div class="footer">'
    '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
    '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
    '</div>',
    unsafe_allow_html=True
)
