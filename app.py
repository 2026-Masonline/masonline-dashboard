import streamlit as st

# La carga de reportes se mudó a la pestaña "Cargar Reportes" del menú de
# la izquierda (archivo pages/0_📤_Cargar_Reportes.py) — ahí sí aparece
# como un ítem más del menú, cosa que esta página "app" (la principal) no
# hace nunca en Streamlit. Esta pantalla solo te manda para allá.

st.set_page_config(
    page_title="MásOnline | Ecommerce",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #ffffff; }
    .block-container { max-width: 700px; padding: 3rem 1.2rem 1.2rem; }
    .hero-brand { font-size: 28px; font-weight: 800; letter-spacing: -.5px; color:#20252b; margin-bottom: 3px; }
    .hero-brand span { font-weight: 400; }
    .hero-sub { font-size: 11px; letter-spacing: 3px; margin-bottom: 24px; opacity: .85; color:#20252b; }
    .redirect-box {
        background: white; border: 1px solid #e8ebef; border-radius: 14px;
        padding: 20px 22px; box-shadow: 0 2px 10px rgba(0,0,0,.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-brand">Más<span>Online</span></div>
<div class="hero-sub">E-COMMERCE &nbsp;·&nbsp; CARGA DE DATOS</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="redirect-box">
  <div style="font-size:14px;font-weight:800;color:#20252b;margin-bottom:6px;">
    La carga de reportes se mudó 📤
  </div>
  <div style="font-size:13px;color:#6b7280;">
    Ahora vive en la pestaña <b>Cargar Reportes</b>, en el menú de la izquierda
    (abajo de Comparativo) — ahí vas a encontrar las mismas tarjetas de
    siempre para subir los Excel de Venta y los reportes operativos.
  </div>
</div>
""", unsafe_allow_html=True)

try:
    st.page_link("pages/0_📤_Cargar_Reportes.py", label="Ir a Cargar Reportes", icon="📤")
except Exception:
    pass

# Si la versión de Streamlit lo soporta, salta directo sin que haya que
# tocar nada — si falla (versión vieja), no pasa nada, ya le dejamos el
# link de arriba.
try:
    st.switch_page("pages/0_📤_Cargar_Reportes.py")
except Exception:
    pass
