import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configuración visual
st.set_page_config(
    page_title="Panel de Control - Prop Firms",
    page_icon="📈",
    layout="wide"
)

# Conexión segura a Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Configura las credenciales de Supabase en los 'Secrets' de Streamlit.")
    st.stop()

# Función para consultar las cuentas
def obtener_cuentas():
    res = supabase.table("cuentas").select("*").execute()
    return res.data

# Título del panel
st.title("📈 Mi Dashboard de Cuentas de Fondeo")
st.caption("Visión consolidada en tiempo real conectada a MetaTrader 5.")

st.divider()

# Botón para refrescar
if st.button("🔄 Actualizar Datos"):
    st.rerun()

# Lectura de datos
datos = obtener_cuentas()

if not datos:
    st.info("ℹ️ Aún no hay cuentas conectadas. Ejecuta el conector en tu MetaTrader 5 para empezar a ver tus métricas aquí.")
else:
    df = pd.DataFrame(datos)
    
    # Resumen Global
    st.subheader("🌐 Resumen Global de Capital")
    
    tot_balance = df["balance"].sum()
    tot_inicial = df["balance_inicial"].sum()
    tot_beneficio = tot_balance - tot_inicial
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capital Total Gestionado", f"${tot_balance:,.2f}", f"${tot_beneficio:,.2f}")
    c2.metric("Cuentas Totales", len(df))
    c3.metric("Cuentas Fondeadas", len(df[df["estado"] == "Fondeada"]))
    c4.metric("Cuentas Challenge", len(df[df["estado"] == "Challenge"]))
    
    st.divider()
    
    # Detalle de cada cuenta
    st.subheader("📋 Detalle por Cuenta")
    
    for _, fila in df.iterrows():
        estado_label = "🟢 Fondeada" if fila['estado'] == "Fondeada" else "🔵 Challenge"
        with st.expander(f"**{fila['nombre_cuenta']}** [{fila['account_number']}] — {estado_label}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Balance / Equidad", f"${fila['balance']:,.2f}", f"Equidad: ${fila['equidad']:,.2f}")
            
            margen_diario = fila['perdida_diaria_max'] - fila['perdida_diaria_actual']
            col2.metric("Límite Pérdida Diaria", f"${fila['perdida_diaria_max']:,.2f}", f"Margen seguro: ${margen_diario:,.2f}")
            
            if fila["estado"] == "Challenge":
                ganado = fila['balance'] - fila['balance_inicial']
                obj = fila['objetivo_profit']
                progreso = min(max(ganado / obj, 0.0), 1.0) if obj > 0 else 1.0
                col3.metric("Objetivo Profit", f"${obj:,.2f}", f"Ganado: ${ganado:,.2f}")
                st.progress(progreso, text=f"{progreso*100:.1f}% alcanzado")
            else:
                beneficio = fila['balance'] - fila['balance_inicial']
                col3.metric("Acumulado para Payout", f"${beneficio:,.2f}")
            
            st.caption(f"Última actualización: {fila.get('ultima_actualizacion', 'N/A')}")
