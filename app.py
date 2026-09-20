import streamlit as st
from pathlib import Path
import base64

st.set_page_config(
    page_title="MásOnline | Panel",
    page_icon="🏠",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #ffffff; }
    .block-container { max-width: 1100px; padding: 0 1.2rem 1.2rem; }

    .hero {
        background: #ffffff;
        margin: -1rem -1.2rem 1.4rem;
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

    .section {
        font-size: 20px; font-weight: 800; color: #20252b;
        margin: 10px 0 18px;
    }

    .home-card {
        background: white; border-radius: 14px; padding: 26px 24px;
        box-shadow: 0 2px 10px rgba(0,0,0,.06);
        border: 1px solid #e8ebef; min-height: 150px;
    }
    .home-icon { font-size: 34px; margin-bottom: 10px; }
    .home-title { color: #20252b; font-size: 18px; font-weight: 800; }
    .home-text { color: #6b7280; font-size: 13px; margin-top: 8px; line-height: 1.5; }

    .footer {
        display: flex; justify-content: space-between; color: #6b7280;
        font-size: 12px; margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

LOGO_FILE = Path(__file__).resolve().parent / "masonline_logo.png"

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
    <div class="hero-sub">PANEL DE INDICADORES</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section">¿Qué querés ver?</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="home-card">
      <div class="home-icon">📊</div>
      <div class="home-title">Dashboard de Ventas</div>
      <div class="home-text">
        Venta acumulada, participación e-commerce, comparaciones vs. mes
        anterior y año anterior, resumen para GDN y venta por fin de semana.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(
        "pages/2_📊_Ventas.py",
        label="Ir al Dashboard de Ventas",
        icon="📊",
        use_container_width=True,
    )

with col2:
    st.markdown("""
    <div class="home-card">
      <div class="home-icon">🚨</div>
      <div class="home-title">Panel Operativo</div>
      <div class="home-text">
        Pedidos +72h, reclamos, On Time de preparación y delivery, Fill
        Rate, cancelados y faltantes.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link(
        "pages/1_🚨_Operativo.py",
        label="Ir al Panel Operativo",
        icon="🚨",
        use_container_width=True,
    )

st.markdown(
    '<div class="footer">'
    '<span>MásOnline &nbsp;|&nbsp; E-commerce</span>'
    '</div>',
    unsafe_allow_html=True
)
