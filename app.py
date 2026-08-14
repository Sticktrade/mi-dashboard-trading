import streamlit as st
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
# 1. CONFIGURACIÓN VISUAL (STICKTRADE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="StickTrade",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS avanzados estilo Notion Dark Mode
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
    .green-text { color: #26A69A; font-weight: 700; }
    .red-text { color: #EF5350; font-weight: 700; }
    .blue-text { color: #2962FF; }

    /* Estilos para Alineación de Filas */
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    
    /* Modal de Zoom Súper Grande a Pantalla Casi Completa Estilo Lightbox Notion */
    div[data-testid="stDialog"] > div {
        max-width: 92vw !important;
        width: 92vw !important;
        background-color: #12151C !important;
        border: 1px solid #282D3C !important;
        border-radius: 12px !important;
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

def update_op_capturas(op_row, new_capturas_list):
    json_str = json.dumps(new_capturas_list)
    op_id = op_row.get("id")
    if op_id is not None:
        return supabase.table("operaciones").update({"capturas": json_str}).eq("id", op_id).execute()
    else:
        acc_num = op_row.get("account_number")
        fecha_val = op_row.get("fecha")
        return supabase.table("operaciones").update({"capturas": json_str}).eq("account_number", acc_num).eq("fecha", fecha_val).execute()

# MODAL FLOTANTE MAXIMIZADO A CASI PANTALLA COMPLETA
@st.dialog("🔍 Vista Ampliada de la Captura", width="large")
def mostrar_modal_zoom(cap):
    img_src = cap.get("url") or cap.get("base64")
    if img_src:
        st.image(img_src, use_container_width=True)
    
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.markdown(f"**Etiqueta:** `{cap.get('tipo', 'Gráfico')}`")
    with col_m2:
        nota_txt = cap.get('nota')
        if nota_txt:
            st.markdown(f"**Notas técnicas:** {nota_txt}")
        else:
            st.caption("Sin notas técnicas registradas.")

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL / AGRUPACIÓN INTELIGENTE CON PERSISTENCIA Y DESPLEGABLES CONTRAÍDOS
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ StickTrade")
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
            
            with st.sidebar.expander(f"🔍 Ver {len(lista_accs)} sub-cuentas", expanded=False):
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
st.title("📈 StickTrade — Dashboard")
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
        <div class="{color}" style="font-size:12px;">{pct_global:+.2f}% (${tot_ganado:,.2f})</div>
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
    
    st.components.v1.html(html_grid, height=620, scrolling=True)
    
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
# TAB 4: HISTORIAL DE OPERACIONES DIARIAS & TABLA ESTILO NOTION
# =============================================================================
with tab_trades:
    st.subheader("📖 Historial & Analítica de Operaciones")
    st.caption("Filtra y revisa las sesiones por fecha, cuenta y estado.")
    
    # CALCULAMOS LA SEMANA EN CURSO POR DEFECTO (LUNES A HOY)
    hoy = datetime.date.today()
    lunes_semana_actual = hoy - datetime.timedelta(days=hoy.weekday())
    
    col_f1, col_f2 = st.columns([2, 2])
    
    with col_f1:
        # date_input libre sin min_value/max_value para habilitar el selector de año libre
        rango_fechas = st.date_input(
            "📅 Rango de Fechas:",
            value=(lunes_semana_actual, hoy),
            key="filtro_rango_fechas"
        )
        
    with col_f2:
        filtro_estados = st.multiselect(
            "🎯 Filtrar Resultado:",
            options=["WIN", "LOSS", "BE"],
            default=["WIN", "LOSS", "BE"],
            key="filtro_multiselect_estados"
        )
        
    if df_ops.empty:
        st.info("No hay operaciones registradas para las cuentas seleccionadas.")
    else:
        map_bal_inicial = {str(c["account_number"]): float(c["balance_inicial"]) for c in cuentas_raw} if cuentas_raw else {}
        
        df_ops_copy = df_ops.copy()
        df_ops_copy["acc_id_str"] = df_ops_copy["account_number"].astype(str)
        
        if "capturas" not in df_ops_copy.columns:
            df_ops_copy["capturas"] = None
        if "resultado" not in df_ops_copy.columns:
            df_ops_copy["resultado"] = 0.0
        if "nombre_cuenta" not in df_ops_copy.columns:
            df_ops_copy["nombre_cuenta"] = "Cuenta"
            
        df_diario = df_ops_copy.groupby(["fecha_dia", "acc_id_str", "nombre_cuenta"]).agg({
            "resultado": "sum"
        }).reset_index()
        
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
        
        # FILTRADO DE FECHAS SEGURO
        if isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 2:
            f_start, f_end = rango_fechas[0], rango_fechas[1]
            df_filtered_tab4 = df_diario[(df_diario["fecha_dia"] >= f_start) & (df_diario["fecha_dia"] <= f_end)]
        elif isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 1:
            f_start = rango_fechas[0]
            df_filtered_tab4 = df_diario[df_diario["fecha_dia"] == f_start]
        else:
            df_filtered_tab4 = df_diario.copy()
            
        if filtro_estados:
            df_filtered_tab4 = df_filtered_tab4[df_filtered_tab4["clasificacion"].isin(filtro_estados)]
            
        df_filtered_tab4 = df_filtered_tab4.sort_values("fecha_dia", ascending=False)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if df_filtered_tab4.empty:
            st.warning("⚠️ No se encontraron operaciones para el rango de fechas seleccionado.")
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
            
            # -----------------------------------------------------------------
            # TABLA LIMPIA EXACTA ESTILO NOTION
            # -----------------------------------------------------------------
            st.subheader("📑 Detalle de Sesiones Diarias & Capturas")
            st.caption("Tabla de historial alineada. Haz clic en el botón de estado para abrir las capturas.")
            
            hdr_c1, hdr_c2, hdr_c3, hdr_c4, hdr_c5, hdr_c6 = st.columns([1.1, 1.8, 1.2, 1.3, 1.1, 1.6])
            hdr_c1.markdown("<span style='color:#787B86; font-size:12px; font-weight:700;'>FECHA</span>", unsafe_allow_html=True)
            hdr_c2.markdown("<span style='color:#787B86; font-size:12px; font-weight:700;'>CUENTA</span>", unsafe_allow_html=True)
            hdr_c3.markdown("<span style='color:#787B86; font-size:12px; font-weight:700;'>ID CUENTA</span>", unsafe_allow_html=True)
            hdr_c4.markdown("<span style='color:#787B86; font-size:12px; font-weight:700;'>RESULTADO ($)</span>", unsafe_allow_html=True)
            hdr_c5.markdown("<span style='color:#787B86; font-size:12px; font-weight:700;'>% REND.</span>", unsafe_allow_html=True)
            hdr_c6.markdown("<span style='color:#787B86; font-size:12px; font-weight:700;'>ESTADO / CAPTURAS</span>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 6px 0 10px 0; border-color: #282D3C;'>", unsafe_allow_html=True)

            list_sessions = df_filtered_tab4.to_dict("records")
            
            for idx, row in enumerate(list_sessions):
                f_str = str(row["fecha_dia"])
                acc_name = str(row["nombre_cuenta"])
                acc_id_str = str(row["acc_id_str"])
                res_num = float(row["resultado"])
                pct_num = float(row["pct_rendimiento"])
                clasif = str(row["clasificacion"])
                
                matching_ops = [
                    op for op in ops_raw 
                    if str(op.get("account_number")) == acc_id_str and str(op.get("fecha", "")).startswith(f_str)
                ]
                
                op_row = matching_ops[0] if matching_ops else {
                    "account_number": acc_id_str,
                    "fecha": f_str,
                    "nombre_cuenta": acc_name,
                    "resultado": res_num
                }
                
                capturas_list = parse_capturas(op_row.get("capturas"))
                num_caps = len(capturas_list)
                
                if clasif == "WIN":
                    badge = f"🟩 WIN ({num_caps})"
                    res_html = f"<span class='green-text'>+${res_num:,.2f}</span>"
                    pct_html = f"<span class='green-text'>+{pct_num:.2f}%</span>"
                elif clasif == "LOSS":
                    badge = f"🟥 LOSS ({num_caps})"
                    res_html = f"<span class='red-text'>-${abs(res_num):,.2f}</span>"
                    pct_html = f"<span class='red-text'>{pct_num:.2f}%</span>"
                else:
                    badge = f"⚪ BE ({num_caps})"
                    res_html = f"<span>${res_num:,.2f}</span>"
                    pct_html = f"<span>{pct_num:.2f}%</span>"

                row_key = f"pop_{acc_id_str}_{f_str}_{idx}"
                
                c1, c2, c3, c4, c5, c6 = st.columns([1.1, 1.8, 1.2, 1.3, 1.1, 1.6])
                
                with c1:
                    st.markdown(f"<span style='font-size:13px;'>{f_str}</span>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<span style='font-size:13px; font-weight:600;'>{acc_name}</span>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<code style='background:#1A1E29; color:#A3A6AF; padding:2px 6px; border-radius:4px;'>#{acc_id_str}</code>", unsafe_allow_html=True)
                with c4:
                    st.markdown(res_html, unsafe_allow_html=True)
                with c5:
                    st.markdown(pct_html, unsafe_allow_html=True)
                with c6:
                    with st.popover(badge, use_container_width=True):
                        st.markdown(f"### 📊 Sesión: {acc_name} (`#{acc_id_str}`)")
                        st.markdown(f"**Fecha:** `{f_str}` | **Resultado:** {res_html} ({pct_html})", unsafe_allow_html=True)
                        st.markdown("---")
                        
                        # GALERÍA DE CAPTURAS
                        st.markdown(f"##### 🖼️ Capturas de Pantalla ({num_caps})")
                        if capturas_list:
                            grid_cols = st.columns(min(len(capturas_list), 2))
                            for c_idx, cap in enumerate(capturas_list):
                                target_col = grid_cols[c_idx % 2]
                                with target_col:
                                    st.markdown(f"**Captura {c_idx+1}: {cap.get('tipo', 'Gráfico')}**")
                                    img_src = cap.get("url") or cap.get("base64")
                                    if img_src:
                                        st.image(img_src, use_container_width=True)
                                        
                                        b_col1, b_col2 = st.columns([2, 1])
                                        with b_col1:
                                            if st.button(f"🔍 Zoom", key=f"zoom_pop_{row_key}_{c_idx}", use_container_width=True):
                                                mostrar_modal_zoom(cap)
                                        with b_col2:
                                            if st.button("🗑️", key=f"del_pop_{row_key}_{c_idx}", help="Eliminar captura", use_container_width=True):
                                                capturas_list.pop(c_idx)
                                                try:
                                                    update_op_capturas(op_row, capturas_list)
                                                    st.success("Captura eliminada.")
                                                    st.cache_data.clear()
                                                    st.rerun()
                                                except Exception as ex_del:
                                                    st.error(f"Error al eliminar: {ex_del}")
                        else:
                            st.info("No hay capturas adjuntas aún para esta sesión.")

                        # ZONA NATIVA DE SUBIDA DE ARCHIVO
                        st.markdown("---")
                        st.markdown("##### 📤 Adjuntar Nueva Captura")
                        
                        tipo_f = st.selectbox("Tipo / Etiqueta:", ["Contexto (TF Mayor)", "Entrada / Ejecución", "Salida / PnL", "Otro"], key=f"sel_tipo_f_{row_key}")
                        nota_f = st.text_input("Nota técnica:", placeholder="Ej: Ruptura de estructura en POI", key=f"inp_nota_f_{row_key}")

                        uploaded_file = st.file_uploader("Selecciona o arrastra tu archivo de captura aquí", type=['png', 'jpg', 'jpeg', 'webp'], key=f"up_{row_key}")

                        if uploaded_file is not None:
                            st.image(uploaded_file, caption="✅ Imagen lista para guardar", use_container_width=True)

                            if st.button("💾 Guardar Captura", key=f"btn_save_f_{row_key}", use_container_width=True):
                                bytes_data = uploaded_file.getvalue()
                                b64_encoded = base64.b64encode(bytes_data).decode("utf-8")
                                b64_string = f"data:{uploaded_file.type};base64,{b64_encoded}"
                                
                                nueva_c = {
                                    "tipo": tipo_f,
                                    "nota": nota_f,
                                    "url": b64_string,
                                    "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                }
                                capturas_list.append(nueva_c)
                                try:
                                    update_op_capturas(op_row, capturas_list)
                                    st.success("¡Imagen guardada con éxito!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as ex_f:
                                    st.error(f"Error al guardar: {ex_f}")
                
                st.markdown("<hr style='margin: 4px 0; border-color: #1E222E;'>", unsafe_allow_html=True)
