import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración visual
st.set_page_config(
    page_title="Mis Cuentas Trading - Dashboard Pro",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .metric-box {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2962FF;
    }
    .stProgress > div > div > div > div {
        background-color: #00E676;
    }
</style>
""", unsafe_allow_html=True)

# Conexión a Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

st.title("📊 Mis Cuentas Trading")
st.caption("Panel de control unificado y registro automatizado de operaciones.")

# Cargar datos de cuentas y operaciones
@st.cache_data(ttl=5)
def cargar_datos():
    res_cuentas = supabase.table("cuentas").select("*").execute()
    res_ops = supabase.table("operaciones").select("*").order("fecha", desc=True).execute()
    return res_cuentas.data, res_ops.data

try:
    cuentas_data, ops_data = cargar_datos()
except Exception as e:
    st.error(f"Error conectando con la base de datos: {e}")
    st.stop()

# --- KPI GLOBALES ---
if cuentas_data:
    df_c = pd.DataFrame(cuentas_data)
    
    tot_inicial = df_c["balance_inicial"].sum()
    tot_actual = df_c["balance"].sum()
    tot_ganado = tot_actual - tot_inicial
    porcentaje_global = (tot_ganado / tot_inicial * 100) if tot_inicial > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Capital Inicial Total", f"${tot_inicial:,.2f}")
    col2.metric("Capital Actual Total", f"${tot_actual:,.2f}", f"{porcentaje_global:+.2f}%")
    col3.metric("Total Ganado / Perdido", f"${tot_ganado:,.2f}", delta_color="normal" if tot_ganado >= 0 else "inverse")
    col4.metric("Cuentas Monitoreadas", len(df_c))

st.divider()

# --- TABLA DE CUENTAS (Estilo Notion Mejorado) ---
st.subheader("📋 Estado de Mis Cuentas")

if not cuentas_data:
    st.info("Esperando datos de MetaTrader 5...")
else:
    filas_cuentas = []
    for c in cuentas_data:
        bal_ini = c["balance_inicial"]
        bal_act = c["balance"]
        ganancia = bal_act - bal_ini
        pct_ganancia = (ganancia / bal_ini * 100) if bal_ini > 0 else 0
        
        # Calcular Alerta de Estado
        if c["estado"] == "Challenge":
            obj = c["objetivo_profit"]
            pct_obj = (ganancia / obj * 100) if obj > 0 else 0
            if c["perdida_diaria_actual"] > (c["perdida_diaria_max"] * 0.7):
                estado_alerta = f"🚨 ALERTA PÉRDIDA: -{(c['perdida_diaria_actual']/c['perdida_diaria_max']*100):.0f}%"
            elif ganancia >= 0:
                estado_alerta = f"📈 GANANCIA: {pct_obj:.0f}% del Obj"
            else:
                estado_alerta = f"📉 PÉRDIDA: {pct_ganancia:.1f}%"
        else:
            if ganancia >= 0:
                estado_alerta = f"💰 PAYOUT ACUMULADO: +${ganancia:,.2f}"
            else:
                estado_alerta = f"📉 PÉRDIDA: {pct_ganancia:.1f}%"
        
        filas_cuentas.append({
            "Nombre": c["nombre_cuenta"],
            "Capital Inicial": f"${bal_ini:,.2f}",
            "Capital Actual": f"${bal_act:,.2f}",
            "Total Ganado ($)": f"${ganancia:,.2f}",
            "Rendimiento (%)": f"{pct_ganancia:+.2f}%",
            "Fase / Estado": c["estado"],
            "Límite Pérdida Diaria Disp.": f"${(c['perdida_diaria_max'] - c['perdida_diaria_actual']):,.2f}",
            "Objetivo Ganancia": f"${c['objetivo_profit']:,.2f}" if c["estado"] == "Challenge" else "N/A",
            "Estado / Alerta": estado_alerta
        })
    
    st.dataframe(pd.DataFrame(filas_cuentas), use_container_width=True)

st.divider()

# --- REGISTRO DE OPERACIONES (Trade Log) ---
st.subheader("📖 Registro Automático de Operaciones")

if not ops_data:
    st.info("No hay trades cerrados registrados aún en el historial.")
else:
    df_ops = pd.DataFrame(ops_data)
    
    # Filtro por cuenta
    cuentas_unicas = ["Todas"] + list(df_ops["nombre_cuenta"].unique())
    filtro_c = st.selectbox("Filtrar operaciones por cuenta:", cuentas_unicas)
    
    if filtro_c != "Todas":
        df_ops = df_ops[df_ops["nombre_cuenta"] == filtro_c]
    
    # Dar formato a la tabla de operaciones
    df_mostrar = pd.DataFrame({
        "Fecha": pd.to_datetime(df_ops["fecha"]).dt.strftime('%Y-%m-%d %H:%M'),
        "Cuenta": df_ops["nombre_cuenta"],
        "Símbolo": df_ops["simbolo"],
        "Tipo": df_ops["tipo"],
        "Resultado ($)": df_ops["resultado"].apply(lambda x: f"${x:,.2f}"),
        "% Sobre Base": df_ops["porcentaje_base"].apply(lambda x: f"{x:+.2f}%"),
        "Win/Loss": df_ops["win_loss"].apply(lambda x: "🟩 WIN" if x=="WIN" else ("🟥 LOSS" if x=="LOSS" else "⚪ BE")),
        "Comentario / Nota MT5": df_ops["comentario"]
    })
    
    st.dataframe(df_mostrar, use_container_width=True)
