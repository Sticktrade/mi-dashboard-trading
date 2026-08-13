import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(
    page_title="Panel de Control - Prop Firms",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Mi Dashboard de Cuentas de Fondeo")

# Verificar credenciales
if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
    st.error("⚠️ Faltan las claves en los Secrets de Streamlit. Revisa la configuración.")
    st.stop()

# Conectar
try:
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"❌ Error al iniciar el cliente de Supabase: {e}")
    st.stop()

# Consultar datos con captura de error detallada
try:
    res = supabase.table("cuentas").select("*").execute()
    datos = res.data
    st.success("✅ ¡Conexión con Supabase establecida correctamente!")
except Exception as e:
    st.error(f"❌ Error al consultar la tabla 'cuentas': {e}")
    st.info("Revisa que en los Secrets la URL empiece por 'https://' y que la clave sea la 'anon / public'.")
    st.stop()

# --- SI HAY DATOS O ESTÁ VACÍA ---
if not datos:
    st.info("ℹ️ La base de datos está conectada pero vacía. En cuanto ejecutemos el conector en MetaTrader 5, aparecerán aquí tus cuentas.")
else:
    st.write(pd.DataFrame(datos))
