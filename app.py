import streamlit as st
import pandas as pd
import tempfile
from pathlib import Path

st.set_page_config(
    page_title="MásOnline | Ecommerce",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #ffffff; }
    .block-container { max-width: 900px; padding: 2.6rem 1.2rem 1.2rem; }

    .hero-brand { font-size: 28px; font-weight: 800; letter-spacing: -.5px; color:#20252b; margin-bottom: 3px; }
    .hero-brand span { font-weight: 400; }
    .hero-sub {
        font-size: 11px; letter-spacing: 3px; margin-bottom: 24px;
        opacity: .85; color:#20252b;
    }

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

    @media (max-width: 600px) {
        .block-container { padding: 1.6rem 0.6rem 1rem; }
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).resolve().parent / "data.csv"
DATA_TIENDAS_FILE = Path(__file__).resolve().parent / "data_tiendas.csv"

try:
    base_df = pd.read_csv(DATA_FILE)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    for col in ["company_tax", "ecommerce_tax", "orders", "units"]:
        base_df[col] = pd.to_numeric(base_df[col], errors="coerce").fillna(0)
    base_df = base_df.dropna(subset=["date"])
except Exception as e:
    st.error(f"No se pudo leer data.csv: {e}")
    st.stop()

# Desglose por tienda (para "Top 10 tiendas" en Venta diaria). Es un archivo
# aparte, "data_tiendas.csv", que puede no existir todavía la primera vez.
TIENDAS_COLUMNS = ["date", "Tienda", "Nombre", "company_tax", "ecommerce_tax", "orders", "units"]

def _empty_tiendas_df():
    """DataFrame vacío con las columnas de data_tiendas.csv, pero con "date"
    ya tipado como fecha — si no, cualquier filtro con .dt más adelante
    explota con 'Can only use .dt accessor with datetimelike values' apenas
    data_tiendas.csv todavía no existe en el repo (primera vez)."""
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

st.markdown("""
<div class="hero-brand">Más<span>Online</span></div>
<div class="hero-sub">E-COMMERCE &nbsp;·&nbsp; CARGA DE DATOS</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin-bottom:14px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    ACTUALIZAR DATOS
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí acá el Excel "Venta Con y sin Impuesto". Una vez cargado y guardado, los datos
    se ven solos en las pestañas Venta diaria y Venta fin de semana — no hace falta
    subir el archivo de nuevo ahí.
  </div>
</div>
""", unsafe_allow_html=True)

u1, u2, u3 = st.columns(3)

with u1:
    st.markdown("""
    <div class="upload-box upload-current">
      <div class="upload-title">MES EN CURSO</div>
      <div class="upload-text">Subí el Excel del mes en curso</div>
    </div>
    """, unsafe_allow_html=True)
    upload_current = st.file_uploader(
        "Archivo mes en curso",
        type=["xlsx", "xls"],
        key="upload_current",
        label_visibility="collapsed",
        help="Reporte Venta Con y sin Impuesto del mes en curso."
    )

with u2:
    st.markdown("""
    <div class="upload-box upload-prev">
      <div class="upload-title">MES ANTERIOR</div>
      <div class="upload-text">Subí el Excel del mes anterior</div>
    </div>
    """, unsafe_allow_html=True)
    upload_prev = st.file_uploader(
        "Archivo mes anterior",
        type=["xlsx", "xls"],
        key="upload_prev",
        label_visibility="collapsed",
        help="Reporte Venta Con y sin Impuesto del mes anterior."
    )

with u3:
    st.markdown("""
    <div class="upload-box upload-ly">
      <div class="upload-title">MISMO PERÍODO AÑO PASADO</div>
      <div class="upload-text">Subí el Excel del mismo mes, año pasado</div>
    </div>
    """, unsafe_allow_html=True)
    upload_ly = st.file_uploader(
        "Archivo año pasado",
        type=["xlsx", "xls"],
        key="upload_ly",
        label_visibility="collapsed",
        help="Reporte Venta Con y sin Impuesto del mismo mes del año pasado."
    )

# ---------------------------------------------------------------------
# Reporte diario + Faltantes: se suben acá y quedan guardados en una carpeta
# compartida en el servidor, para que las pestañas Operativo, Productividad
# Pickers y Resumen los lean directo, sin tener que subirlos de nuevo ahí.
# ---------------------------------------------------------------------

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin:22px 0 14px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    CARGAR REPORTES (Operativo)
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Ya no se sube más el Reporte diario combinado. Cada sección se sube en su
    propio archivo, aparte: Pedidos +72h, Reclamos Operativos, On Time, Delivery,
    Fill Rate, Faltantes y Pickers.
  </div>
</div>
""", unsafe_allow_html=True)

def upload_box_reporte(col, title, help_text, key):
    with col:
        st.markdown(f"""
        <div class="upload-box">
          <div class="upload-title">{title}</div>
          <div class="upload-text">{help_text}</div>
        </div>
        """, unsafe_allow_html=True)
        return st.file_uploader(title, type=["xlsx", "xls"], key=key, label_visibility="collapsed")

r1, r2, r3, r4 = st.columns(4)
f_pedidos = upload_box_reporte(
    r1, "PEDIDOS +72H",
    "Archivo de Pedidos +72h.",
    "f_pedidos"
)
f_reclamos = upload_box_reporte(
    r2, "RECLAMOS OPERATIVOS",
    "Archivo nuevo de Reclamos Operativos, aparte del Reporte diario.",
    "f_reclamos"
)
f_ontime = upload_box_reporte(
    r3, "ON-TIME",
    "Archivo nuevo de On Time, aparte del Reporte diario.",
    "f_ontime"
)
f_delivery = upload_box_reporte(
    r4, "DELIVERY",
    "Archivo nuevo de Delivery, aparte del Reporte diario.",
    "f_delivery"
)

r5, r6, r7, r8 = st.columns(4)
f_fillrate = upload_box_reporte(
    r5, "FILL RATE",
    "Archivo nuevo de Fill Rate, aparte del Reporte diario.",
    "f_fillrate"
)
f_faltantes = upload_box_reporte(r6, "FALTANTES", "SKUs marcados como faltante ECOM por tienda.", "f_faltantes")
f_pickers = upload_box_reporte(
    r7, "PICKERS",
    "Archivo nuevo de Productividad Pickers, aparte del Reporte diario.",
    "f_pickers"
)
f_vsventas = upload_box_reporte(
    r8, "COMPARATIVO",
    "Archivo 'Vs de ventas' (hojas 2025/2026) para la pestaña Comparativo.",
    "f_vsventas"
)

st.markdown(
    '<div style="font-size:11px;color:#9aa1ab;margin:-4px 0 14px;">'
    'Delivery todavía guarda el archivo pero no arma ninguna sección — eso lo '
    'conectamos cuando tengamos un archivo de ejemplo. FILL RATE ya arma la '
    'sección de Operativo con el archivo de Faltantes por depósito '
    '(missing-item-by-wh). La tarjeta ON-TIME funciona igual que PICKERS: si '
    'subís ahí el archivo de Productividad Pickers, también arma "Tiempo '
    'promedio de preparación por tienda" y el % on time acumulado del mes en '
    'Operativo. COMPARATIVO alimenta la pestaña Comparativo (resumen del mes '
    'vs. mismo período del año anterior) — subí ahí el archivo "Vs de ventas" '
    'con una hoja por año.</div>',
    unsafe_allow_html=True
)

SHARED_DIR = Path(tempfile.gettempdir()) / "masonline_shared_uploads"
SHARED_DIR.mkdir(parents=True, exist_ok=True)
SHARED_FALTANTES_PATH = SHARED_DIR / "faltantes.xlsx"
SHARED_PEDIDOS_PATH = SHARED_DIR / "pedidos.xlsx"
SHARED_PICKERS_PATH = SHARED_DIR / "pickers.xlsx"
SHARED_RECLAMOS_PATH = SHARED_DIR / "reclamos.xlsx"
SHARED_ONTIME_PATH = SHARED_DIR / "ontime.xlsx"
SHARED_DELIVERY_PATH = SHARED_DIR / "delivery.xlsx"
SHARED_FILLRATE_PATH = SHARED_DIR / "fillrate.xlsx"
SHARED_VSVENTAS_PATH = SHARED_DIR / "vsventas.xlsx"

def save_shared_bytes(uploaded_file, shared_path):
    """Si se subió un archivo nuevo en esta sesión, lo guarda en la carpeta
    compartida para que las demás pestañas lo lean. Devuelve True si había
    algo (nuevo o ya guardado antes)."""
    if uploaded_file is not None:
        try:
            shared_path.write_bytes(uploaded_file.getvalue())
        except Exception:
            pass
        return True
    return shared_path.exists()

faltantes_guardado = save_shared_bytes(f_faltantes, SHARED_FALTANTES_PATH)
pedidos_guardado = save_shared_bytes(f_pedidos, SHARED_PEDIDOS_PATH)
pickers_guardado = save_shared_bytes(f_pickers, SHARED_PICKERS_PATH)
reclamos_guardado = save_shared_bytes(f_reclamos, SHARED_RECLAMOS_PATH)
ontime_guardado = save_shared_bytes(f_ontime, SHARED_ONTIME_PATH)
delivery_guardado = save_shared_bytes(f_delivery, SHARED_DELIVERY_PATH)
fillrate_guardado = save_shared_bytes(f_fillrate, SHARED_FILLRATE_PATH)
vsventas_guardado = save_shared_bytes(f_vsventas, SHARED_VSVENTAS_PATH)

if pedidos_guardado or faltantes_guardado:
    st.markdown(
        '<div style="font-size:11.5px;color:#0ca30c;font-weight:700;margin:-2px 0 2px;">'
        '● Listo — ya lo podés ver en la pestaña Operativo.</div>',
        unsafe_allow_html=True
    )

# Código de tienda (columna "Tienda" del Excel) -> nombre. Mismo listado que
# se usa en "Productividad Pickers" (viene del archivo "Picker x tienda").
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

def norm_tienda_code(v):
    """El Excel trae el código de tienda como número (1002, 1002.0, etc.).
    Lo normalizamos siempre a texto sin decimales, para que coincida con las
    claves de TIENDA_MAP y con lo que ya se guarda en data_tiendas.csv."""
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return str(v).strip()

def tienda_nombre(codigo):
    return TIENDA_MAP.get(codigo, codigo)

def normalize_uploaded_excel(file):
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
        "Fecha",
        "Facturacion",
        "Venta - Ecommerce",
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
    out["source"] = "Reporte subido"

    # Desglose por tienda, para "Top 10 tiendas" en Venta diaria. Si el
    # archivo no trae columna "Tienda" (no debería pasar), seguimos igual,
    # simplemente sin el desglose para ese archivo.
    out_tiendas = _empty_tiendas_df()
    if "Tienda" in d.columns:
        dt = d.copy()
        dt["Tienda"] = dt["Tienda"].apply(norm_tienda_code)
        out_tiendas = dt.groupby(["Fecha", "Tienda"], as_index=False).agg(
            company_tax=("Facturacion", "sum"),
            ecommerce_tax=("Venta - Ecommerce", "sum"),
            orders=("Pedidos Facturados con Venta Operativa - Ecommerce", "sum"),
            units=("Cantidad Venta Operativa - Ecommerce", "sum")
        )
        out_tiendas = out_tiendas.rename(columns={"Fecha": "date"})
        out_tiendas["Nombre"] = out_tiendas["Tienda"].apply(tienda_nombre)
        out_tiendas = out_tiendas[TIENDAS_COLUMNS]

    return out, out_tiendas

df = base_df.copy()
df_tiendas = base_df_tiendas.copy()

def replace_period(uploaded_file, year, month, label):
    global df, df_tiendas

    if uploaded_file is None:
        return

    try:
        incoming, incoming_tiendas = normalize_uploaded_excel(uploaded_file)

        incoming = incoming[
            (incoming["date"].dt.year == year) &
            (incoming["date"].dt.month == month)
        ].copy()

        if incoming.empty:
            st.error(f"{label}: no encontré datos de {month:02d}/{year} en el archivo.")
            return

        df = df[
            ~(
                (df["date"].dt.year == year) &
                (df["date"].dt.month == month)
            )
        ].copy()

        df = pd.concat([df, incoming], ignore_index=True)

        df = (
            df.sort_values("date")
            .drop_duplicates(subset=["date"], keep="last")
            .reset_index(drop=True)
        )

        if len(incoming_tiendas):
            incoming_tiendas = incoming_tiendas[
                (incoming_tiendas["date"].dt.year == year) &
                (incoming_tiendas["date"].dt.month == month)
            ].copy()

            df_tiendas = df_tiendas[
                ~(
                    (df_tiendas["date"].dt.year == year) &
                    (df_tiendas["date"].dt.month == month)
                )
            ].copy()

            df_tiendas = pd.concat([df_tiendas, incoming_tiendas], ignore_index=True)

            df_tiendas = (
                df_tiendas.sort_values(["date", "Tienda"])
                .drop_duplicates(subset=["date", "Tienda"], keep="last")
                .reset_index(drop=True)
            )

        # GUARDAR LOS DATOS EN GITHUB
        try:
            import urllib.request
            import urllib.error
            import json
            import base64
            from datetime import datetime
            from zoneinfo import ZoneInfo

            token = st.secrets.get("GITHUB_TOKEN")

            if token:
                repo = "2026-Masonline/masonline-dashboard"
                path = "data.csv"
                branch = "main"

                url = f"https://api.github.com/repos/{repo}/contents/{path}"

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "Masonline-Dashboard"
                }

                # Obtener SHA actual de data.csv
                request_get = urllib.request.Request(
                    f"{url}?ref={branch}",
                    headers=headers,
                    method="GET"
                )

                with urllib.request.urlopen(request_get, timeout=30) as response:
                    github_file = json.loads(response.read().decode("utf-8"))

                sha = github_file["sha"]

                save_df = df.sort_values("date")

                csv_text = save_df.to_csv(
                    index=False,
                    date_format="%Y-%m-%d"
                )

                content_b64 = base64.b64encode(
                    csv_text.encode("utf-8")
                ).decode("utf-8")

                payload = {
                    "message": f"Actualizar datos ecommerce - {label}",
                    "content": content_b64,
                    "sha": sha,
                    "branch": branch
                }

                request_put = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        **headers,
                        "Content-Type": "application/json"
                    },
                    method="PUT"
                )

                with urllib.request.urlopen(
                    request_put,
                    timeout=30
                ) as response:
                    response.read()

                # Guardar también el desglose por tienda (data_tiendas.csv),
                # para "Top 10 tiendas" en Venta diaria. Si esto falla no
                # queremos tapar el éxito del guardado principal (data.csv),
                # así que va aparte y en silencio (aviso chiquito nada más).
                if len(df_tiendas):
                    try:
                        path_t = "data_tiendas.csv"
                        url_t = f"https://api.github.com/repos/{repo}/contents/{path_t}"

                        sha_t = None
                        request_get_t = urllib.request.Request(
                            f"{url_t}?ref={branch}",
                            headers=headers,
                            method="GET"
                        )
                        try:
                            with urllib.request.urlopen(request_get_t, timeout=30) as response:
                                sha_t = json.loads(response.read().decode("utf-8"))["sha"]
                        except urllib.error.HTTPError as e_get:
                            if e_get.code != 404:
                                raise
                            # 404 = todavía no existe data_tiendas.csv en el repo;
                            # se crea solo, sin mandar "sha" en el payload.

                        save_df_tiendas = df_tiendas.sort_values(["date", "Tienda"])
                        csv_text_t = save_df_tiendas.to_csv(index=False, date_format="%Y-%m-%d")
                        content_b64_t = base64.b64encode(csv_text_t.encode("utf-8")).decode("utf-8")

                        payload_t = {
                            "message": f"Actualizar datos por tienda - {label}",
                            "content": content_b64_t,
                            "branch": branch
                        }
                        if sha_t:
                            payload_t["sha"] = sha_t

                        request_put_t = urllib.request.Request(
                            url_t,
                            data=json.dumps(payload_t).encode("utf-8"),
                            headers={**headers, "Content-Type": "application/json"},
                            method="PUT"
                        )
                        with urllib.request.urlopen(request_put_t, timeout=30) as response:
                            response.read()
                    except Exception:
                        st.caption(
                            "⚠️ El desglose por tienda (Top 10 tiendas) no se pudo guardar esta vez — "
                            "el resto de los datos sí se guardó bien."
                        )

                st.success(
                    f"{label}: datos cargados y guardados correctamente."
                )

            else:
                st.warning(
                    "Los datos se cargaron para esta sesión, "
                    "pero GITHUB_TOKEN no está configurado."
                )

        except Exception as github_error:
            st.error(
                f"Los datos se cargaron, pero no se pudieron guardar en GitHub: "
                f"{github_error}"
            )

    except Exception as e:
        st.error(f"{label}: no pude procesar el Excel: {e}")

replace_period(upload_current, 2026, 9, "Mes en curso")
replace_period(upload_prev, 2026, 8, "Mes anterior")
replace_period(upload_ly, 2025, 9, "Mismo período año pasado")

if not (upload_current or upload_prev or upload_ly):
    st.markdown(
        '<div style="color:#6b7280;font-size:12px;margin-top:12px;">'
        'Todavía no subiste ningún archivo en esta sesión. Para ver los últimos datos '
        'guardados, andá a <b>Venta diaria</b> o <b>Venta fin de semana</b> en el menú '
        'de la izquierda.'
        '</div>',
        unsafe_allow_html=True
    )
