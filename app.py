import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración visual de la página
st.set_page_config(
    page_title="Panel de Control - Prop Firms",
    page_icon="📈",
    layout="wide"
)

# Estilo visual moderno / oscuro
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2A2E39;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal
st.title("📈 Mi Dashboard de Cuentas de Fondeo")
st.write("Visión consolidada en tiempo real de todas tus cuentas y challenges.")

st.divider()

# --- DATOS DE EJEMPLO (Se reemplazarán automáticamente cuando conectemos MetaTrader) ---
cuentas_ejemplo = [
    {
        "Nombre": "FTMO $100k (Fondeada)",
        "Estado": "Fondeada",
        "Balance Inicial": 100000,
        "Balance Actual": 104250,
        "Equidad": 104800,
        "Perdida Diaria Max": 5000,
        "Perdida Diaria Actual": 450,
        "Objetivo Profit": 0,
    },
    {
        "Nombre": "Funding Pips $50k (Challenge F1)",
        "Estado": "Challenge",
        "Balance Inicial": 50000,
        "Balance Actual": 52300,
        "Equidad": 52300,
        "Perdida Diaria Max": 2500,
        "Perdida Diaria Actual": 120,
        "Objetivo Profit": 4000, # 8%
    }
]

# Sidebar / Menú lateral
st.sidebar.header("🔍 Filtros de Cuenta")
opciones_cuentas = ["Todas las Cuentas"] + [c["Nombre"] for c in cuentas_ejemplo]
cuenta_seleccionada = st.sidebar.selectbox("Seleccionar Cuenta:", opciones_cuentas)

# --- RESUMEN GLOBAL ---
st.subheader("🌐 Resumen Global de Capital")

tot_balance = sum([c["Balance Actual"] for c in cuentas_ejemplo])
tot_inicial = sum([c["Balance Inicial"] for c in cuentas_ejemplo])
tot_beneficio = tot_balance - tot_inicial

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Capital Total Gestionado", value=f"${tot_balance:,.2f}", delta=f"${tot_beneficio:,.2f}")

with col2:
    st.metric(label="Cuentas Activas", value=len(cuentas_ejemplo))

with col3:
    st.metric(label="Cuentas Fondeadas", value=sum(1 for c in cuentas_ejemplo if c["Estado"] == "Fondeada"))

with col4:
    st.metric(label="Cuentas en Challenge", value=sum(1 for c in cuentas_ejemplo if c["Estado"] == "Challenge"))

st.divider()

# --- DETALLE DE CUENTAS ---
st.subheader("📋 Detalle de Cuentas")

for c in cuentas_ejemplo:
    if cuenta_seleccionada == "Todas las Cuentas" or cuenta_seleccionada == c["Nombre"]:
        with st.expander(f"🔹 **{c['Nombre']}** — [{c['Estado']}]", expanded=True):
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric("Balance / Equidad", f"${c['Balance Actual']:,.2f}", f"Equidad: ${c['Equidad']:,.2f}")
            
            # Cálculo de pérdida diaria
            margen_diario = c['Perdida Diaria Max'] - c['Perdida Diaria Actual']
            m2.metric("Límite Pérdida Diaria", f"${c['Perdida Diaria Max']:,.2f}", f"Margen seguro: ${margen_diario:,.2f}")
            
            if c["Estado"] == "Challenge":
                ganado = c['Balance Actual'] - c['Balance Inicial']
                progreso = min(max(ganado / c['Objetivo Profit'], 0.0), 1.0) if c['Objetivo Profit'] > 0 else 1.0
                m3.metric("Objetivo Profit", f"${c['Objetivo Profit']:,.2f}", f"Ganado: ${ganado:,.2f}")
                
                st.write("**Progreso del Challenge:**")
                st.progress(progreso, text=f"{progreso*100:.1f}% alcanzado")
            else:
                beneficio_payout = c['Balance Actual'] - c['Balance Inicial']
                m3.metric("Acumulado para Payout", f"${beneficio_payout:,.2f}")
                st.caption("🟢 Cuenta en fase de explotación de beneficios.")
