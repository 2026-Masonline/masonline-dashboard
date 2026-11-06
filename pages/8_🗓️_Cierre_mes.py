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

LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"
_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
_RESUMEN_FONT_BOLD_PATH = _FONTS_DIR / "DejaVuSans-Bold.ttf"
_RESUMEN_FONT_REG_PATH = _FONTS_DIR / "DejaVuSans.ttf"

# ---------------------------------------------------------------------
# Venta $ / Facturación: esta página tiene su PROPIO archivo guardado
# aparte (cuadro de carga acá abajo), separado de data.csv — a pedido de
# Emi: si subiera el Excel "Venta Con y sin Impuesto" por la vía de
# siempre (página principal), eso actualiza data.csv y le cambia los
# números a Venta diaria / Venta fin de semana, que no quiere tocar
# cuando solo está cerrando un mes acá. Queda 100% independiente: no se
# completa con data.csv los días/meses que todavía no se subieron acá.
# Pedidos y Unidades siguen saliendo de "Vs de ventas" (compartido con el
# resto de las páginas, ver más abajo), sin cambios.
# ---------------------------------------------------------------------
SHARED_DIR_CIERRE = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_CIERRE_VENTA_PATH = SHARED_DIR_CIERRE / "cierre_mes_venta.csv"
SHARED_CIERRE_VENTA_TIENDAS_PATH = SHARED_DIR_CIERRE / "cierre_mes_venta_tiendas.csv"
# Pedidos (Vs de ventas) de esta página, independiente del "vsventas.xlsx"
# compartido que usan Comparativo/Venta diaria/etc. — mismo motivo que la
# Venta $ de arriba: a pedido de Emi, subirlo acá no les tiene que tocar
# nada a esas otras páginas.
SHARED_CIERRE_PEDIDOS_PATH = SHARED_DIR_CIERRE / "cierre_mes_pedidos.xlsx"

# Código de tienda (columna "Tienda" del Excel) -> nombre. Mismo listado
# que ya usa la página principal, copiado acá porque cada página arma su
# propia lógica (convención del proyecto).
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

def _cierre_norm_tienda_code(v):
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return str(v).strip()

def _cierre_tienda_nombre(codigo):
    return TIENDA_MAP.get(codigo, codigo)

def _cierre_github_headers():
    token = st.secrets.get("GITHUB_TOKEN") if hasattr(st, "secrets") else None
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Masonline-Dashboard",
    }

def _cierre_fetch_from_github(shared_path):
    headers = _cierre_github_headers()
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
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read()
    except Exception:
        return None

def _cierre_get_shared_bytes(shared_path):
    if shared_path.exists():
        try:
            data = shared_path.read_bytes()
            if data:
                return data
        except Exception:
            pass
    content = _cierre_fetch_from_github(shared_path)
    if content:
        try:
            shared_path.parent.mkdir(parents=True, exist_ok=True)
            shared_path.write_bytes(content)
        except Exception:
            pass
        return content
    return None

def _cierre_save_to_github(shared_path, content_bytes, label):
    headers = _cierre_github_headers()
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
            with urllib.request.urlopen(request_get, timeout=60) as response:
                sha = _json.loads(response.read().decode("utf-8"))["sha"]
        except urllib.error.HTTPError as e_get:
            if e_get.code != 404:
                raise
            # 404 = todavía no existe ese archivo en el repo; se crea solo.
        payload = {
            "message": f"Actualizar reporte - {label}",
            "content": _base64.b64encode(content_bytes).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        request_put = urllib.request.Request(
            url, data=_json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"}, method="PUT",
        )
        with urllib.request.urlopen(request_put, timeout=60) as response:
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

def _cierre_normalize_uploaded_excel(file):
    """Mismo formato que 'Venta Con y sin Impuesto' (Fecha/Facturacion/
    Venta - Ecommerce), pero sin exigir las columnas de Pedidos/Cantidad:
    esta página ya saca esos dos datos de 'Vs de ventas'."""
    raw = pd.read_excel(file, sheet_name=0, header=None)
    header_row = None
    for i in range(min(10, len(raw))):
        vals = raw.iloc[i].astype(str).str.strip().tolist()
        if "Fecha" in vals and "Facturacion" in vals and "Venta - Ecommerce" in vals:
            header_row = i
            break
    if header_row is None:
        raise ValueError(
            "no encontré las columnas Fecha, Facturacion y Venta - Ecommerce"
        )
    d = pd.read_excel(file, sheet_name=0, header=header_row)
    required = ["Fecha", "Facturacion", "Venta - Ecommerce"]
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError("faltan columnas: " + ", ".join(missing))
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    for c in required[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    COL_COMPANY_NETO = "Venta Comercial Operativa"
    if COL_COMPANY_NETO in d.columns:
        d[COL_COMPANY_NETO] = pd.to_numeric(d[COL_COMPANY_NETO], errors="coerce").fillna(0)
    else:
        d[COL_COMPANY_NETO] = d["Facturacion"]
    d = d.dropna(subset=["Fecha"])

    out = d.groupby("Fecha", as_index=False).agg(
        company_tax=("Facturacion", "sum"),
        company_tax_neto=(COL_COMPANY_NETO, "sum"),
        ecommerce_tax=("Venta - Ecommerce", "sum"),
    )
    out = out.rename(columns={"Fecha": "date"})

    out_tiendas = pd.DataFrame(columns=["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax"])
    if "Tienda" in d.columns:
        dt = d.copy()
        dt["Tienda"] = dt["Tienda"].apply(_cierre_norm_tienda_code)
        out_tiendas = dt.groupby(["Fecha", "Tienda"], as_index=False).agg(
            company_tax=("Facturacion", "sum"),
            ecommerce_tax=("Venta - Ecommerce", "sum"),
        )
        out_tiendas = out_tiendas.rename(columns={"Fecha": "date"})
        out_tiendas["Nombre"] = out_tiendas["Tienda"].apply(_cierre_tienda_nombre)

    return out, out_tiendas

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:14px 16px;margin-bottom:16px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    CARGAR VENTA DEL MES A CERRAR
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí acá el/los Excel "Venta Con y sin Impuesto" del mes que estás cerrando (podés
    elegir más de uno a la vez). Queda guardado solo para esta página — no modifica
    Venta diaria ni Venta fin de semana.
  </div>
</div>
""", unsafe_allow_html=True)

_cierre_uploads = st.file_uploader(
    "Archivos Venta Con y sin Impuesto (Cierre de mes)",
    type=["xlsx", "xls"],
    key="cierre_mes_upload",
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if _cierre_uploads:
    _cierre_nuevas, _cierre_nuevas_tiendas, _cierre_errores = [], [], []
    for _cf in _cierre_uploads:
        try:
            _co, _cot = _cierre_normalize_uploaded_excel(_cf)
            _cierre_nuevas.append(_co)
            if len(_cot):
                _cierre_nuevas_tiendas.append(_cot)
        except Exception as _ce:
            _cierre_errores.append(f"{_cf.name}: {_ce}")

    if _cierre_errores:
        st.error("No pude procesar: " + " · ".join(_cierre_errores))

    if _cierre_nuevas:
        _cierre_prev_bytes = _cierre_get_shared_bytes(SHARED_CIERRE_VENTA_PATH)
        _cierre_prev_df = pd.DataFrame(columns=["date", "company_tax", "company_tax_neto", "ecommerce_tax"])
        if _cierre_prev_bytes:
            try:
                _cierre_prev_df = pd.read_csv(io.BytesIO(_cierre_prev_bytes))
                _cierre_prev_df["date"] = pd.to_datetime(_cierre_prev_df["date"], errors="coerce")
            except Exception:
                pass
        _cierre_combinado = pd.concat([_cierre_prev_df] + _cierre_nuevas, ignore_index=True)
        _cierre_combinado = (
            _cierre_combinado.dropna(subset=["date"])
            .sort_values("date")
            .drop_duplicates(subset=["date"], keep="last")
            .reset_index(drop=True)
        )
        _cierre_csv_bytes = _cierre_combinado.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")
        try:
            SHARED_CIERRE_VENTA_PATH.parent.mkdir(parents=True, exist_ok=True)
            SHARED_CIERRE_VENTA_PATH.write_bytes(_cierre_csv_bytes)
        except Exception:
            pass
        _cierre_ok, _cierre_err = _cierre_save_to_github(
            SHARED_CIERRE_VENTA_PATH, _cierre_csv_bytes, "Cierre de mes (Venta)"
        )

        if _cierre_nuevas_tiendas:
            _cierre_prev_bytes_t = _cierre_get_shared_bytes(SHARED_CIERRE_VENTA_TIENDAS_PATH)
            _cierre_prev_df_t = pd.DataFrame(
                columns=["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax"]
            )
            if _cierre_prev_bytes_t:
                try:
                    _cierre_prev_df_t = pd.read_csv(io.BytesIO(_cierre_prev_bytes_t))
                    _cierre_prev_df_t["date"] = pd.to_datetime(_cierre_prev_df_t["date"], errors="coerce")
                    _cierre_prev_df_t["Tienda"] = _cierre_prev_df_t["Tienda"].astype(str)
                except Exception:
                    pass
            _cierre_combinado_t = pd.concat([_cierre_prev_df_t] + _cierre_nuevas_tiendas, ignore_index=True)
            _cierre_combinado_t = (
                _cierre_combinado_t.dropna(subset=["date"])
                .sort_values(["date", "Tienda"])
                .drop_duplicates(subset=["date", "Tienda"], keep="last")
                .reset_index(drop=True)
            )
            _cierre_csv_bytes_t = _cierre_combinado_t.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")
            try:
                SHARED_CIERRE_VENTA_TIENDAS_PATH.parent.mkdir(parents=True, exist_ok=True)
                SHARED_CIERRE_VENTA_TIENDAS_PATH.write_bytes(_cierre_csv_bytes_t)
            except Exception:
                pass
            _cierre_save_to_github(
                SHARED_CIERRE_VENTA_TIENDAS_PATH, _cierre_csv_bytes_t, "Cierre de mes (Venta por tienda)"
            )

        if _cierre_ok:
            st.success("Archivo(s) cargados y guardados — ya se ven abajo.")
        else:
            st.warning(
                "Se cargó para esta sesión, pero el respaldo permanente en GitHub falló "
                f"({_cierre_err}) — si la app se reinicia vas a tener que volver a subirlo."
            )

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:14px 16px;margin-bottom:16px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    CARGAR PEDIDOS DEL MES A CERRAR
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí acá el Excel "Vs de ventas" (Pedidos) del mes que estás cerrando. Queda guardado
    solo para esta página — no modifica Comparativo, Venta diaria ni el resto de las
    pestañas que usan ese mismo reporte. Reemplaza al anterior con cada subida (subí el
    archivo completo, con todas las hojas/años que necesites ver acá).
  </div>
</div>
""", unsafe_allow_html=True)

_cierre_pedidos_upload = st.file_uploader(
    "Archivo Vs de ventas / Pedidos (Cierre de mes)",
    type=["xlsx", "xls"],
    key="cierre_mes_pedidos_upload",
    label_visibility="collapsed",
)

if _cierre_pedidos_upload is not None:
    _cierre_pedidos_bytes_nuevo = _cierre_pedidos_upload.getvalue()
    try:
        SHARED_CIERRE_PEDIDOS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SHARED_CIERRE_PEDIDOS_PATH.write_bytes(_cierre_pedidos_bytes_nuevo)
    except Exception:
        pass
    _cierre_pedidos_ok, _cierre_pedidos_err = _cierre_save_to_github(
        SHARED_CIERRE_PEDIDOS_PATH, _cierre_pedidos_bytes_nuevo, "Cierre de mes (Pedidos)"
    )
    if _cierre_pedidos_ok:
        st.success("Archivo de Pedidos cargado y guardado — ya se ve abajo.")
    else:
        st.warning(
            "Se cargó para esta sesión, pero el respaldo permanente en GitHub falló "
            f"({_cierre_pedidos_err}) — si la app se reinicia vas a tener que volver a subirlo."
        )

_cierre_venta_bytes = _cierre_get_shared_bytes(SHARED_CIERRE_VENTA_PATH)
if _cierre_venta_bytes:
    base_df = pd.read_csv(io.BytesIO(_cierre_venta_bytes))
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "company_tax_neto"]:
        if col not in base_df.columns:
            base_df[col] = 0
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    base_df = base_df.dropna(subset=["date"])
else:
    base_df = pd.DataFrame(columns=["date", "company_tax", "company_tax_neto", "ecommerce_tax"])
    base_df["date"] = pd.to_datetime(base_df["date"])

# "orders"/"units" de acá quedan en 0 a propósito: más abajo se pisan
# siempre con lo que traiga "Vs de ventas" (fuente real de Pedidos y
# Unidades en esta página) para las fechas que tenga; si Vs de ventas no
# tiene una fecha puntual, antes caía a data.csv como respaldo — ahora, al
# ser esta página independiente, esa fecha simplemente queda en 0 en vez
# de arrastrar un dato de otra fuente.
base_df["orders"] = 0
base_df["units"] = 0
# Guardamos la Compañía CON impuesto aparte (antes de pisarla con la
# versión sin impuesto) — la tarjeta COMPAÑÍA sigue mostrando sin
# impuesto, pero el % SHARE compara impuesto contra impuesto (Ecommerce
# con impuesto / Compañía con impuesto), a pedido de Emi.
base_df["company_tax_con_impuesto"] = base_df["company_tax"]
base_df["company_tax"] = base_df["company_tax_neto"].where(
    base_df["company_tax_neto"].notna(), base_df["company_tax"]
)

TIENDAS_COLUMNS = ["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax", "orders", "units"]

_cierre_tiendas_bytes = _cierre_get_shared_bytes(SHARED_CIERRE_VENTA_TIENDAS_PATH)
if _cierre_tiendas_bytes:
    base_df_tiendas = pd.read_csv(io.BytesIO(_cierre_tiendas_bytes))
    base_df_tiendas["date"] = pd.to_datetime(base_df_tiendas["date"], errors="coerce")
    base_df_tiendas["Tienda"] = base_df_tiendas["Tienda"].astype(str)
    for col in ["company_tax", "ecommerce_tax"]:
        base_df_tiendas[col] = pd.to_numeric(base_df_tiendas[col], errors="coerce").fillna(0)
    base_df_tiendas = base_df_tiendas.dropna(subset=["date"])
    base_df_tiendas["orders"] = 0
    base_df_tiendas["units"] = 0
    base_df_tiendas = base_df_tiendas[TIENDAS_COLUMNS]
else:
    base_df_tiendas = pd.DataFrame(columns=TIENDAS_COLUMNS)
    base_df_tiendas["date"] = pd.to_datetime(base_df_tiendas["date"])

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()
if len(df_tiendas):
    df_tiendas["date"] = pd.to_datetime(df_tiendas["date"], errors="coerce")
    df_tiendas = df_tiendas.dropna(subset=["date"]).copy()

# ---------------------------------------------------------------------
# Pedidos y Unidades: salen del "Vs de ventas" PROPIO de esta página
# (cuadro "CARGAR PEDIDOS DEL MES A CERRAR" más arriba, archivo
# SHARED_CIERRE_PEDIDOS_PATH) — no del "vsventas.xlsx" compartido que usan
# Venta diaria, Comparativo, Venta hoy, etc., a pedido de Emi (mismo
# motivo que la Venta $). Se cuentan por fecha de CREACIÓN del pedido —
# mismo criterio que Venta diaria.
# ---------------------------------------------------------------------
SHARED_VSVENTAS_PATH_PEDIDOS = SHARED_CIERRE_PEDIDOS_PATH


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
    "salesChannelPrefix", "totalAmount", "itemsQuantity",
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
    # itemsQuantity es la columna que siempre viene en el archivo; algunos
    # exports no traen itemsPickedQuantity (o la traen vacía), y ahí las
    # Unidades quedaban en 0 — a pedido de Emi, ahora toma itemsQuantity
    # como principal, con itemsPickedQuantity como respaldo solo si
    # itemsQuantity no está.
    if "itemsQuantity" in d.columns:
        unidades_col = pd.to_numeric(d["itemsQuantity"], errors="coerce").fillna(0)
    elif "itemsPickedQuantity" in d.columns:
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
        'Subí el Excel "Venta Con y sin Impuesto" de ese mes en el cuadro de arriba.'
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


st.markdown(
    '<div class="footer">'
    '<span>Fuente: venta con impuesto de MicroStrategy.</span>'
    '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
    '</div>',
    unsafe_allow_html=True
)
