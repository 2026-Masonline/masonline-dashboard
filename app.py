import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------
# Configuración general de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ventas · Panel de control",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------
# Sistema de diseño: colores, tipografía, estilos
# ---------------------------------------------------------
NAVY = "#12213D"
NAVY_LIGHT = "#1C3159"
TEAL = "#0E7C7B"
TEAL_SOFT = "#DCEEEE"
AMBER = "#E0973C"
AMBER_SOFT = "#FBEADA"
INK = "#1F2430"
SLATE = "#6B7280"
BG = "#F6F7F9"
CARD_BORDER = "#E4E6EB"

PALETTE_SEQUENCE = [TEAL, NAVY, AMBER, "#8FB8B7", "#5B7A99"]

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {INK};
}}

.stApp {{
    background-color: {BG};
}}

h1, h2, h3 {{
    font-family: 'Sora', sans-serif !important;
    color: {INK};
}}

/* Título principal */
.dash-header {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 2px solid {NAVY};
    padding-bottom: 0.6rem;
    margin-bottom: 1.6rem;
}}
.dash-header h1 {{
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0;
}}
.dash-header span {{
    color: {SLATE};
    font-size: 0.9rem;
}}

/* Sidebar oscuro */
section[data-testid="stSidebar"] {{
    background-color: {NAVY};
}}
section[data-testid="stSidebar"] * {{
    color: #E7ECF5 !important;
}}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background-color: {TEAL} !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    font-family: 'Sora', sans-serif !important;
    color: #FFFFFF !important;
}}

/* Bloques KPI */
.kpi-row {{
    display: flex;
    gap: 1rem;
    margin-bottom: 0.5rem;
}}
.kpi-block {{
    flex: 1;
    background: #FFFFFF;
    border: 1px solid {CARD_BORDER};
    border-left: 4px solid {TEAL};
    border-radius: 4px;
    padding: 0.9rem 1.1rem;
}}
.kpi-block.alt {{
    border-left-color: {NAVY};
}}
.kpi-label {{
    font-size: 0.8rem;
    font-weight: 600;
    color: #4B5160;
    margin-bottom: 0.25rem;
}}
.kpi-value {{
    font-family: 'Sora', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: {INK};
    line-height: 1.2;
}}
.kpi-delta {{
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 0.3rem;
}}
.kpi-delta.up {{ color: {TEAL}; }}
.kpi-delta.down {{ color: {AMBER}; }}

/* Encabezados de sección */
.section-title {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-top: 1.4rem;
    margin-bottom: 0.6rem;
}}
.section-title .bar {{
    width: 4px;
    height: 1.3rem;
    background-color: {TEAL};
    border-radius: 2px;
}}
.section-title h3 {{
    margin: 0;
    font-size: 1.15rem;
    font-weight: 600;
}}

div[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid {CARD_BORDER};
    border-radius: 4px;
    padding: 0.6rem 0.8rem;
}}

hr {{
    border-color: {CARD_BORDER};
}}
</style>
"""

CHART_FONT = dict(family="Inter, sans-serif", color=INK)


def style_fig(fig, title=None):
    fig.update_layout(
        font=CHART_FONT,
        title=dict(text=title, font=dict(family="Sora, sans-serif", size=16, color=INK)) if title else None,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50 if title else 20, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
    )
    fig.update_xaxes(gridcolor="#EDEEF2", zeroline=False)
    fig.update_yaxes(gridcolor="#EDEEF2", zeroline=False)
    return fig


def section_title(text):
    st.markdown(
        f'<div class="section-title"><div class="bar"></div><h3>{text}</h3></div>',
        unsafe_allow_html=True,
    )


DEFAULT_FILE = "Venta_Con_y_sin_Impuesto__20_.xlsx"

COLUMN_MAP = {
    0: "Mes",
    1: "Fecha",
    2: "Dia",
    3: "Tienda_Cod",
    4: "Tienda_Nombre",
    5: "Facturacion",
    6: "Venta_Ecommerce",
    7: "Venta_Operativa",
    8: "Venta_Operativa_Ecommerce",
    9: "Cantidad_Venta_Ecommerce",
    10: "Pedidos_Ecommerce",
}


@st.cache_data(show_spinner="Cargando datos...")
def load_data(file) -> pd.DataFrame:
    df = pd.read_excel(file, header=2)
    df = df.rename(columns={df.columns[i]: name for i, name in COLUMN_MAP.items()})
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    numeric_cols = [
        "Facturacion",
        "Venta_Ecommerce",
        "Venta_Operativa",
        "Venta_Operativa_Ecommerce",
        "Cantidad_Venta_Ecommerce",
        "Pedidos_Ecommerce",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Tienda"] = df["Tienda_Cod"].astype(str) + " - " + df["Tienda_Nombre"].astype(str)
    return df


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# Carga del archivo
# ---------------------------------------------------------
st.markdown(
    '<div class="dash-header"><h1>Ventas — Panel de control</h1>'
    '<span>Facturación, ecommerce y performance por tienda</span></div>',
    unsafe_allow_html=True,
)

data_source = None
if Path(DEFAULT_FILE).exists():
    data_source = DEFAULT_FILE
else:
    uploaded = st.file_uploader("Subí el archivo Excel de ventas (.xlsx)", type=["xlsx"])
    if uploaded is not None:
        data_source = uploaded

if data_source is None:
    st.info("Subí el archivo para comenzar, o colocá el Excel junto a este script con el nombre "
            f"'{DEFAULT_FILE}'.")
    st.stop()

df = load_data(data_source)

# ---------------------------------------------------------
# Filtros (sidebar)
# ---------------------------------------------------------
st.sidebar.header("Filtros")

meses_disponibles = sorted(df["Mes"].unique(), key=lambda m: df.loc[df["Mes"] == m, "Fecha"].min())
meses_sel = st.sidebar.multiselect("Mes", meses_disponibles, default=meses_disponibles)

tiendas_disponibles = sorted(df["Tienda"].unique())
tiendas_sel = st.sidebar.multiselect("Tienda", tiendas_disponibles, default=[])

fecha_min, fecha_max = df["Fecha"].min(), df["Fecha"].max()
rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max,
)

df_f = df[df["Mes"].isin(meses_sel)]
if tiendas_sel:
    df_f = df_f[df_f["Tienda"].isin(tiendas_sel)]
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    inicio, fin = pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])
    df_f = df_f[(df_f["Fecha"] >= inicio) & (df_f["Fecha"] <= fin)]

if df_f.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ---------------------------------------------------------
# KPIs principales
# ---------------------------------------------------------
facturacion_total = df_f["Facturacion"].sum()
venta_ecommerce_total = df_f["Venta_Ecommerce"].sum()
pedidos_total = df_f["Pedidos_Ecommerce"].sum()
ticket_promedio = venta_ecommerce_total / pedidos_total if pedidos_total > 0 else 0

# Deltas mes contra mes, cuando hay al menos dos meses en la selección
resumen_mes_kpi = df_f.groupby("Mes", as_index=False)[
    ["Facturacion", "Venta_Ecommerce", "Pedidos_Ecommerce"]
].sum()
resumen_mes_kpi = resumen_mes_kpi.sort_values(
    by="Mes", key=lambda s: s.map({m: df.loc[df["Mes"] == m, "Fecha"].min() for m in s})
)


def delta_html(serie):
    if len(resumen_mes_kpi) < 2 or serie.iloc[0] == 0:
        return ""
    var = (serie.iloc[-1] - serie.iloc[0]) / serie.iloc[0] * 100
    cls = "up" if var >= 0 else "down"
    signo = "+" if var >= 0 else ""
    return f'<div class="kpi-delta {cls}">{signo}{var:.1f}% vs {resumen_mes_kpi["Mes"].iloc[0]}</div>'


kpis = [
    ("Facturación total (con imp.)", f"${facturacion_total:,.0f}", delta_html(resumen_mes_kpi["Facturacion"]), ""),
    ("Venta Ecommerce total", f"${venta_ecommerce_total:,.0f}", delta_html(resumen_mes_kpi["Venta_Ecommerce"]), "alt"),
    ("Pedidos Ecommerce", f"{pedidos_total:,.0f}", delta_html(resumen_mes_kpi["Pedidos_Ecommerce"]), ""),
    ("Ticket promedio Ecommerce", f"${ticket_promedio:,.0f}", "", "alt"),
]

kpi_html = '<div class="kpi-row">'
for label, value, delta, alt_class in kpis:
    kpi_html += (
        f'<div class="kpi-block {alt_class}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta}'
        f'</div>'
    )
kpi_html += "</div>"
st.markdown(kpi_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# Comparación Agosto vs Septiembre (u otros meses seleccionados)
# ---------------------------------------------------------
section_title("Comparación mensual")

resumen_mes = (
    df_f.groupby("Mes", as_index=False)[["Facturacion", "Venta_Ecommerce", "Pedidos_Ecommerce"]]
    .sum()
)
resumen_mes = resumen_mes.sort_values(
    by="Mes", key=lambda s: s.map({m: df.loc[df["Mes"] == m, "Fecha"].min() for m in s})
)

c1, c2 = st.columns([2, 1])
with c1:
    fig_mes = px.bar(
        resumen_mes.melt(id_vars="Mes", value_vars=["Facturacion", "Venta_Ecommerce"],
                          var_name="Métrica", value_name="Monto"),
        x="Mes", y="Monto", color="Métrica", barmode="group",
        color_discrete_map={"Facturacion": NAVY, "Venta_Ecommerce": TEAL},
    )
    fig_mes = style_fig(fig_mes, "Facturación vs Venta Ecommerce por mes")
    st.plotly_chart(fig_mes, use_container_width=True)

with c2:
    st.dataframe(
        resumen_mes.rename(columns={
            "Facturacion": "Facturación",
            "Venta_Ecommerce": "Venta Ecommerce",
            "Pedidos_Ecommerce": "Pedidos",
        }),
        hide_index=True,
        use_container_width=True,
    )
    if len(resumen_mes) == 2:
        variacion = (
            (resumen_mes["Facturacion"].iloc[1] - resumen_mes["Facturacion"].iloc[0])
            / resumen_mes["Facturacion"].iloc[0] * 100
        )
        st.metric(
            f"Variación Facturación ({resumen_mes['Mes'].iloc[0]} → {resumen_mes['Mes'].iloc[1]})",
            f"{variacion:+.1f}%",
        )

# ---------------------------------------------------------
# Ranking de tiendas
# ---------------------------------------------------------
section_title("Ranking de tiendas")

metrica_ranking = st.selectbox(
    "Métrica para el ranking",
    ["Facturacion", "Venta_Ecommerce", "Venta_Operativa", "Pedidos_Ecommerce"],
    format_func=lambda x: {
        "Facturacion": "Facturación",
        "Venta_Ecommerce": "Venta Ecommerce",
        "Venta_Operativa": "Venta Operativa",
        "Pedidos_Ecommerce": "Pedidos Ecommerce",
    }[x],
)

ranking = df_f.groupby("Tienda", as_index=False)[metrica_ranking].sum().sort_values(
    metrica_ranking, ascending=False
)

top_n = st.slider("Cantidad de tiendas a mostrar en cada extremo", 3, 20, 10)

r1, r2 = st.columns(2)
with r1:
    fig_top = px.bar(
        ranking.head(top_n).sort_values(metrica_ranking),
        x=metrica_ranking, y="Tienda", orientation="h",
        color_discrete_sequence=[TEAL],
    )
    fig_top = style_fig(fig_top, f"Top {top_n} tiendas")
    st.plotly_chart(fig_top, use_container_width=True)

with r2:
    fig_bottom = px.bar(
        ranking.tail(top_n).sort_values(metrica_ranking, ascending=False).sort_values(metrica_ranking),
        x=metrica_ranking, y="Tienda", orientation="h",
        color_discrete_sequence=[AMBER],
    )
    fig_bottom = style_fig(fig_bottom, f"Bottom {top_n} tiendas")
    st.plotly_chart(fig_bottom, use_container_width=True)

# ---------------------------------------------------------
# Evolución diaria
# ---------------------------------------------------------
section_title("Evolución diaria")

metrica_evolucion = st.selectbox(
    "Métrica para la evolución diaria",
    ["Facturacion", "Venta_Ecommerce", "Venta_Operativa", "Pedidos_Ecommerce"],
    format_func=lambda x: {
        "Facturacion": "Facturación",
        "Venta_Ecommerce": "Venta Ecommerce",
        "Venta_Operativa": "Venta Operativa",
        "Pedidos_Ecommerce": "Pedidos Ecommerce",
    }[x],
    key="metrica_evolucion",
)

serie_diaria = df_f.groupby("Fecha", as_index=False)[metrica_evolucion].sum()

fig_evolucion = go.Figure()
fig_evolucion.add_trace(
    go.Scatter(
        x=serie_diaria["Fecha"], y=serie_diaria[metrica_evolucion],
        mode="lines+markers",
        line=dict(color=NAVY, width=2),
        marker=dict(color=TEAL, size=6),
        fill="tozeroy",
        fillcolor="rgba(14, 124, 123, 0.08)",
    )
)
fig_evolucion = style_fig(fig_evolucion, f"Evolución diaria — {metrica_evolucion.replace('_', ' ')}")
st.plotly_chart(fig_evolucion, use_container_width=True)

# ---------------------------------------------------------
# Tabla de detalle
# ---------------------------------------------------------
with st.expander("Ver datos detallados"):
    st.dataframe(
        df_f[[
            "Fecha", "Mes", "Dia", "Tienda", "Facturacion", "Venta_Ecommerce",
            "Venta_Operativa", "Venta_Operativa_Ecommerce",
            "Cantidad_Venta_Ecommerce", "Pedidos_Ecommerce",
        ]].sort_values("Fecha"),
        use_container_width=True,
        hide_index=True,
    )
