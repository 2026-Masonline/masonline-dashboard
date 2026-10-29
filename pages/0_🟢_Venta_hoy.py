import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import tempfile
import io
import re
import html

st.set_page_config(
    page_title="MásOnline | Venta hoy",
    page_icon="🟢",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #ffffff; }
    .block-container { max-width: 1200px; padding: 0 1.2rem 1.2rem; }

    .hero {
        background: #ffffff;
        margin: -1rem -1.2rem 1.2rem;
        padding: 22px 28px;
        color: #20252b;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 4px solid #2f9e66;
    }
    .hero-brand { font-size: 30px; font-weight: 800; letter-spacing: -.5px; }
    .hero-brand span { font-weight: 400; }
    .hero-sub { font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }
    .hero-date { text-align: right; font-size: 19px; font-weight: 800; }
    .hero-date small { display: block; font-size: 12px; font-weight: 400; margin-top: 4px; opacity: .8; }

    .live-badge {
        display: inline-block; font-size: 11px; font-weight: 800; color: #e8432c;
        background: #fdeceb; padding: 3px 12px; border-radius: 20px; margin-top: 6px;
    }

    .card {
        background: white; border-radius: 14px; padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        min-height: 110px; border: 1px solid #e8ebef;
    }
    .label { color: #6b7280; font-size: 14px; font-weight: 700; }
    .value { color: #20252b; font-size: 30px; font-weight: 800; margin-top: 7px; }
    .small { color: #20252b; font-size: 13px; font-weight: 700; margin-top: 7px; }

    .section { font-size: 20px; font-weight: 800; color: #20252b; margin: 26px 0 12px; }
    .section-desc { color:#6b7280; font-size:13px; margin-top:-8px; margin-bottom:12px; }

    .empty-box {
        background: #fafafa; border: 1px dashed #d8dde3; border-radius: 12px;
        padding: 22px; color: #6b7280; font-size: 14px; text-align: center;
    }

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    table.rank-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    table.rank-table thead th {
        background: #e9f7ef; color: #208653; font-weight: 700;
        padding: 10px 14px; text-align: left; white-space: nowrap;
    }
    table.rank-table td {
        padding: 12px 14px; border-top: 1px solid #f1f3f5; color: #20252b;
    }
    .rank-table-card {
        background: white; border-radius: 14px; overflow: hidden;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.06);
    }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero img { max-width: 170px !important; height: 40px !important; }
        .hero-brand { font-size: 22px; }
        .hero-date { text-align: left; }
        .section { font-size: 17px; margin: 20px 0 8px; }
        .value { font-size: 24px; }
    }
</style>
""", unsafe_allow_html=True)

# "Venta hoy" vive en pages/, por eso sube un nivel extra (.parent.parent)
# para llegar a los mismos data.csv / data_tiendas.csv / logo que usa "app".
DATA_FILE = Path(__file__).resolve().parent.parent / "data.csv"
DATA_TIENDAS_FILE = Path(__file__).resolve().parent.parent / "data_tiendas.csv"
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"

try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

TIENDAS_COLUMNS = ["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax", "orders", "units"]
try:
    if DATA_TIENDAS_FILE.exists():
        base_df_tiendas = pd.read_csv(DATA_TIENDAS_FILE)
        base_df_tiendas["date"] = pd.to_datetime(base_df_tiendas["date"], errors="coerce")
        base_df_tiendas["Tienda"] = base_df_tiendas["Tienda"].astype(str)
        for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
            base_df_tiendas[col] = pd.to_numeric(base_df_tiendas[col], errors="coerce").fillna(0)
        base_df_tiendas = base_df_tiendas.dropna(subset=["date"])
    else:
        base_df_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)
except Exception:
    base_df_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)

st.markdown(
    '<div style="color:#6b7280;font-size:12px;margin:-6px 0 14px;">'
    'Esta pestaña, a diferencia de "Venta diaria", muestra el día de HOY tal cual '
    'viene en el archivo, aunque todavía esté incompleto. Subí el Excel "Venta Con y '
    'sin Impuesto" del mes en curso desde la pestaña <b>app</b> para que se actualice acá.'
    '</div>',
    unsafe_allow_html=True
)

TIENDA_MAP = {
    "1002": "Rio IV", "1003": "San Luis", "1004": "San Fernando", "1005": "Las Heras",
    "1006": "San Juan", "1007": "La Rioja", "1008": "Corrientes", "1010": "Córdoba Sur",
    "1011": "Salta", "1012": "Santiago", "1013": "Tigre", "1014": "Lujan",
    "1015": "Maipú", "1016": "Avellaneda 2", "1017": "La Tablada", "1018": "Quilmes",
    "1020": "Tucumán", "1021": "Neuquén 2", "1022": "Bariloche", "1023": "La Pampa",
    "1024": "Formosa", "1026": "Catamarca", "1027": "Mataderos", "1028": "Alte Brown",
    "1029": "Moreno", "1030": "José C Paz", "1031": "Jujuy", "1032": "Malvinas Arg",
    "1033": "Rio Salí", "1035": "3 de Febrero", "1036": "Moreno Shopping", "1037": "San Martin",
    "1038": "Cipolletti", "1039": "Paraná 2", "1042": "Trelew", "1043": "Laferrere",
    "1044": "Hurlingham (AV, Villegas)", "1045": "Hurlingham (AV, Vergara)", "1046": "Pergamino",
    "1050": "Lanús", "1051": "Posadas", "1052": "Oran", "1053": "Viedma",
    "1054": "Olavarría", "1055": "Villa Mercedes", "1056": "Villa Nueva",
    "1057": "Comodoro Rivadavia", "1058": "Resistencia", "1059": "Gonzalez Catán",
    "1060": "Fuerza Aérea (Cba)", "1061": "Junín", "1067": "San Martín (Mza)",
    "1068": "Palmares (Mza)", "1069": "STS", "1074": "Goya (Ctes)",
    "1075": "Salta Fuerza Aérea", "1076": "Lomas de Zamora", "1077": "Gral Pico (La Pampa)",
    "1078": "Salta Tartagal", "1080": "Santiago del Estero Sur", "1081": "Rawson San Juan",
    "1082": "Tucumán (Av, Jujuy)", "1084": "San Vicente", "1085": "Corrientes (Av, Maipú)",
    "1086": "Formosa II", "1087": "Pilar", "1088": "Tuc, Concepción", "1092": "San Juan Norte",
    "1093": "Comodoro Rivadavia Norte", "1096": "Caseros", "1097": "Donato Alvarez (Cba)",
    "1098": "R,S, Peña, Chaco", "1099": "Posadas II", "1100": "Santa Rosa (La Pampa) II",
    "1106": "Tuc, Ejército Del Norte", "1108": "Puerto Madryn", "1110": "Claypole",
    "1111": "San Pedro de Jujuy", "1114": "Clorinda", "1115": "General Roca",
    "1116": "Moron", "1119": "Moreno Derqui", "2997": "Constituyentes", "2998": "San Justo",
    "2999": "Avellaneda", "3601": "La Plata", "3602": "Bahía Blanca", "3603": "Santa Fe",
    "3604": "Paraná", "3605": "Córdoba Oeste", "3606": "Córdoba Este", "3608": "Neuquén",
    "3613": "Mendoza", "4001": "Campana",
}

# Formato de cada tienda (Full 1 / Full 2 / GM), del Excel "Tienda - Formato -
# Coordinador" que pasó Emi (hoja "Tiendas", columna "Form").
TIENDA_FORMATO = {
    "1002": "Full 1", "1003": "Full 1", "1004": "Full 1", "1005": "GM", "1006": "Full 1",
    "1007": "Full 2", "1008": "Full 1", "1010": "GM", "1011": "Full 1", "1012": "Full 2",
    "1013": "GM", "1014": "Full 1", "1015": "GM", "1016": "GM", "1017": "GM", "1018": "GM",
    "1020": "Full 1", "1021": "GM", "1022": "Full 2", "1023": "Full 2", "1024": "Full 1",
    "1026": "Full 2", "1027": "GM", "1028": "GM", "1029": "GM", "1030": "GM", "1031": "Full 1",
    "1032": "GM", "1033": "Full 2", "1035": "Full 1", "1036": "GM", "1037": "GM",
    "1038": "Full 1", "1039": "GM", "1042": "Full 2", "1043": "GM", "1044": "GM",
    "1045": "GM", "1046": "Full 2", "1050": "GM", "1051": "Full 2", "1052": "Full 2",
    "1053": "Full 2", "1054": "Full 1", "1055": "Full 1", "1056": "Full 2", "1057": "Full 1",
    "1058": "Full 1", "1059": "GM", "1060": "GM", "1061": "Full 2", "1067": "Full 2",
    "1068": "GM", "1069": "GM", "1074": "Full 2", "1075": "GM", "1076": "GM", "1077": "Full 2",
    "1078": "Full 2", "1080": "Full 1", "1081": "GM", "1082": "GM", "1084": "Full 2",
    "1085": "GM", "1086": "GM", "1087": "Full 1", "1088": "Full 2", "1092": "GM",
    "1093": "GM", "1096": "GM", "1097": "GM", "1098": "Full 2", "1099": "GM", "1100": "GM",
    "1106": "GM", "1108": "Full 2", "1110": "GM", "1111": "Full 2", "1114": "Full 2",
    "1115": "Full 1", "1116": "GM", "1119": "GM", "2997": "Full 1", "2998": "Full 1",
    "2999": "Full 1", "3601": "Full 1", "3602": "Full 1", "3603": "Full 1", "3604": "Full 1",
    "3605": "Full 1", "3606": "Full 1", "3608": "Full 1", "3613": "Full 1", "4001": "Full 2",
}

def _vh_norm_tienda_code(v):
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return str(v).strip()

def _vh_tienda_nombre(codigo):
    return TIENDA_MAP.get(codigo, codigo)

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()

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

# ---------------------------------------------------------------------
# Método de entrega + pedidos por tienda de HOY: esto NO sale de "Venta Con
# y sin Impuesto" (no trae esa info) — sale del archivo de Pedidos
# ("order-operation" / "Vs de ventas"), el MISMO archivo compartido que ya
# usan Comparativo / Venta fin de semana / Venta diaria. Se puede subir
# acá mismo (abajo) o desde la pestaña "app" — es un solo archivo
# compartido, no uno aparte: subirlo desde cualquiera de los dos lados
# actualiza el mismo dato para todas las pestañas.
# ---------------------------------------------------------------------
SHARED_DIR_PEDIDOS = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_VSVENTAS_PATH_PEDIDOS = SHARED_DIR_PEDIDOS / "vsventas.xlsx"

def _vh_pedidos_github_headers():
    token = st.secrets.get("GITHUB_TOKEN") if hasattr(st, "secrets") else None
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Masonline-Dashboard",
    }

def _vh_pedidos_fetch_from_github(shared_path):
    headers = _vh_pedidos_github_headers()
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

def _vh_pedidos_get_shared_bytes(shared_path):
    if shared_path.exists():
        try:
            data = shared_path.read_bytes()
            if data:
                return data
        except Exception:
            pass
    content = _vh_pedidos_fetch_from_github(shared_path)
    if content:
        try:
            shared_path.parent.mkdir(parents=True, exist_ok=True)
            shared_path.write_bytes(content)
        except Exception:
            pass
        return content
    return None

def _vh_pedidos_save_to_github(shared_path, content_bytes, label):
    """Guarda este archivo en GitHub (carpeta shared_uploads/), igual que
    hace "app" — para que quede disponible para siempre y las demás
    pestañas (Comparativo, Venta fin de semana, Venta diaria) lo vean
    también, sin importar si se subió desde acá o desde "app"."""
    headers = _vh_pedidos_github_headers()
    if not headers:
        return False, "no hay credenciales de GitHub configuradas (GITHUB_TOKEN)"
    import urllib.request
    import urllib.error
    import json as _json
    import base64 as _base64
    repo = "2026-Masonline/masonline-dashboard"
    branch = "main"
    repo_path = f"shared_uploads/{shared_path.name}"
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    try:
        sha = None
        request_get = urllib.request.Request(f"{url}?ref={branch}", headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request_get, timeout=120) as response:
                sha = _json.loads(response.read().decode("utf-8"))["sha"]
        except urllib.error.HTTPError as e_get:
            if e_get.code != 404:
                raise
        payload = {
            "message": f"Actualizar reporte - {label}",
            "content": _base64.b64encode(content_bytes).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        request_put = urllib.request.Request(
            url,
            data=_json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(request_put, timeout=120) as response:
            response.read()
        return True, None
    except urllib.error.HTTPError as e:
        try:
            detalle = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            detalle = ""
        return False, f"HTTP {e.code} {e.reason} {detalle}".strip()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"[:300]

def _vh_pedidos_save_shared_bytes(uploaded_file, shared_path, label):
    """Si se subió un archivo nuevo, lo guarda local + GitHub y devuelve
    los bytes nuevos (para usarlos ya mismo en esta misma corrida, sin
    esperar un refresh). Si falla el respaldo en GitHub, lo avisa en
    pantalla (no falla en silencio)."""
    if uploaded_file is None:
        return None
    content = uploaded_file.getvalue()
    try:
        shared_path.parent.mkdir(parents=True, exist_ok=True)
        shared_path.write_bytes(content)
    except Exception:
        pass
    ok, err = _vh_pedidos_save_to_github(shared_path, content, label)
    if ok:
        st.success(f"{label}: archivo cargado y guardado correctamente.")
    else:
        st.error(
            f"⚠️ {label}: se guardó para esta sesión, pero el respaldo permanente "
            f"en GitHub falló, así que si la app se reinicia vas a perder este "
            f"archivo. Detalle técnico: {err}"
        )
    return content

_VH_PEDIDOS_RAW_COLS = {
    "commerceDateCreated", "deliveryFinishDate", "commerceId", "commerceSequentialId",
    "salesChannelPrefix", "totalAmount", "itemsPickedQuantity",
}

_VH_METODO_ENTREGA_LABELS = {
    "delivery": "Envío a domicilio",
    "store_pickup": "Retiro en tienda",
    "drive_through": "Pickup (drive-through)",
}

def _vh_metodo_entrega_label(v):
    s = str(v).strip() if v is not None and not pd.isna(v) else ""
    return _VH_METODO_ENTREGA_LABELS.get(s, s if s else "Sin especificar")

# Traducción del "status" crudo del export (order-operation) — lista
# relevada sobre el archivo real de Pedidos ("Estados +72.xlsx", Enero a
# Octubre 2026). Cualquier status nuevo que no esté en el diccionario se
# muestra tal cual viene, en vez de ocultarse.
_VH_ESTADO_PEDIDO_LABELS = {
    "delivered": "Entregado",
    "canceled": "Cancelado",
    "cancelled": "Cancelado",
    "readyForDelivery": "Listo para entregar",
    "notDelivered": "No entregado",
    "readyForPicking": "Listo para picking",
    "readyForInvoice": "Listo para facturar",
    "inDelivery": "En camino",
    "cancelationRequested": "Cancelación solicitada",
    "pendingCandidatesConfirmation": "Pendiente de confirmación",
    "needsRescheduling": "Necesita reprogramación",
    "processingRepacking": "En repacking",
}

def _vh_estado_pedido_label(v):
    s = str(v).strip() if v is not None and not pd.isna(v) else ""
    return _VH_ESTADO_PEDIDO_LABELS.get(s, s if s else "Sin especificar")

def _vh_pedidos_codigo_tienda(v, tienda_codes):
    if pd.isna(v):
        s = ""
    else:
        try:
            s = str(int(float(v))) if isinstance(v, float) and v == int(v) else str(v).strip()
        except (TypeError, ValueError):
            s = str(v).strip()
    if s in tienda_codes:
        return s
    candidatos = re.findall(r"\d{3,6}", s)
    for c in candidatos:
        if c in tienda_codes:
            return c
    return candidatos[-1] if candidatos else s

@st.cache_data(ttl=180, show_spinner=False)
def _vh_cargar_pedidos_completo(vsventas_bytes, tienda_codes_tuple):
    """Parsea y combina TODAS las hojas del archivo de Pedidos una sola vez
    (cacheado 3 minutos por archivo) — sin filtrar todavía por ninguna
    fecha puntual. Devuelve un DataFrame con una fila por pedido entregado
    (columnas Id/Pedido/Tienda/Metodo/Monto/Unidades + FechaEntrega y
    FechaCreacion ya normalizadas), para poder recortar después por
    CUALQUIER fecha que el archivo subido traiga (no solo "hoy"), sin
    tener que volver a abrir el Excel cada vez. None si todavía no hay
    archivo subido."""
    if vsventas_bytes is None:
        return None
    try:
        xl = pd.ExcelFile(io.BytesIO(vsventas_bytes))
    except Exception:
        return None
    tienda_codes = set(tienda_codes_tuple)
    partes = []
    for name in xl.sheet_names:
        try:
            d = xl.parse(name)
        except Exception:
            continue
        d.columns = [str(c).replace("\xa0", " ").strip() for c in d.columns]
        if not _VH_PEDIDOS_RAW_COLS.issubset(set(d.columns)):
            continue
        es_pm = d["salesChannelPrefix"].astype(str).str.strip().str.upper() == "PM"
        es_rma = d["commerceId"].astype(str).str.upper().str.contains("RMA", na=False)
        d = d[~es_pm & ~es_rma & d["commerceSequentialId"].notna()]
        d = d.drop_duplicates(subset=["commerceSequentialId"])
        if not len(d):
            continue

        fecha_creacion = pd.to_datetime(d["commerceDateCreated"], errors="coerce").dt.normalize()
        fecha_entrega = pd.to_datetime(d["deliveryFinishDate"], errors="coerce").dt.normalize()
        tienda_col = (
            d["shippingWarehouseReferenceId"].apply(lambda v: _vh_pedidos_codigo_tienda(v, tienda_codes))
            if "shippingWarehouseReferenceId" in d.columns else ""
        )
        metodo_col = d["shippingsType"] if "shippingsType" in d.columns else ""
        estado_col = d["status"] if "status" in d.columns else ""
        if "totalAmount" in d.columns:
            # totalAmount a veces viene como texto con signo "$" (ej.
            # "$85783.3") en vez de número — hay que limpiarlo antes de
            # sumarlo, si no pd.to_numeric lo deja todo en NaN -> 0.
            _monto_txt = (
                d["totalAmount"].astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            monto_col = pd.to_numeric(_monto_txt, errors="coerce").fillna(0)
        else:
            monto_col = 0
        if "itemsQuantity" in d.columns:
            unidades_col = pd.to_numeric(d["itemsQuantity"], errors="coerce").fillna(0)
        else:
            # Si no viene itemsQuantity, usamos itemsPickedQuantity (ya es
            # una columna obligatoria) como mejor aproximación.
            unidades_col = pd.to_numeric(d["itemsPickedQuantity"], errors="coerce").fillna(0)
        partes.append(pd.DataFrame({
            "Id": d["commerceSequentialId"].values,
            "Pedido": d["commerceId"].values,
            "Tienda": tienda_col,
            "Metodo": metodo_col,
            "Estado": estado_col,
            "Monto": monto_col,
            "Unidades": unidades_col,
            "FechaEntrega": fecha_entrega.values,
            "FechaCreacion": fecha_creacion.values,
        }))

    cols = ["Id", "Pedido", "Tienda", "Metodo", "Estado", "Monto", "Unidades", "FechaEntrega", "FechaCreacion"]
    if not partes:
        return pd.DataFrame(columns=cols)
    out = pd.concat(partes, ignore_index=True, sort=False)
    # Dedup por ID de pedido (no por Tienda+Metodo juntos — varios pedidos
    # distintos de la misma tienda con el mismo método son normales y no
    # son duplicados).
    out = out.drop_duplicates(subset=["Id"])
    return out[cols]

def _vh_pedidos_del_dia(completo, fecha):
    """A partir del DataFrame completo (ya parseado y cacheado), recorta
    los pedidos ENTREGADOS ese día puntual (fecha de entrega) y cuenta los
    CREADOS ese mismo día (fecha de creación) — misma lógica de siempre,
    pero para cualquier `fecha` (date de Python), no solo la de hoy.
    Devuelve (entregados_df, creados_count); entregados_df es None si
    `completo` es None (todavía no hay archivo subido)."""
    detalle_cols = ["Pedido", "Tienda", "Metodo", "Estado", "Monto", "Unidades"]
    if completo is None:
        return None, 0
    if not len(completo):
        return completo[detalle_cols], 0
    entregados = completo[completo["FechaEntrega"].dt.date == fecha]
    creados_count = int((completo["FechaCreacion"].dt.date == fecha).sum())
    return entregados[detalle_cols], creados_count

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin:18px 0 10px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    SUBIR ARCHIVO DE PEDIDOS ("Vs de ventas" / order-operation)
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí acá el Excel de Pedidos para actualizar "Método de entrega" y "Tiendas con
    más pedidos" al instante — es el MISMO archivo compartido que usan Comparativo,
    Venta fin de semana y Venta diaria (no hace falta subirlo de nuevo en "app").
  </div>
</div>
""", unsafe_allow_html=True)
upload_pedidos_hoy = st.file_uploader(
    "Archivo de Pedidos", type=["xlsx", "xls"], key="upload_pedidos_venta_hoy",
    label_visibility="collapsed",
    help='Archivo "Vs de ventas" / order-operation (commerceDateCreated, deliveryFinishDate, shippingsType, etc.)'
)
_vsventas_bytes_nuevo = _vh_pedidos_save_shared_bytes(
    upload_pedidos_hoy, SHARED_VSVENTAS_PATH_PEDIDOS, "Pedidos (desde Venta hoy)"
)

_vsventas_bytes_hoy = _vsventas_bytes_nuevo or _vh_pedidos_get_shared_bytes(SHARED_VSVENTAS_PATH_PEDIDOS)
_tienda_codes_hoy = tuple(sorted(TIENDA_MAP.keys()))
_pedidos_completo_hoy = _vh_cargar_pedidos_completo(_vsventas_bytes_hoy, _tienda_codes_hoy)

# Fecha a mostrar: el archivo de Pedidos puede traer varios días (no solo
# "hoy" en el sentido estricto) — se arma un selector con las fechas de
# ENTREGA que realmente trae el archivo subido, para poder elegir cualquiera
# de ellas (por defecto, la más reciente) en vez de depender de que coincida
# con la fecha real de hoy.
_fechas_disponibles_hoy = (
    sorted(_pedidos_completo_hoy["FechaEntrega"].dropna().dt.date.unique(), reverse=True)
    if _pedidos_completo_hoy is not None and len(_pedidos_completo_hoy)
    else []
)
if _fechas_disponibles_hoy:
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#6b7280;margin:8px 0 2px;">'
        'FECHA A MOSTRAR (de entrega)</div>',
        unsafe_allow_html=True
    )
    fecha_mostrada = st.selectbox(
        "Fecha a mostrar", _fechas_disponibles_hoy,
        format_func=lambda d: d.strftime("%d/%m/%Y") + (" (hoy)" if d == arg_today else ""),
        key="vh_fecha_pedidos", label_visibility="collapsed"
    )
else:
    fecha_mostrada = arg_today

pedidos_detalle_hoy, pedidos_creados_hoy_count = _vh_pedidos_del_dia(_pedidos_completo_hoy, fecha_mostrada)

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
    {fecha_mostrada.strftime('%d/%m/%Y')}
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Método de entrega + Tiendas con más pedidos (por CANTIDAD de pedidos,
# no por venta) — fuente: archivo de Pedidos ("Vs de ventas"), filtrado a
# los pedidos ENTREGADOS hoy (fecha de entrega, no de creación).
# ---------------------------------------------------------------------
st.markdown('<div class="section">Pedidos del día</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="section-desc">Entregados (fecha de entrega) y creados (fecha de creación) '
    f'el <b>{fecha_mostrada.strftime("%d/%m/%Y")}</b>, con el desglose por método de entrega '
    f'— sale del archivo de Pedidos.</div>',
    unsafe_allow_html=True
)

if pedidos_detalle_hoy is None:
    st.markdown(
        '<div class="empty-box">Todavía no se subió el archivo de Pedidos. '
        'Subilo en la caja de arriba ("Subir archivo de Pedidos") para ver estas tarjetas.</div>',
        unsafe_allow_html=True
    )
else:
    entregados_count = len(pedidos_detalle_hoy)
    _metodo_orden = ["Envío a domicilio", "Retiro en tienda", "Pickup (drive-through)"]
    if entregados_count:
        metodo_tmp = pedidos_detalle_hoy.assign(
            MetodoLabel=pedidos_detalle_hoy["Metodo"].apply(_vh_metodo_entrega_label)
        )
        metodo_agg = metodo_tmp.groupby("MetodoLabel", as_index=False).agg(
            Pedidos=("MetodoLabel", "size"), Monto=("Monto", "sum")
        ).set_index("MetodoLabel")
        # Métodos conocidos primero (en el orden fijo de arriba), cualquier
        # método nuevo que no esté en esa lista se agrega al final.
        etiquetas = _metodo_orden + [m for m in metodo_agg.index if m not in _metodo_orden]
    else:
        metodo_agg = pd.DataFrame(columns=["Pedidos", "Monto"])
        etiquetas = _metodo_orden

    # Tarjeta "Total de pedidos entregados" (del día elegido) + "Pedidos creados" (mismo día).
    _fecha_card = fecha_mostrada.strftime("%d/%m")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #2f9e66;">
          <div class="label" style="color:#208653;">TOTAL PEDIDOS ENTREGADOS</div>
          <div class="value" style="color:#208653;">{intfmt(entregados_count)}</div>
          <div class="small">Por fecha de entrega — {_fecha_card}</div>
        </div>
        """, unsafe_allow_html=True)
    with cc2:
        st.markdown(f"""
        <div class="card" style="border-top:4px solid #59636e;">
          <div class="label">PEDIDOS CREADOS</div>
          <div class="value">{intfmt(pedidos_creados_hoy_count)}</div>
          <div class="small">Por fecha de creación — {_fecha_card}</div>
        </div>
        """, unsafe_allow_html=True)

    # Estados de los pedidos (en español) — sobre el mismo conjunto de
    # pedidos con fecha de entrega en el día elegido. Útil porque no todos
    # los que caen en esa fecha terminan realmente "Entregado": puede haber
    # cancelados, listos para entregar todavía, etc.
    st.markdown(
        f'<div style="font-size:13px;font-weight:800;color:#20252b;margin:16px 0 8px;">'
        f'ESTADOS DE LOS PEDIDOS — {_fecha_card}</div>',
        unsafe_allow_html=True
    )
    if entregados_count:
        estado_tmp = pedidos_detalle_hoy.assign(
            EstadoLabel=pedidos_detalle_hoy["Estado"].apply(_vh_estado_pedido_label)
        )
        estado_agg = (
            estado_tmp.groupby("EstadoLabel", as_index=False)
            .agg(Cantidad=("EstadoLabel", "size"))
            .sort_values("Cantidad", ascending=False)
        )
        _estado_rows = "".join(
            '<tr>'
            f'<td>{html.escape(str(r.EstadoLabel))}</td>'
            f'<td style="text-align:center;font-weight:800;color:#20252b;">{intfmt(r.Cantidad)}</td>'
            f'<td style="text-align:right;color:#6b7280;">{pct(r.Cantidad / entregados_count)}</td>'
            '</tr>'
            for r in estado_agg.itertuples()
        )
        st.markdown(
            '<div class="rank-table-card"><div class="table-scroll">'
            '<table class="rank-table"><thead><tr>'
            '<th>Estado</th><th style="text-align:center;">Pedidos</th><th style="text-align:right;">%</th>'
            f'</tr></thead><tbody>{_estado_rows}</tbody></table>'
            '</div></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="empty-box">Sin pedidos para esta fecha 🎉</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:13px;font-weight:800;color:#20252b;margin:16px 0 8px;">'
        'MÉTODO DE ENTREGA (entregados hoy)</div>',
        unsafe_allow_html=True
    )
    _metodo_colores = ["#f5a623", "#e8432c", "#59636e", "#2f9e66", "#3b82c4"]
    metodo_cols = st.columns(len(etiquetas))
    for i, metodo_label in enumerate(etiquetas):
        cant = int(metodo_agg["Pedidos"].get(metodo_label, 0))
        monto = float(metodo_agg["Monto"].get(metodo_label, 0))
        color = _metodo_colores[i % len(_metodo_colores)]
        with metodo_cols[i]:
            st.markdown(f"""
            <div class="card" style="border-top:4px solid {color};">
              <div class="label" style="color:{color};">{metodo_label.upper()}</div>
              <div class="value">{intfmt(cant)}</div>
              <div class="small">{money(monto)}</div>
            </div>
            """, unsafe_allow_html=True)

    # Formato de tienda (Full 1 / Full 2 / GM) — mismo criterio (entregados
    # hoy), agrupado por el formato de la tienda en vez de por método.
    st.markdown(
        '<div style="font-size:13px;font-weight:800;color:#20252b;margin:16px 0 8px;">'
        'FORMATO DE TIENDA (entregados hoy)</div>',
        unsafe_allow_html=True
    )
    _formato_orden = ["Full 1", "Full 2", "GM"]
    if entregados_count:
        formato_tmp = pedidos_detalle_hoy.assign(
            FormatoLabel=pedidos_detalle_hoy["Tienda"].apply(
                lambda t: TIENDA_FORMATO.get(str(t), "Sin formato")
            )
        )
        formato_agg = formato_tmp.groupby("FormatoLabel", as_index=False).agg(
            Pedidos=("FormatoLabel", "size"), Monto=("Monto", "sum")
        ).set_index("FormatoLabel")
        etiquetas_formato = _formato_orden + [f for f in formato_agg.index if f not in _formato_orden]
    else:
        formato_agg = pd.DataFrame(columns=["Pedidos", "Monto"])
        etiquetas_formato = _formato_orden
    _formato_colores = ["#2f9e66", "#3b82c4", "#e8432c", "#9ca3af"]
    formato_cols = st.columns(len(etiquetas_formato))
    for i, formato_label in enumerate(etiquetas_formato):
        cant = int(formato_agg["Pedidos"].get(formato_label, 0))
        monto = float(formato_agg["Monto"].get(formato_label, 0))
        color = _formato_colores[i % len(_formato_colores)]
        with formato_cols[i]:
            st.markdown(f"""
            <div class="card" style="border-top:4px solid {color};">
              <div class="label" style="color:{color};">{formato_label.upper()}</div>
              <div class="value">{intfmt(cant)}</div>
              <div class="small">{money(monto)}</div>
            </div>
            """, unsafe_allow_html=True)

def _vh_tabla_tiendas_pedidos(tienda_pedidos_agg):
    rows_html = ""
    for i, r in enumerate(tienda_pedidos_agg.itertuples(), start=1):
        codigo = str(r.Tienda)
        nombre = TIENDA_MAP.get(codigo, "")
        tienda_label = f"{codigo} - {nombre}" if nombre else codigo
        formato = TIENDA_FORMATO.get(codigo, "Sin formato")
        rows_html += (
            '<tr>'
            f'<td>{i}</td>'
            f'<td>{tienda_label}</td>'
            f'<td>{formato}</td>'
            f'<td style="text-align:center;font-weight:800;color:#208653;">{intfmt(r.Pedidos)}</td>'
            f'<td style="text-align:right;font-weight:800;color:#20252b;">{money(r.Monto)}</td>'
            '</tr>'
        )
    return (
        '<div class="rank-table-card">'
        '<div class="table-scroll">'
        '<table class="rank-table"><thead><tr>'
        '<th></th><th>Tienda</th><th>Formato</th>'
        '<th style="text-align:center;">Pedidos</th>'
        '<th style="text-align:right;">Total $</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>'
        '</div></div>'
    )

st.markdown('<div class="section">Top 5 tiendas con más pedidos (hoy)</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Ranking por CANTIDAD de pedidos entregados hoy (no por venta) — '
    'misma fuente que el método de entrega.</div>',
    unsafe_allow_html=True
)

if pedidos_detalle_hoy is not None and len(pedidos_detalle_hoy):
    tienda_pedidos_agg_full = (
        pedidos_detalle_hoy.groupby("Tienda", as_index=False)
        .agg(Pedidos=("Tienda", "size"), Monto=("Monto", "sum"))
        .sort_values("Pedidos", ascending=False)
    )
    st.markdown(_vh_tabla_tiendas_pedidos(tienda_pedidos_agg_full.head(5)), unsafe_allow_html=True)

    st.markdown('<div class="section">Todas las tiendas (hoy)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Listado completo, misma fuente y orden que el Top 5.</div>',
        unsafe_allow_html=True
    )
    st.markdown(_vh_tabla_tiendas_pedidos(tienda_pedidos_agg_full), unsafe_allow_html=True)
elif pedidos_detalle_hoy is not None:
    st.markdown(
        '<div class="empty-box">Todavía no hay pedidos registrados hoy en el archivo de Pedidos.</div>',
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------
# Descarga de un HTML standalone con el resumen de Pedidos de hoy (mismo
# diseño que el dashboard), para mandar por mail o guardar aparte.
# ---------------------------------------------------------------------
if pedidos_detalle_hoy is not None and len(pedidos_detalle_hoy):
    _dl_metodo_tmp = pedidos_detalle_hoy.assign(
        MetodoLabel=pedidos_detalle_hoy["Metodo"].apply(_vh_metodo_entrega_label)
    )
    _dl_metodo_agg = _dl_metodo_tmp.groupby("MetodoLabel", as_index=False).agg(
        Pedidos=("MetodoLabel", "size"), Monto=("Monto", "sum")
    ).set_index("MetodoLabel")
    _dl_metodo_orden = ["Envío a domicilio", "Retiro en tienda", "Pickup (drive-through)"]
    _dl_metodo_etiquetas = _dl_metodo_orden + [m for m in _dl_metodo_agg.index if m not in _dl_metodo_orden]

    _dl_formato_tmp = pedidos_detalle_hoy.assign(
        FormatoLabel=pedidos_detalle_hoy["Tienda"].apply(lambda t: TIENDA_FORMATO.get(str(t), "Sin formato"))
    )
    _dl_formato_agg = _dl_formato_tmp.groupby("FormatoLabel", as_index=False).agg(
        Pedidos=("FormatoLabel", "size"), Monto=("Monto", "sum")
    ).set_index("FormatoLabel")
    _dl_formato_orden = ["Full 1", "Full 2", "GM"]
    _dl_formato_etiquetas = _dl_formato_orden + [f for f in _dl_formato_agg.index if f not in _dl_formato_orden]

    _dl_tienda_agg = (
        pedidos_detalle_hoy.groupby("Tienda", as_index=False)
        .agg(Pedidos=("Tienda", "size"), Monto=("Monto", "sum"))
        .sort_values("Pedidos", ascending=False)
    )

    _dl_estado_tmp = pedidos_detalle_hoy.assign(
        EstadoLabel=pedidos_detalle_hoy["Estado"].apply(_vh_estado_pedido_label)
    )
    _dl_estado_agg = (
        _dl_estado_tmp.groupby("EstadoLabel", as_index=False)
        .agg(Cantidad=("EstadoLabel", "size"))
        .sort_values("Cantidad", ascending=False)
    )

    def _dl_estado_html(agg, titulo, total):
        header = f'<div class="rank-table-header">🧾 {html.escape(titulo)}</div>'
        if not len(agg) or not total:
            return (
                f'<div class="rank-table-card">{header}'
                '<div style="padding:20px;color:#9ca3af;font-size:13px;">Sin datos.</div></div>'
            )
        rows_html = "".join(
            '<tr>'
            f'<td>{html.escape(str(r.EstadoLabel))}</td>'
            f'<td style="text-align:center;font-weight:800;color:#20252b;">{intfmt(r.Cantidad)}</td>'
            f'<td style="text-align:right;color:#6b7280;">{pct(r.Cantidad / total)}</td>'
            '</tr>'
            for r in agg.itertuples()
        )
        return (
            f'<div class="rank-table-card">{header}'
            '<table class="rank-table"><thead><tr>'
            '<th>Estado</th><th style="text-align:center;">Pedidos</th><th style="text-align:right;">%</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table></div>'
        )

    def _dl_cards_html(etiquetas, agg, colores):
        out = ""
        for i, label in enumerate(etiquetas):
            cant = int(agg["Pedidos"].get(label, 0))
            monto = float(agg["Monto"].get(label, 0))
            color = colores[i % len(colores)]
            out += f"""
            <div class="card" style="border-top:4px solid {color};">
              <div class="label" style="color:{color};">{html.escape(label.upper())}</div>
              <div class="value">{intfmt(cant)}</div>
              <div class="small">{html.escape(money(monto))}</div>
            </div>
            """
        return out

    def _dl_tabla_html(df_agg, titulo):
        header = f'<div class="rank-table-header">🏆 {html.escape(titulo)}</div>'
        if not len(df_agg):
            return (
                f'<div class="rank-table-card">{header}'
                '<div style="padding:20px;color:#9ca3af;font-size:13px;">Sin datos.</div></div>'
            )
        rows_html = ""
        for i, r in enumerate(df_agg.itertuples(), start=1):
            codigo = str(r.Tienda)
            nombre = TIENDA_MAP.get(codigo, "")
            tienda_label = f"{codigo} - {nombre}" if nombre else codigo
            formato = TIENDA_FORMATO.get(codigo, "Sin formato")
            rows_html += (
                '<tr>'
                f'<td><span class="rank-badge">{i}</span></td>'
                f'<td>{html.escape(tienda_label)}</td>'
                f'<td>{html.escape(formato)}</td>'
                f'<td style="text-align:center;">{intfmt(r.Pedidos)}</td>'
                f'<td style="text-align:right;font-weight:800;color:#208653;">{html.escape(money(r.Monto))}</td>'
                '</tr>'
            )
        return (
            f'<div class="rank-table-card">{header}'
            '<table class="rank-table"><thead><tr>'
            '<th></th><th>Tienda</th><th>Formato</th>'
            '<th style="text-align:center;">Pedidos</th>'
            '<th style="text-align:right;">Total $</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table></div>'
        )

    def _dl_detalle_pedidos_html(detalle_df, titulo):
        """Listado pedido por pedido: número de pedido, tienda, método de
        entrega, unidades y monto — el "detalle" que pidió Emi, no solo el
        agregado por tienda/método."""
        header = f'<div class="rank-table-header">🧾 {html.escape(titulo)}</div>'
        if not len(detalle_df):
            return (
                f'<div class="rank-table-card">{header}'
                '<div style="padding:20px;color:#9ca3af;font-size:13px;">Sin datos.</div></div>'
            )
        detalle_df = detalle_df.sort_values(["Tienda", "Pedido"])
        rows_html = ""
        for r in detalle_df.itertuples():
            codigo = str(r.Tienda)
            nombre = TIENDA_MAP.get(codigo, "")
            tienda_label = f"{codigo} - {nombre}" if nombre else codigo
            metodo_label = _vh_metodo_entrega_label(r.Metodo)
            rows_html += (
                '<tr>'
                f'<td>{html.escape(str(r.Pedido))}</td>'
                f'<td>{html.escape(tienda_label)}</td>'
                f'<td>{html.escape(metodo_label)}</td>'
                f'<td style="text-align:center;">{intfmt(r.Unidades)}</td>'
                f'<td style="text-align:right;font-weight:800;color:#208653;">{html.escape(money(r.Monto))}</td>'
                '</tr>'
            )
        return (
            f'<div class="rank-table-card">{header}'
            '<table class="rank-table"><thead><tr>'
            '<th>N° de pedido</th><th>Tienda</th><th>Método de entrega</th>'
            '<th style="text-align:center;">Unidades</th>'
            '<th style="text-align:right;">Monto</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table></div>'
        )

    if LOGO_FILE.exists():
        _dl_logo_b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode("utf-8")
        _dl_logo_html = (
            f'<img src="data:image/png;base64,{_dl_logo_b64}" '
            'style="height:50px;max-width:300px;object-fit:contain;">'
        )
    else:
        _dl_logo_html = '<div style="font-size:28px;font-weight:800;">Más<span style="font-weight:400;">Online</span></div>'

    _dl_metodo_colores = ["#f5a623", "#e8432c", "#59636e", "#2f9e66", "#3b82c4"]
    _dl_formato_colores = ["#2f9e66", "#3b82c4", "#e8432c", "#9ca3af"]

    _html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MásOnline | Pedidos de hoy</title>
<style>
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    padding: 34px 42px 42px;
    background: #ffffff;
    color: #20252b;
    font-family: Arial, Helvetica, sans-serif;
}}
.container {{ max-width: 1300px; margin: 0 auto; }}
.hero {{
    background: #ffffff;
    padding: 18px 0 26px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 4px solid #2f9e66;
    margin-bottom: 20px;
}}
.hero-sub {{ font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }}
.hero-date {{ text-align: right; font-size: 19px; font-weight: 800; }}
.kpis {{ display: grid; gap: 16px; margin-bottom: 10px; }}
.kpis-2 {{ grid-template-columns: repeat(2, 1fr); }}
.card {{
    background: white; border: 1px solid #e8ebef; border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06); padding: 20px 22px; min-height: 110px;
}}
.label {{ color: #6b7280; font-size: 13px; font-weight: 700; }}
.value {{ color: #20252b; font-size: 28px; font-weight: 800; margin-top: 7px; }}
.small {{ color: #20252b; font-size: 13px; font-weight: 700; margin-top: 7px; }}
.section {{ font-size: 19px; font-weight: 800; margin: 26px 0 10px; }}
.rank-table-card {{
    background: white; border: 1px solid #e8ebef; border-radius: 14px;
    overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,.06); margin-bottom: 10px;
}}
.rank-table-header {{ background: #2f9e66; color: #fff; font-weight: 800; font-size: 15px; padding: 13px 20px; }}
table.rank-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
table.rank-table thead th {{
    background: #e9f7ef; color: #208653; font-weight: 700; padding: 10px 14px;
    text-align: left; white-space: nowrap; text-transform: uppercase;
    border-bottom: 1px solid #e8ebef;
}}
table.rank-table td {{ padding: 8px 12px; border-bottom: 1px solid #eef0ef; }}
.rank-badge {{
    display: inline-block; min-width: 20px; text-align: center; background: #2f9e66;
    color: #fff; border-radius: 6px; font-size: 12px; font-weight: 700; padding: 2px 6px;
}}
.footer {{ display: flex; justify-content: space-between; color: #6b7280; font-size: 12px; margin-top: 18px; }}
@media (max-width: 700px) {{
    .hero {{ flex-direction: column; align-items: flex-start; gap: 10px; }}
    .hero-date {{ text-align: left; }}
    .kpis {{ grid-template-columns: 1fr !important; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="hero">
  <div>
    {_dl_logo_html}
    <div class="hero-sub">E-COMMERCE</div>
  </div>
  <div class="hero-date">{fecha_mostrada.strftime('%d/%m/%Y')}</div>
</div>

<div class="section">Pedidos del día</div>
<div class="kpis kpis-2">
  <div class="card" style="border-top:4px solid #2f9e66;">
    <div class="label" style="color:#208653;">TOTAL PEDIDOS ENTREGADOS</div>
    <div class="value" style="color:#208653;">{intfmt(len(pedidos_detalle_hoy))}</div>
    <div class="small">Por fecha de entrega — {fecha_mostrada.strftime('%d/%m')}</div>
  </div>
  <div class="card" style="border-top:4px solid #59636e;">
    <div class="label">PEDIDOS CREADOS</div>
    <div class="value">{intfmt(pedidos_creados_hoy_count)}</div>
    <div class="small">Por fecha de creación — {fecha_mostrada.strftime('%d/%m')}</div>
  </div>
</div>

<div class="section">Estados de los pedidos</div>
{_dl_estado_html(_dl_estado_agg, f"ESTADOS · PEDIDOS {fecha_mostrada.strftime('%d/%m')}", len(pedidos_detalle_hoy))}

<div class="section">Método de entrega</div>
<div class="kpis" style="grid-template-columns: repeat({len(_dl_metodo_etiquetas)}, 1fr);">
{_dl_cards_html(_dl_metodo_etiquetas, _dl_metodo_agg, _dl_metodo_colores)}
</div>

<div class="section">Formato de tienda</div>
<div class="kpis" style="grid-template-columns: repeat({len(_dl_formato_etiquetas)}, 1fr);">
{_dl_cards_html(_dl_formato_etiquetas, _dl_formato_agg, _dl_formato_colores)}
</div>

<div class="section">Top 5 tiendas con más pedidos</div>
{_dl_tabla_html(_dl_tienda_agg.head(5), f"TOP 5 · PEDIDOS {fecha_mostrada.strftime('%d/%m')}")}

<div class="section">Todas las tiendas</div>
{_dl_tabla_html(_dl_tienda_agg, f"TODAS LAS TIENDAS · PEDIDOS {fecha_mostrada.strftime('%d/%m')}")}

<div class="section">Detalle de pedidos</div>
{_dl_detalle_pedidos_html(pedidos_detalle_hoy, f"DETALLE · PEDIDOS ENTREGADOS {fecha_mostrada.strftime('%d/%m')} ({intfmt(len(pedidos_detalle_hoy))})")}

<div class="footer">
  <span>Fuente: archivo de Pedidos ("Vs de ventas" / order-operation).</span>
  <span>MásOnline | E-commerce</span>
</div>

</div>
</body>
</html>
"""

    st.download_button(
        "⬇️ Descargar resumen de Pedidos (HTML)",
        data=_html_doc,
        file_name=f"pedidos_{fecha_mostrada.strftime('%Y-%m-%d')}.html",
        mime="text/html",
    )
