import re
import base64
import unicodedata
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="MásOnline | Operativo",
    page_icon="🚨",
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
    .hero-date { text-align: right; font-size: 15px; font-weight: 700; color:#6b7280; }
    .hero-date small { display: block; font-size: 12px; font-weight: 400; margin-top: 4px; }

    .upload-box {
        background: white; border-radius: 14px; padding: 14px 16px 10px;
        border: 1px solid #e8ebef; box-shadow: 0 2px 10px rgba(0,0,0,.05);
        margin-bottom: 6px; min-height: 74px; border-top: 4px solid #ff5a1f;
    }
    .upload-title { color:#20252b; font-size:13px; font-weight:800; }
    .upload-text { color:#6b7280; font-size:11.5px; margin-top:4px; }

    .section {
        font-size: 19px; font-weight: 800; color: #20252b;
        margin: 26px 0 4px; display:flex; align-items:center; gap:10px;
    }
    .section .count-pill {
        font-size: 15px; font-weight: 800; background:#fdeee5; color:#ff5a1f;
        border-radius: 999px; padding: 3px 15px; box-shadow: 0 1px 5px rgba(255,90,31,.22);
    }
    .section-desc { color:#6b7280; font-size:12.5px; margin: -2px 0 10px; }

    .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin-top: 10px; }
    .kpi {
        background: white; border-radius: 14px; padding: 16px 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06); border: 1px solid #e8ebef;
    }
    .kpi .label { color: #6b7280; font-size: 11.5px; font-weight: 700; text-transform:uppercase; letter-spacing:.04em;}
    .kpi .value { color: #20252b; font-size: 26px; font-weight: 800; margin-top: 6px; }
    .kpi .sub { color: #6b7280; font-size: 12px; margin-top: 6px; }
    .kpi.good .value { color:#0ca30c; }
    .kpi.warn .value { color:#c98500; }
    .kpi.crit .value { color:#d03b3b; }

    a.kpi-link { text-decoration: none; display: block; }
    a.kpi-link .kpi { cursor: pointer; transition: box-shadow .15s, transform .15s; position: relative; }
    a.kpi-link .kpi::after {
        content: "⬇ HTML"; position: absolute; top: 10px; right: 12px;
        font-size: 9.5px; font-weight: 700; color: #ff5a1f; opacity: 0;
        transition: opacity .15s; letter-spacing: .03em;
    }
    a.kpi-link:hover .kpi { box-shadow: 0 6px 18px rgba(0,0,0,.14); transform: translateY(-2px); }
    a.kpi-link:hover .kpi::after { opacity: 1; }

    .badge {
        display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 700;
        padding: 3px 10px; border-radius: 999px; white-space: nowrap;
    }
    .badge.good { background: #e6f5e6; color: #0ca30c; }
    .badge.warning { background: #fdf1d9; color: #c98500; }
    .badge.serious { background: #fdeae1; color: #ec835a; }
    .badge.critical { background: #fbe6e6; color: #d03b3b; }
    .badge.neutral { background: #eef0eb; color: #565d5f; }

    .empty-box {
        background:#fafaf8; border:1px dashed #dfe2db; border-radius:12px;
        padding: 22px; text-align:center; color:#868d8e; font-size:13px; margin-top:8px;
    }

    .resumen-title {
        font-size: 12.5px; font-weight: 800; color:#565d5f; text-transform:uppercase;
        letter-spacing:.04em; margin: 4px 0 6px;
    }
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
    table.dashtable tbody tr.total-row {
        background: #d7ecfc; font-weight: 800; color:#0f3a5c;
        border-top: 2px solid #7fb8e8;
    }
    table.dashtable tbody tr.total-row td { padding: 10px 12px; font-size: 13.5px; }
    table.dashtable tbody tr.total-row:hover { background: #d7ecfc; }

    div[data-testid="stDownloadButton"] button {
        background: #ffffff; color: #ff5a1f; border: 1.5px solid #ff5a1f;
        border-radius: 8px; font-size: 12.5px; font-weight: 700; padding: 4px 14px;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: #ff5a1f; color: #ffffff; border-color: #ff5a1f;
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

def strip_sucursal(v):
    """Quita el prefijo 'Sucursal ' y normaliza espacios, para poder unificar
    nombres de tienda que vienen distinto de una hoja a otra."""
    s = norm_txt(v)
    s = re.sub(r"(?i)^sucursal\s+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fold_tienda_key(s):
    """Clave sin acentos/mayúsculas para agrupar nombres de tienda equivalentes
    aunque vengan escritos distinto entre hojas (ej. 'Cordoba Oeste' vs 'Córdoba Oeste')."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()

def build_tienda_canon_map(dfs):
    """Unifica nombres de tienda entre hojas (mayúsculas/minúsculas, acentos, prefijo
    'Sucursal', espacios) usando la ortografía más frecuente como canónica."""
    from collections import Counter
    counts = {}
    for d in dfs:
        if d is None or "Tienda" not in d.columns:
            continue
        for v in d["Tienda"]:
            s = strip_sucursal(v)
            if not s:
                continue
            key = fold_tienda_key(s)
            counts.setdefault(key, Counter())[s] += 1
    return {key: c.most_common(1)[0][0] for key, c in counts.items()}

def apply_tienda_canon(d, canon_map):
    if d is None or "Tienda" not in d.columns:
        return d
    d = d.copy()
    d["Tienda"] = d["Tienda"].apply(strip_sucursal).apply(
        lambda s: canon_map.get(fold_tienda_key(s), s)
    )
    return d

def ar_number(v):
    """Parse an Argentine-formatted number that may come as a plain value
    or as a string like '9.473 ▼ 12.6%vs MA' / '1.565' / '$464K'."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = norm_txt(v)
    if not s:
        return 0.0
    token = s.split(" ")[0]
    token = token.replace("$", "")
    mult = 1.0
    if token.upper().endswith("K"):
        mult = 1_000.0
        token = token[:-1]
    elif token.upper().endswith("M"):
        mult = 1_000_000.0
        token = token[:-1]
    token = token.replace("%", "")
    token = token.replace(".", "").replace(",", ".")
    try:
        return float(token) * mult
    except ValueError:
        return 0.0

def find_sheet(xl, required_cols):
    """Return the (sheet_name, df) whose normalized columns cover required_cols."""
    required = {c.lower() for c in required_cols}
    for name in xl.sheet_names:
        try:
            df = xl.parse(name)
        except Exception:
            continue
        df = norm_cols(df)
        cols = {c.lower() for c in df.columns}
        if required.issubset(cols):
            return name, df
    return None, None

def load_section(uploaded_file, required_cols):
    """Load an uploaded file (single-sheet export OR the full Reporte diario.xlsx)
    and return the dataframe matching required_cols, or None."""
    if uploaded_file is None:
        return None
    try:
        xl = pd.ExcelFile(uploaded_file)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return None
    name, df = find_sheet(xl, required_cols)
    if df is None:
        st.error(
            "No encontré una hoja con las columnas esperadas "
            f"({', '.join(required_cols)}) en el archivo subido."
        )
        return None
    return df

def money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "$0"
    return f"${v:,.0f}".replace(",", ".")

def pct1(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:.1f}%".replace(".", ",")

def badge(level, label):
    icons = {"good": "●", "warning": "▲", "serious": "▲", "critical": "✕", "neutral": "●"}
    return f'<span class="badge {level}">{icons.get(level,"●")} {label}</span>'

def table_html(df):
    """Tabla de detalle, con el estilo .dashtable en vez del default de pandas."""
    return df.to_html(escape=False, index=False, classes="dashtable", border=0)

def resumen_table_html(agg, label_col, col_formatters, total_label="Total general"):
    """Tabla resumen tipo tabla dinámica de Excel: una fila por tienda + una fila
    de 'Total general' resaltada al pie. col_formatters: {columna: función de formato}."""
    cols = list(col_formatters.keys())
    thead = "".join(f"<th>{c}</th>" for c in [label_col] + cols)
    body_rows = []
    for _, r in agg.iterrows():
        tds = f"<td>{r[label_col]}</td>" + "".join(
            f"<td>{col_formatters[c](r[c])}</td>" for c in cols
        )
        body_rows.append(f"<tr>{tds}</tr>")
    total_tds = f"<td>{total_label}</td>" + "".join(
        f"<td>{col_formatters[c](agg[c].sum())}</td>" for c in cols
    )
    body_rows.append(f'<tr class="total-row">{total_tds}</tr>')
    return (
        '<table class="dashtable"><thead><tr>' + thead + '</tr></thead>'
        '<tbody>' + "".join(body_rows) + '</tbody></table>'
    )

def export_section_html(section_title, section_desc, body_html):
    """Arma un HTML standalone (con el mismo look del panel) para descargar una sección sola."""
    corte_html = ""
    if now_ref is not None:
        corte_html = (
            '<div class="hero-date">Corte del reporte<br>'
            f'<small>{now_ref.strftime("%d/%m/%Y %H:%M")}</small></div>'
        )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>MásOnline · {section_title}</title>
<style>
{APP_CSS}
body {{ margin:0; background:#fafaf8; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }}
.wrap {{ max-width: 1400px; margin: 0 auto; padding: 0 20px 28px; }}
</style>
</head>
<body>
<div class="hero">
  <div>
    {brand_html}
    <div class="hero-sub">ALERTAS OPERATIVAS</div>
  </div>
  {corte_html}
</div>
<div class="wrap">
<div class="section">{section_title}</div>
<div class="section-desc">{section_desc}</div>
{body_html}
</div>
</body>
</html>"""

def section_download_button(html_doc, filename, key):
    st.download_button(
        "⬇️ Descargar esta sección (HTML)",
        data=html_doc.encode("utf-8"),
        file_name=filename,
        mime="text/html",
        key=key,
    )

# ---- severity rules (same thresholds as el Pulso Operativo VMont) ----

def sev_pedido_72h(dias):
    if dias >= 10:
        return "critical", "Crítico"
    if dias >= 6:
        return "serious", "Grave"
    return "warning", "Atención"

def sev_reclamo(horas, estado):
    if estado in ("Cerrado", "No aplica-Anulado"):
        return "neutral", estado
    if horas > 72:
        return "critical", ">72h sin acción"
    if horas >= 24:
        return "warning", "24–72h"
    return "good", "<24h"

def sev_ontime(pct):
    if pct >= 95:
        return "good", "OK"
    if pct >= 90:
        return "warning", "Atención"
    if pct >= 80:
        return "serious", "Grave"
    return "critical", "Crítico"

def sev_fr(pct, unidades):
    if not unidades:
        return "neutral", "Sin actividad"
    if pct >= 97:
        return "good", "OK"
    if pct >= 93:
        return "warning", "Atención"
    if pct >= 85:
        return "serious", "Grave"
    return "critical", "Crítico"

def sev_faltante(alta_rotacion):
    if alta_rotacion:
        return "critical", "Alta rotación"
    return "warning", "Faltante"

# ---------------------------------------------------------------------
# HTML de cada sección, generado antes que las tarjetas KPI para poder
# linkearlas directo (clickear la tarjeta baja el HTML de esa sección).
# ---------------------------------------------------------------------

def html_doc_pedidos(pedidos_f):
    if pedidos_f is None or not len(pedidos_f):
        return None
    show = pedidos_f.copy().sort_values("Dias", ascending=False)
    show["Días"] = show["Dias"].round(1)
    show["Monto"] = show["MontoNum"].apply(money)
    show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Pedido", "Tienda", "Estado", "Fecha", "Días", "Monto", "Urgencia"]
    agg = pedidos_f.groupby("Tienda").agg(
        Cantidad=("Pedido", "count")
    ).reset_index().sort_values("Cantidad", ascending=False)
    resumen_html = resumen_table_html(agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}"})
    body = (
        '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )
    return export_section_html(
        "📦 Pedidos sin movimiento +72hs",
        "Pedidos que llevan más de 3 días en el mismo estado sin avanzar.",
        body
    )

def html_doc_reclamos(reclamos_f):
    if reclamos_f is None or not len(reclamos_f):
        return None
    abiertos = reclamos_f[reclamos_f["Estado"].isin(["Nuevo", "En proceso"])]
    if not len(abiertos):
        return None
    show = abiertos.copy().sort_values("Horas", ascending=False)
    show["Horas"] = show["Horas"].round(1)
    show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha", "Horas", "Urgencia"]
    agg = abiertos.groupby("Tienda").apply(lambda g: pd.Series({
        "Cantidad": len(g),
        ">72h": int((g["Horas"] > 72).sum()),
        "24–72h": int(((g["Horas"] >= 24) & (g["Horas"] <= 72)).sum()),
    })).reset_index().sort_values("Cantidad", ascending=False)
    resumen_html = resumen_table_html(
        agg, "Tienda",
        {"Cantidad": lambda v: f"{int(v)}", ">72h": lambda v: f"{int(v)}", "24–72h": lambda v: f"{int(v)}"}
    )
    agg_tipo = abiertos.groupby("Tipo").agg(
        Cantidad=("Pedido", "count")
    ).reset_index().sort_values("Cantidad", ascending=False)
    resumen_tipo_html = resumen_table_html(agg_tipo, "Tipo", {"Cantidad": lambda v: f"{int(v)}"})
    body = (
        '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
        '<div style="flex:1;min-width:260px;">'
        '<div class="resumen-title">Resumen por tienda (abiertos)</div>' + resumen_html + '</div>'
        '<div style="flex:1;min-width:260px;">'
        '<div class="resumen-title">Resumen por tipo (abiertos)</div>' + resumen_tipo_html + '</div>'
        '</div>'
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )
    return export_section_html(
        "🗣️ Reclamos operativos",
        "Franjas de alerta: 24hs y 72hs sin acción.",
        body
    )

def prepa_bundle(prepa_f):
    """Arma todo lo que necesita On Time Preparación: detalle, totales y el
    Top 5 de tiendas con peor % on time (por debajo del 95%)."""
    if prepa_f is None or not len(prepa_f):
        return None
    show = prepa_f.copy().sort_values("OntimePct")
    show["Ontime %"] = show["OntimePct"].apply(pct1)
    show["Estado"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    show["Pedidos"] = show["Pedidos"].astype(int)
    show["Fuera de horario"] = show["Fuera"].astype(int)
    detail_cols = ["Tienda", "Formato", "Pedidos", "Fuera de horario", "Ontime %", "Estado"]

    ped_tot = int(prepa_f["Pedidos"].sum())
    fuera_tot = int(prepa_f["Fuera"].sum())
    ot_pct_tot = 100 * (1 - fuera_tot / ped_tot) if ped_tot else 0

    peores = show[show["OntimePct"] < 95].head(5)
    if len(peores):
        top5_html = table_html(peores[detail_cols])
    else:
        top5_html = '<div class="empty-box">Ninguna tienda por debajo del 95% 🎉</div>'

    body = (
        f'<div class="resumen-title">Total — {ped_tot} pedidos · {fuera_tot} fuera de horario · '
        f'{pct1(ot_pct_tot)} on time</div>'
        '<div class="resumen-title" style="margin-top:18px;">Top 5 tiendas con % on time &lt; 95%</div>'
        + top5_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )
    html_doc = export_section_html(
        "⏱️ On Time Preparación",
        "Porcentaje de pedidos preparados en horario, por tienda.",
        body
    )
    return {
        "show": show, "detail_cols": detail_cols, "ped_tot": ped_tot, "fuera_tot": fuera_tot,
        "ot_pct_tot": ot_pct_tot, "top5_html": top5_html, "html_doc": html_doc,
    }

def html_doc_prepa(prepa_f):
    b = prepa_bundle(prepa_f)
    return b["html_doc"] if b else None

def html_doc_fr(fr_f):
    if fr_f is None or not len(fr_f):
        return None
    show = fr_f.copy().sort_values("FRPct")
    show["Unidades"] = show["Unidades"].astype(int)
    show["Sin sustituto"] = show["SinSustituto"].astype(int)
    show["Con sustituto"] = show["ConSustituto"].astype(int)
    show["Monto faltante"] = show["MontoFaltante"].apply(money)
    show["FR %"] = show["FRPct"].apply(pct1)
    show["Estado"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Tienda", "Unidades", "Sin sustituto", "Con sustituto", "Monto faltante", "FR %", "Estado"]
    return export_section_html(
        "🧩 Fill Rate — con y sin sustituto",
        "Unidades faltantes por tienda: cubiertas con reemplazo vs. no entregadas.",
        table_html(show[detail_cols])
    )

def cancelados_bundle(can_f):
    """Arma el Top 10 de tiendas con más cancelados, el resumen completo por
    tienda y el detalle pedido a pedido, para la sección y para el HTML."""
    if can_f is None or not len(can_f):
        return None
    agg = can_f.groupby("Tienda").agg(
        Cancelados=("Pedido", "count"), Monto=("Total $", "sum")
    ).reset_index().sort_values("Cancelados", ascending=False)

    top10 = agg.head(10)[["Tienda", "Cancelados"]]
    top10_html = resumen_table_html(
        top10, "Tienda", {"Cancelados": lambda v: f"{int(v)}"}, total_label="Total (top 10)"
    )

    resumen_html = resumen_table_html(agg, "Tienda", {"Cancelados": lambda v: f"{int(v)}", "Monto": money})

    det = can_f.copy().sort_values("Fecha", ascending=False)
    det["Total $"] = det["Total $"].apply(money)
    detail_cols = ["Pedido", "Tienda", "Fecha", "Total $"]

    body = (
        '<div class="resumen-title">Top 10 tiendas con más cancelados</div>' + top10_html +
        '<div class="resumen-title" style="margin-top:18px;">Resumen completo por tienda</div>' + resumen_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(det[detail_cols])
    )
    html_doc = export_section_html(
        "🚫 Pedidos cancelados",
        "Cancelaciones por tienda en el período del reporte.",
        body
    )
    return {
        "agg": agg, "top10_html": top10_html, "resumen_html": resumen_html,
        "det": det, "detail_cols": detail_cols, "html_doc": html_doc,
    }

def html_doc_cancelados(can_f):
    b = cancelados_bundle(can_f)
    return b["html_doc"] if b else None

def html_doc_faltantes(falt_f):
    if falt_f is None or not len(falt_f):
        return None
    show = falt_f.copy().sort_values(["AltaRotacion", "VentaProm"], ascending=[False, False])
    show["Días sin venta"] = show["DiasSinVenta"]
    show["Venta prom. semanal"] = show["VentaProm"].round(1)
    show["Prioridad"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
    detail_cols = ["Tienda", "Producto", "Categoria", "Días sin venta", "Venta prom. semanal", "Prioridad"]
    agg = falt_f.groupby("Tienda").agg(
        Cantidad=("Producto", "count"), AltaRotacion=("AltaRotacion", "sum")
    ).reset_index().rename(columns={"AltaRotacion": "Alta rotación"}).sort_values("Cantidad", ascending=False)
    resumen_html = resumen_table_html(
        agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}", "Alta rotación": lambda v: f"{int(v)}"}
    )
    body = (
        '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
        '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
        + table_html(show[detail_cols])
    )
    return export_section_html(
        "📉 Faltantes ECOM",
        "SKUs marcados como faltante para e-commerce, por tienda.",
        body
    )

def kpi_link_wrap(inner_html, html_doc, filename):
    """Envuelve una tarjeta KPI en un link que descarga el HTML de esa sección al clickearla."""
    if not html_doc:
        return inner_html
    b64 = base64.b64encode(html_doc.encode("utf-8")).decode("utf-8")
    return (
        f'<a class="kpi-link" href="data:text/html;base64,{b64}" download="{filename}" '
        'title="Descargar esta sección como HTML">' + inner_html + '</a>'
    )

# ---------------------------------------------------------------------
# Header + uploaders
# ---------------------------------------------------------------------

# El logo vive en la raíz del repo; esta página está un nivel adentro (pages/).
LOGO_FILE = Path(__file__).resolve().parent.parent / "masonline_logo.png"
if LOGO_FILE.exists():
    logo_b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode("utf-8")
    brand_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        'style="height:48px;max-width:280px;object-fit:contain;">'
    )
else:
    brand_html = '<div class="hero-brand">🚨 Operativo</div>'

st.markdown(f"""
<div class="hero">
  <div>
    {brand_html}
    <div class="hero-sub">ALERTAS OPERATIVAS</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:white;border:1px solid #e8ebef;border-radius:12px;
padding:12px 16px;margin-bottom:14px;">
  <div style="font-size:13px;font-weight:800;color:#20252b;margin-bottom:5px;">
    CARGAR REPORTES
  </div>
  <div style="font-size:12px;color:#6b7280;">
    Subí el archivo de cada sección (podés subir la hoja individual o el "Reporte diario.xlsx" completo —
    lo detecto solo por sus columnas). On Time Preparación y On Time Delivery salen del mismo archivo
    ("Data Ontime Prepa"), así que comparten un único uploader.
  </div>
</div>
""", unsafe_allow_html=True)

def upload_box(col, title, help_text, key):
    with col:
        st.markdown(f"""
        <div class="upload-box">
          <div class="upload-title">{title}</div>
          <div class="upload-text">{help_text}</div>
        </div>
        """, unsafe_allow_html=True)
        return st.file_uploader(title, type=["xlsx", "xls"], key=key, label_visibility="collapsed")

u1, u2, u3, u4 = st.columns(4)
f_72h = upload_box(u1, "PEDIDOS +72HS", "Pedidos sin movimiento hace más de 72hs.", "f_72h")
f_reclamos = upload_box(u2, "RECLAMOS OPERATIVOS", "Reclamos abiertos por tienda.", "f_reclamos")
f_ontime = upload_box(u3, "ON TIME (PREPARACIÓN + DELIVERY)", "Data Ontime Prepa: alimenta las dos secciones.", "f_ontime")
f_fr = upload_box(u4, "FILL RATE", "Unidades no entregadas, con y sin sustituto.", "f_fr")

u5, u6, u7, _ = st.columns(4)
f_cancelados = upload_box(u5, "CANCELADOS", "Pedidos cancelados del período.", "f_cancelados")
f_faltantes = upload_box(u6, "FALTANTES", "SKUs marcados como faltante ECOM por tienda.", "f_faltantes")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Parse each section
# ---------------------------------------------------------------------

now_ref = None  # se calcula como el máximo timestamp visto en los archivos cargados

df_72h_raw = load_section(f_72h, ["Pedido", "Tienda", "Fecha", "Estado", "Monto"])
df_reclamos_raw = load_section(f_reclamos, ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha"])
df_ontime_raw = load_section(f_ontime, ["Tienda", "Pedifod", "Fuera", "ONTIME"])
df_fr_raw = load_section(f_fr, ["Tienda", "FR", "Limpio"])
df_cancelados_raw = load_section(f_cancelados, ["Pedido", "Tienda", "Fecha", "Estado", "Total $"])
df_faltantes_raw = load_section(
    f_faltantes,
    ["Tienda@DESC", "SKU@DESC", "Etiqueta_Stock", "Dias sin venta"]
)

candidate_times = []

pedidos_72h = None
if df_72h_raw is not None:
    d = df_72h_raw.copy()
    d = d[~d["Estado"].astype(str).str.lower().isin(["delivered", "canceled", "cancelled"])]
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    pedidos_72h = d

reclamos = None
if df_reclamos_raw is not None:
    d = df_reclamos_raw.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    reclamos = d

cancelados = None
if df_cancelados_raw is not None:
    d = df_cancelados_raw.copy()
    d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
    d = d.dropna(subset=["Fecha"])
    candidate_times.append(d["Fecha"].max())
    cancelados = d

if candidate_times:
    now_ref = max([t for t in candidate_times if pd.notna(t)])
else:
    now_ref = pd.Timestamp(datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None))

# ---- Pedidos +72h ----
if pedidos_72h is not None:
    pedidos_72h["Dias"] = (now_ref - pedidos_72h["Fecha"]).dt.total_seconds() / 86400
    pedidos_72h = pedidos_72h[pedidos_72h["Dias"] >= 3].copy()
    pedidos_72h["MontoNum"] = pedidos_72h["Monto"].apply(ar_number)
    pedidos_72h["Tienda"] = pedidos_72h["Tienda"].apply(norm_txt)
    pedidos_72h[["Sev", "SevLabel"]] = pedidos_72h["Dias"].apply(
        lambda d: pd.Series(sev_pedido_72h(d))
    )

# ---- Reclamos ----
if reclamos is not None:
    reclamos["Horas"] = (now_ref - reclamos["Fecha"]).dt.total_seconds() / 3600
    reclamos["Tienda"] = reclamos["Tienda"].apply(norm_txt)
    reclamos["Estado"] = reclamos["Estado"].apply(norm_txt)
    reclamos["Tipo"] = reclamos["Tipo"].apply(norm_txt)
    reclamos[["Sev", "SevLabel"]] = reclamos.apply(
        lambda r: pd.Series(sev_reclamo(r["Horas"], r["Estado"])), axis=1
    )

# ---- On Time (Preparación directo + Delivery por método) ----
ontime_prepa = None
ontime_delivery = None
if df_ontime_raw is not None:
    d = df_ontime_raw.copy()
    for c in ["Pedifod", "Retiro", "Pickup", "Delivery", "Fuera", "ONTIME"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
        else:
            d[c] = 0
    d["Tienda"] = d["Tienda"].apply(norm_txt)
    d = d.rename(columns={"Pedifod": "Pedidos"})
    d["OntimePct"] = d["ONTIME"] * 100 if d["ONTIME"].max() <= 1.5 else d["ONTIME"]

    # Preparación: % on time directo, por tienda
    prepa = d[["Tienda", "Formato", "Pedidos", "Fuera", "OntimePct"]].copy()
    prepa[["Sev", "SevLabel"]] = prepa["OntimePct"].apply(lambda p: pd.Series(sev_ontime(p)))
    ontime_prepa = prepa

    # Delivery: pedidos fuera de horario, discriminados por método de entrega
    deliv = d[["Tienda", "Formato", "Pedidos", "Retiro", "Pickup", "Delivery", "Fuera"]].copy()
    deliv["% Retiro"] = np.where(deliv["Fuera"] > 0, deliv["Retiro"] / deliv["Fuera"] * 100, 0)
    deliv["% Pickup"] = np.where(deliv["Fuera"] > 0, deliv["Pickup"] / deliv["Fuera"] * 100, 0)
    deliv["% Delivery"] = np.where(deliv["Fuera"] > 0, deliv["Delivery"] / deliv["Fuera"] * 100, 0)
    ontime_delivery = deliv

# ---- Fill Rate ----
fill_rate = None
if df_fr_raw is not None:
    d = df_fr_raw.copy()
    unidades_plus_col = "Unidades +" if "Unidades +" in d.columns else None
    no_entregado_plus_col = "No entregado +" if "No entregado +" in d.columns else None
    reemplazo_plus_col = "Reemplazo +" if "Reemplazo +" in d.columns else None

    rows = []
    for _, r in d.iterrows():
        tienda = norm_txt(r.get("Tienda"))
        unidades = ar_number(r.get(unidades_plus_col)) if unidades_plus_col else ar_number(r.get("Unidades"))
        sin_sustituto = ar_number(r.get(no_entregado_plus_col)) if no_entregado_plus_col else ar_number(r.get("no entregado"))
        con_sustituto = ar_number(r.get(reemplazo_plus_col)) if reemplazo_plus_col else ar_number(r.get("Reemplazo"))
        monto_faltante = r.get("Monto")
        monto_faltante = float(monto_faltante) if pd.notna(monto_faltante) and isinstance(monto_faltante, (int, float, np.integer, np.floating)) else ar_number(r.get("Monto N/E +"))
        limpio = r.get("Limpio")
        if pd.notna(limpio):
            fr_pct = float(limpio) * 100
        else:
            fr_pct = ar_number(r.get("FR"))
        rows.append({
            "Tienda": tienda, "Unidades": unidades, "SinSustituto": sin_sustituto,
            "ConSustituto": con_sustituto, "MontoFaltante": monto_faltante, "FRPct": fr_pct
        })
    fr_df = pd.DataFrame(rows)
    fr_df[["Sev", "SevLabel"]] = fr_df.apply(
        lambda r: pd.Series(sev_fr(r["FRPct"], r["Unidades"])), axis=1
    )
    fill_rate = fr_df

# ---- Cancelados ----
if cancelados is not None:
    cancelados["Tienda"] = cancelados["Tienda"].apply(norm_txt)
    cancelados["Total $"] = pd.to_numeric(cancelados["Total $"], errors="coerce").fillna(0)

# ---- Faltantes ----
faltantes = None
if df_faltantes_raw is not None:
    d = df_faltantes_raw.copy()
    d["Tienda"] = d["Tienda@DESC"].apply(norm_txt)
    d["Producto"] = d["SKU@DESC"].apply(norm_txt) if "SKU@DESC" in d.columns else ""
    d["Categoria"] = d["Clase@DESC"].apply(norm_txt) if "Clase@DESC" in d.columns else ""
    d["DiasSinVenta"] = pd.to_numeric(d.get("Dias sin venta"), errors="coerce")
    d["VentaProm"] = pd.to_numeric(d.get("Venta Promedio Semanal"), errors="coerce").fillna(0)
    alta_col = "ALTA_ROTACION" if "ALTA_ROTACION" in d.columns else "Alerta_Alta_Rotacion"
    d["AltaRotacion"] = d.get(alta_col, "No").apply(lambda v: norm_txt(v).lower() in ("si", "sí", "yes", "true", "1"))
    d["Etiqueta"] = d.get("Etiqueta_Stock", "").apply(norm_txt)
    d = d[d["Etiqueta"] != ""]
    d[["Sev", "SevLabel"]] = d["AltaRotacion"].apply(lambda a: pd.Series(sev_faltante(a)))
    faltantes = d

# ---------------------------------------------------------------------
# Unificar nombres de tienda entre hojas (mayúsc/minúsc, prefijo "Sucursal")
# y armar el filtro de tienda
# ---------------------------------------------------------------------

_canon_map = build_tienda_canon_map(
    [pedidos_72h, reclamos, ontime_prepa, ontime_delivery, fill_rate, cancelados, faltantes]
)
pedidos_72h = apply_tienda_canon(pedidos_72h, _canon_map)
reclamos = apply_tienda_canon(reclamos, _canon_map)
ontime_prepa = apply_tienda_canon(ontime_prepa, _canon_map)
ontime_delivery = apply_tienda_canon(ontime_delivery, _canon_map)
fill_rate = apply_tienda_canon(fill_rate, _canon_map)
cancelados = apply_tienda_canon(cancelados, _canon_map)
faltantes = apply_tienda_canon(faltantes, _canon_map)

all_stores = set()
for d in [pedidos_72h, reclamos, ontime_prepa, fill_rate, cancelados, faltantes]:
    if d is not None and "Tienda" in d.columns:
        all_stores.update([s for s in d["Tienda"].unique() if s])

any_data_loaded = len(all_stores) > 0

if any_data_loaded:
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
      <div style="font-size:12px;color:#6b7280;">
        Corte del reporte: <b style="color:#20252b;">{now_ref.strftime('%d/%m/%Y %H:%M')}</b>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tienda_sel = st.selectbox("Tienda", ["Todas las tiendas"] + sorted(all_stores), label_visibility="collapsed")
    filtro_tienda = None if tienda_sel == "Todas las tiendas" else tienda_sel

    def ftr(d):
        if d is None or filtro_tienda is None:
            return d
        return d[d["Tienda"] == filtro_tienda]

    pedidos_f = ftr(pedidos_72h)
    reclamos_f = ftr(reclamos)
    prepa_f = ftr(ontime_prepa)
    deliv_f = ftr(ontime_delivery)
    fr_f = ftr(fill_rate)
    can_f = ftr(cancelados)
    falt_f = ftr(faltantes)

    # ---- KPI row ----
    def kpi_card(label, value, sub, cls=""):
        return f"""
        <div class="kpi {cls}">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="sub">{sub}</div>
        </div>
        """

    kpis = []
    if pedidos_f is not None:
        card = kpi_card(
            "Pedidos +72h sin mover", f"{len(pedidos_f)}",
            f"{money(pedidos_f['MontoNum'].sum())} en pedidos",
            "crit" if len(pedidos_f) > 0 else "good"
        )
        kpis.append(kpi_link_wrap(card, html_doc_pedidos(pedidos_f), "operativo_pedidos_72h.html"))
    if reclamos_f is not None:
        abiertos = reclamos_f[reclamos_f["Estado"].isin(["Nuevo", "En proceso"])]
        r72 = (abiertos["Horas"] > 72).sum()
        r24 = ((abiertos["Horas"] >= 24) & (abiertos["Horas"] <= 72)).sum()
        card = kpi_card(
            "Reclamos abiertos", f"{len(abiertos)}",
            f"{r72} &gt;72h · {r24} 24–72h",
            "crit" if r72 > 0 else ("warn" if r24 > 0 else "good")
        )
        kpis.append(kpi_link_wrap(card, html_doc_reclamos(reclamos_f), "operativo_reclamos.html"))
    if prepa_f is not None and len(prepa_f):
        ped_tot = prepa_f["Pedidos"].sum()
        fuera_tot = prepa_f["Fuera"].sum()
        ot_pct = 100 * (1 - fuera_tot / ped_tot) if ped_tot else 0
        card = kpi_card(
            "On time preparación", pct1(ot_pct),
            f"Total: {int(ped_tot)} pedidos · {int(fuera_tot)} fuera de horario",
            "good" if ot_pct >= 95 else ("warn" if ot_pct >= 90 else "crit")
        )
        kpis.append(kpi_link_wrap(card, html_doc_prepa(prepa_f), "operativo_ontime_preparacion.html"))
    if fr_f is not None and len(fr_f):
        unid_tot = fr_f["Unidades"].sum()
        sin_tot = fr_f["SinSustituto"].sum()
        con_tot = fr_f["ConSustituto"].sum()
        fr_pct_tot = 100 * (1 - (sin_tot + con_tot) / unid_tot) if unid_tot else 0
        card = kpi_card(
            "Fill rate (con+sin sust.)", pct1(fr_pct_tot),
            f"{int(sin_tot)} unid. sin sustituto",
            "good" if fr_pct_tot >= 97 else ("warn" if fr_pct_tot >= 93 else "crit")
        )
        kpis.append(kpi_link_wrap(card, html_doc_fr(fr_f), "operativo_fill_rate.html"))
    if can_f is not None:
        card = kpi_card(
            "Pedidos cancelados", f"{len(can_f)}",
            f"{money(can_f['Total $'].sum())} totales"
        )
        kpis.append(kpi_link_wrap(card, html_doc_cancelados(can_f), "operativo_cancelados.html"))
    if falt_f is not None:
        alta = falt_f["AltaRotacion"].sum()
        card = kpi_card(
            "SKUs faltantes ECOM", f"{len(falt_f)}",
            f"{alta} de alta rotación",
            "crit" if alta > 0 else "warn"
        )
        kpis.append(kpi_link_wrap(card, html_doc_faltantes(falt_f), "operativo_faltantes.html"))

    if kpis:
        st.markdown(f'<div class="kpi-row">{"".join(kpis)}</div>', unsafe_allow_html=True)

    # ---- Pedidos +72h ----
    st.markdown(
        '<div class="section">📦 Pedidos sin movimiento +72hs</div>'
        '<div class="section-desc">Pedidos que llevan más de 3 días en el mismo estado sin avanzar.</div>',
        unsafe_allow_html=True
    )
    if pedidos_f is not None:
        if len(pedidos_f):
            show = pedidos_f.copy().sort_values("Dias", ascending=False)
            show["Días"] = show["Dias"].round(1)
            show["Monto"] = show["MontoNum"].apply(money)
            show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
            detail_cols = ["Pedido", "Tienda", "Estado", "Fecha", "Días", "Monto", "Urgencia"]

            agg = pedidos_f.groupby("Tienda").agg(
                Cantidad=("Pedido", "count")
            ).reset_index().sort_values("Cantidad", ascending=False)

            st.markdown('<div class="resumen-title">Resumen por tienda</div>', unsafe_allow_html=True)
            resumen_html = resumen_table_html(
                agg, "Tienda", {"Cantidad": lambda v: f"{int(v)}"}
            )
            st.write(resumen_html, unsafe_allow_html=True)

            with st.expander(f"Ver detalle de pedidos ({len(show)})"):
                with st.container(height=380):
                    st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

            export_body = (
                '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
                '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
                + table_html(show[detail_cols])
            )
            html_doc = export_section_html(
                "📦 Pedidos sin movimiento +72hs",
                "Pedidos que llevan más de 3 días en el mismo estado sin avanzar.",
                export_body
            )
            section_download_button(html_doc, "operativo_pedidos_72h.html", "dl_72h")
        else:
            st.markdown('<div class="empty-box">Sin pedidos estancados para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Pedidos +72hs para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Reclamos ----
    st.markdown(
        f'<div class="section">🗣️ Reclamos operativos '
        f'<span class="count-pill">{len(reclamos_f) if reclamos_f is not None else 0}</span></div>'
        '<div class="section-desc">Franjas de alerta: 24hs y 72hs sin acción.</div>',
        unsafe_allow_html=True
    )
    if reclamos_f is not None:
        solo_abiertos = st.checkbox("Mostrar solo abiertos (Nuevo / En proceso)", value=True, key="chk_reclamos")
        show = reclamos_f.copy()
        if solo_abiertos:
            show = show[show["Estado"].isin(["Nuevo", "En proceso"])]
        if len(show):
            show = show.sort_values("Horas", ascending=False)
            show["Horas"] = show["Horas"].round(1)
            show["Urgencia"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
            detail_cols = ["Reclamo", "Pedido", "Tienda", "Tipo", "Estado", "Fecha", "Horas", "Urgencia"]

            base = reclamos_f.copy()
            if solo_abiertos:
                base = base[base["Estado"].isin(["Nuevo", "En proceso"])]
            agg = base.groupby("Tienda").apply(lambda g: pd.Series({
                "Cantidad": len(g),
                ">72h": int((g["Horas"] > 72).sum()),
                "24–72h": int(((g["Horas"] >= 24) & (g["Horas"] <= 72)).sum()),
            })).reset_index().sort_values("Cantidad", ascending=False)
            agg_tipo = base.groupby("Tipo").agg(
                Cantidad=("Pedido", "count")
            ).reset_index().sort_values("Cantidad", ascending=False)

            resumen_html = resumen_table_html(
                agg, "Tienda",
                {"Cantidad": lambda v: f"{int(v)}", ">72h": lambda v: f"{int(v)}", "24–72h": lambda v: f"{int(v)}"}
            )
            resumen_tipo_html = resumen_table_html(agg_tipo, "Tipo", {"Cantidad": lambda v: f"{int(v)}"})
            resumen_side_by_side = (
                '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Resumen por tienda</div>' + resumen_html + '</div>'
                '<div style="flex:1;min-width:260px;">'
                '<div class="resumen-title">Resumen por tipo</div>' + resumen_tipo_html + '</div>'
                '</div>'
            )
            export_body = (
                resumen_side_by_side +
                '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
                + table_html(show[detail_cols])
            )
            html_doc = export_section_html(
                "🗣️ Reclamos operativos",
                "Franjas de alerta: 24hs y 72hs sin acción.",
                export_body
            )

            r72_tot = int((base["Horas"] > 72).sum())
            r24_tot = int(((base["Horas"] >= 24) & (base["Horas"] <= 72)).sum())
            mini_card = kpi_card(
                "Reclamos abiertos" if solo_abiertos else "Reclamos (todos)", f"{len(show)}",
                f"{r72_tot} &gt;72h · {r24_tot} 24–72h — clickeá para bajar el HTML",
                "crit" if r72_tot > 0 else ("warn" if r24_tot > 0 else "good")
            )
            st.markdown(
                f'<div class="kpi-row" style="margin:4px 0 14px; grid-template-columns: minmax(230px, 340px);">'
                f'{kpi_link_wrap(mini_card, html_doc, "operativo_reclamos.html")}</div>',
                unsafe_allow_html=True
            )

            col_tienda, col_tipo = st.columns(2)
            with col_tienda:
                st.markdown('<div class="resumen-title">Resumen por tienda</div>', unsafe_allow_html=True)
                st.write(resumen_html, unsafe_allow_html=True)
            with col_tipo:
                st.markdown('<div class="resumen-title">Resumen por tipo</div>', unsafe_allow_html=True)
                st.write(resumen_tipo_html, unsafe_allow_html=True)

            with st.expander(f"Ver detalle de reclamos ({len(show)})"):
                with st.container(height=380):
                    st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

            section_download_button(html_doc, "operativo_reclamos.html", "dl_reclamos")
        else:
            st.markdown('<div class="empty-box">Sin reclamos para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Reclamos para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- On Time Preparación ----
    st.markdown(
        f'<div class="section">⏱️ On Time Preparación '
        f'<span class="count-pill">{len(prepa_f) if prepa_f is not None else 0}</span></div>'
        '<div class="section-desc">Porcentaje de pedidos preparados en horario, por tienda.</div>',
        unsafe_allow_html=True
    )
    if prepa_f is not None and len(prepa_f):
        b = prepa_bundle(prepa_f)
        show, detail_cols, html_doc = b["show"], b["detail_cols"], b["html_doc"]

        mini_card = kpi_card(
            "On time preparación", pct1(b["ot_pct_tot"]),
            f"Total: {b['ped_tot']} pedidos · {b['fuera_tot']} fuera de horario — clickeá para bajar el HTML",
            "good" if b["ot_pct_tot"] >= 95 else ("warn" if b["ot_pct_tot"] >= 90 else "crit")
        )
        st.markdown(
            f'<div class="kpi-row" style="margin:4px 0 14px; grid-template-columns: minmax(230px, 340px);">'
            f'{kpi_link_wrap(mini_card, html_doc, "operativo_ontime_preparacion.html")}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="resumen-title">Top 5 tiendas con % on time &lt; 95%</div>',
            unsafe_allow_html=True
        )
        st.write(b["top5_html"], unsafe_allow_html=True)

        st.markdown('<div class="resumen-title" style="margin-top:14px;">Detalle completo</div>', unsafe_allow_html=True)
        with st.container(height=380):
            st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

        section_download_button(html_doc, "operativo_ontime_preparacion.html", "dl_prepa")
    else:
        st.markdown('<div class="empty-box">Subí el archivo de On Time para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- On Time Delivery (por método) ----
    st.markdown(
        f'<div class="section">🚚 On Time Delivery — por método '
        f'<span class="count-pill">{len(deliv_f) if deliv_f is not None else 0}</span></div>'
        '<div class="section-desc">De los pedidos fuera de horario, cuántos correspondieron a cada método de entrega.</div>',
        unsafe_allow_html=True
    )
    if deliv_f is not None and len(deliv_f):
        tot_retiro = deliv_f["Retiro"].sum()
        tot_pickup = deliv_f["Pickup"].sum()
        tot_delivery = deliv_f["Delivery"].sum()
        tot_fuera = deliv_f["Fuera"].sum()
        c1, c2, c3 = st.columns(3)
        for col, label, val in zip(
            [c1, c2, c3],
            ["Retiro", "Pickup", "Delivery"],
            [tot_retiro, tot_pickup, tot_delivery]
        ):
            share = (val / tot_fuera * 100) if tot_fuera else 0
            with col:
                st.markdown(kpi_card(f"FUERA DE HORARIO · {label.upper()}", f"{int(val)}", f"{pct1(share)} del total fuera"), unsafe_allow_html=True)
        show = deliv_f.copy().sort_values("Fuera", ascending=False)
        for c in ["Pedidos", "Retiro", "Pickup", "Delivery", "Fuera"]:
            show[c] = show[c].astype(int)
        show["% Retiro"] = show["% Retiro"].apply(pct1)
        show["% Pickup"] = show["% Pickup"].apply(pct1)
        show["% Delivery"] = show["% Delivery"].apply(pct1)
        detail_cols = ["Tienda", "Formato", "Pedidos", "Fuera", "Retiro", "% Retiro", "Pickup", "% Pickup", "Delivery", "% Delivery"]
        with st.container(height=380):
            st.write(table_html(show[detail_cols]), unsafe_allow_html=True)
        html_doc = export_section_html(
            "🚚 On Time Delivery — por método",
            "De los pedidos fuera de horario, cuántos correspondieron a cada método de entrega.",
            table_html(show[detail_cols])
        )
        section_download_button(html_doc, "operativo_ontime_delivery.html", "dl_delivery")
    else:
        st.markdown('<div class="empty-box">Subí el archivo de On Time para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Fill Rate ----
    st.markdown(
        f'<div class="section">🧩 Fill Rate — con y sin sustituto '
        f'<span class="count-pill">{len(fr_f) if fr_f is not None else 0}</span></div>'
        '<div class="section-desc">Unidades faltantes por tienda: cubiertas con reemplazo vs. no entregadas.</div>',
        unsafe_allow_html=True
    )
    if fr_f is not None and len(fr_f):
        show = fr_f.copy().sort_values("FRPct")
        show["Unidades"] = show["Unidades"].astype(int)
        show["Sin sustituto"] = show["SinSustituto"].astype(int)
        show["Con sustituto"] = show["ConSustituto"].astype(int)
        show["Monto faltante"] = show["MontoFaltante"].apply(money)
        show["FR %"] = show["FRPct"].apply(pct1)
        show["Estado"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
        detail_cols = ["Tienda", "Unidades", "Sin sustituto", "Con sustituto", "Monto faltante", "FR %", "Estado"]
        with st.container(height=380):
            st.write(table_html(show[detail_cols]), unsafe_allow_html=True)
        html_doc = export_section_html(
            "🧩 Fill Rate — con y sin sustituto",
            "Unidades faltantes por tienda: cubiertas con reemplazo vs. no entregadas.",
            table_html(show[detail_cols])
        )
        section_download_button(html_doc, "operativo_fill_rate.html", "dl_fr")
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Fill Rate para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Cancelados ----
    st.markdown(
        f'<div class="section">🚫 Pedidos cancelados '
        f'<span class="count-pill">{len(can_f) if can_f is not None else 0}</span></div>'
        '<div class="section-desc">Cancelaciones por tienda en el período del reporte.</div>',
        unsafe_allow_html=True
    )
    if can_f is not None:
        if len(can_f):
            b = cancelados_bundle(can_f)

            st.markdown('<div class="resumen-title">Top 10 tiendas con más cancelados</div>', unsafe_allow_html=True)
            st.write(b["top10_html"], unsafe_allow_html=True)

            with st.expander(f"Ver resumen completo por tienda ({len(b['agg'])} tiendas)"):
                st.write(b["resumen_html"], unsafe_allow_html=True)

            with st.expander(f"Ver detalle de pedidos cancelados ({len(b['det'])})"):
                with st.container(height=380):
                    st.write(table_html(b["det"][b["detail_cols"]]), unsafe_allow_html=True)

            section_download_button(b["html_doc"], "operativo_cancelados.html", "dl_cancelados")
        else:
            st.markdown('<div class="empty-box">Sin cancelaciones para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Cancelados para ver esta sección.</div>', unsafe_allow_html=True)

    # ---- Faltantes ----
    st.markdown(
        f'<div class="section">📉 Faltantes ECOM '
        f'<span class="count-pill">{len(falt_f) if falt_f is not None else 0}</span></div>'
        '<div class="section-desc">SKUs marcados como faltante para e-commerce, por tienda. Los de alta rotación se priorizan primero.</div>',
        unsafe_allow_html=True
    )
    if falt_f is not None:
        if len(falt_f):
            show = falt_f.copy().sort_values(["AltaRotacion", "VentaProm"], ascending=[False, False])
            show["Días sin venta"] = show["DiasSinVenta"]
            show["Venta prom. semanal"] = show["VentaProm"].round(1)
            show["Prioridad"] = show.apply(lambda r: badge(r["Sev"], r["SevLabel"]), axis=1)
            detail_cols = ["Tienda", "Producto", "Categoria", "Días sin venta", "Venta prom. semanal", "Prioridad"]

            agg = falt_f.groupby("Tienda").agg(
                Cantidad=("Producto", "count"), AltaRotacion=("AltaRotacion", "sum")
            ).reset_index().rename(columns={"AltaRotacion": "Alta rotación"})
            agg = agg.sort_values("Cantidad", ascending=False)

            st.markdown('<div class="resumen-title">Resumen por tienda</div>', unsafe_allow_html=True)
            resumen_html = resumen_table_html(
                agg, "Tienda",
                {"Cantidad": lambda v: f"{int(v)}", "Alta rotación": lambda v: f"{int(v)}"}
            )
            st.write(resumen_html, unsafe_allow_html=True)

            with st.expander(f"Ver detalle de faltantes ({len(show)})"):
                with st.container(height=380):
                    st.write(table_html(show[detail_cols]), unsafe_allow_html=True)

            export_body = (
                '<div class="resumen-title">Resumen por tienda</div>' + resumen_html +
                '<div class="resumen-title" style="margin-top:18px;">Detalle completo</div>'
                + table_html(show[detail_cols])
            )
            html_doc = export_section_html(
                "📉 Faltantes ECOM",
                "SKUs marcados como faltante para e-commerce, por tienda.",
                export_body
            )
            section_download_button(html_doc, "operativo_faltantes.html", "dl_faltantes")
        else:
            st.markdown('<div class="empty-box">Sin faltantes para esta selección 🎉</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-box">Subí el archivo de Faltantes para ver esta sección.</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="color:#6b7280;font-size:11.5px;text-align:center;margin-top:18px;">'
        'Operativo · datos del Reporte diario · esta página no guarda historial: volvé a subir los archivos '
        'actualizados para regenerar el panel.</div>',
        unsafe_allow_html=True
    )

else:
    st.markdown(
        '<div class="empty-box" style="margin-top:20px;">'
        'Subí al menos un archivo arriba para ver el panel operativo.</div>',
        unsafe_allow_html=True
    )
