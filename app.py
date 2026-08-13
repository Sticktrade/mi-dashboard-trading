import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
import datetime
from supabase import create_client

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN VISUAL (ESTILO TRADELIO / TRADINGVIEW DARK THEME)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tradelio Pro - Analytics de Fondeo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS avanzados
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background-color: #131722;
        color: #E0E3EB;
    }
    
    /* Contenedores y Tarjetas */
    .metric-card {
        background-color: #1E222D;
        border: 1px solid #2A2E39;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .metric-title {
        color: #787B86;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        margin-top: 4px;
    }
    
    .green-text { color: #26A69A; }
    .red-text { color: #EF5350; }
    .blue-text { color: #2962FF; }

    /* Calendario de Trading */
    .cal-container {
        background-color: #1E222D;
        border: 1px solid #2A2E39;
        border-radius: 12px;
        padding: 20px;
    }
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        margin-top: 10px;
    }
    .cal-header-day {
        text-align: center;
        color: #787B86;
        font-weight: 700;
        font-size: 12px;
        padding-bottom: 6px;
    }
    .cal-day-box {
        background-color: #2A2E39;
        border-radius: 8px;
        min-height: 75px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 1px solid #363A45;
    }
    .cal-day-box.empty {
        background-color: transparent;
        border: none;
    }
    .cal-day-box.win {
        background: linear-gradient(135deg, rgba(38, 166, 154, 0.25) 0%, rgba(38, 166, 154, 0.08) 100%);
        border: 1px solid rgba(38, 166, 154, 0.4);
    }
    .cal-day-box.loss {
        background: linear-gradient(135deg, rgba(239, 83, 80, 0.25) 0%, rgba(239, 83, 80, 0.08) 100%);
        border: 1px solid rgba(239, 83, 80, 0.4);
    }
    .cal-day-num {
        font-size: 12px;
        font-weight: 600;
        color: #A3A6AF;
    }
    .cal-day-pnl {
        font-size: 13px;
        font-weight: 700;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONEXIÓN A CONECTOR SUPABASE
# -----------------------------------------------------------------------------
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

@st.cache_data(ttl=3)
def cargar_datos():
    res_cuentas = supabase.table("cuentas").select("*").execute()
    res_ops = supabase.table("operaciones").select("*").order("fecha", desc=True).execute()
    return res_cuentas.data, res_ops.data

cuentas_raw, ops_raw = cargar_datos()

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL / FILTROS
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ Tradelio Analytics")
st.sidebar.caption("Analizador Inteligente de Prop Firms")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### 🔍 Filtros de Cuenta")

lista_cuentas = ["Todas las Cuentas"]
if cuentas_raw:
    lista_cuentas += [c["nombre_cuenta"] for c in cuentas_raw]

cuenta_filtro = st.sidebar.selectbox("Seleccionar Prop Firm / Cuenta:", lista_cuentas)

# Filtrar Datos
cuentas = cuentas_raw if cuenta_filtro == "Todas las Cuentas" else [c for c in cuentas_raw if c["nombre_cuenta"] == cuenta_filtro]

df_ops = pd.DataFrame(ops_raw) if ops_raw else pd.DataFrame()

if not df_ops.empty:
    df_ops['fecha_dt'] = pd.to_datetime(df_ops['fecha'])
    df_ops['fecha_dia'] = df_ops['fecha_dt'].dt.date
    if cuenta_filtro != "Todas las Cuentas":
        df_ops = df_ops[df_ops["nombre_cuenta"] == cuenta_filtro]

# -----------------------------------------------------------------------------
# 4. ENCABEZADO Y KPI CARDS
# -----------------------------------------------------------------------------
st.title("📈 Panel de Control & Analytics")
st.caption(f"Visualización consolidada — {cuenta_filtro}")

# Cálculos Generales
tot_inicial = sum([c["balance_inicial"] for c in cuentas]) if cuentas else 0
tot_actual = sum([c["balance"] for c in cuentas]) if cuentas else 0
tot_ganado = tot_actual - tot_inicial
pct_global = (tot_ganado / tot_inicial * 100) if tot_inicial > 0 else 0

# Métricas de Trading
total_trades = len(df_ops) if not df_ops.empty else 0
wins = len(df_ops[df_ops['win_loss'] == 'WIN']) if not df_ops.empty else 0
losses = len(df_ops[df_ops['win_loss'] == 'LOSS']) if not df_ops.empty else 0
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

gross_profit = df_ops[df_ops['resultado'] > 0]['resultado'].sum() if not df_ops.empty else 0
gross_loss = abs(df_ops[df_ops['resultado'] < 0]['resultado'].sum()) if not df_ops.empty else 0
profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)

avg_win = df_ops[df_ops['resultado'] > 0]['resultado'].mean() if wins > 0 else 0
avg_loss = abs(df_ops[df_ops['resultado'] < 0]['resultado'].mean()) if losses > 0 else 0
risk_reward = (avg_win / avg_loss) if avg_loss > 0 else 0

# Fila de Tarjetas KPI
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    color = "green-text" if tot_ganado >= 0 else "red-text"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Capital Gestionado</div>
        <div class="metric-value">${tot_actual:,.2f}</div>
        <div class="{color}" style="font-size:12px; font-weight:700;">{pct_global:+.2f}% (${tot_ganado:,.2f})</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Win Rate</div>
        <div class="metric-value blue-text">{win_rate:.1f}%</div>
        <div style="color:#787B86; font-size:12px;">{wins}W / {losses}L ({total_trades} trades)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Profit Factor</div>
        <div class="metric-value">{profit_factor:.2f}</div>
        <div style="color:#787B86; font-size:12px;">G: ${gross_profit:,.0f} / P: ${gross_loss:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Ratio R/R Real</div>
        <div class="metric-value">1 : {risk_reward:.2f}</div>
        <div style="color:#787B86; font-size:12px;">Avg W: ${avg_win:,.0f} | Avg L: ${avg_loss:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    cant_cuentas = len(cuentas)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Cuentas Monitoreadas</div>
        <div class="metric-value">{cant_cuentas}</div>
        <div style="color:#787B86; font-size:12px;">Fondeadas y Challenges</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. PESTAÑAS PRINCIPALES DEL DASHBOARD
# -----------------------------------------------------------------------------
tab_analytics, tab_calendar, tab_cuentas, tab_trades = st.tabs([
    "📊 Gráficos & Analytics",
    "📅 Calendario de Resultados",
    "🛡️ Estado de Cuentas",
    "📖 Historial de Operaciones"
])

# =============================================================================
# TAB 1: GRÁFICOS Y ANALYTICS
# =============================================================================
with tab_analytics:
    if df_ops.empty:
        st.info("ℹ️ No hay operaciones registradas aún para generar las gráficas.")
    else:
        # Ordenar cronológicamente para la curva acumulada
        df_ops_sorted = df_ops.sort_values("fecha_dt").copy()
        df_ops_sorted["cum_pnl"] = df_ops_sorted["resultado"].cumsum()
        
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
            # Curva de Equidad
            fig_equity = go.Figure()
            fig_equity.add_trace(go.Scatter(
                x=df_ops_sorted["fecha_dt"],
                y=df_ops_sorted["cum_pnl"],
                mode='lines',
                name='PnL Acumulado',
                line=dict(color='#2962FF', width=3),
                fill='tozeroy',
                fillcolor='rgba(41, 98, 255, 0.12)'
            ))
            fig_equity.update_layout(
                title='<b>Evolución de la Curva de Equidad ($)</b>',
                paper_bgcolor='#1E222D',
                plot_bgcolor='#1E222D',
                font=dict(color='#E0E3EB'),
                xaxis=dict(gridcolor='#2A2E39', showgrid=True),
                yaxis=dict(gridcolor='#2A2E39', showgrid=True),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380
            )
            st.plotly_chart(fig_equity, use_container_width=True)
            
        with col_g2:
            # Gráfico Donut Win/Loss/BE
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses', 'BE'],
                values=[wins, losses, total_trades - (wins + losses)],
                hole=.6,
                marker=dict(colors=['#26A69A', '#EF5350', '#787B86'])
            )])
            fig_donut.update_layout(
                title='<b>Distribución Win / Loss</b>',
                paper_bgcolor='#1E222D',
                font=dict(color='#E0E3EB'),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380,
                showlegend=True
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
        # Gráfico PnL Diario
        daily_pnl = df_ops.groupby('fecha_dia')['resultado'].sum().reset_index()
        daily_pnl['color'] = daily_pnl['resultado'].apply(lambda x: '#26A69A' if x >= 0 else '#EF5350')
        
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily_pnl['fecha_dia'],
            y=daily_pnl['resultado'],
            marker_color=daily_pnl['color'],
            name='PnL Diario'
        ))
        fig_daily.update_layout(
            title='<b>Rendimiento Diario Net ($)</b>',
            paper_bgcolor='#1E222D',
            plot_bgcolor='#1E222D',
            font=dict(color='#E0E3EB'),
            xaxis=dict(gridcolor='#2A2E39', showgrid=True),
            yaxis=dict(gridcolor='#2A2E39', showgrid=True),
            margin=dict(l=20, r=20, t=40, b=20),
            height=320
        )
        st.plotly_chart(fig_daily, use_container_width=True)

# =============================================================================
# TAB 2: CALENDARIO TRADELIO (VISUAL TRADING CALENDAR)
# =============================================================================
with tab_calendar:
    st.subheader("📅 Calendario Mensual de Resultados")
    
    # Selectores de Mes y Año
    now = datetime.datetime.now()
    c_m, c_y = st.columns([1, 1])
    with c_m:
        mes_sel = st.selectbox("Mes:", range(1, 13), index=now.month - 1, format_func=lambda x: calendar.month_name[x])
    with c_y:
        ano_sel = st.number_input("Año:", min_value=2024, max_value=2030, value=now.year)
        
    # Agrupar PnL por día de fecha
    pnl_diario_map = {}
    if not df_ops.empty:
        df_mes = df_ops[(df_ops['fecha_dt'].dt.month == mes_sel) & (df_ops['fecha_dt'].dt.year == ano_sel)]
        if not df_mes.empty:
            pnl_diario_map = df_mes.groupby('fecha_dia')['resultado'].sum().to_dict()

    # Construir HTML del Calendario
    cal = calendar.monthcalendar(int(ano_sel), int(mes_sel))
    
    html_cal = f"""
    <div class="cal-container">
        <div style="text-align:center; font-weight:700; font-size:18px; margin-bottom:15px; color:#E0E3EB;">
            {calendar.month_name[mes_sel]} {ano_sel}
        </div>
        <div class="cal-grid">
            <div class="cal-header-day">LUN</div>
            <div class="cal-header-day">MAR</div>
            <div class="cal-header-day">MIÉ</div>
            <div class="cal-header-day">JUE</div>
            <div class="cal-header-day">VIE</div>
            <div class="cal-header-day">SÁB</div>
            <div class="cal-header-day">DOM</div>
    """
    
    dias_ganadores = 0
    dias_perdedores = 0
    total_pnl_mes = 0.0

    for week in cal:
        for day in week:
            if day == 0:
                html_cal += '<div class="cal-day-box empty"></div>'
            else:
                fecha_obj = datetime.date(int(ano_sel), int(mes_sel), day)
                pnl = pnl_diario_map.get(fecha_obj, None)
                
                box_class = "cal-day-box"
                pnl_str = ""
                pnl_style = "color:#787B86;"
                
                if pnl is not None:
                    total_pnl_mes += pnl
                    if pnl > 0.01:
                        box_class += " win"
                        pnl_str = f"+${pnl:,.2f}"
                        pnl_style = "color:#26A69A;"
                        dias_ganadores += 1
                    elif pnl < -0.01:
                        box_class += " loss"
                        pnl_str = f"-${abs(pnl):,.2f}"
                        pnl_style = "color:#EF5350;"
                        dias_perdedores += 1
                    else:
                        pnl_str = "$0.00"
                
                html_cal += f"""
                <div class="{box_class}">
                    <div class="cal-day-num">{day}</div>
                    <div class="cal-day-pnl" style="{pnl_style}">{pnl_str}</div>
                </div>
                """
                
    html_cal += "</div></div>"
    
    st.markdown(html_cal, unsafe_allow_html=True)
    
    # Resumen del mes
    st.markdown("<br>", unsafe_allow_html=True)
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("PnL Total del Mes", f"${total_pnl_mes:,.2f}")
    mc2.metric("Días Verdes (Win)", f"{dias_ganadores} días")
    mc3.metric("Días Rojos (Loss)", f"{dias_perdedores} días")

# =============================================================================
# TAB 3: ESTADO DE CUENTAS & REGLAS DE PROP FIRMS
# =============================================================================
with tab_cuentas:
    st.subheader("🛡️ Monitoreo de Reglas y Drawdown por Cuenta")
    
    if not cuentas:
        st.info("No hay cuentas para mostrar.")
    else:
        for c in cuentas:
            bal_ini = c["balance_inicial"]
            bal_act = c["balance"]
            equidad = c["equidad"]
            ganancia = bal_act - bal_ini
            
            p_diaria_max = c["perdida_diaria_max"]
            p_diaria_act = c["perdida_diaria_actual"]
            margen_diario = p_diaria_max - p_diaria_act
            
            with st.expander(f"🔹 **{c['nombre_cuenta']}** — [{c['estado']}]", expanded=True):
                col_c1, col_c2, col_c3 = st.columns(3)
                
                col_c1.metric("Balance / Equidad", f"${bal_act:,.2f}", f"Equidad: ${equidad:,.2f}")
                col_c2.metric("Margen Pérdida Diaria", f"${margen_diario:,.2f}", f"Límite Máx: ${p_diaria_max:,.2f}")
                
                if c["estado"] != "Fondeada":
                    obj = c["objetivo_profit"]
                    pct_prog = min(max(ganancia / obj, 0.0), 1.0) if obj > 0 else 1.0
                    col_c3.metric("Objetivo Profit Target", f"${obj:,.2f}", f"Ganado: ${ganancia:,.2f}")
                    
                    st.write("**Progreso hacia el Pase de Fase:**")
                    st.progress(pct_prog, text=f"{pct_prog*100:.1f}% alcanzado (${ganancia:,.2f} / ${obj:,.2f})")
                else:
                    col_c3.metric("Beneficio Acumulado (Payout)", f"${ganancia:,.2f}")
                    st.caption("🟢 Cuenta Fondeada activa en fase de retiro de ganancias.")
                
                # Barra de riesgo de pérdida diaria
                pct_drawdown = min(max(p_diaria_act / p_diaria_max, 0.0), 1.0) if p_diaria_max > 0 else 0
                st.write("**Uso del Pérdida Diaria Máxima del Día:**")
                st.progress(pct_drawdown, text=f"{pct_drawdown*100:.1f}% consumido (${p_diaria_act:,.2f} / ${p_diaria_max:,.2f})")

# =============================================================================
# TAB 4: HISTORIAL DE OPERACIONES (TRADE LOG)
# =============================================================================
with tab_trades:
    st.subheader("📖 Registro de Operaciones (Trade Log)")
    
    if df_ops.empty:
        st.info("No hay registro de operaciones aún.")
    else:
        df_view = pd.DataFrame({
            "Fecha": pd.to_datetime(df_ops["fecha"]).dt.strftime('%Y-%m-%d %H:%M'),
            "Cuenta": df_ops["nombre_cuenta"],
            "Símbolo": df_ops["simbolo"],
            "Tipo": df_ops["tipo"],
            "Resultado ($)": df_ops["resultado"].apply(lambda x: f"${x:,.2f}"),
            "% Rendimiento": df_ops["porcentaje_base"].apply(lambda x: f"{x:+.2f}%"),
            "Estado": df_ops["win_loss"].apply(lambda x: "🟩 WIN" if x=="WIN" else ("cd 🟥 LOSS" if x=="LOSS" else "⚪ BE")),
            "Comentario MT5": df_ops["comentario"]
        })
        
        st.dataframe(df_view, use_container_width=True, height=450)
