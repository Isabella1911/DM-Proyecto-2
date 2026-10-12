"""Aplicación del Proyecto 2: seguimiento celular en embriones de pez cebra.

Ejecutar desde la raíz del repositorio:  streamlit run app/app.py
"""
import streamlit as st

st.set_page_config(page_title="Seguimiento celular · Biohub", page_icon="🔬", layout="wide")

paginas = st.navigation([
    st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True),
    st.Page("paginas/explorar.py", title="Explorar los datos", icon=":material/query_stats:"),
    st.Page("paginas/modelos.py", title="Probar los modelos", icon=":material/biotech:"),
    st.Page("paginas/rendimiento.py", title="Rendimiento", icon=":material/leaderboard:"),
])

with st.sidebar:
    st.caption("CC3084 Data Science · UVG · Semestre II 2026")
    st.caption("Isabella Obando · Anthony Lou · Fabian Prado · Fernando Mendoza")

paginas.run()
