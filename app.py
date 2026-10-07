import io
import json
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="MásOnline | Pedidos STS",
    page_icon="🧾",
    layout="wide"
)

APP_CSS = """
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
    .hero-brand { font-size: 26px; font-weight: 800; letter-spacing: -.5px; }
    .hero-sub { font-size: 11px; letter-spacing: 3px; margin-top: 3px; opacity: .85; }

    .section {
        font-size: 19px; font-weight: 800; color: #20252b;
        margin: 26px 0 4px; display:flex; align-items:center; gap:10px;
    }
    .section-desc { color:#6b7280; font-size:12.5px; margin: -2px 0 10px; }

    .kpi-row { display:flex; gap:14px; margin-top:6px; flex-wrap:wrap; }
    .kpi {
        background:#fafaf8; border:1px solid #eef0ef; border-radius:12px;
        padding:14px 18px; flex:1; min-width:150px;
    }
    .kpi .label { color:#6b7280; font-size:11.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
    .kpi .value { color:#ff5a1f; font-size:26px; font-weight:800; margin-top:6px; }

    table.dashtable {
        width: 100%; border-collapse: collapse; font-size: 13px;
        background: white; border-radius: 10px; overflow: hidden;
    }
    table.dashtable thead th {
        background: #20252b; color: #ffffff; text-align: left;
        padding: 9px 12px; font-size: 11.5px; font-weight: 700;
        text-transform: uppercase; letter-spacing: .03em;
        position: sticky; top: 0;
    }
    table.dashtable tbody td {
        padding: 8px 12px; border-bottom: 1px solid #eef0ef; color:#20252b;
    }
    table.dashtable tbody tr:nth-child(even) { background: #fafaf8; }
    table.dashtable tbody tr:hover { background: #fdf1e8; }

    div[data-testid="stExpander"] {
        border: 1px solid #e8ebef; border-radius: 10px; margin-top: 6px;
    }
    div[data-testid="stExpander"] summary {
        background: #f4f5f4; border-radius: 10px; padding: 10px 14px;
    }
    div[data-testid="stExpander"] summary:hover {
        background: #fdeee5;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #20252b !important; font-weight: 800 !important; font-size: 13.5px !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #ff5a1f !important;
    }

    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; max-height: 640px; overflow-y: auto; }

    div[data-testid="stDownloadButton"] button {
        background: #ffffff; color: #ff5a1f; border: 1.5px solid #ff5a1f;
        border-radius: 8px; font-size: 12.5px; font-weight: 700; padding: 4px 14px;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: #ff5a1f; color: #ffffff; border-color: #ff5a1f;
    }

    @media (max-width: 600px) {
        .block-container { padding: 0 0.6rem 1rem; }
        .hero { flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 18px; margin: -1rem -0.6rem 1rem; }
        .hero-brand { font-size: 20px; }
        .section { font-size: 16px; margin: 20px 0 4px; }
        table.dashtable { font-size: 12px; }
        table.dashtable thead th, table.dashtable tbody td { padding: 7px 8px; }
        .kpi { min-width: 130px; padding: 12px 14px; }
        .kpi .value { font-size: 22px; }
    }
"""

st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def norm_cols(df):
    df = df.copy()
    df.columns = [str(c).replace("\xa0", " ").strip() for c in df.columns]
    return df

def norm_txt(v):
    if pd.isna(v):
        return ""
    return str(v).replace("\xa0", " ").strip()

def norm_codigo(v):
    """Como norm_txt, pero evita que un código (commerceSequentialId,
    shippingWarehouseReferenceId) quede como '2998.0' por venir de una
    columna numérica del Excel."""
    if pd.isna(v):
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return norm_txt(v)

def safe_open_excel(file_bytes):
    if file_bytes is None:
        return None
    try:
        return pd.ExcelFile(io.BytesIO(file_bytes))
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return None

def table_html(df):
    inner = df.to_html(escape=False, index=False, classes="dashtable", border=0)
    return f'<div class="table-scroll">{inner}</div>'

def kpi_card(label, value):
    return (
        '<div class="kpi">'
        '<div class="label">' + str(label) + '</div>'
        '<div class="value">' + str(value) + '</div>'
        '</div>'
    )

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

def mes_label(ts):
    if pd.isna(ts):
        return ""
    return f"{MESES_ES.get(ts.month, ts.month).capitalize()} {ts.year}"

# Código de tienda (shippingWarehouseReferenceId) -> nombre. Mismo listado
# que usan Productividad Pickers y la pestaña app.
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

def tienda_nombre(codigo):
    return TIENDA_MAP.get(norm_txt(codigo), norm_txt(codigo))

# ---------------------------------------------------------------------
# Almacenamiento: esta pestaña ahora guarda los pedidos MES A MES. Cada
# vez que se sube un archivo (el export "order-operation" de un mes), se
# arman las 3 columnas pedidas y se guarda en su propia "tarjeta" —
# shared_uploads/pedidos_sts_meses/<AAAA-MM>.csv en GitHub — sin tocar los
# meses ya cargados. Un índice aparte (pedidos_sts_index.json) lleva la
# lista de qué meses ya tienen datos. Si se vuelve a subir un mes que ya
# estaba, se reemplaza (no se duplica).
# ---------------------------------------------------------------------

SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

MESES_SUBDIR = "pedidos_sts_meses"
SHARED_MESES_DIR = SHARED_DIR / MESES_SUBDIR
SHARED_MESES_DIR.mkdir(parents=True, exist_ok=True)

INDEX_LOCAL_PATH = SHARED_DIR / "pedidos_sts_index.json"
INDEX_REPO_PATH = "shared_uploads/pedidos_sts_index.json"

GITHUB_REPO = "2026-Masonline/masonline-dashboard"
GITHUB_BRANCH = "main"

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

def _github_get_raw(repo_path):
    """Trae un archivo del repo en formato "raw" (soporta archivos grandes;
    el formato normal devuelve contenido vacío sin avisar para archivos de
    más de 1 MB)."""
    headers = _github_headers()
    if not headers:
        return None
    import urllib.request
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}?ref={GITHUB_BRANCH}"
    raw_headers = {**headers, "Accept": "application/vnd.github.raw+json"}
    try:
        request_get = urllib.request.Request(url, headers=raw_headers, method="GET")
        with urllib.request.urlopen(request_get, timeout=30) as response:
            return response.read()
    except Exception:
        return None

def _github_put(repo_path, content_bytes, label):
    """Guarda (crea o actualiza) un archivo en el repo."""
    headers = _github_headers()
    if not headers:
        return False
    import urllib.request
    import urllib.error
    import base64
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}"
    try:
        sha = None
        request_get = urllib.request.Request(f"{url}?ref={GITHUB_BRANCH}", headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request_get, timeout=30) as response:
                sha = json.loads(response.read().decode("utf-8"))["sha"]
        except urllib.error.HTTPError as e_get:
            if e_get.code != 404:
                raise
        payload = {
            "message": f"Actualizar reporte - {label}",
            "content": base64.b64encode(content_bytes).decode("utf-8"),
            "branch": GITHUB_BRANCH,
        }
        if sha:
            payload["sha"] = sha
        request_put = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(request_put, timeout=30) as response:
            response.read()
        return True
    except Exception:
        return False

def _month_local_path(month_key):
    return SHARED_MESES_DIR / f"{month_key}.csv"

def _month_repo_path(month_key):
    return f"shared_uploads/{MESES_SUBDIR}/{month_key}.csv"

def load_index():
    """Lista de meses (ej. '2026-01') que ya tienen datos guardados,
    ordenada del más reciente al más viejo."""
    try:
        if INDEX_LOCAL_PATH.exists():
            data = INDEX_LOCAL_PATH.read_bytes()
            if data:
                return sorted(set(json.loads(data.decode("utf-8"))), reverse=True)
    except Exception:
        pass
    raw = _github_get_raw(INDEX_REPO_PATH)
    if raw:
        try:
            meses = json.loads(raw.decode("utf-8"))
            try:
                INDEX_LOCAL_PATH.write_bytes(raw)
            except Exception:
                pass
            return sorted(set(meses), reverse=True)
        except Exception:
            return []
    return []

def save_index(meses):
    meses = sorted(set(meses), reverse=True)
    content = json.dumps(meses).encode("utf-8")
    try:
        INDEX_LOCAL_PATH.write_bytes(content)
    except Exception:
        pass
    _github_put(INDEX_REPO_PATH, content, "Pedidos STS (índice de meses)")
    return meses

def load_month_df(month_key):
    path = _month_local_path(month_key)
    content = None
    if path.exists():
        try:
            data = path.read_bytes()
            if data:
                content = data
        except Exception:
            pass
    if content is None:
        content = _github_get_raw(_month_repo_path(month_key))
        if content:
            try:
                path.write_bytes(content)
            except Exception:
                pass
    if not content:
        return None
    try:
        df = pd.read_csv(
            io.BytesIO(content),
            dtype={"Numero de pedido": str, "Numero de tienda": str, "Mes": str},
        )
        df["_mes_ord"] = pd.PeriodIndex(df["_mes_ord"].astype(str), freq="M")
        return df
    except Exception:
        return None

def save_month_df(month_key, df_mes):
    out = df_mes[["Mes", "Numero de pedido", "Numero de tienda", "_mes_ord"]].copy()
    out["_mes_ord"] = out["_mes_ord"].astype(str)
    content = out.to_csv(index=False).encode("utf-8")
    path = _month_local_path(month_key)
    try:
        path.write_bytes(content)
    except Exception:
        pass
    _github_put(_month_repo_path(month_key), content, f"Pedidos STS {month_key}")
    meses = load_index()
    if month_key not in meses:
        meses.append(month_key)
        save_index(meses)

# ---------------------------------------------------------------------
# Procesar un archivo recién subido: arma las 3 columnas pedidas —
# Mes (de deliveryFinishDate), Número de pedido (commerceSequentialId) y
# Número de tienda (shippingWarehouseReferenceId) — juntando TODAS las
# hojas del archivo que tengan esas columnas (por si viene una hoja por
# período). Se descartan las filas sin commerceSequentialId (Pick&Mix /
# devoluciones RMA, que no tienen un "número de pedido" real).
# ---------------------------------------------------------------------

REQUIRED_COLS = ["commerceSequentialId", "shippingWarehouseReferenceId", "deliveryFinishDate"]

def find_all_sheets(xl, required_cols):
    required = {c.lower() for c in required_cols}
    frames = []
    hojas_usadas = []
    hojas_descartadas = []
    for name in xl.sheet_names:
        try:
            df = xl.parse(name)
        except Exception as e:
            hojas_descartadas.append(f"{name} (no se pudo leer: {e})")
            continue
        df = norm_cols(df)
        cols = {c.lower() for c in df.columns}
        if required.issubset(cols):
            frames.append(df)
            hojas_usadas.append(f"{name} ({len(df):,} filas)".replace(",", "."))
        else:
            faltantes = required - cols
            hojas_descartadas.append(f"{name} (sin columnas: {', '.join(sorted(faltantes))})")
    if not frames:
        return None, hojas_usadas, hojas_descartadas
    return pd.concat(frames, ignore_index=True), hojas_usadas, hojas_descartadas

def procesar_archivo(file_bytes):
    xl = safe_open_excel(file_bytes)
    if xl is None:
        return {"ok": False, "hojas_usadas": [], "hojas_descartadas": []}
    df_raw, hojas_usadas, hojas_descartadas = find_all_sheets(xl, REQUIRED_COLS)
    if df_raw is None:
        return {"ok": False, "hojas_usadas": hojas_usadas, "hojas_descartadas": hojas_descartadas}
    d = df_raw.copy()
    filas_antes = len(d)
    d["_fecha"] = pd.to_datetime(d["deliveryFinishDate"], errors="coerce")
    sin_fecha_valida = int(d["_fecha"].isna().sum())
    d = d.dropna(subset=["commerceSequentialId", "_fecha"]).copy()
    d["Mes"] = d["_fecha"].apply(mes_label)
    d["_mes_ord"] = d["_fecha"].dt.to_period("M")
    d["Numero de pedido"] = d["commerceSequentialId"].apply(norm_codigo)
    d["Numero de tienda"] = d["shippingWarehouseReferenceId"].apply(norm_codigo)
    return {
        "ok": True,
        "data": d[["Mes", "Numero de pedido", "Numero de tienda", "_mes_ord"]],
        "hojas_usadas": hojas_usadas,
        "hojas_descartadas": hojas_descartadas,
        "filas_antes": filas_antes,
        "sin_fecha_valida": sin_fecha_valida,
    }

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.markdown("""
<div class="hero">
  <div>
    <div class="hero-brand">🧾 Pedidos STS</div>
    <div class="hero-sub">MES · NÚMERO DE PEDIDO · NÚMERO DE TIENDA</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Cargar un mes
# ---------------------------------------------------------------------

st.markdown('<div class="section">Cargar pedidos de un mes</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">Subí acá el archivo de Pedidos (export "order-operation") de un mes — '
    'se guarda en su propia tarjeta, abajo, y se suma a los meses ya cargados sin borrarlos. '
    'Si volvés a subir un mes que ya estaba, lo reemplaza.</div>',
    unsafe_allow_html=True
)
nuevo_archivo = st.file_uploader(
    "Archivo de Pedidos", type=["xlsx", "xls"], key="pedidos_sts_upload", label_visibility="collapsed"
)

if nuevo_archivo is not None:
    firma = (nuevo_archivo.name, nuevo_archivo.size)
    if st.session_state.get("_pedidos_sts_firma") != firma:
        with st.spinner("Procesando archivo…"):
            resultado = procesar_archivo(nuevo_archivo.getvalue())
        if not resultado["ok"]:
            st.error(
                "No encontré las columnas necesarias (commerceSequentialId, "
                "shippingWarehouseReferenceId, deliveryFinishDate) en ninguna hoja de ese archivo."
            )
        else:
            d_nuevo = resultado["data"]
            if d_nuevo.empty:
                st.warning("El archivo no tiene pedidos con fecha de entrega válida.")
            else:
                resumen = []
                with st.spinner("Guardando por mes…"):
                    for mes_ord, grupo in d_nuevo.groupby("_mes_ord"):
                        month_key = str(mes_ord)
                        save_month_df(month_key, grupo)
                        resumen.append(
                            f"{grupo['Mes'].iloc[0]} ({len(grupo):,} pedidos)".replace(",", ".")
                        )
                st.success("Guardado → " + " · ".join(resumen))
            with st.expander("Detalle técnico de este archivo"):
                st.markdown(
                    f"**Hojas usadas** ({len(resultado['hojas_usadas'])}): "
                    + (", ".join(resultado["hojas_usadas"]) if resultado["hojas_usadas"] else "ninguna")
                )
                if resultado["hojas_descartadas"]:
                    st.markdown(
                        f"**Hojas descartadas** ({len(resultado['hojas_descartadas'])}): "
                        + ", ".join(resultado["hojas_descartadas"])
                    )
        st.session_state["_pedidos_sts_firma"] = firma

# ---------------------------------------------------------------------
# Armar la tabla combinada con todos los meses ya guardados
# ---------------------------------------------------------------------

index_meses = load_index()
frames = [load_month_df(m) for m in index_meses]
frames = [f for f in frames if f is not None and not f.empty]

if not frames:
    st.markdown("""
    <div style="background:white;border:1px solid #e8ebef;border-radius:12px;
    padding:12px 16px;margin:14px 0;">
      <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
        TODAVÍA NO HAY MESES CARGADOS
      </div>
      <div style="font-size:12px;color:#6b7280;">
        Subí arriba el archivo de Pedidos de un mes para empezar a armar el listado.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

tabla = pd.concat(frames, ignore_index=True).sort_values(
    ["_mes_ord", "Numero de pedido"], ascending=[False, True]
)

# ---------------------------------------------------------------------
# Cards por mes
# ---------------------------------------------------------------------

st.markdown('<div class="section">Meses cargados</div>', unsafe_allow_html=True)
resumen_meses = (
    tabla.groupby(["_mes_ord", "Mes"])
    .agg(pedidos=("Numero de pedido", "count"), tiendas=("Numero de tienda", "nunique"))
    .reset_index()
    .sort_values("_mes_ord", ascending=False)
)
cards_meses = "".join(
    kpi_card(row["Mes"], f"{row['pedidos']:,}".replace(",", "."))
    for _, row in resumen_meses.iterrows()
)
st.markdown(f'<div class="kpi-row">{cards_meses}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Filtro de Mes
# ---------------------------------------------------------------------

meses_disponibles = (
    tabla[["_mes_ord", "Mes"]].drop_duplicates().sort_values("_mes_ord", ascending=False)
)
opciones_mes = ["Todos los meses"] + meses_disponibles["Mes"].tolist()
mes_elegido = st.selectbox("**Mes**", opciones_mes)

if mes_elegido != "Todos los meses":
    tabla_f = tabla[tabla["Mes"] == mes_elegido]
else:
    tabla_f = tabla

tabla_f = tabla_f[["Mes", "Numero de pedido", "Numero de tienda"]].reset_index(drop=True)

st.markdown(
    f'<div class="kpi-row">{kpi_card("Pedidos listados", f"{len(tabla_f):,}".replace(",", "."))}'
    f'{kpi_card("Tiendas", tabla_f["Numero de tienda"].nunique())}</div>',
    unsafe_allow_html=True
)

csv_bytes = tabla_f.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "⬇ Descargar CSV (todo lo filtrado)",
    data=csv_bytes,
    file_name="pedidos_sts.csv",
    mime="text/csv",
)

st.markdown('<div class="section">Listado por tienda</div>', unsafe_allow_html=True)

if tabla_f.empty:
    st.markdown(
        '<div style="background:#fafaf8;border:1px dashed #dfe2db;border-radius:12px;'
        'padding:22px;text-align:center;color:#868d8e;font-size:13px;margin-top:8px;">'
        'No hay pedidos para ese mes.</div>',
        unsafe_allow_html=True
    )
else:
    # Orden de tienda: numérico si el código lo permite, para que 998 no
    # quede antes que 1002 por orden de texto.
    tiendas_orden = sorted(
        tabla_f["Numero de tienda"].unique(),
        key=lambda t: (0, int(t)) if t.isdigit() else (1, t)
    )
    for tienda in tiendas_orden:
        sub = tabla_f[tabla_f["Numero de tienda"] == tienda][["Mes", "Numero de pedido"]]
        nombre = tienda_nombre(tienda)
        with st.expander(f"{nombre} ({tienda}) — {len(sub)} pedido(s)"):
            st.markdown(
                f'<div style="font-weight:800;font-size:15px;color:#20252b;margin-bottom:8px;">'
                f'{nombre} <span style="font-weight:400;color:#6b7280;font-size:12.5px;">(tienda {tienda})</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown(table_html(sub.reset_index(drop=True)), unsafe_allow_html=True)
