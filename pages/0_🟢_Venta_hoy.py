import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import tempfile
import io
import re

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
    'viene en el archivo, aunque todavía esté incompleto. Podés subir acá mismo el '
    'Excel del mes en curso, o hacerlo desde la pestaña <b>app</b> — es el mismo archivo '
    'y queda guardado para las dos.'
    '</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------
# Caja de carga "MES EN CURSO", acá mismo (para no tener que ir a "app" a
# subir el archivo de hoy). Mismo procesamiento exacto que usa "app":
# parsea el Excel "Venta Con y sin Impuesto", reemplaza el mes en curso en
# data.csv / data_tiendas.csv y guarda en GitHub.
# ---------------------------------------------------------------------
st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin-bottom:10px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    SUBIR EXCEL DE HOY (MES EN CURSO)
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí acá el Excel "Venta Con y sin Impuesto" del mes en curso (con la fila de hoy
    adentro) para actualizar esta pestaña al instante.
  </div>
</div>
""", unsafe_allow_html=True)
upload_hoy = st.file_uploader(
    "Archivo mes en curso", type=["xlsx", "xls"], key="upload_hoy_venta",
    label_visibility="collapsed",
    help="Reporte Venta Con y sin Impuesto del mes en curso."
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

def _vh_norm_tienda_code(v):
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return str(v).strip()

def _vh_tienda_nombre(codigo):
    return TIENDA_MAP.get(codigo, codigo)

def _vh_normalize_uploaded_excel(file):
    raw = pd.read_excel(file, sheet_name=0, header=None)
    header_row = None
    for i in range(min(10, len(raw))):
        vals = raw.iloc[i].astype(str).str.strip().tolist()
        if "Fecha" in vals and "Facturacion" in vals and "Venta - Ecommerce" in vals:
            header_row = i
            break
    if header_row is None:
        raise ValueError(
            "No encontré las columnas Fecha, Facturacion y Venta - Ecommerce en el archivo."
        )
    d = pd.read_excel(file, sheet_name=0, header=header_row)
    required = [
        "Fecha", "Facturacion", "Venta - Ecommerce",
        "Cantidad Venta Operativa - Ecommerce",
        "Pedidos Facturados con Venta Operativa - Ecommerce"
    ]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError("Faltan columnas: " + ", ".join(missing))
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    for c in required[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d = d.dropna(subset=["Fecha"])
    out = d.groupby("Fecha", as_index=False).agg(
        company_tax=("Facturacion", "sum"),
        ecommerce_tax=("Venta - Ecommerce", "sum"),
        orders=("Pedidos Facturados con Venta Operativa - Ecommerce", "sum"),
        units=("Cantidad Venta Operativa - Ecommerce", "sum")
    )
    out = out.rename(columns={"Fecha": "date"})
    out_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)
    out_tiendas["date"] = pd.to_datetime(out_tiendas["date"])
    if "Tienda" in d.columns:
        dt = d.copy()
        dt["Tienda"] = dt["Tienda"].apply(_vh_norm_tienda_code)
        out_tiendas = dt.groupby(["Fecha", "Tienda"], as_index=False).agg(
            company_tax=("Facturacion", "sum"),
            ecommerce_tax=("Venta - Ecommerce", "sum"),
            orders=("Pedidos Facturados con Venta Operativa - Ecommerce", "sum"),
            units=("Cantidad Venta Operativa - Ecommerce", "sum")
        )
        out_tiendas = out_tiendas.rename(columns={"Fecha": "date"})
        out_tiendas["Nombre"] = out_tiendas["Tienda"].apply(_vh_tienda_nombre)
        out_tiendas = out_tiendas[TIENDAS_COLUMNS]
    return out, out_tiendas

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()

def _vh_replace_period(uploaded_file, year, month, label):
    global df, df_tiendas
    if uploaded_file is None:
        return
    try:
        incoming, incoming_tiendas = _vh_normalize_uploaded_excel(uploaded_file)
        incoming = incoming[
            (incoming["date"].dt.year == year) & (incoming["date"].dt.month == month)
        ].copy()
        if incoming.empty:
            st.error(f"{label}: no encontré datos de {month:02d}/{year} en el archivo.")
            return

        df = df[~((df["date"].dt.year == year) & (df["date"].dt.month == month))].copy()
        df = pd.concat([df, incoming], ignore_index=True)
        df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

        if len(incoming_tiendas):
            incoming_tiendas = incoming_tiendas[
                (incoming_tiendas["date"].dt.year == year) & (incoming_tiendas["date"].dt.month == month)
            ].copy()
            df_tiendas = df_tiendas[
                ~((df_tiendas["date"].dt.year == year) & (df_tiendas["date"].dt.month == month))
            ].copy()
            df_tiendas = pd.concat([df_tiendas, incoming_tiendas], ignore_index=True)
            df_tiendas = (
                df_tiendas.sort_values(["date", "Tienda"])
                .drop_duplicates(subset=["date", "Tienda"], keep="last")
                .reset_index(drop=True)
            )

        try:
            import urllib.request
            import urllib.error
            import json as _json

            token = st.secrets.get("GITHUB_TOKEN")
            if token:
                repo = "2026-Masonline/masonline-dashboard"
                branch = "main"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "Masonline-Dashboard"
                }

                path = "data.csv"
                url = f"https://api.github.com/repos/{repo}/contents/{path}"
                request_get = urllib.request.Request(f"{url}?ref={branch}", headers=headers, method="GET")
                with urllib.request.urlopen(request_get, timeout=30) as response:
                    github_file = _json.loads(response.read().decode("utf-8"))
                sha = github_file["sha"]

                csv_text = df.sort_values("date").to_csv(index=False, date_format="%Y-%m-%d")
                content_b64 = base64.b64encode(csv_text.encode("utf-8")).decode("utf-8")
                payload = {
                    "message": f"Actualizar datos ecommerce - {label}",
                    "content": content_b64, "sha": sha, "branch": branch
                }
                request_put = urllib.request.Request(
                    url, data=_json.dumps(payload).encode("utf-8"),
                    headers={**headers, "Content-Type": "application/json"}, method="PUT"
                )
                with urllib.request.urlopen(request_put, timeout=30) as response:
                    response.read()

                if len(df_tiendas):
                    try:
                        path_t = "data_tiendas.csv"
                        url_t = f"https://api.github.com/repos/{repo}/contents/{path_t}"
                        sha_t = None
                        request_get_t = urllib.request.Request(f"{url_t}?ref={branch}", headers=headers, method="GET")
                        try:
                            with urllib.request.urlopen(request_get_t, timeout=30) as response:
                                sha_t = _json.loads(response.read().decode("utf-8"))["sha"]
                        except urllib.error.HTTPError as e_get:
                            if e_get.code != 404:
                                raise
                        csv_text_t = df_tiendas.sort_values(["date", "Tienda"]).to_csv(index=False, date_format="%Y-%m-%d")
                        content_b64_t = base64.b64encode(csv_text_t.encode("utf-8")).decode("utf-8")
                        payload_t = {"message": f"Actualizar datos por tienda - {label}", "content": content_b64_t, "branch": branch}
                        if sha_t:
                            payload_t["sha"] = sha_t
                        request_put_t = urllib.request.Request(
                            url_t, data=_json.dumps(payload_t).encode("utf-8"),
                            headers={**headers, "Content-Type": "application/json"}, method="PUT"
                        )
                        with urllib.request.urlopen(request_put_t, timeout=30) as response:
                            response.read()
                    except Exception:
                        st.caption(
                            "⚠️ El desglose por tienda no se pudo guardar esta vez — "
                            "el resto de los datos sí se guardó bien."
                        )
                st.success(f"{label}: datos cargados y guardados correctamente.")
            else:
                st.warning("Los datos se cargaron para esta sesión, pero GITHUB_TOKEN no está configurado.")
        except Exception as github_error:
            st.error(f"Los datos se cargaron, pero no se pudieron guardar en GitHub: {github_error}")
    except Exception as e:
        st.error(f"{label}: no pude procesar el Excel: {e}")

_hoy_tmp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
_vh_replace_period(upload_hoy, _hoy_tmp.year, _hoy_tmp.month, "Mes en curso (desde Venta hoy)")

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
# y sin Impuesto" (no trae esa info) — sale del archivo de Pedidos ("Vs de
# ventas"), el mismo que ya se sube para Comparativo / Venta fin de semana.
# Si todavía no se subió ese archivo, esta parte queda vacía hasta que se
# suba (no hace falta volver a subirlo acá, es compartido entre pestañas).
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
def _vh_cargar_pedidos_hoy(vsventas_bytes, tienda_codes_tuple, hoy_str):
    """Pedidos creados HOY, con su método de entrega y tienda — para los
    desgloses de abajo. Cacheado 3 minutos por archivo+día."""
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
        fecha = pd.to_datetime(d["commerceDateCreated"], errors="coerce").dt.normalize()
        d = d[fecha.astype(str).str[:10] == hoy_str]
        if not len(d):
            continue
        tienda_col = (
            d["shippingWarehouseReferenceId"].apply(lambda v: _vh_pedidos_codigo_tienda(v, tienda_codes))
            if "shippingWarehouseReferenceId" in d.columns else ""
        )
        metodo_col = d["shippingsType"] if "shippingsType" in d.columns else ""
        partes.append(pd.DataFrame({
            "Id": d["commerceSequentialId"].values,
            "Tienda": tienda_col,
            "Metodo": metodo_col,
        }))
    if not partes:
        return pd.DataFrame(columns=["Tienda", "Metodo"])
    out = pd.concat(partes, ignore_index=True, sort=False)
    # Dedup por ID de pedido (no por Tienda+Metodo juntos — varios pedidos
    # distintos de la misma tienda con el mismo método son normales y no
    # son duplicados).
    out = out.drop_duplicates(subset=["Id"])
    return out[["Tienda", "Metodo"]]

arg_today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
hoy_df = df[df["date"].dt.date == arg_today]

_vsventas_bytes_hoy = _vh_pedidos_get_shared_bytes(SHARED_VSVENTAS_PATH_PEDIDOS)
_tienda_codes_hoy = tuple(sorted(TIENDA_MAP.keys()))
pedidos_detalle_hoy = _vh_cargar_pedidos_hoy(_vsventas_bytes_hoy, _tienda_codes_hoy, arg_today.strftime("%Y-%m-%d"))

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
    {arg_today.strftime('%d/%m/%Y')}
    <small>Venta de HOY (en vivo)</small>
    <div class="live-badge">● EN VIVO · PARCIAL</div>
  </div>
</div>
""", unsafe_allow_html=True)

if not len(hoy_df):
    st.markdown(
        '<div class="empty-box">Todavía no hay datos de hoy — subí el Excel '
        '"Venta Con y sin Impuesto" del mes en curso (con la fila de hoy adentro) '
        'en la pestaña <b>app</b> para verlos acá.</div>',
        unsafe_allow_html=True
    )
    st.stop()

hoy_company = hoy_df["company_tax"].sum()
hoy_ecom = hoy_df["ecommerce_tax"].sum()
hoy_orders = hoy_df["orders"].sum()
hoy_units = hoy_df["units"].sum()
hoy_share = (hoy_ecom / hoy_company) if hoy_company else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #f5a623;">
      <div class="label" style="color:#f5a623;">PARTICIPACIÓN E-COMMERCE</div>
      <div class="value">{pct(hoy_share)}</div>
      <div class="small">Sobre la venta compañía de hoy</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #e8432c;">
      <div class="label" style="color:#e8432c;">VENTA ECOMMERCE</div>
      <div class="value" style="color:#e8432c;">{money(hoy_ecom)}</div>
      <div class="small">Compañía: {money(hoy_company)}</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #59636e;">
      <div class="label">PEDIDOS</div>
      <div class="value">{intfmt(hoy_orders)}</div>
      <div class="small">Pedidos Facturados (parcial)</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="card" style="border-top:4px solid #2f9e66;">
      <div class="label" style="color:#208653;">UNIDADES</div>
      <div class="value" style="color:#208653;">{intfmt(hoy_units)}</div>
      <div class="small">Vendidas hoy (parcial)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    '<div style="color:#9ca3af;font-size:12px;margin-top:14px;">'
    'Parcial — el día todavía no cerró, estos números van a seguir subiendo a medida '
    'que se actualice el archivo. "Pedidos" sale del Excel tal cual (Pedidos Facturados), '
    'no del ajuste por fecha de entrega que usan Venta diaria / Venta fin de semana.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown('<div class="section">Tiendas hoy</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Ranking por venta ecommerce de hoy, con pedidos de cada tienda.</div>',
    unsafe_allow_html=True
)

hoy_tiendas = df_tiendas[df_tiendas["date"].dt.date == arg_today] if len(df_tiendas) else df_tiendas
if len(hoy_tiendas):
    agg = (
        hoy_tiendas.groupby(["Tienda", "Nombre"], as_index=False)
        .agg(ecommerce_tax=("ecommerce_tax", "sum"), orders=("orders", "sum"))
        .sort_values("ecommerce_tax", ascending=False)
    )
    rows_html = ""
    for i, r in enumerate(agg.itertuples(), start=1):
        nombre = str(r.Nombre) if r.Nombre else ""
        tienda_label = f"{r.Tienda} - {nombre}" if nombre else str(r.Tienda)
        rows_html += (
            '<tr>'
            f'<td>{i}</td>'
            f'<td>{tienda_label}</td>'
            f'<td style="text-align:center;">{intfmt(r.orders)}</td>'
            f'<td style="text-align:right;font-weight:800;color:#208653;">{money(r.ecommerce_tax)}</td>'
            '</tr>'
        )
    st.markdown(
        '<div class="rank-table-card">'
        '<div class="table-scroll">'
        '<table class="rank-table"><thead><tr>'
        '<th></th><th>Tienda</th>'
        '<th style="text-align:center;">Pedidos eCommerce</th>'
        '<th style="text-align:right;">Venta eCommerce (con impuesto)</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>'
        '</div></div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="empty-box">Todavía no hay desglose por tienda para hoy. '
        'Se completa solo la próxima vez que se suba el Excel desde "app" '
        '(si trae las columnas Tienda y Nombre).</div>',
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------
# Método de entrega + Tiendas con más pedidos (por CANTIDAD de pedidos,
# no por venta) — fuente: archivo de Pedidos ("Vs de ventas"), filtrado a
# los pedidos creados hoy.
# ---------------------------------------------------------------------
st.markdown('<div class="section">Método de entrega</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Cantidad de pedidos de hoy por método de entrega '
    '(sale del archivo de Pedidos / "Vs de ventas", el mismo que se usa en Comparativo).</div>',
    unsafe_allow_html=True
)

if pedidos_detalle_hoy is None:
    st.markdown(
        '<div class="empty-box">Todavía no se subió el archivo de Pedidos ("Vs de ventas"). '
        'Se completa solo cuando ese archivo esté disponible (se sube en Comparativo / '
        'Venta fin de semana / Venta diaria — es compartido entre pestañas).</div>',
        unsafe_allow_html=True
    )
elif not len(pedidos_detalle_hoy):
    st.markdown(
        '<div class="empty-box">Todavía no hay pedidos registrados hoy en el archivo de Pedidos.</div>',
        unsafe_allow_html=True
    )
else:
    metodo_agg = (
        pedidos_detalle_hoy.assign(MetodoLabel=pedidos_detalle_hoy["Metodo"].apply(_vh_metodo_entrega_label))
        .groupby("MetodoLabel", as_index=False)
        .size()
        .rename(columns={"size": "Pedidos"})
        .sort_values("Pedidos", ascending=False)
    )
    total_metodo = int(metodo_agg["Pedidos"].sum())
    rows_html = ""
    for i, r in enumerate(metodo_agg.itertuples(), start=1):
        pct = (r.Pedidos / total_metodo * 100) if total_metodo else 0
        rows_html += (
            '<tr>'
            f'<td>{i}</td>'
            f'<td>{r.MetodoLabel}</td>'
            f'<td style="text-align:center;font-weight:800;color:#208653;">{intfmt(r.Pedidos)}</td>'
            f'<td style="text-align:right;">{pct:.1f}%</td>'
            '</tr>'
        )
    st.markdown(
        '<div class="rank-table-card">'
        '<div class="table-scroll">'
        '<table class="rank-table"><thead><tr>'
        '<th></th><th>Método de entrega</th>'
        '<th style="text-align:center;">Pedidos</th>'
        '<th style="text-align:right;">% del total</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>'
        '</div></div>',
        unsafe_allow_html=True
    )

st.markdown('<div class="section">Tiendas con más pedidos (hoy)</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Ranking por CANTIDAD de pedidos de hoy (no por venta) — '
    'misma fuente que el método de entrega.</div>',
    unsafe_allow_html=True
)

if pedidos_detalle_hoy is not None and len(pedidos_detalle_hoy):
    tienda_pedidos_agg = (
        pedidos_detalle_hoy.groupby("Tienda", as_index=False)
        .size()
        .rename(columns={"size": "Pedidos"})
        .sort_values("Pedidos", ascending=False)
    )
    rows_html = ""
    for i, r in enumerate(tienda_pedidos_agg.itertuples(), start=1):
        codigo = str(r.Tienda)
        nombre = TIENDA_MAP.get(codigo, "")
        tienda_label = f"{codigo} - {nombre}" if nombre else codigo
        rows_html += (
            '<tr>'
            f'<td>{i}</td>'
            f'<td>{tienda_label}</td>'
            f'<td style="text-align:center;font-weight:800;color:#208653;">{intfmt(r.Pedidos)}</td>'
            '</tr>'
        )
    st.markdown(
        '<div class="rank-table-card">'
        '<div class="table-scroll">'
        '<table class="rank-table"><thead><tr>'
        '<th></th><th>Tienda</th>'
        '<th style="text-align:center;">Pedidos</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table>'
        '</div></div>',
        unsafe_allow_html=True
    )
elif pedidos_detalle_hoy is not None:
    st.markdown(
        '<div class="empty-box">Todavía no hay pedidos registrados hoy en el archivo de Pedidos.</div>',
        unsafe_allow_html=True
    )
