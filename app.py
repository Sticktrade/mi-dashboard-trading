import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar
import datetime
import json
import base64
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
    :root {
        --primary-color: #2962FF !important;
    }

    /* Fondo principal de la app */
    .stApp {
        background-color: #12151C;
        color: #E0E3EB;
    }
    
    /* Pestañas (Tabs) */
    button[data-baseweb="tab"] {
        color: #787B86 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2962FF !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #2962FF !important;
    }
    div[data-baseweb="tab-border"] {
        background-color: #282D3C !important;
    }
    
    /* Checkboxes */
    div[data-baseweb="checkbox"] {
        margin-bottom: 4px;
        padding: 2px 4px;
        border-radius: 6px;
        transition: background-color 0.2s;
    }
    div[data-baseweb="checkbox"]:hover {
        background-color: #1A1E29;
    }
    div[data-baseweb="checkbox"] input:checked + div,
    div[role="checkbox"][aria-checked="true"] {
        background-color: #2962FF !important;
        border-color: #2962FF !important;
    }
    div[data-baseweb="checkbox"] svg {
        fill: #FFFFFF !important;
    }
    div[data-baseweb="checkbox"] span {
        color: #E0E3EB !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    
    /* Estilos del desplegable de subcuentas en la barra lateral */
    .stSidebar div[data-testid="stExpander"] {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        margin-top: -6px !important;
        margin-bottom: 8px !important;
    }
    .stSidebar div[data-testid="stExpander"] details {
        border: none !important;
        background-color: transparent !important;
    }
    .stSidebar div[data-testid="stExpander"] summary {
        background-color: transparent !important;
        border: none !important;
        padding: 2px 6px !important;
        color: #787B86 !important;
        font-size: 12px !important;
    }
    .stSidebar div[data-testid="stExpander"] summary:hover {
        color: #2962FF !important;
    }
    .stSidebar div[data-testid="stExpander"] div[data-testid="stStyleContainer"],
    .stSidebar div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
        padding-left: 14px !important;
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 8px !important;
        border: 1px solid #282D3C !important;
        background-color: #1A1E29 !important;
        color: #E0E3EB !important;
    }
    .stButton > button:hover {
        border-color: #2962FF !important;
        color: #2962FF !important;
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

    /* Tarjeta de Capturas */
    .screenshot-card {
        background-color: #1A1E29;
        border: 1px solid #282D3C;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .screenshot-card:hover {
        border-color: #2962FF;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONEXIÓN A SUPABASE Y FUNCIONES AUXILIARES
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

def parse_capturas(capturas_data):
    if not capturas_data:
        return []
    if isinstance(capturas_data, str):
        try:
            return json.loads(capturas_data)
        except:
            return []
    elif isinstance(capturas_data, list):
        return capturas_data
    return []

def file_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        b64 = base64.b64encode(bytes_data).decode('utf-8')
        mime = uploaded_file.type if uploaded_file.type else 'image/png'
        return f"data:{mime};base64,{b64}"
    return None

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL / AGRUPACIÓN INTELIGENTE DE CUENTAS
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ StickTrade Platform")
st.sidebar.caption("Analytics de Cuentas de Fondeo")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### 🔍 Selección de Cuentas")

grupos_cuentas = {}
if cuentas_raw:
    for c in cuentas_raw:
        nombre = c["nombre_cuenta"]
        if nombre not in grupos_cuentas:
            grupos_cuentas[nombre] = []
        grupos_cuentas[nombre].append(c)

col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("Todas", use_container_width=True):
    if cuentas_raw:
        for c in cuentas_raw:
            st.session_state[f"chk_{c['account_number']}"] = True
        for grp_n in grupos_cuentas.keys():
            st.session_state[f"master_{grp_n}"] = True
        st.rerun()

if col_b2.button("Ninguna", use_container_width=True):
    if cuentas_raw:
        for c in cuentas_raw:
            st.session_state[f"chk_{c['account_number']}"] = False
        for grp_n in grupos_cuentas.keys():
            st.session_state[f"master_{grp_n}"] = False
        st.rerun()

st.sidebar.markdown("<br>", unsafe_allow_html=True)

cuentas_seleccionadas_ids = []

if cuentas_raw:
    for nombre_grp, lista_accs in grupos_cuentas.items():
        if len(lista_accs) == 1:
            acc = lista_accs[0]
            acc_id = str(acc["account_number"])
            key = f"chk_{acc_id}"
            if key not in st.session_state:
                st.session_state[key] = True
                
            label = f"{acc['nombre_cuenta']} — ${acc['balance']:,.2f}"
            if st.sidebar.checkbox(label, value=st.session_state[key], key=key):
                cuentas_seleccionadas_ids.append(acc_id)
        else:
            child_ids = [str(a["account_number"]) for a in lista_accs]
            tot_bal_grp = sum([a["balance"] for a in lista_accs])
            master_key = f"master_{nombre_grp}"
            
            for cid in child_ids:
                if f"chk_{cid}" not in st.session_state:
                    st.session_state[f"chk_{cid}"] = True
            
            if master_key not in st.session_state:
                st.session_state[master_key] = all(st.session_state.get(f"chk_{cid}", True) for cid in child_ids)

            def make_callbacks(grp_k=master_key, c_ids=child_ids):
                def on_m_change():
                    m_val = st.session_state[grp_k]
                    for cid in c_ids:
                        st.session_state[f"chk_{cid}"] = m_val
                def on_c_change():
                    st.session_state[grp_k] = all(st.session_state.get(f"chk_{cid}", True) for cid in c_ids)
                return on_m_change, on_c_change

            cb_master, cb_child = make_callbacks()

            master_label = f"{nombre_grp} ({len(lista_accs)} ctas) — ${tot_bal_grp:,.2f}"
            st.sidebar.checkbox(
                master_label, 
                value=st.session_state[master_key], 
                key=master_key, 
                on_change=cb_master
            )
            
            with st.sidebar.expander(f"🔍 Ver {len(lista_accs)} sub-cuentas", expanded=True):
                for acc in lista_accs:
                    acc_id = str(acc["account_number"])
                    cid_key = f"chk_{acc_id}"
                    
                    child_label = f"#{acc_id} — ${acc['balance']:,.2f} [{acc['estado']}]"
                    if st.checkbox(
                        child_label, 
                        value=st.session_state[cid_key], 
                        key=cid_key, 
                        on_change=cb_child
                    ):
                        cuentas_seleccionadas_ids.append(acc_id)

else:
    st.sidebar.info("Cargando cuentas...")

if cuentas_seleccionadas_ids:
    cuentas = [c for c in cuentas_raw if str(c["account_number"]) in cuentas_seleccionadas_ids]
else:
    cuentas = []

df_ops = pd.DataFrame(ops_raw) if ops_raw else pd.DataFrame()

if not df_ops.empty:
    df_ops['fecha_dt'] = pd.to_datetime(df_ops['fecha'])
    df_ops['fecha_dia'] = df_ops['fecha_dt'].dt.date
    if cuentas_seleccionadas_ids:
        df_ops = df_ops[df_ops["account_number"].astype(str).isin(cuentas_seleccionadas_ids)]
    else:
        df_ops = pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. ENCABEZADO Y KPI CARDS
# -----------------------------------------------------------------------------
st.title("📈 StickTrade Platform — Dashboard")
st.caption("Visión consolidada y métricas de rendimiento en tiempo real.")

tot_inicial = sum([c["balance_inicial"] for c in cuentas]) if cuentas else 0
tot_actual = sum([c["balance"] for c in cuentas]) if cuentas else 0
tot_ganado = tot_actual - tot_inicial
pct_global = (tot_ganado / tot_inicial * 100) if tot_inicial > 0 else 0

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
    
    now = datetime.datetime.now()
    c_m, c_y = st.columns([1, 1])
    with c_m:
        mes_sel = st.selectbox("Mes:", range(1, 13), index=now.month - 1, format_func=lambda x: calendar.month_name[x])
    with c_y:
        ano_sel = st.number_input("Año:", min_value=2024, max_value=2030, value=now.year)
        
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

    cal_obj = calendar.Calendar(firstweekday=6)
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
        
        html_grid += f"<div class='week-summary-card'><div><span class='week-title'>Week {w_idx}</span><span class='week-pct {pct_cls}'>{week_pct:+.2f}%</span></div><div class='week-val'>${week_pnl:,.2f}</div></div>"
        
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
    
    components.html(html_grid, height=620, scrolling=True)
    
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
            pct_ganancia = (ganancia / bal_ini * 100) if bal_ini > 0 else 0
            
            p_diaria_max = c["perdida_diaria_max"]
            p_diaria_act = c["perdida_diaria_actual"]
            margen_diario = p_diaria_max - p_diaria_act
            
            with st.expander(f"🔹 **{c['nombre_cuenta']}** [{c['account_number']}] — [{c['estado']}]", expanded=True):
                col_c1, col_c2, col_c3 = st.columns(3)
                
                # Metric 1: Balance Actual
                delta_bal = f"{ganancia:+,.2f} ({pct_ganancia:+.2f}%)" if ganancia != 0 else "$0.00"
                col_c1.metric(
                    "Balance Actual", 
                    f"${bal_act:,.2f}", 
                    delta=delta_bal
                )
                col_c1.caption(f"Equidad actual: ${equidad:,.2f}")
                
                # Metric 2: Margen Pérdida Diaria
                delta_loss = f"-${p_diaria_act:,.2f}" if p_diaria_act > 0 else "Sin pérdidas hoy"
                col_c2.metric(
                    "Margen Pérdida Diaria", 
                    f"${margen_diario:,.2f}", 
                    delta=delta_loss,
                    delta_color="normal" if p_diaria_act > 0 else "off"
                )
                col_c2.caption(f"Límite máximo diario: ${p_diaria_max:,.2f}")
                
                # Metric 3: Objetivo Profit Target o Payout
                if c["estado"] != "Fondeada":
                    obj = c["objetivo_profit"]
                    pct_prog = min(max(ganancia / obj, 0.0), 1.0) if obj > 0 else 1.0
                    delta_obj = f"{ganancia:+,.2f} de {obj:,.2f}"
                    
                    col_c3.metric(
                        "Objetivo Profit Target", 
                        f"${obj:,.2f}", 
                        delta=delta_obj
                    )
                else:
                    delta_payout = f"{ganancia:+,.2f}" if ganancia != 0 else "$0.00"
                    col_c3.metric(
                        "Beneficio Acumulado (Payout)", 
                        f"${ganancia:,.2f}", 
                        delta=delta_payout
                    )
                
                # Formateo con etiquetas de color Streamlit :red[...] y :green[...]
                if ganancia < 0:
                    str_ganancia = f":red[-\\${abs(ganancia):,.2f}]"
                elif ganancia > 0:
                    str_ganancia = f":green[+\\${ganancia:,.2f}]"
                else:
                    str_ganancia = "\\$0.00"
                    
                str_obj = f"\\${c.get('objetivo_profit', 0):,.2f}"
                
                # Progreso hacia el Objetivo
                if c["estado"] != "Fondeada":
                    obj = c["objetivo_profit"]
                    st.write("**Progreso hacia el Objetivo (Phase Pass):**")
                    txt_p = f"{pct_prog*100:.1f}% alcanzado ({str_ganancia} / {str_obj})"
                    st.progress(
                        pct_prog, 
                        text=txt_p
                    )
                else:
                    st.caption("🟢 Cuenta Fondeada activa.")
                
                # Uso del Límite de Pérdida Diaria
                if p_diaria_act > 0:
                    str_p_act = f":red[-\\${p_diaria_act:,.2f}]"
                else:
                    str_p_act = f":green[\\$0.00]"
                    
                str_p_max = f"\\${p_diaria_max:,.2f}"
                
                pct_drawdown = min(max(p_diaria_act / p_diaria_max, 0.0), 1.0) if p_diaria_max > 0 else 0
                st.write("**Límite de Pérdida Diaria Consumido Hoy:**")
                txt_d = f"{pct_drawdown*100:.1f}% consumido ({str_p_act} / {str_p_max})"
                st.progress(
                    pct_drawdown, 
                    text=txt_d
                )

# =============================================================================
# TAB 4: HISTORIAL DE OPERACIONES DIARIAS & CAPTURAS ESTILO NOTION
# =============================================================================
with tab_trades:
    st.subheader("📖 Historial, Analítica & Capturas de Operaciones")
    st.caption("Monitorea sesiones diarias y adjunta capturas gráficas (con soporte Ctrl+V o subidor) para cada trade.")
    
    if df_ops.empty:
        st.info("No hay operaciones para la selección de cuentas actual.")
    else:
        map_bal_inicial = {str(c["account_number"]): float(c["balance_inicial"]) for c in cuentas_raw} if cuentas_raw else {}
        
        df_ops_copy = df_ops.copy()
        df_ops_copy["acc_id_str"] = df_ops_copy["account_number"].astype(str)
        
        df_diario = df_ops_copy.groupby(["fecha_dia", "acc_id_str", "nombre_cuenta"])["resultado"].sum().reset_index()
        
        df_diario["balance_inicial"] = df_diario["acc_id_str"].map(map_bal_inicial)
        df_diario["pct_rendimiento"] = (df_diario["resultado"] / df_diario["balance_inicial"]) * 100.0
        
        def clasificar_resultado(pct):
            if pct > 0.10:
                return "WIN"
            elif pct < -0.10:
                return "LOSS"
            else:
                return "BE"
                
        df_diario["clasificacion"] = df_diario["pct_rendimiento"].apply(clasificar_resultado)
        
        col_f1, col_f2 = st.columns([2, 2])
        
        min_f = df_diario["fecha_dia"].min()
        max_f = df_diario["fecha_dia"].max()
        
        with col_f1:
            rango_fechas = st.date_input(
                "📅 Rango de Fechas:",
                value=(min_f, max_f),
                min_value=min_f,
                max_value=max_f
            )
            
        with col_f2:
            filtro_estados = st.multiselect(
                "🎯 Filtrar Resultado:",
                options=["WIN", "LOSS", "BE"],
                default=["WIN", "LOSS", "BE"]
            )
            
        if isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 2:
            f_start, f_end = rango_fechas[0], rango_fechas[1]
            df_filtered_tab4 = df_diario[(df_diario["fecha_dia"] >= f_start) & (df_diario["fecha_dia"] <= f_end)]
        else:
            df_filtered_tab4 = df_diario.copy()
            
        if filtro_estados:
            df_filtered_tab4 = df_filtered_tab4[df_filtered_tab4["clasificacion"].isin(filtro_estados)]
            
        df_filtered_tab4 = df_filtered_tab4.sort_values("fecha_dia", ascending=False)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if df_filtered_tab4.empty:
            st.info("No hay registros que coincidan con los filtros aplicados.")
        else:
            chart_col1, chart_col2 = st.columns([1, 1])
            
            with chart_col1:
                acc_stats = df_filtered_tab4.groupby(["nombre_cuenta", "clasificacion"]).size().reset_index(name="cantidad")
                acc_totals = acc_stats.groupby("nombre_cuenta")["cantidad"].sum().reset_index(name="total_cuenta")
                acc_stats = pd.merge(acc_stats, acc_totals, on="nombre_cuenta")
                acc_stats["pct_cuenta"] = (acc_stats["cantidad"] / acc_stats["total_cuenta"]) * 100.0
                
                fig_hbar = px.bar(
                    acc_stats,
                    y="nombre_cuenta",
                    x="pct_cuenta",
                    color="clasificacion",
                    orientation='h',
                    title="<b>Distribución Win / Loss / BE por Cuenta (%)</b>",
                    color_discrete_map={'WIN': '#26A69A', 'LOSS': '#EF5350', 'BE': '#787B86'},
                    text=acc_stats['pct_cuenta'].apply(lambda x: f"{x:.0f}%")
                )
                fig_hbar.update_layout(
                    barmode='stack',
                    paper_bgcolor='#1A1E29',
                    plot_bgcolor='#1A1E29',
                    font=dict(color='#E0E3EB'),
                    xaxis=dict(title="% del Total de Días Operados", gridcolor='#282D3C', range=[0, 100]),
                    yaxis=dict(title="", gridcolor='#282D3C'),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=330,
                    showlegend=True
                )
                st.plotly_chart(fig_hbar, use_container_width=True)
                
            with chart_col2:
                tot_counts = df_filtered_tab4["clasificacion"].value_counts().reset_index()
                tot_counts.columns = ["clasificacion", "cantidad"]
                
                color_map = {'WIN': '#26A69A', 'LOSS': '#EF5350', 'BE': '#787B86'}
                tot_counts['color'] = tot_counts['clasificacion'].map(color_map)
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=tot_counts['clasificacion'],
                    values=tot_counts['cantidad'],
                    hole=.5,
                    marker=dict(colors=tot_counts['color']),
                    textinfo='label+percent+value',
                    hovertemplate="%{label}: %{value} días (%{percent})<extra></extra>"
                )])
                fig_pie.update_layout(
                    title="<b>Total Periodo Filtrado (Días & %)</b>",
                    paper_bgcolor='#1A1E29',
                    font=dict(color='#E0E3EB'),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=330,
                    showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
            st.divider()
            
            st.subheader("📋 Detalle de Sesiones Diarias")
            
            df_tab4_view = pd.DataFrame({
                "Fecha": df_filtered_tab4["fecha_dia"].astype(str),
                "Cuenta": df_filtered_tab4["nombre_cuenta"],
                "ID Cuenta": df_filtered_tab4["acc_id_str"],
                "Resultado Final ($)": df_filtered_tab4["resultado"].apply(lambda x: f"${x:,.2f}"),
                "% Rendimiento": df_filtered_tab4["pct_rendimiento"].apply(lambda x: f"{x:+.2f}%"),
                "Estado": df_filtered_tab4["clasificacion"].apply(
                    lambda x: "🟩 WIN" if x == "WIN" else ("ffffff 🟥 LOSS" if x == "LOSS" else "⚪ BE")
                )
            })
            
            df_tab4_view["Estado"] = df_tab4_view["Estado"].str.replace("ffffff ", "")
            st.dataframe(df_tab4_view, use_container_width=True, height=280)
            
            st.divider()

            # -----------------------------------------------------------------
            # SECCIÓN DE CAPTURAS DE PANTALLA ESTILO NOTION
            # -----------------------------------------------------------------
            st.subheader("📸 Galería de Capturas & Análisis de Trades")
            st.caption("Selecciona una operación de la lista para gestionar o subir sus capturas de gráfico (hasta 2 o más capturas por operación).")

            # Mapeo de opciones para el selector de trade
            df_ops_select = df_ops_copy.sort_values("fecha_dt", ascending=False).copy()
            
            def make_op_label(row):
                f_str = row['fecha_dt'].strftime('%Y-%m-%d %H:%M')
                acc_name = row['nombre_cuenta']
                res = row['resultado']
                res_str = f"+${res:,.2f}" if res >= 0 else f"-${abs(res):,.2f}"
                wl = row.get('win_loss', 'N/A')
                return f"[{f_str}] {acc_name} (#{row['account_number']}) — {res_str} ({wl})"

            ops_list = df_ops_select.to_dict('records')
            
            if ops_list:
                op_opciones = {make_op_label(r): r for r in ops_list}
                sel_label = st.selectbox(
                    "🎯 Selecciona una Operación para Ver/Adjuntar Capturas:", 
                    options=list(op_opciones.keys()),
                    key="sb_select_trade_for_screenshots"
                )
                
                selected_op = op_opciones[sel_label]
                op_id = selected_op["id"]
                
                # Cargar capturas actuales de la operación
                raw_capturas = selected_op.get("capturas", [])
                list_capturas = parse_capturas(raw_capturas)
                
                # Encabezado del trade seleccionado
                res_val = selected_op['resultado']
                res_color = "green-text" if res_val >= 0 else "red-text"
                
                st.markdown(f"""
                <div style="background-color: #1A1E29; border: 1px solid #282D3C; border-radius: 10px; padding: 16px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 18px; font-weight: 800; color: #FFFFFF;">Operación #{selected_op.get('account_number')} — {selected_op.get('nombre_cuenta')}</span>
                            <br><span style="color: #787B86; font-size: 13px;">Fecha: {selected_op.get('fecha')} | Estado: {selected_op.get('win_loss')}</span>
                        </div>
                        <div style="text-align: right;">
                            <span class="{res_color}" style="font-size: 22px; font-weight: 800;">{res_val:+,.2f} USD</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- VISUALIZACIÓN DE CAPTURAS EXISTENTES ---
                st.markdown(f"#### 🖼️ Capturas Guardadas ({len(list_capturas)} subidas)")
                
                if list_capturas:
                    cols = st.columns(min(len(list_capturas), 3))
                    for idx, cap in enumerate(list_capturas):
                        col_target = cols[idx % 3]
                        with col_target:
                            st.markdown(f"**Captura {idx + 1}: {cap.get('tipo', 'Gráfico')}**")
                            img_data = cap.get("url") or cap.get("base64")
                            if img_data:
                                st.image(img_data, use_container_width=True)
                                
                                c_b1, c_b2 = st.columns([2, 1])
                                with c_b1:
                                    if st.button(f"🔍 Ver en Grande #{idx+1}", key=f"btn_zoom_{op_id}_{idx}", use_container_width=True):
                                        st.session_state[f"active_zoom_{op_id}"] = cap
                                with c_b2:
                                    if st.button(f"🗑️", key=f"btn_del_{op_id}_{idx}", help="Eliminar captura", use_container_width=True):
                                        list_capturas.pop(idx)
                                        try:
                                            supabase.table("operaciones").update({"capturas": json.dumps(list_capturas)}).eq("id", op_id).execute()
                                            st.success("Captura eliminada.")
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Error al eliminar: {err}")
                else:
                    st.info("Esta operación aún no tiene capturas de pantalla adjuntas.")

                # Modal / Vista Ampliada estilo Notion
                zoom_cap = st.session_state.get(f"active_zoom_{op_id}")
                if zoom_cap:
                    st.markdown("---")
                    st.markdown("### 🔍 Vista Detallada de la Captura (Estilo Notion)")
                    
                    z_col1, z_col2 = st.columns([3, 1])
                    with z_col1:
                        st.image(zoom_cap.get("url") or zoom_cap.get("base64"), use_container_width=True, caption=f"Tipo: {zoom_cap.get('tipo')} | Subida: {zoom_cap.get('fecha_subida', 'N/A')}")
                    with z_col2:
                        st.markdown(f"""
                        <div style="background-color: #1A1E29; border: 1px solid #282D3C; border-radius: 10px; padding: 14px;">
                            <h4 style="margin-top:0; color:#2962FF;">Detalles del Trade</h4>
                            <p><b>Cuenta:</b> {selected_op.get('nombre_cuenta')}</p>
                            <p><b>ID Cuenta:</b> #{selected_op.get('account_number')}</p>
                            <p><b>Fecha:</b> {selected_op.get('fecha')}</p>
                            <p><b>Resultado:</b> <span class="{res_color}">${res_val:,.2f}</span></p>
                            <p><b>Tipo Captura:</b> {zoom_cap.get('tipo')}</p>
                            <p><b>Notas/Observación:</b> {zoom_cap.get('nota', 'Sin notas adicionales')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("❌ Cerrar Vista Ampliada", key=f"close_zoom_{op_id}", use_container_width=True):
                            del st.session_state[f"active_zoom_{op_id}"]
                            st.rerun()

                st.markdown("---")
                st.markdown("#### 📤 Añadir Nueva Captura (Soporta `Ctrl + V` y Archivos)")
                
                tab_up1, tab_up2 = st.tabs(["📋 Pegar Imagen (Ctrl + V)", "📁 Subir Archivo (Drag & Drop)"])
                
                # --- MÉTODO 1: PEGAR CON CTRL + V ---
                with tab_up1:
                    st.caption("Instrucciones: Toma una captura (Win+Shift+S o PrtScn), haz clic en el cuadro de abajo y presiona **Ctrl + V**. ¡La imagen se pegará en tiempo real!")
                    
                    html_paste_box = f"""
                    <div id="paste-container" style="
                        background-color: #1A1E29; 
                        border: 2px dashed #2962FF; 
                        border-radius: 10px; 
                        padding: 24px; 
                        text-align: center; 
                        color: #E0E3EB; 
                        cursor: pointer;
                        transition: all 0.2s ease;">
                        <p style="font-size: 16px; font-weight: 700; margin: 0; color: #2962FF;">
                            📋 HAZ CLIC AQUÍ Y PRESIONA CTRL + V
                        </p>
                        <p style="font-size: 12px; color: #787B86; margin-top: 6px;">
                            Pega directamente la captura del gráfico tomada de TradingView, MetaTrader o tu pantalla.
                        </p>
                        <img id="paste-preview" style="max-width: 100%; max-height: 250px; display: none; margin-top: 12px; border-radius: 8px; border: 1px solid #282D3C;" />
                    </div>

                    <script>
                        const container = document.getElementById('paste-container');
                        const preview = document.getElementById('paste-preview');

                        container.addEventListener('click', () => {{
                            container.style.borderColor = '#26A69A';
                        }});

                        window.addEventListener('paste', (e) => {{
                            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                            for (let item of items) {{
                                if (item.kind === 'file' && item.type.startsWith('image/')) {{
                                    const blob = item.getAsFile();
                                    const reader = new FileReader();
                                    reader.onload = function(event) {{
                                        const b64Data = event.target.result;
                                        preview.src = b64Data;
                                        preview.style.display = 'block';
                                        
                                        navigator.clipboard.writeText(b64Data).then(() => {{
                                            container.innerHTML += '<p style="color:#26A69A; font-weight:bold; margin-top:8px;">¡Imagen capturada! Pégala abajo o usa la confirmación directa.</p>';
                                        }}).catch(err => {{}});
                                        
                                        let txtInput = parent.document.querySelector('textarea[aria-label="pasted_b64_field"]');
                                        if(txtInput) {{
                                            txtInput.value = b64Data;
                                            txtInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        }}
                                    }};
                                    reader.readAsDataURL(blob);
                                }}
                            }}
                        }});
                    </script>
                    """
                    components.html(html_paste_box, height=260)
                    
                    col_p1, col_p2 = st.columns([2, 1])
                    with col_p1:
                        tipo_cap_paste = st.selectbox("Etiqueta / Tipo de Captura:", ["Contexto (TF Mayor)", "Entrada / Ejecución", "Salida / PnL", "Otro"], key=f"tipo_p_{op_id}")
                        nota_paste = st.text_input("Nota breve u observación:", placeholder="Ej: Falsa ruptura en horario de NY con divergencia", key=f"nota_p_{op_id}")
                    with col_p2:
                        pasted_b64 = st.text_area("Código de Imagen Pegada (Ctrl + V):", help="Si pegaste la captura arriba, presiona Ctrl + V en esta caja para confirmar la imagen.", key=f"pasted_area_{op_id}", height=100)

                    if st.button("💾 Guardar Captura Pegada", key=f"save_paste_{op_id}", use_container_width=True):
                        if pasted_b64 and len(pasted_b64) > 50:
                            nueva_cap = {
                                "tipo": tipo_cap_paste,
                                "nota": nota_paste,
                                "url": pasted_b64.strip(),
                                "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            }
                            list_capturas.append(nueva_cap)
                            try:
                                supabase.table("operaciones").update({"capturas": json.dumps(list_capturas)}).eq("id", op_id).execute()
                                st.success("¡Captura pegada guardada exitosamente!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al guardar en la base de datos: {ex}")
                        else:
                            st.warning("Por favor pega la captura en la caja de confirmación (Ctrl + V).")

                # --- MÉTODO 2: SUBIDOR TRADICIONAL DE ARCHIVOS ---
                with tab_up2:
                    up_file = st.file_uploader("Selecciona una imagen desde tu equipo (PNG, JPG, WEBP):", type=["png", "jpg", "jpeg", "webp"], key=f"file_up_{op_id}")
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        tipo_cap_file = st.selectbox("Etiqueta de la Imagen:", ["Contexto (TF Mayor)", "Entrada / Ejecución", "Salida / PnL", "Otro"], key=f"tipo_f_{op_id}")
                    with col_u2:
                        nota_file = st.text_input("Nota breve u observación:", placeholder="Ej: Setup perfecto en zona de demanda", key=f"nota_f_{op_id}")

                    if st.button("💾 Subir y Guardar Archivo", key=f"save_file_{op_id}", use_container_width=True):
                        if up_file is not None:
                            b64_str = file_to_base64(up_file)
                            if b64_str:
                                nueva_cap = {
                                    "tipo": tipo_cap_file,
                                    "nota": nota_file,
                                    "url": b64_str,
                                    "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                list_capturas.append(nueva_cap)
                                try:
                                    supabase.table("operaciones").update({"capturas": json.dumps(list_capturas)}).eq("id", op_id).execute()
                                    st.success("¡Imagen subida y guardada exitosamente!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error al guardar en Supabase: {ex}")
                        else:
                            st.warning("Por favor selecciona un archivo de imagen antes de guardar.")
