import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
import datetime
from supabase import create_client

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN VISUAL (STICKTRADE PLATFORM)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="StickTrade Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS avanzados
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background-color: #12151C;
        color: #E0E3EB;
    }
    
    /* Estilo de los Checkboxes de Selección de Cuentas */
    div[data-baseweb="checkbox"] {
        margin-bottom: 8px;
        padding: 4px 8px;
        border-radius: 6px;
        transition: background-color 0.2s;
    }
    div[data-baseweb="checkbox"]:hover {
        background-color: #1A1E29;
    }
    
    /* Cuadro de Check cuando está activo (Azul TradingView #2962FF) */
    div[data-baseweb="checkbox"] input:checked + div {
        background-color: #2962FF !important;
        border-color: #2962FF !important;
    }
    
    div[data-baseweb="checkbox"] span {
        color: #E0E3EB !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    
    /* Tarjetas KPI */
    .metric-card {
        background-color: #1A1E29;
        border: 1px solid #282D3C;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .metric-title {
        color: #787B86;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        margin-top: 4px;
    }
    
    .green-text { color: #26A69A; }
    .red-text { color: #EF5350; }
    .blue-text { color: #2962FF; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONEXIÓN A SUPABASE
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
# 3. BARRA LATERAL / LISTA DE CHECKBOXES
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ StickTrade Platform")
st.sidebar.caption("Analytics de Cuentas de Fondeo")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### 🔍 Selección de Cuentas")

nombres_cuentas_disponibles = sorted(list(set([c["nombre_cuenta"] for c in cuentas_raw]))) if cuentas_raw else []

# Botones rápidos para Seleccionar/Deseleccionar todas
col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("Todas", use_container_width=True):
    for c in nombres_cuentas_disponibles:
        st.session_state[f"chk_{c}"] = True
    st.rerun()

if col_b2.button("Ninguna", use_container_width=True):
    for c in nombres_cuentas_disponibles:
        st.session_state[f"chk_{c}"] = False
    st.rerun()

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Lista de Checkboxes
cuentas_seleccionadas = []
if nombres_cuentas_disponibles:
    for c_nombre in nombres_cuentas_disponibles:
        if f"chk_{c_nombre}" not in st.session_state:
            st.session_state[f"chk_{c_nombre}"] = True
            
        checked = st.sidebar.checkbox(
            c_nombre, 
            value=st.session_state[f"chk_{c_nombre}"], 
            key=f"chk_{c_nombre}"
        )
        if checked:
            cuentas_seleccionadas.append(c_nombre)
else:
    st.sidebar.info("Cargando cuentas...")

# Filtrar Cuentas y Operaciones
if cuentas_seleccionadas:
    cuentas = [c for c in cuentas_raw if c["nombre_cuenta"] in cuentas_seleccionadas]
else:
    cuentas = []

df_ops = pd.DataFrame(ops_raw) if ops_raw else pd.DataFrame()

if not df_ops.empty:
    df_ops['fecha_dt'] = pd.to_datetime(df_ops['fecha'])
    df_ops['fecha_dia'] = df_ops['fecha_dt'].dt.date
    if cuentas_seleccionadas:
        df_ops = df_ops[df_ops["nombre_cuenta"].isin(cuentas_seleccionadas)]
    else:
        df_ops = pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. ENCABEZADO Y KPI CARDS
# -----------------------------------------------------------------------------
st.title("📈 StickTrade Platform — Dashboard")
st.caption("Visión consolidada y métricas de rendimiento en tiempo real.")

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
        <div style="color:#787B86; font-size:12px;">G: ${gross_profit:,.0f} | P: ${gross_loss:,.0f}</div>
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
        <div class="metric-title">Cuentas Seleccionadas</div>
        <div class="metric-value">{cant_cuentas}</div>
        <div style="color:#787B86; font-size:12px;">Fondeadas & Challenges</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. PESTAÑAS PRINCIPALES DEL DASHBOARD
# -----------------------------------------------------------------------------
tab_calendar, tab_analytics, tab_cuentas, tab_trades = st.tabs([
    "📅 Calendario de Resultados",
    "📊 Gráficos & Analytics",
    "🛡️ Estado de Cuentas",
    "📖 Historial de Operaciones"
])

# =============================================================================
# TAB 1: CALENDARIO VISUAL
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
        
    # Agrupar PnL por día
    daily_stats = {}
    if not df_ops.empty:
        df_mes = df_ops[(df_ops['fecha_dt'].dt.month == mes_sel) & (df_ops['fecha_dt'].dt.year == ano_sel)]
        if not df_mes.empty:
            for f_dia, group in df_mes.groupby('fecha_dia'):
                pnl = group['resultado'].sum()
                tr_cnt = len(group)
                w_cnt = len(group[group['win_loss'] == 'WIN'])
                wr_val = (w_cnt / tr_cnt * 100) if tr_cnt > 0 else 0
                daily_stats[f_dia] = {
                    'pnl': pnl,
                    'trades': tr_cnt,
                    'win_rate': wr_val
                }

    # Construcción del Calendario HTML limpio
    cal_obj = calendar.Calendar(firstweekday=6) # Inicio en Domingo
    month_weeks = cal_obj.monthdayscalendar(int(ano_sel), int(mes_sel))
    
    css_cal = """
    <style>
        body { margin:0; padding:0; background-color:#12151C; color:#E0E3EB; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .tradelio-cal-container { background-color: #12151C; border: 1px solid #222631; border-radius: 12px; padding: 10px; }
        .tradelio-grid { display: grid; grid-template-columns: 130px repeat(7, 1fr); gap: 8px; }
        .tradelio-header { text-align: center; font-weight: 700; font-size: 11px; color: #787B86; text-transform: uppercase; padding-bottom: 4px; }
        .week-summary-card { background-color: #1A1E29; border: 1px solid #282D3C; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; justify-content: center; min-height: 85px; box-sizing: border-box; }
        .week-title { font-size: 11px; color: #A3A6AF; font-weight: 600; }
        .week-pct { font-size: 11px; font-weight: 700; margin-left: 4px; }
        .week-pct.green { color: #26A69A; }
        .week-pct.red { color: #EF5350; }
        .week-pct.neutral { color: #787B86; }
        .week-val { font-size: 17px; font-weight: 800; margin-top: 4px; color: #FFFFFF; }
        .day-box { background-color: #1A1E29; border: 1px solid #282D3C; border-radius: 8px; padding: 8px; min-height: 85px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; }
        .day-box.empty-day { background-color: #141722; border: 1px solid #1E222E; }
        .day-box.win-day { background: linear-gradient(180deg, rgba(38, 166, 154, 0.3) 0%, rgba(38, 166, 154, 0.08) 100%); border: 1px solid rgba(38, 166, 154, 0.5); }
        .day-box.loss-day { background: linear-gradient(180deg, rgba(239, 83, 80, 0.3) 0%, rgba(239, 83, 80, 0.08) 100%); border: 1px solid rgba(239, 83, 80, 0.5); }
        .day-num { font-size: 11px; font-weight: 700; color: #D1D4DC; text-align: right; }
        .day-content { text-align: right; }
        .day-pnl { font-size: 13px; font-weight: 800; color: #FFFFFF; }
        .day-meta { font-size: 9px; color: #A3A6AF; margin-top: 2px; }
        .green-meta { color: #26A69A; font-weight: 700; }
        .red-meta { color: #EF5350; font-weight: 700; }
    </style>
    """
    
    html_grid = f"{css_cal}<div class='tradelio-cal-container'><div class='tradelio-grid'>"
    html_grid += "<div class='tradelio-header'>SEMANA</div><div class='tradelio-header'>DOM</div><div class='tradelio-header'>LUN</div><div class='tradelio-header'>MAR</div><div class='tradelio-header'>MIÉ</div><div class='tradelio-header'>JUE</div><div class='tradelio-header'>VIE</div><div class='tradelio-header'>SÁB</div>"
    
    dias_ganadores = 0
    dias_perdedores = 0
    total_pnl_mes = 0.0

    for w_idx, week in enumerate(month_weeks, start=1):
        week_pnl = 0.0
        for day in week:
            if day != 0:
                fecha_obj = datetime.date(int(ano_sel), int(mes_sel), day)
                if fecha_obj in daily_stats:
                    week_pnl += daily_stats[fecha_obj]['pnl']
                    
        total_pnl_mes += week_pnl
        week_pct = (week_pnl / tot_inicial * 100) if tot_inicial > 0 else 0
        pct_cls = "green" if week_pnl > 0 else ("red" if week_pnl < 0 else "neutral")
        
        # Tarjeta Semanal
        html_grid += f"<div class='week-summary-card'><div><span class='week-title'>Week {w_idx}</span><span class='week-pct {pct_cls}'>{week_pct:+.2f}%</span></div><div class='week-val'>${week_pnl:,.2f}</div></div>"
        
        # Tarjetas Diarias
        for day in week:
            if day == 0:
                html_grid += "<div class='day-box empty-day'></div>"
            else:
                fecha_obj = datetime.date(int(ano_sel), int(mes_sel), day)
                if fecha_obj in daily_stats:
                    st_day = daily_stats[fecha_obj]
                    pnl = st_day['pnl']
                    tr = st_day['trades']
                    wr = st_day['win_rate']
                    
                    if pnl > 0.01:
                        box_cls = "win-day"
                        pnl_fmt = f"${pnl:,.2f}" if abs(pnl) < 1000 else f"${pnl/1000:.2f}K"
                        meta_str = f"{tr} ops | <span class='green-meta'>{wr:.0f}%</span>"
                        dias_ganadores += 1
                    elif pnl < -0.01:
                        box_cls = "loss-day"
                        pnl_fmt = f"-${abs(pnl):,.2f}" if abs(pnl) < 1000 else f"-${abs(pnl)/1000:.2f}K"
                        meta_str = f"{tr} ops | <span class='red-meta'>{wr:.0f}%</span>"
                        dias_perdedores += 1
                    else:
                        box_cls = ""
                        pnl_fmt = "$0.00"
                        meta_str = f"{tr} ops"
                        
                    html_grid += f"<div class='day-box {box_cls}'><div class='day-num'>{day}</div><div class='day-content'><div class='day-pnl'>{pnl_fmt}</div><div class='day-meta'>{meta_str}</div></div></div>"
                else:
                    html_grid += f"<div class='day-box'><div class='day-num'>{day}</div></div>"
                    
    html_grid += "</div></div>"
    
    # Renderizado seguro en iFrame HTML
    components.html(html_grid, height=620, scrolling=True)
    
    # Métricas del mes
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("PnL Total del Mes", f"${total_pnl_mes:,.2f}")
    mc2.metric("Días Verdes (Win)", f"{dias_ganadores} días")
    mc3.metric("Días Rojos (Loss)", f"{dias_perdedores} días")

# =============================================================================
# TAB 2: GRÁFICOS Y ANALYTICS
# =============================================================================
with tab_analytics:
    if df_ops.empty:
        st.info("ℹ️ No hay operaciones registradas para generar las gráficas.")
    else:
        df_ops_sorted = df_ops.sort_values("fecha_dt").copy()
        df_ops_sorted["cum_pnl"] = df_ops_sorted["resultado"].cumsum()
        
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
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
                paper_bgcolor='#1A1E29',
                plot_bgcolor='#1A1E29',
                font=dict(color='#E0E3EB'),
                xaxis=dict(gridcolor='#282D3C', showgrid=True),
                yaxis=dict(gridcolor='#282D3C', showgrid=True),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380
            )
            st.plotly_chart(fig_equity, use_container_width=True)
            
        with col_g2:
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses', 'BE'],
                values=[wins, losses, total_trades - (wins + losses)],
                hole=.6,
                marker=dict(colors=['#26A69A', '#EF5350', '#787B86'])
            )])
            fig_donut.update_layout(
                title='<b>Distribución Win / Loss</b>',
                paper_bgcolor='#1A1E29',
                font=dict(color='#E0E3EB'),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380,
                showlegend=True
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
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
            paper_bgcolor='#1A1E29',
            plot_bgcolor='#1A1E29',
            font=dict(color='#E0E3EB'),
            xaxis=dict(gridcolor='#282D3C', showgrid=True),
            yaxis=dict(gridcolor='#282D3C', showgrid=True),
            margin=dict(l=20, r=20, t=40, b=20),
            height=320
        )
        st.plotly_chart(fig_daily, use_container_width=True)

# =============================================================================
# TAB 3: ESTADO DE CUENTAS
# =============================================================================
with tab_cuentas:
    st.subheader("🛡️ Monitoreo de Reglas y Drawdown por Cuenta")
    
    if not cuentas:
        st.info("No hay cuentas seleccionadas.")
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
                    st.caption("🟢 Cuenta Fondeada activa.")
                
                pct_drawdown = min(max(p_diaria_act / p_diaria_max, 0.0), 1.0) if p_diaria_max > 0 else 0
                st.write("**Uso del Límite de Pérdida Diaria:**")
                st.progress(pct_drawdown, text=f"{pct_drawdown*100:.1f}% consumido (${p_diaria_act:,.2f} / ${p_diaria_max:,.2f})")

# =============================================================================
# TAB 4: HISTORIAL DE OPERACIONES
# =============================================================================
with tab_trades:
    st.subheader("📖 Registro de Operaciones (Trade Log)")
    
    if df_ops.empty:
        st.info("No hay operaciones para la selección actual.")
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
