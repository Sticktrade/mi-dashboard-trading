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
# 1. CONFIGURACIÓN VISUAL (STICKTRADE - DISEÑO INSTITUCIONAL)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="StickTrade",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de fuentes, iconos (FontAwesome) y CSS personalizado
st.markdown("""
<link href="https://fonts.googleapis.com" rel="preconnect">
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

<style>
    :root {
        --primary-color: #2962FF !important;
        --bg-main: #0B0E14;
        --bg-sec: #111622;
        --bg-card: #161D2E;
        --border-main: #1E293B;
        --border-light: #2D384D;
        --text-main: #E2E8F0;
        --text-muted: #94A3B8;
        
        --win-color: #10B981;
        --loss-color: #F43F5E;
        --be-color: #64748B;
        --blue-accent: #2962FF;
    }

    /* Tipografía y Fondos Base */
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
    }
    
    .font-mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* TABS */
    button[data-baseweb="tab"] {
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--text-main) !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: var(--primary-color) !important;
    }
    div[data-baseweb="tab-border"] {
        background-color: var(--border-main) !important;
    }
    
    /* CHECKBOXES Y RADIO BUTTONS */
    div[data-baseweb="checkbox"], div[data-baseweb="radio"] {
        margin-bottom: 4px;
        padding: 4px 6px;
        border-radius: 6px;
        transition: background-color 0.2s;
    }
    div[data-baseweb="checkbox"]:hover, div[data-baseweb="radio"]:hover {
        background-color: var(--bg-sec);
    }
    div[data-baseweb="checkbox"] input:checked + div,
    div[role="checkbox"][aria-checked="true"],
    div[data-baseweb="radio"] input:checked + div {
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
    }
    div[data-baseweb="checkbox"] svg {
        fill: #FFFFFF !important;
    }
    div[data-baseweb="checkbox"] span, div[data-baseweb="radio"] span {
        color: var(--text-main) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    
    /* SIDEBAR Y EXPANDERS */
    .stSidebar {
        background-color: rgba(17, 22, 34, 0.95) !important;
        border-right: 1px solid var(--border-main) !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid var(--border-light) !important;
        background-color: var(--bg-card) !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stExpander"] details {
        border: none !important;
        background-color: transparent !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 12px !important;
        color: var(--text-main) !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }
    div[data-testid="stExpander"] summary:hover {
        color: var(--primary-color) !important;
    }

    /* BOTONES */
    .stButton > button {
        border-radius: 6px !important;
        border: 1px solid var(--border-light) !important;
        background-color: var(--bg-sec) !important;
        color: var(--text-main) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
        background-color: var(--bg-card) !important;
    }
    
    /* KPI CARDS (Rediseñadas tipo Tailwind) */
    .kpi-card {
        background-color: rgba(22, 29, 46, 0.9);
        border: 1px solid var(--border-main);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        border-color: var(--border-light);
    }
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.025em;
    }
    .kpi-meta {
        margin-top: 10px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        border: 1px solid;
    }
    .badge-win { background-color: rgba(16, 185, 129, 0.15); color: var(--win-color); border-color: rgba(16, 185, 129, 0.2); }
    .badge-loss { background-color: rgba(244, 63, 94, 0.15); color: var(--loss-color); border-color: rgba(244, 63, 94, 0.2); }
    .badge-be { background-color: rgba(100, 116, 139, 0.15); color: var(--be-color); border-color: rgba(100, 116, 139, 0.2); }

    .color-win { color: var(--win-color) !important; font-weight: 700; }
    .color-loss { color: var(--loss-color) !important; font-weight: 700; }
    .color-be { color: var(--be-color) !important; font-weight: 700; }
    .color-blue { color: var(--blue-accent) !important; font-weight: 700; }

    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    
    /* MODAL Y SOPORTE DE GESTOS TÁCTILES */
    img {
        touch-action: pan-x pan-y pinch-zoom !important;
        max-width: 100% !important;
        object-fit: contain !important;
        -webkit-user-select: auto !important;
        user-select: auto !important;
    }
    div[data-testid="stDialog"] img, div[data-testid="stPopover"] img {
        touch-action: pan-x pan-y pinch-zoom !important;
        cursor: zoom-in;
    }
    div[data-testid="stDialog"] > div {
        max-width: 92vw !important;
        width: 92vw !important;
        background-color: var(--bg-main) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 12px !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. CONEXIÓN A SUPABASE Y FUNCIONES AUXILIARES OPTIMIZADAS
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

def obtener_tarifa_por_lote(nombre_cuenta):
    n_lower = str(nombre_cuenta).lower().strip()
    if "wall street" in n_lower:
        return 3.0
    elif "funding pips" in n_lower:
        return 5.0
    elif "fiver" in n_lower:
        return 4.0
    elif "funded next" in n_lower or "fundednext" in n_lower:
        return 5.0
    elif "orion" in n_lower:
        return 4.0
    return 4.0

@st.cache_data
def process_raw_operations(ops_list):
    if not ops_list:
        return []
    
    processed_ops = []
    for op in ops_list:
        op_dict = dict(op)
        
        tipo_op = str(op_dict.get('tipo', '')).upper()
        if tipo_op == "WITHDRAWAL":
            op_dict['raw_profit'] = float(op_dict.get('resultado', 0.0) or 0.0)
            op_dict['comision_calc'] = 0.0
            op_dict['swap_calc'] = 0.0
            op_dict['resultado'] = float(op_dict.get('resultado', 0.0) or 0.0)
            op_dict['simbolo'] = "WITHDRAWAL"
            processed_ops.append(op_dict)
            continue

        def find_val(candidates):
            for k, v in op_dict.items():
                clean_k = str(k).strip().lower().replace("_", "").replace("-", "").replace(" ", "")
                for cand in candidates:
                    clean_cand = cand.strip().lower().replace("_", "").replace("-", "").replace(" ", "")
                    if clean_k == clean_cand:
                        if v is not None and str(v).strip() != "":
                            try:
                                v_clean = str(v).replace("$", "").replace(",", "").strip()
                                return k, float(v_clean)
                            except (ValueError, TypeError):
                                pass
            return None, 0.0

        def find_str_val(candidates):
            for k, v in op_dict.items():
                clean_k = str(k).strip().lower().replace("_", "").replace("-", "").replace(" ", "")
                for cand in candidates:
                    clean_cand = cand.strip().lower().replace("_", "").replace("-", "").replace(" ", "")
                    if clean_k == clean_cand:
                        if v is not None and str(v).strip() != "":
                            return str(v).strip().upper()
            return "N/A"

        profit_keys = ['resultado', 'profit', 'ganancia', 'pnl', 'netprofit', 'rawprofit', 'beneficio', 'monto']
        comm_keys   = ['comision', 'comisiones', 'commission', 'commissions', 'comm', 'fee', 'fees']
        swap_keys   = ['swap', 'swaps', 'rollover']
        vol_keys    = ['volume', 'volumen', 'lotes', 'lots', 'lotaje']
        sym_keys    = ['simbolo', 'symbol', 'instrumento', 'par', 'ticker', 'item', 'asset', 'pair']

        p_key, raw_profit = find_val(profit_keys)
        c_key, comm_val   = find_val(comm_keys)
        s_key, swap_val   = find_val(swap_keys)
        v_key, vol_val    = find_val(vol_keys)
        sym_val           = find_str_val(sym_keys)

        nombre_cta = op_dict.get('nombre_cuenta', '')
        
        if abs(comm_val) == 0.0 and vol_val > 0.0:
            tarifa = obtener_tarifa_por_lote(nombre_cta)
            comm_val = vol_val * tarifa

        net_result = raw_profit - abs(comm_val) + swap_val

        op_dict['raw_profit'] = raw_profit
        op_dict['comision_calc'] = abs(comm_val)
        op_dict['swap_calc'] = swap_val
        op_dict['resultado'] = net_result
        op_dict['simbolo'] = sym_val
        op_dict['comm_column_found'] = c_key if c_key else "NINGUNA"

        processed_ops.append(op_dict)
        
    return processed_ops

@st.cache_data(ttl=300)
def cargar_datos():
    res_cuentas = supabase.table("cuentas").select("*").execute()
    res_ops = supabase.table("operaciones").select("*").order("fecha", desc=True).execute()
    
    ops_data = res_ops.data
    if ops_data:
        ops_data = process_raw_operations(ops_data)
        
    return res_cuentas.data, ops_data

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

@st.cache_data
def obtener_df_diario_clasificado(df_input, cuentas_lista):
    if df_input.empty:
        return pd.DataFrame()
    
    df_trading = df_input[df_input.get("tipo", "").astype(str).str.upper() != "WITHDRAWAL"].copy()
    if df_trading.empty:
        return pd.DataFrame()
    
    map_bal_inicial = {str(c["account_number"]): float(c["balance_inicial"]) for c in cuentas_lista} if cuentas_lista else {}
    df_trading["acc_id_str"] = df_trading["account_number"].astype(str)
    
    if "nombre_cuenta" not in df_trading.columns:
        df_trading["nombre_cuenta"] = "Cuenta"
        
    df_diario = df_trading.groupby(["fecha_dia", "acc_id_str", "nombre_cuenta"]).agg({
        "resultado": "sum"
    }).reset_index()
    
    df_diario["balance_inicial"] = df_diario["acc_id_str"].map(lambda x: map_bal_inicial.get(x, 100000.0))
    df_diario["pct_rendimiento"] = (df_diario["resultado"] / df_diario["balance_inicial"]) * 100.0
    
    def clasificar(pct):
        if pct > 0.10:
            return "WIN"
        elif pct < -0.10:
            return "LOSS"
        else:
            return "BE"
            
    df_diario["clasificacion"] = df_diario["pct_rendimiento"].apply(clasificar)
    return df_diario

@st.dialog("🔍 Vista Ampliada de la Captura", width="large")
def mostrar_modal_zoom(cap):
    img_src = cap.get("url") or cap.get("base64")
    if img_src:
        st.markdown(f"""
        <div style="width:100%; overflow:auto; text-align:center; -webkit-overflow-scrolling:touch;">
            <img src="{img_src}" style="max-width:100%; height:auto; touch-action: pan-x pan-y pinch-zoom !important; border-radius:8px;" />
        </div>
        """, unsafe_allow_html=True)
    
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.markdown(f"**Etiqueta:** `{cap.get('tipo', 'Gráfico')}`")
    with col_m2:
        nota_txt = cap.get('nota')
        if nota_txt:
            st.markdown(f"**Notas técnicas:** {nota_txt}")
        else:
            st.caption("Sin notas técnicas registradas.")
@st.dialog("⚙️ Gestionar Estado de Cuentas", width="large")
def modal_gestionar_estados(cuentas_raw_list):
    st.markdown("Si la automatización falló, puedes forzar el cambio de estado de tus cuentas manualmente aquí. **Esto actualizará tu base de datos en Supabase.**")
    st.divider()
    
    cambios = {}
    
    # Crear una fila por cada cuenta
    for c in cuentas_raw_list:
        acc_id = str(c["account_number"])
        acc_name = c.get("nombre_cuenta", "Cuenta")
        est_actual = str(c.get("estado", "Challenge"))
        
        # Determinar el índice actual para el selectbox
        est_lower = est_actual.lower()
        if "breached" in est_lower or "quemada" in est_lower or "eliminada" in est_lower:
            idx = 2
        elif "fondeada" in est_lower or "funded" in est_lower:
            idx = 1
        else:
            idx = 0
            
        opciones = ["Challenge", "Funded", "Breached"]
        
        # 1. ENVOLVEMOS LA FILA EN UN RECUADRO CON BORDE
        with st.container(border=True):
            
            # 2. AJUSTAMOS LAS COLUMNAS PARA REDUCIR EL ESPACIO VACÍO
            col_txt, col_sel = st.columns([3, 2]) 
            
            with col_txt:
                # Mejoramos el diseño de la etiqueta para que se vea más profesional
                st.markdown(f"""
                <div style='margin-top:6px; font-size:15px; font-weight:600;'>
                    {acc_name} 
                    <code style='font-size:12px; margin-left:8px; color:var(--text-muted); background-color:var(--bg-main); padding:3px 6px; border-radius:6px; border: 1px solid var(--border-light);'>#{acc_id}</code>
                </div>
                """, unsafe_allow_html=True)
                
            with col_sel:
                nuevo_estado = st.selectbox(
                    "Estado", 
                    options=opciones, 
                    index=idx, 
                    key=f"edit_est_{acc_id}",
                    label_visibility="collapsed"
                )
                
                if nuevo_estado != opciones[idx]:
                    cambios[acc_id] = nuevo_estado
                
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("💾 Guardar Cambios en Base de Datos", use_container_width=True):
        if cambios:
            with st.spinner("Actualizando base de datos..."):
                try:
                    for a_id, n_est in cambios.items():
                        supabase.table("cuentas").update({"estado": n_est}).eq("account_number", a_id).execute()
                    st.success("¡Estados actualizados correctamente!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar la base de datos: {e}")
        else:
            st.info("No realizaste ningún cambio.")
# -----------------------------------------------------------------------------
# 3. BARRA LATERAL / ORGANIZACIÓN DE CUENTAS
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
    <div style="width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(to top right, #2962FF, #06B6D4); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 6px -1px rgba(41, 98, 255, 0.2);">
        <i class="fa-solid fa-chart-candlestick" style="color: white; font-size: 16px;"></i>
    </div>
    <div style="display: flex; flex-direction: column;">
        <span style="font-size: 16px; font-weight: 800; color: white; letter-spacing: -0.5px;">StickTrade</span>
        <span style="font-size: 10px; color: #94A3B8;">Analytics de Cuentas de Fondeo</span>
    </div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### <i class='fa-solid fa-sliders' style='color:#2962FF; margin-right:4px;'></i> Selección de Cuentas", unsafe_allow_html=True)

# ---> NUEVO BOTÓN PARA ABRIR EL MODAL <---
if st.sidebar.button("⚙️ Gestionar Estados", use_container_width=True):
    if cuentas_raw:
        modal_gestionar_estados(cuentas_raw)
    else:
        st.sidebar.warning("No hay cuentas cargadas.")
# ------------------------------------------

cuentas_funded = []
cuentas_challenges = []
cuentas_breached = []

if cuentas_raw:
    for c in cuentas_raw:
        est = str(c.get("estado", "")).strip().lower()
        if "fondeada" in est or "funded" in est:
            cuentas_funded.append(c)
        elif "breached" in est or "quemada" in est or "eliminada" in est:
            cuentas_breached.append(c)
        else:
            cuentas_challenges.append(c)

def agrupar_por_nombre(lista_cuentas):
    grupos = {}
    for c in lista_cuentas:
        n = c.get("nombre_cuenta", "Cuenta")
        if n not in grupos:
            grupos[n] = []
        grupos[n].append(c)
    return grupos

if "init_accounts_state" not in st.session_state:
    st.session_state["init_accounts_state"] = True
    if cuentas_raw:
        for c in cuentas_raw:
            acc_id = str(c["account_number"])
            nombre_c = str(c.get("nombre_cuenta", "")).lower()
            est_c = str(c.get("estado", "")).lower()
            key_c = f"chk_{acc_id}"
            
            if "breached" in est_c or "quemada" in est_c or "nova" in nombre_c:
                st.session_state[key_c] = False
            else:
                st.session_state[key_c] = True

        for prefix, lista_cat in [("funded", cuentas_funded), ("challenges", cuentas_challenges), ("breached", cuentas_breached)]:
            for grp_n, acc_list in agrupar_por_nombre(lista_cat).items():
                child_ids = [str(a["account_number"]) for a in acc_list]
                st.session_state[f"master_{prefix}_{grp_n}"] = all(st.session_state.get(f"chk_{cid}", False) for cid in child_ids)

col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("Todas", use_container_width=True):
    if cuentas_raw:
        for c in cuentas_funded + cuentas_challenges:
            acc_id = str(c["account_number"])
            st.session_state[f"chk_{acc_id}"] = True
        for c in cuentas_breached:
            acc_id = str(c["account_number"])
            st.session_state[f"chk_{acc_id}"] = False

        for grp_n in agrupar_por_nombre(cuentas_funded).keys():
            st.session_state[f"master_funded_{grp_n}"] = True
        for grp_n in agrupar_por_nombre(cuentas_challenges).keys():
            st.session_state[f"master_challenges_{grp_n}"] = True
        for grp_n in agrupar_por_nombre(cuentas_breached).keys():
            st.session_state[f"master_breached_{grp_n}"] = False
        st.rerun()

if col_b2.button("Ninguna", use_container_width=True):
    if cuentas_raw:
        for c in cuentas_raw:
            acc_id = str(c["account_number"])
            st.session_state[f"chk_{acc_id}"] = False
        for prefix in ["funded", "challenges", "breached"]:
            for grp_n in agrupar_por_nombre(eval(f"cuentas_{prefix}")).keys():
                st.session_state[f"master_{prefix}_{grp_n}"] = False
        st.rerun()

st.sidebar.markdown("<br>", unsafe_allow_html=True)

cuentas_seleccionadas_ids = []

def render_seccion_cuentas(prefix, grupos_dict):
    for nombre_grp, lista_accs in grupos_dict.items():
        child_ids = [str(a["account_number"]) for a in lista_accs]
        master_key = f"master_{prefix}_{nombre_grp}"

        if master_key not in st.session_state:
            st.session_state[master_key] = all(st.session_state.get(f"chk_{cid}", False) for cid in child_ids)

        def make_callbacks(grp_k=master_key, c_ids=child_ids):
            def on_m_change():
                m_val = st.session_state[grp_k]
                for cid in c_ids:
                    st.session_state[f"chk_{cid}"] = m_val
            def on_c_change():
                st.session_state[grp_k] = all(st.session_state.get(f"chk_{cid}", False) for cid in c_ids)
            return on_m_change, on_c_change

        cb_master, cb_child = make_callbacks()

        if len(lista_accs) == 1:
            acc = lista_accs[0]
            acc_id = str(acc["account_number"])
            key = f"chk_{acc_id}"
            label = f"{acc['nombre_cuenta']} — ${acc['balance']:,.2f}"
            if st.checkbox(label, value=st.session_state.get(key, True), key=key, on_change=cb_child):
                cuentas_seleccionadas_ids.append(acc_id)
        else:
            tot_bal = sum(a["balance"] for a in lista_accs)
            master_label = f"**{nombre_grp}** ({len(lista_accs)} ctas) — ${tot_bal:,.2f}"
            st.checkbox(
                master_label,
                value=st.session_state.get(master_key, False),
                key=master_key,
                on_change=cb_master
            )
            with st.expander(f"🔍 Ver {len(lista_accs)} sub-cuentas", expanded=False):
                for acc in lista_accs:
                    acc_id = str(acc["account_number"])
                    cid_key = f"chk_{acc_id}"
                    child_label = f"#{acc_id} — ${acc['balance']:,.2f} [{acc['estado']}]"
                    if st.checkbox(
                        child_label,
                        value=st.session_state.get(cid_key, False),
                        key=cid_key,
                        on_change=cb_child
                    ):
                        cuentas_seleccionadas_ids.append(acc_id)

with st.sidebar.expander("🟢 Funded", expanded=True):
    if not cuentas_funded:
        st.caption("Sin cuentas fondeadas.")
    else:
        render_seccion_cuentas("funded", agrupar_por_nombre(cuentas_funded))

with st.sidebar.expander("🎯 Challenges", expanded=True):
    if not cuentas_challenges:
        st.caption("Sin cuentas challenge.")
    else:
        render_seccion_cuentas("challenges", agrupar_por_nombre(cuentas_challenges))

with st.sidebar.expander("🔻 Breached", expanded=False):
    if not cuentas_breached:
        st.caption("Sin cuentas breached.")
    else:
        render_seccion_cuentas("breached", agrupar_por_nombre(cuentas_breached))

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

df_ops_trading = df_ops[df_ops.get("tipo", "").astype(str).str.upper() != "WITHDRAWAL"].copy() if not df_ops.empty else pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. ENCABEZADO Y KPI CARDS
# -----------------------------------------------------------------------------
st.markdown("""
<div style="display:flex; align-items:center; gap: 12px; margin-bottom: 0.5rem;">
    <div style="padding: 8px; border-radius: 8px; background-color: var(--bg-card); border: 1px solid var(--border-light); color: var(--blue-accent);">
        <i class="fa-solid fa-chart-line" style="font-size: 1.25rem;"></i>
    </div>
    <h1 style="margin: 0; font-size: 24px; font-weight: 800; color: white;">StickTrade <span style="color:#64748B; font-weight:300;">—</span> Dashboard</h1>
</div>
<p style="color: #94A3B8; font-size: 13px; margin-top: 0; margin-bottom: 1.5rem;">Visión consolidada y métricas de rendimiento cuantitativo en tiempo real.</p>
""", unsafe_allow_html=True)

tot_inicial = sum([c["balance_inicial"] for c in cuentas]) if cuentas else 0
tot_actual = sum([c["balance"] for c in cuentas]) if cuentas else 0
tot_ganado = tot_actual - tot_inicial
pct_global = (tot_ganado / tot_inicial * 100) if tot_inicial > 0 else 0

df_diario_kpi = obtener_df_diario_clasificado(df_ops_trading, cuentas_raw)

if not df_diario_kpi.empty:
    wins = len(df_diario_kpi[df_diario_kpi['clasificacion'] == 'WIN'])
    losses = len(df_diario_kpi[df_diario_kpi['clasificacion'] == 'LOSS'])
    be_cnt = len(df_diario_kpi[df_diario_kpi['clasificacion'] == 'BE'])
    total_dias_operados = len(df_diario_kpi)
    win_rate = (wins / total_dias_operados * 100) if total_dias_operados > 0 else 0
else:
    wins, losses, be_cnt, total_dias_operados, win_rate = 0, 0, 0, 0, 0

gross_profit = df_ops_trading[df_ops_trading['resultado'] > 0]['resultado'].sum() if not df_ops_trading.empty else 0
gross_loss = abs(df_ops_trading[df_ops_trading['resultado'] < 0]['resultado'].sum()) if not df_ops_trading.empty else 0
profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)

avg_win = df_ops_trading[df_ops_trading['resultado'] > 0]['resultado'].mean() if wins > 0 else 0
avg_loss = abs(df_ops_trading[df_ops_trading['resultado'] < 0]['resultado'].mean()) if losses > 0 else 0
risk_reward = (avg_win / avg_loss) if avg_loss > 0 else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    badge_class = "badge-win" if tot_ganado >= 0 else "badge-loss"
    val_color = "white"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header"><span>Capital Gestionado</span><i class="fa-solid fa-vault"></i></div>
        <div class="kpi-value" style="color: {val_color};">${tot_actual:,.2f}</div>
        <div class="kpi-meta"><span class="badge {badge_class}">{pct_global:+.2f}% (${tot_ganado:,.2f})</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header"><span>Win Rate</span><i class="fa-solid fa-bullseye"></i></div>
        <div class="kpi-value color-win">{win_rate:.1f}%</div>
        <div class="kpi-meta color-muted">
            <span class="color-win">{wins}W</span> / <span class="color-loss">{losses}L</span> / <span style="color:var(--be-color)">{be_cnt}BE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header"><span>Profit Factor</span><i class="fa-solid fa-scale-balanced"></i></div>
        <div class="kpi-value" style="color: white;">{profit_factor:.2f}</div>
        <div class="kpi-meta color-muted">
            <span class="color-win">G: ${gross_profit:,.0f}</span> | <span class="color-loss">P: ${gross_loss:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header"><span>Ratio R/R Real</span><i class="fa-solid fa-arrows-split-up-and-left"></i></div>
        <div class="kpi-value" style="color: white;">1 : {risk_reward:.2f}</div>
        <div class="kpi-meta" style="color:#E2E8F0;">
            Avg W: <span style="font-weight:bold;">${avg_win:,.0f}</span> | Avg L: <span style="font-weight:bold;">${avg_loss:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    cant_cuentas = len(cuentas)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header"><span>Cuentas Filtro</span><i class="fa-solid fa-layer-group"></i></div>
        <div class="kpi-value color-blue">{cant_cuentas}</div>
        <div class="kpi-meta" style="color:var(--text-muted); font-family:'Inter', sans-serif;">Fondeadas & Challenges</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. PESTAÑAS PRINCIPALES DEL DASHBOARD
# -----------------------------------------------------------------------------
tab_calendar, tab_estado_analytics, tab_trades = st.tabs([
    "📅 Calendario de Resultados",
    "🛡️ Estado & Analytics",
    "📖 Historial de Operaciones"
])

# =============================================================================
# TAB 1: CALENDARIO DE RESULTADOS (MENSUAL + ANUAL MES A MES)
# =============================================================================
with tab_calendar:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown("<h3 style='font-size:18px; font-weight:700;'><i class='fa-regular fa-calendar-days' style='color:var(--blue-accent); margin-right:6px;'></i> Calendario Mensual de Resultados</h3>", unsafe_allow_html=True)
    with col_t2:
        mostrar_simbolos_cal = st.toggle("👁️ Desglose por símbolo", value=True, key="toggle_simbolos_cal")
    
    now = datetime.datetime.now()
    c_m, c_y = st.columns([1, 1])
    
    MESES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    with c_m:
        mes_sel = st.selectbox("Mes:", range(1, 13), index=now.month - 1, format_func=lambda x: MESES_ES[x-1])
    with c_y:
        ano_sel = st.number_input("Año Mensual:", min_value=2024, max_value=2030, value=now.year, key="ano_mensual_sel")
        
    daily_stats = {}
    if not df_ops_trading.empty:
        df_mes = df_ops_trading[(df_ops_trading['fecha_dt'].dt.month == mes_sel) & (df_ops_trading['fecha_dt'].dt.year == ano_sel)]
        if not df_mes.empty:
            for f_dia, group in df_mes.groupby('fecha_dia'):
                pnl = group['resultado'].sum()
                tr_cnt = len(group)
                w_cnt = len(group[group['resultado'] > 0])
                wr_val = (w_cnt / tr_cnt * 100) if tr_cnt > 0 else 0
                
                acc_breakdown = []
                for acc_num, acc_group in group.groupby('account_number'):
                    acc_pnl = acc_group['resultado'].sum()
                    acc_tr = len(acc_group)
                    acc_name = acc_group['nombre_cuenta'].iloc[0] if 'nombre_cuenta' in acc_group.columns else str(acc_num)
                    
                    sym_breakdown = []
                    for sym_name, sym_group in acc_group.groupby('simbolo'):
                        sym_pnl = sym_group['resultado'].sum()
                        sym_tr = len(sym_group)
                        sym_breakdown.append({
                            'symbol': sym_name,
                            'pnl': sym_pnl,
                            'trades': sym_tr
                        })

                    acc_breakdown.append({
                        'name': acc_name,
                        'account_number': acc_num,
                        'pnl': acc_pnl,
                        'trades': acc_tr,
                        'symbols': sym_breakdown
                    })

                daily_stats[f_dia] = {
                    'pnl': pnl,
                    'trades': tr_cnt,
                    'win_rate': wr_val,
                    'accounts': acc_breakdown
                }

    cal_obj = calendar.Calendar(firstweekday=6)
    month_weeks = cal_obj.monthdayscalendar(int(ano_sel), int(mes_sel))
    
    css_cal = """
    <style>
        :root {
            --primary-color: #2962FF; --bg-main: #0B0E14; --bg-sec: #111622;
            --bg-card: #161D2E; --border-main: #1E293B; --border-light: #2D384D;
            --text-main: #E2E8F0; --text-muted: #94A3B8; --win-color: #10B981;
            --loss-color: #F43F5E; --be-color: #64748B;
        }
        body { margin:0; padding:0; background-color: var(--bg-main); color: var(--text-main); font-family: 'Inter', sans-serif; }
        .tradelio-cal-container { background-color: var(--bg-main); border: 1px solid var(--border-light); border-radius: 12px; padding: 25px 15px 45px 15px; overflow: visible !important; }
        .tradelio-grid { display: grid; grid-template-columns: 130px repeat(7, 1fr); gap: 8px; overflow: visible !important; }
        .tradelio-header { text-align: center; font-weight: 700; font-size: 11px; color: var(--text-muted); text-transform: uppercase; padding-bottom: 4px; }
        .week-summary-card { background-color: var(--bg-card); border: 1px solid var(--border-main); border-radius: 8px; padding: 10px; display: flex; flex-direction: column; justify-content: center; min-height: 85px; box-sizing: border-box; }
        .week-title { font-size: 11px; color: var(--text-muted); font-weight: 600; }
        .week-pct { font-size: 11px; font-weight: 700; margin-left: 4px; }
        .week-pct.green { color: var(--win-color) !important; }
        .week-pct.red { color: var(--loss-color) !important; }
        .week-pct.neutral { color: var(--be-color); }
        .week-val { font-size: 16px; font-weight: 800; margin-top: 4px; color: #FFFFFF; font-family: 'JetBrains Mono', monospace; }
        
        .day-box { position: relative; background-color: var(--bg-card); border: 1px solid var(--border-main); border-radius: 8px; padding: 8px; min-height: 85px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; cursor: pointer; transition: border-color 0.2s; }
        .day-box:hover { border-color: var(--border-light); }
        .day-box.empty-day { background-color: var(--bg-sec); border: 1px solid var(--border-main); cursor: default; }
        
        .day-box.win-day { background-color: rgba(16, 185, 129, 0.1) !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; }
        .day-box.loss-day { background-color: rgba(244, 63, 94, 0.1) !important; border: 1px solid rgba(244, 63, 94, 0.3) !important; }
        
        .day-num { font-size: 11px; font-weight: 700; color: #E2E8F0; text-align: right; }
        .day-content { text-align: right; }
        .day-pnl { font-size: 13px; font-weight: 800; color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace; }
        .day-meta { font-size: 9px; color: var(--text-muted); margin-top: 2px; }
        .green-meta { color: var(--win-color) !important; font-weight: 700; }
        .red-meta { color: var(--loss-color) !important; font-weight: 700; }

        .day-tooltip {
            visibility: hidden;
            opacity: 0;
            position: absolute;
            background-color: var(--bg-card);
            border: 1px solid var(--primary-color);
            border-radius: 8px;
            padding: 10px 12px;
            width: 270px;
            max-height: 280px;
            overflow-y: auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.85);
            z-index: 9999;
            transition: opacity 0.2s ease, visibility 0.2s ease;
            pointer-events: none;
            text-align: left;
        }

        .day-tooltip.tooltip-down { top: 105% !important; bottom: auto !important; }
        .day-tooltip.tooltip-up { bottom: 105% !important; top: auto !important; }
        .day-tooltip.align-left { left: 0 !important; transform: none !important; }
        .day-tooltip.align-right { right: 0 !important; left: auto !important; transform: none !important; }
        .day-tooltip.align-center { left: 50% !important; transform: translateX(-50%) !important; }

        .day-box:hover .day-tooltip {
            visibility: visible;
            opacity: 1;
        }
        .tooltip-title { font-size: 10px; font-weight: 800; color: var(--primary-color); border-bottom: 1px solid var(--border-main); padding-bottom: 4px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .tooltip-row { display: flex; justify-content: space-between; align-items: center; font-size: 11px; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace; }
        .tooltip-acc-name { color: var(--text-main); font-weight: 600; font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 170px; font-family: 'Inter', sans-serif;}
        .tooltip-acc-val { font-weight: 800; font-size: 11px; color: #FFFFFF !important; }
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
        
        for day_col_idx, day in enumerate(week):
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
                    
                    v_cls = "tooltip-down" if w_idx <= 2 else "tooltip-up"
                    if day_col_idx <= 1:
                        h_cls = "align-left"
                    elif day_col_idx >= 5:
                        h_cls = "align-right"
                    else:
                        h_cls = "align-center"

                    tooltip_html = f"<div class='day-tooltip {v_cls} {h_cls}'>"
                    tooltip_html += f"<div class='tooltip-title'>📊 {fecha_obj.strftime('%d %b %Y')}</div>"
                    
                    for acc_info in st_day.get('accounts', []):
                        pnl_acc = acc_info['pnl']
                        tr_acc = acc_info['trades']
                        acc_n = acc_info['name']
                        sign_str = "+" if pnl_acc > 0 else ""
                        
                        tooltip_html += f"""
                        <div class='tooltip-row'>
                            <span class='tooltip-acc-name'><span style='color:var(--text-muted); font-weight:700;'>({tr_acc} ops)</span> {acc_n}</span>
                            <span class='tooltip-acc-val'>{sign_str}${pnl_acc:,.2f}</span>
                        </div>
                        """
                        if mostrar_simbolos_cal and acc_info.get('symbols'):
                            tooltip_html += "<div style='margin-left:8px; margin-bottom:6px; padding-left:6px; border-left:1px solid var(--border-light);'>"
                            for s_info in acc_info['symbols']:
                                s_sym = s_info['symbol']
                                s_pnl = s_info['pnl']
                                s_tr = s_info['trades']
                                s_sign = "+" if s_pnl > 0 else ""
                                tooltip_html += f"""
                                <div class='tooltip-row' style='font-size:10px; color:var(--text-main); margin-bottom:2px;'>
                                    <span style='font-family:Inter;'>↳ <b>{s_sym}</b> <span style='color:var(--text-muted);'>({s_tr} ops)</span></span>
                                    <span style='font-weight:700;'>{s_sign}${s_pnl:,.2f}</span>
                                </div>
                                """
                            tooltip_html += "</div>"
                    tooltip_html += "</div>"
                        
                    html_grid += f"<div class='day-box {box_cls}'>{tooltip_html}<div class='day-num'>{day}</div><div class='day-content'><div class='day-pnl'>{pnl_fmt}</div><div class='day-meta'>{meta_str}</div></div></div>"
                else:
                    html_grid += f"<div class='day-box'><div class='day-num'>{day}</div></div>"
                    
    html_grid += "</div></div>"
    
    st.components.v1.html(html_grid, height=660, scrolling=True)
    
    # MÉTRICAS DEL MES SELECCIONADO
    pct_mes = (total_pnl_mes / tot_inicial * 100) if tot_inicial > 0 else 0.0

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("PnL Total del Mes", f"${total_pnl_mes:,.2f}", delta=f"{pct_mes:+.2f}%")
    mc2.metric("% Rendimiento Mes", f"{pct_mes:+.2f}%")
    mc3.metric("Días Verdes (Win)", f"{dias_ganadores} días")
    mc4.metric("Días Rojos (Loss)", f"{dias_perdedores} días")

    # =========================================================================
    # SECCIÓN ANUAL MES A MES
    # =========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    col_a_hdr1, col_a_hdr2 = st.columns([3, 1])
    with col_a_hdr1:
        st.markdown("<h3 style='font-size:16px; font-weight:700;'><i class='fa-regular fa-calendar' style='color:var(--blue-accent); margin-right:6px;'></i> Resumen Anual — Calendario Mes a Mes</h3>", unsafe_allow_html=True)
        st.caption("Evolución mensual consolidada según las cuentas seleccionadas.")
    with col_a_hdr2:
        ano_sel_annual = st.number_input("Año Resumen Anual:", min_value=2024, max_value=2030, value=now.year, key="ano_annual_sel")

    df_ano = df_ops_trading[df_ops_trading['fecha_dt'].dt.year == ano_sel_annual] if not df_ops_trading.empty else pd.DataFrame()
    
    css_annual = """
    <style>
        :root {
            --primary-color: #2962FF; --bg-main: #0B0E14; --bg-sec: #111622;
            --bg-card: #161D2E; --border-main: #1E293B; --border-light: #2D384D;
            --text-main: #E2E8F0; --text-muted: #94A3B8; --win-color: #10B981;
            --loss-color: #F43F5E; --be-color: #64748B;
        }
        body { margin:0; padding:0; background-color: var(--bg-main); color: var(--text-main); font-family: 'Inter', sans-serif; }
        .annual-container { background-color: var(--bg-main); border: 1px solid var(--border-light); border-radius: 12px; padding: 25px 15px 45px 15px; overflow: visible !important; }
        .annual-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; overflow: visible !important; }
        
        .month-card {
            position: relative;
            background-color: var(--bg-card);
            border: 1px solid var(--border-main);
            border-radius: 10px;
            padding: 12px 14px;
            box-sizing: border-box;
            cursor: pointer;
            transition: border-color 0.2s ease;
            min-height: 95px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .month-card:hover {
            border-color: var(--border-light) !important;
        }
        .month-card.win-month { background-color: rgba(16, 185, 129, 0.1) !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; }
        .month-card.loss-month { background-color: rgba(244, 63, 94, 0.1) !important; border: 1px solid rgba(244, 63, 94, 0.3) !important; }

        .month-header { display: flex; justify-content: space-between; align-items: center; }
        .month-title { font-size: 12px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .month-pct { font-size: 11px; font-weight: 800; font-family: 'JetBrains Mono', monospace;}
        .month-pct.green { color: var(--win-color) !important; }
        .month-pct.red { color: var(--loss-color) !important; }
        .month-pct.neutral { color: var(--be-color) !important; }

        .month-pnl { font-size: 18px; font-weight: 800; color: #FFFFFF !important; margin-top: 4px; font-family: 'JetBrains Mono', monospace;}
        .month-meta { font-size: 10px; color: var(--text-muted); margin-top: 2px; }

        .month-tooltip {
            visibility: hidden;
            opacity: 0;
            position: absolute;
            background-color: var(--bg-card);
            border: 1px solid var(--primary-color);
            border-radius: 8px;
            padding: 10px 12px;
            width: 270px;
            max-height: 280px;
            overflow-y: auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.85);
            z-index: 9999;
            transition: opacity 0.2s ease, visibility 0.2s ease;
            pointer-events: none;
            text-align: left;
        }

        .month-tooltip.tooltip-down { top: 105% !important; bottom: auto !important; }
        .month-tooltip.tooltip-up { bottom: 105% !important; top: auto !important; }
        .month-tooltip.align-left { left: 0 !important; transform: none !important; }
        .month-tooltip.align-right { right: 0 !important; left: auto !important; transform: none !important; }
        .month-tooltip.align-center { left: 50% !important; transform: translateX(-50%) !important; }

        .month-card:hover .month-tooltip {
            visibility: visible;
            opacity: 1;
        }
        .tooltip-title { font-size: 10px; font-weight: 800; color: var(--primary-color); border-bottom: 1px solid var(--border-main); padding-bottom: 4px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .tooltip-row { display: flex; justify-content: space-between; align-items: center; font-size: 11px; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace; }
        .tooltip-acc-name { color: var(--text-main); font-weight: 600; font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 170px; font-family: 'Inter', sans-serif;}
        .tooltip-acc-val { font-weight: 800; font-size: 11px; color: #FFFFFF !important; }
    </style>
    """
    html_annual = f"{css_annual}<div class='annual-container'><div class='annual-grid'>"

    total_pnl_ano = 0.0
    meses_ganadores = 0
    meses_perdedores = 0

    for m in range(1, 13):
        m_name = MESES_ES[m-1]
        
        if not df_ano.empty:
            df_m_ops = df_ano[df_ano['fecha_dt'].dt.month == m]
        else:
            df_m_ops = pd.DataFrame()

        if not df_m_ops.empty:
            pnl_m = df_m_ops['resultado'].sum()
            tr_m = len(df_m_ops)
            pct_m = (pnl_m / tot_inicial * 100) if tot_inicial > 0 else 0.0
            
            total_pnl_ano += pnl_m

            df_diario_m = obtener_df_diario_clasificado(df_m_ops, cuentas_raw)
            if not df_diario_m.empty:
                w_days = len(df_diario_m[df_diario_m['clasificacion'] == 'WIN'])
                l_days = len(df_diario_m[df_diario_m['clasificacion'] == 'LOSS'])
                dias_op = len(df_diario_m)
            else:
                w_days, l_days, dias_op = 0, 0, 0

            acc_m_breakdown = []
            for acc_num, acc_grp in df_m_ops.groupby('account_number'):
                acc_pnl_m = acc_grp['resultado'].sum()
                acc_tr_m = len(acc_grp)
                acc_nm_m = acc_grp['nombre_cuenta'].iloc[0] if 'nombre_cuenta' in acc_grp.columns else str(acc_num)
                
                sym_m_breakdown = []
                for sym_name, sym_grp in acc_grp.groupby('simbolo'):
                    sym_pnl_m = sym_grp['resultado'].sum()
                    sym_tr_m = len(sym_grp)
                    sym_m_breakdown.append({
                        'symbol': sym_name,
                        'pnl': sym_pnl_m,
                        'trades': sym_tr_m
                    })

                acc_m_breakdown.append({
                    'name': acc_nm_m,
                    'pnl': acc_pnl_m,
                    'trades': acc_tr_m,
                    'symbols': sym_m_breakdown
                })

            if pnl_m > 0.01:
                card_cls = "win-month"
                pct_cls = "green"
                pnl_fmt = f"+${pnl_m:,.2f}"
                meses_ganadores += 1
            elif pnl_m < -0.01:
                card_cls = "loss-month"
                pct_cls = "red"
                pnl_fmt = f"-${abs(pnl_m):,.2f}"
                meses_perdedores += 1
            else:
                card_cls = ""
                pct_cls = "neutral"
                pnl_fmt = "$0.00"

            meta_str = f"{dias_op} días op. | <span style='color:var(--win-color); font-weight:700;'>{w_days}W</span> - <span style='color:var(--loss-color); font-weight:700;'>{l_days}L</span>"

            v_cls = "tooltip-down" if m <= 8 else "tooltip-up"

            if m in [1, 5, 9]:
                h_cls = "align-left"
            elif m in [4, 8, 12]:
                h_cls = "align-right"
            else:
                h_cls = "align-center"

            tooltip_m = f"<div class='month-tooltip {v_cls} {h_cls}'>"
            tooltip_m += f"<div class='tooltip-title'>📊 {m_name} {int(ano_sel_annual)}</div>"
            for acc_i in acc_m_breakdown:
                p_acc = acc_i['pnl']
                t_acc = acc_i['trades']
                n_acc = acc_i['name']
                s_str = "+" if p_acc > 0 else ""
                tooltip_m += f"""
                <div class='tooltip-row'>
                    <span class='tooltip-acc-name'><span style='color:var(--text-muted); font-weight:700;'>({t_acc} ops)</span> {n_acc}</span>
                    <span class='tooltip-acc-val'>{s_str}${p_acc:,.2f}</span>
                </div>
                """
                if mostrar_simbolos_cal and acc_i.get('symbols'):
                    tooltip_m += "<div style='margin-left:8px; margin-bottom:6px; padding-left:6px; border-left:1px solid var(--border-light);'>"
                    for s_info in acc_i['symbols']:
                        s_sym = s_info['symbol']
                        s_pnl = s_info['pnl']
                        s_tr = s_info['trades']
                        s_sign = "+" if s_pnl > 0 else ""
                        tooltip_m += f"""
                        <div class='tooltip-row' style='font-size:10px; color:var(--text-main); margin-bottom:2px;'>
                            <span style='font-family:Inter;'>↳ <b>{s_sym}</b> <span style='color:var(--text-muted);'>({s_tr} ops)</span></span>
                            <span style='font-weight:700;'>{s_sign}${s_pnl:,.2f}</span>
                        </div>
                        """
                    tooltip_m += "</div>"
            tooltip_m += "</div>"

            html_annual += f"""
            <div class='month-card {card_cls}'>
                {tooltip_m}
                <div class='month-header'>
                    <span class='month-title'>{m_name}</span>
                    <span class='month-pct {pct_cls}'>{pct_m:+.2f}%</span>
                </div>
                <div class='month-pnl'>{pnl_fmt}</div>
                <div class='month-meta'>{meta_str}</div>
            </div>
            """
        else:
            html_annual += f"""
            <div class='month-card'>
                <div class='month-header'>
                    <span class='month-title'>{m_name}</span>
                    <span class='month-pct neutral'>0.00%</span>
                </div>
                <div class='month-pnl'>$0.00</div>
                <div class='month-meta'>Sin operaciones</div>
            </div>
            """

    html_annual += "</div></div>"
    
    st.components.v1.html(html_annual, height=560, scrolling=True)

    # MÉTRICAS DEL AÑO SELECCIONADO
    pct_ano = (total_pnl_ano / tot_inicial * 100) if tot_inicial > 0 else 0.0

    mc_a1, mc_a2, mc_a3, mc_a4 = st.columns(4)
    mc_a1.metric("PnL Total del Año", f"${total_pnl_ano:,.2f}", delta=f"{pct_ano:+.2f}%")
    mc_a2.metric("% Rendimiento Año", f"{pct_ano:+.2f}%")
    mc_a3.metric("Meses Verdes (Win)", f"{meses_ganadores} meses")
    mc_a4.metric("Meses Rojos (Loss)", f"{meses_perdedores} meses")

# =============================================================================
# TAB 2: ESTADO DE CUENTAS & ANALYTICS (UNIFICADO)
# =============================================================================
with tab_estado_analytics:
    st.markdown("<h3 style='font-size:18px; font-weight:700;'><i class='fa-solid fa-layer-group' style='color:var(--blue-accent); margin-right:6px;'></i> Estado de Cuentas, Monitoreo & Analytics</h3>", unsafe_allow_html=True)
    
    if df_ops_trading.empty:
        st.info("ℹ️ No hay operaciones registradas para las cuentas seleccionadas.")
    else:
        # 1. RENDIMIENTO GLOBAL (Oculto por defecto en un toggle)
        if st.toggle("🌍 Mostrar Rendimiento Consolidado Global (Todas las Cuentas)", key="tgl_global_analytics"):
            filtro_periodo_global = st.radio(
                "📅 Rango Temporal Global:",
                options=["Último mes", "Últimos 3 meses", "Últimos 6 meses", "Último año", "Total (Inicio de vida)"],
                index=4,
                horizontal=True,
                key="analytics_global_period_filter"
            )
            
            hoy = datetime.date.today()
            if filtro_periodo_global == "Último mes":
                fecha_lim_g = hoy - datetime.timedelta(days=30)
            elif filtro_periodo_global == "Últimos 3 meses":
                fecha_lim_g = hoy - datetime.timedelta(days=90)
            elif filtro_periodo_global == "Últimos 6 meses":
                fecha_lim_g = hoy - datetime.timedelta(days=180)
            elif filtro_periodo_global == "Último año":
                fecha_lim_g = hoy - datetime.timedelta(days=365)
            else:
                fecha_lim_g = None

            df_global_filtered = df_ops_trading.copy()
            if fecha_lim_g:
                df_global_filtered = df_global_filtered[df_global_filtered['fecha_dia'] >= fecha_lim_g]

            if df_global_filtered.empty:
                st.warning("⚠️ No se encontraron operaciones en el periodo global seleccionado.")
            else:
                df_ops_sorted = df_global_filtered.sort_values("fecha_dt").copy()
                df_ops_sorted["cum_pnl"] = df_ops_sorted["resultado"].cumsum()
                
                tot_inicial_g = sum([c["balance_inicial"] for c in cuentas]) if cuentas else 0
                df_ops_sorted["balance_cum"] = tot_inicial_g + df_ops_sorted["cum_pnl"]

                df_diario_g = obtener_df_diario_clasificado(df_global_filtered, cuentas_raw)
                if not df_diario_g.empty:
                    wins_g = len(df_diario_g[df_diario_g['clasificacion'] == 'WIN'])
                    losses_g = len(df_diario_g[df_diario_g['clasificacion'] == 'LOSS'])
                    be_g = len(df_diario_g[df_diario_g['clasificacion'] == 'BE'])
                else:
                    wins_g, losses_g, be_g = 0, 0, 0

                min_bg = df_ops_sorted["balance_cum"].min()
                max_bg = df_ops_sorted["balance_cum"].max()
                diff_bg = max_bg - min_bg
                padding_g = max(diff_bg * 0.15, 100.0)
                y_range_g = [min_bg - padding_g, max_bg + padding_g]

                col_g1, col_g2 = st.columns([2, 1])

                with col_g1:
                    fig_balance = go.Figure()
                    fig_balance.add_trace(go.Scatter(
                        x=df_ops_sorted["fecha_dt"],
                        y=df_ops_sorted["balance_cum"],
                        mode='lines',
                        name='Balance Consolidado',
                        line=dict(color='#2962FF', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(41, 98, 255, 0.1)',
                        hovertemplate="<b>Fecha:</b> %{x|%Y-%m-%d}<br><b>Balance:</b> $%{y:,.2f}<extra></extra>"
                    ))
                    fig_balance.update_layout(
                        title=f'<b>Evolución de la Curva de Balance Consolidada ($)</b>',
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#E2E8F0', family='Inter'),
                        xaxis=dict(gridcolor='#1E293B', showgrid=True),
                        yaxis=dict(gridcolor='#1E293B', showgrid=True, range=y_range_g),
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=380
                    )
                    st.plotly_chart(fig_balance, use_container_width=True)

                with col_g2:
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=['Wins', 'Losses', 'BE'],
                        values=[wins_g, losses_g, be_g],
                        hole=.65,
                        marker=dict(colors=['#10B981', '#F43F5E', '#64748B'], line=dict(color='#0B0E14', width=2))
                    )])
                    fig_donut.update_layout(
                        title='<b>Distribución Win / Loss Global</b>',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#E2E8F0', family='Inter'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=380,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()

        # 2. LÓGICA DE ORDENAMIENTO (Fondeada+ > Challenge+ > Fondeada- > Challenge-)
        def obtener_llave_orden(c):
            bal_ini = float(c.get("balance_inicial", 0.0))
            bal_act = float(c.get("balance", 0.0))
            ganancia = bal_act - bal_ini
            estado_t = str(c.get("estado", "Fase 1")).lower()
            es_fondeada = ("fondeada" in estado_t or "funded" in estado_t)
            
            if es_fondeada and ganancia > 0:
                grupo = 1
            elif not es_fondeada and ganancia > 0:
                grupo = 2
            elif es_fondeada and ganancia <= 0:
                grupo = 3
            else:
                grupo = 4
                
            # Retornamos el grupo, y el negativo de la ganancia para ordenar de mayor a menor profit dentro del grupo
            return (grupo, -ganancia)

        cuentas_ordenadas = sorted(cuentas, key=obtener_llave_orden) if cuentas else []

        # 3. RENDERIZADO DE CUENTAS INDIVIDUALES
        if not cuentas_ordenadas:
            st.info("No hay cuentas seleccionadas.")
        else:
            for c in cuentas_ordenadas:
                acc_num_str = str(c["account_number"])
                acc_name = c["nombre_cuenta"]
                bal_ini = float(c.get("balance_inicial", 0.0))
                bal_act = float(c.get("balance", 0.0))
                equidad = float(c.get("equidad", 0.0))
                ganancia = bal_act - bal_ini
                pct_ganancia = (ganancia / bal_ini * 100) if bal_ini > 0 else 0
                
                p_max = float(c.get("perdida_diaria_max", 0.0))
                p_act = float(c.get("perdida_diaria_actual", 0.0))
                margen_max = p_max - p_act
                
                estado_tag = str(c.get("estado", "Fase 1"))
                es_fondeada = ("fondeada" in estado_tag.lower() or "funded" in estado_tag.lower())
                
                with st.expander(f"🔹 {acc_name.upper()} | ID #{acc_num_str} — [{estado_tag.upper()}] | Profit: ${ganancia:,.2f}", expanded=True):
                    
                    st.markdown(f"""
                    <div style="background-color: var(--bg-sec); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light); margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 20px; font-weight: 800; color: #FFFFFF; font-family: 'Inter', sans-serif;">{acc_name}</span>
                            <span style="font-size: 13px; color: var(--text-muted); margin-left: 12px; font-weight: 600; font-family:'JetBrains Mono', monospace;">ID #{acc_num_str}</span>
                        </div>
                        <div>
                            <span style="background-color: var(--primary-color); color: #FFFFFF; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase;">{estado_tag}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # KPI de Balance
                    col_c1, col_c2, col_c3 = st.columns(3)
                    
                    delta_bal = f"{ganancia:+,.2f} ({pct_ganancia:+.2f}%)" if ganancia != 0 else "$0.00"
                    col_c1.metric("Balance Actual", f"${bal_act:,.2f}", delta=delta_bal)
                    col_c1.caption(f"Equidad actual: ${equidad:,.2f}")
                    
                    delta_loss = f"-${p_act:,.2f}" if p_act > 0 else "Sin pérdidas"
                    col_c2.metric("Margen Pérdida Máxima", f"${margen_max:,.2f}", delta=delta_loss, delta_color="normal" if p_act > 0 else "off")
                    col_c2.caption(f"Límite máximo total: ${p_max:,.2f}")
                    
                    if not es_fondeada:
                        obj = float(c.get("objetivo_profit", 0.0))
                        pct_prog = min(max(ganancia / obj, 0.0), 1.0) if obj > 0 else 1.0
                        delta_obj = f"{ganancia:+,.2f} de {obj:,.2f}"
                        col_c3.metric("Objetivo Profit Target", f"${obj:,.2f}", delta=delta_obj)
                    else:
                        delta_payout = f"{ganancia:+,.2f}" if ganancia != 0 else "$0.00"
                        col_c3.metric("Beneficio Acumulado (Payout)", f"${ganancia:,.2f}", delta=delta_payout)
                    
                    # Barras de Progreso
                    if ganancia < 0:
                        str_ganancia = f"<span class='color-loss'>-${abs(ganancia):,.2f}</span>"
                    elif ganancia > 0:
                        str_ganancia = f"<span class='color-win'>+${ganancia:,.2f}</span>"
                    else:
                        str_ganancia = "$0.00"
                        
                    str_obj = f"${c.get('objetivo_profit', 0):,.2f}"
                    
                    if not es_fondeada:
                        pct_p_val = min(max(pct_prog * 100, 0.0), 100.0)
                        st.write("**Progreso hacia el Objetivo (Phase Pass):**")
                        st.markdown(f"""
                        <div style="background-color: var(--bg-sec); border: 1px solid var(--border-main); border-radius: 8px; padding: 3px; width: 100%; margin-top: 4px;">
                            <div style="background-color: var(--win-color); width: {pct_p_val:.1f}%; height: 14px; border-radius: 5px; transition: width 0.4s ease;"></div>
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-top: 6px; margin-bottom: 12px; font-family:'JetBrains Mono', monospace;">{pct_prog*100:.1f}% alcanzado ({str_ganancia} / {str_obj})</div>
                        """, unsafe_allow_html=True)
                    else:
                        st.caption("🟢 Cuenta Fondeada activa.")
                    
                    if p_act > 0:
                        str_p_act = f"<span class='color-loss'>-${p_act:,.2f}</span>"
                    else:
                        str_p_act = f"<span class='color-win'>$0.00</span>"
                        
                    str_p_max = f"${p_max:,.2f}"
                    pct_drawdown = min(max(p_act / p_max, 0.0), 1.0) if p_max > 0 else 0
                    pct_d_val = min(max(pct_drawdown * 100, 0.0), 100.0)
                    
                    st.write("**Límite de Pérdida Máxima Consumido:**")
                    st.markdown(f"""
                    <div style="background-color: var(--bg-sec); border: 1px solid var(--border-main); border-radius: 8px; padding: 3px; width: 100%; margin-top: 4px;">
                        <div style="background-color: var(--loss-color); width: {pct_d_val:.1f}%; height: 14px; border-radius: 5px; transition: width 0.4s ease;"></div>
                    </div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 6px; margin-bottom: 16px; font-family:'JetBrains Mono', monospace;">{pct_drawdown*100:.1f}% consumido ({str_p_act} / {str_p_max})</div>
                    """, unsafe_allow_html=True)

                    # ---------------------------------------------------------
                    # SECCIÓN COLAPSABLE: GRÁFICOS Y ANALYTICS
                    # ---------------------------------------------------------
                    st.markdown("<hr style='border-color: var(--border-light); margin: 8px 0;'>", unsafe_allow_html=True)
                    
                    if st.toggle(f"📊 Ver Gráficos y Analytics", key=f"tgl_charts_{acc_num_str}"):
                        acc_period_filter = st.radio(
                            f"📅 Rango Temporal:",
                            options=["Último mes", "Últimos 3 meses", "Últimos 6 meses", "Último año", "Total (Inicio de vida)"],
                            index=4,
                            horizontal=True,
                            key=f"period_filter_acc_{acc_num_str}"
                        )

                        hoy = datetime.date.today()
                        if acc_period_filter == "Último mes":
                            fecha_lim_acc = hoy - datetime.timedelta(days=30)
                        elif acc_period_filter == "Últimos 3 meses":
                            fecha_lim_acc = hoy - datetime.timedelta(days=90)
                        elif acc_period_filter == "Últimos 6 meses":
                            fecha_lim_acc = hoy - datetime.timedelta(days=180)
                        elif acc_period_filter == "Último año":
                            fecha_lim_acc = hoy - datetime.timedelta(days=365)
                        else:
                            fecha_lim_acc = None

                        df_acc_full = df_ops_trading[df_ops_trading["account_number"].astype(str) == acc_num_str].sort_values("fecha_dt").copy()

                        if fecha_lim_acc:
                            df_acc = df_acc_full[df_acc_full['fecha_dia'] >= fecha_lim_acc].copy()
                        else:
                            df_acc = df_acc_full.copy()

                        if df_acc.empty:
                            st.info("Sin operaciones registradas para esta cuenta en el periodo seleccionado.")
                        else:
                            df_acc["cum_pnl"] = df_acc["resultado"].cumsum()
                            df_acc["balance_cum"] = bal_ini + df_acc["cum_pnl"]

                            df_diario_acc = obtener_df_diario_clasificado(df_acc, cuentas_raw)
                            if not df_diario_acc.empty:
                                w_acc = len(df_diario_acc[df_diario_acc['clasificacion'] == 'WIN'])
                                l_acc = len(df_diario_acc[df_diario_acc['clasificacion'] == 'LOSS'])
                                be_acc = len(df_diario_acc[df_diario_acc['clasificacion'] == 'BE'])
                            else:
                                w_acc, l_acc, be_acc = 0, 0, 0

                            min_ba = df_acc["balance_cum"].min()
                            max_ba = df_acc["balance_cum"].max()
                            diff_ba = max_ba - min_ba
                            padding_a = max(diff_ba * 0.15, 50.0)
                            y_range_a = [min_ba - padding_a, max_ba + padding_a]

                            c_acc_1, c_acc_2 = st.columns([2, 1])

                            with c_acc_1:
                                fig_acc_bal = go.Figure()
                                fig_acc_bal.add_trace(go.Scatter(
                                    x=df_acc["fecha_dt"],
                                    y=df_acc["balance_cum"],
                                    mode='lines',
                                    name=f'Balance #{acc_num_str}',
                                    line=dict(color='#2962FF', width=2.5),
                                    fill='tozeroy',
                                    fillcolor='rgba(41, 98, 255, 0.1)',
                                    hovertemplate="<b>Fecha:</b> %{x|%Y-%m-%d}<br><b>Balance:</b> $%{y:,.2f}<extra></extra>"
                                ))
                                fig_acc_bal.update_layout(
                                    title=f'<b>Curva de Balance — {acc_name}</b>',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    font=dict(color='#E2E8F0', family='Inter'),
                                    xaxis=dict(gridcolor='#1E293B', showgrid=True),
                                    yaxis=dict(gridcolor='#1E293B', showgrid=True, range=y_range_a),
                                    margin=dict(l=20, r=20, t=40, b=20),
                                    height=300
                                )
                                st.plotly_chart(fig_acc_bal, use_container_width=True)

                            with c_acc_2:
                                fig_acc_donut = go.Figure(data=[go.Pie(
                                    labels=['Wins', 'Losses', 'BE'],
                                    values=[w_acc, l_acc, be_acc],
                                    hole=.65,
                                    marker=dict(colors=['#10B981', '#F43F5E', '#64748B'], line=dict(color='#161D2E', width=2))
                                )])
                                fig_acc_donut.update_layout(
                                    title=f'<b>Win/Loss (%)</b>',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    font=dict(color='#E2E8F0', family='Inter'),
                                    margin=dict(l=20, r=20, t=40, b=20),
                                    height=300,
                                    showlegend=True,
                                    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                                )
                                st.plotly_chart(fig_acc_donut, use_container_width=True)

                    # ---------------------------------------------------------
                    # SECCIÓN COLAPSABLE: RETIROS (Solo para Fondeadas)
                    # ---------------------------------------------------------
                    if es_fondeada:
                        if st.toggle("💸 Historial de Retiros & Profit Split (80%)", key=f"tgl_ret_{acc_num_str}"):
                            ops_acc = [
                                op for op in ops_raw 
                                if str(op.get("account_number")) == acc_num_str and str(op.get("tipo", "")).upper() == "WITHDRAWAL"
                            ]
                            
                            if not ops_acc:
                                st.info("Sin retiros registrados en MetaTrader 5 para esta cuenta.")
                            else:
                                tot_bruto_retirado = sum([abs(float(op.get("resultado", 0))) for op in ops_acc])
                                tot_neto_trader = tot_bruto_retirado * 0.80
                                
                                r_c1, r_c2 = st.columns(2)
                                r_c1.metric("Total Retirado (Bruto MT5)", f"${tot_bruto_retirado:,.2f}")
                                r_c2.metric("Retiro Neto Trader (Split 80%)", f"${tot_neto_trader:,.2f}", delta="80% a tu favor", delta_color="normal")
                                
                                st.markdown("---")
                                st.markdown("##### 📜 Desglose de Payouts:")
                                
                                df_ret = pd.DataFrame(ops_acc)
                                df_ret["bruto"] = df_ret["resultado"].apply(lambda x: abs(float(x)))
                                df_ret["neto_80"] = df_ret["bruto"] * 0.80
                                df_ret["fecha_clean"] = df_ret["fecha"].str.slice(0, 10)
                                
                                df_ret_show = df_ret[["fecha_clean", "bruto", "neto_80", "comentario"]].rename(columns={
                                    "fecha_clean": "Fecha",
                                    "bruto": "Monto Bruto ($)",
                                    "neto_80": "Neto Trader 80% ($)",
                                    "comentario": "Detalle / Referencia"
                                })
                                
                                st.dataframe(
                                    df_ret_show.style.format({
                                        "Monto Bruto ($)": "${:,.2f}",
                                        "Neto Trader 80% ($)": "${:,.2f}"
                                    }),
                                    use_container_width=True,
                                    hide_index=True
                                )
# =============================================================================
# TAB 4: HISTORIAL DE OPERACIONES DIARIAS & TABLA CON COLUMNA DE SÍMBOLO
# =============================================================================
with tab_trades:
    st.markdown("<h3 style='font-size:18px; font-weight:700;'><i class='fa-solid fa-receipt' style='color:var(--blue-accent); margin-right:6px;'></i> Historial & Analítica de Operaciones</h3>", unsafe_allow_html=True)
    st.caption("Filtra y revisa las sesiones por fecha, cuenta, símbolo y estado.")
    
    hoy = datetime.date.today()
    lunes_semana_actual = hoy - datetime.timedelta(days=hoy.weekday())
    
    col_f1, col_f2 = st.columns([2, 2])
    
    with col_f1:
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
        
    if df_ops_trading.empty:
        st.info("No hay operaciones registradas para las cuentas seleccionadas.")
    else:
        df_diario = obtener_df_diario_clasificado(df_ops_trading, cuentas_raw)
        
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
                    color_discrete_map={'WIN': '#10B981', 'LOSS': '#F43F5E', 'BE': '#64748B'},
                    text=acc_stats['pct_cuenta'].apply(lambda x: f"{x:.0f}%")
                )
                fig_hbar.update_layout(
                    barmode='stack',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#E2E8F0', family='Inter'),
                    xaxis=dict(title="% del Total de Días Operados", gridcolor='#1E293B', range=[0, 100]),
                    yaxis=dict(title="", gridcolor='#1E293B'),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=330,
                    showlegend=True
                )
                st.plotly_chart(fig_hbar, use_container_width=True)
                
            with chart_col2:
                tot_counts = df_filtered_tab4["clasificacion"].value_counts().reset_index()
                tot_counts.columns = ["clasificacion", "cantidad"]
                
                color_map = {'WIN': '#10B981', 'LOSS': '#F43F5E', 'BE': '#64748B'}
                tot_counts['color'] = tot_counts['clasificacion'].map(color_map)
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=tot_counts['clasificacion'],
                    values=tot_counts['cantidad'],
                    hole=.5,
                    marker=dict(colors=tot_counts['color'], line=dict(color='#0B0E14', width=2)),
                    textinfo='label+percent+value',
                    hovertemplate="%{label}: %{value} días (%{percent})<extra></extra>"
                )])
                fig_pie.update_layout(
                    title="<b>Total Periodo Filtrado (Días & %)</b>",
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#E2E8F0', family='Inter'),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=330,
                    showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
            st.divider()
            
            st.markdown("<h3 style='font-size:16px; font-weight:700;'><i class='fa-solid fa-list-check' style='color:var(--blue-accent); margin-right:6px;'></i> Detalle de Sesiones Diarias & Capturas</h3>", unsafe_allow_html=True)
            st.caption("Tabla de historial alineada. Haz clic en el botón de estado para abrir las capturas.")
            
            hdr_c1, hdr_c2, hdr_c3, hdr_c4, hdr_c5, hdr_c6, hdr_c7 = st.columns([1.0, 1.5, 1.1, 1.2, 1.2, 1.0, 1.5])
            hdr_c1.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>FECHA</span>", unsafe_allow_html=True)
            hdr_c2.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>CUENTA</span>", unsafe_allow_html=True)
            hdr_c3.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>ID CUENTA</span>", unsafe_allow_html=True)
            hdr_c4.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>SÍMBOLO</span>", unsafe_allow_html=True)
            hdr_c5.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>RESULTADO ($)</span>", unsafe_allow_html=True)
            hdr_c6.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>% REND.</span>", unsafe_allow_html=True)
            hdr_c7.markdown("<span style='color:var(--text-muted); font-size:11px; font-weight:700; font-family:JetBrains Mono;'>ESTADO / CAPTURAS</span>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 6px 0 10px 0; border-color: var(--border-light);'>", unsafe_allow_html=True)

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
                    if str(op.get("account_number")) == acc_id_str and str(op.get("fecha", "")).startswith(f_str) and str(op.get("tipo", "")).upper() != "WITHDRAWAL"
                ]
                
                op_row = matching_ops[0] if matching_ops else {
                    "account_number": acc_id_str,
                    "fecha": f_str,
                    "nombre_cuenta": acc_name,
                    "resultado": res_num
                }

                simbolos_list = list(set([str(op.get("simbolo", "N/A")).strip().upper() for op in matching_ops if op.get("simbolo") and str(op.get("simbolo")).upper() != "N/A"]))
                simbolo_str = ", ".join(simbolos_list) if simbolos_list else "N/A"
                
                capturas_list = parse_capturas(op_row.get("capturas"))
                num_caps = len(capturas_list)
                
                if clasif == "WIN":
                    badge = f"🟩 WIN ({num_caps})"
                    res_html = f"<span class='color-win'>+${res_num:,.2f}</span>"
                    pct_html = f"<span class='color-win'>+{pct_num:.2f}%</span>"
                elif clasif == "LOSS":
                    badge = f"🟥 LOSS ({num_caps})"
                    res_html = f"<span class='color-loss'>-${abs(res_num):,.2f}</span>"
                    pct_html = f"<span class='color-loss'>{pct_num:.2f}%</span>"
                else:
                    badge = f"⚪ BE ({num_caps})"
                    res_html = f"<span>${res_num:,.2f}</span>"
                    pct_html = f"<span>{pct_num:.2f}%</span>"

                row_key = f"pop_{acc_id_str}_{f_str}_{idx}"
                
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1.0, 1.5, 1.1, 1.2, 1.2, 1.0, 1.5])
                
                with c1:
                    st.markdown(f"<span style='font-size:13px; font-family:JetBrains Mono;'>{f_str}</span>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<span style='font-size:13px; font-weight:600;'>{acc_name}</span>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<code style='background:var(--bg-sec); color:var(--text-muted); padding:2px 6px; border-radius:4px; font-family:JetBrains Mono;'>#{acc_id_str}</code>", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<span style='font-size:12px; font-weight:700; color:#06B6D4;'>{simbolo_str}</span>", unsafe_allow_html=True)
                with c5:
                    st.markdown(res_html, unsafe_allow_html=True)
                with c6:
                    st.markdown(pct_html, unsafe_allow_html=True)
                with c7:
                    with st.popover(badge, use_container_width=True):
                        st.markdown(f"### 📊 Sesión: {acc_name} (`#{acc_id_str}`)")
                        st.markdown(f"**Fecha:** `{f_str}` | **Símbolo(s):** `{simbolo_str}` | **Resultado Neto:** {res_html} ({pct_html})", unsafe_allow_html=True)
                        
                        tot_comm = sum([float(op.get("comision_calc", 0)) for op in matching_ops])
                        tot_swap = sum([float(op.get("swap_calc", 0)) for op in matching_ops])
                        raw_prof = sum([float(op.get("raw_profit", 0)) for op in matching_ops])
                        
                        if tot_comm > 0 or tot_swap != 0:
                            st.info(f"💵 **Desglose de la Sesión:** Bruto: **${raw_prof:,.2f}** | Comisiones: **-${tot_comm:,.2f}** | Swap: **${tot_swap:,.2f}** ➔ **Neto: ${res_num:,.2f}**")
                        else:
                            st.info("ℹ️ Registro de sesión sin comisiones aplicadas.")
                            
                        st.markdown("---")
                        
                        st.markdown(f"##### 🖼️ Capturas de Pantalla ({num_caps})")
                        if capturas_list:
                            grid_cols = st.columns(min(len(capturas_list), 2))
                            for c_idx, cap in enumerate(capturas_list):
                                target_col = grid_cols[c_idx % 2]
                                with target_col:
                                    st.markdown(f"**Captura {c_idx+1}: {cap.get('tipo', 'Gráfico')}**")
                                    img_src = cap.get("url") or cap.get("base64")
                                    if img_src:
                                        st.markdown(f"""
                                        <div style="width:100%; overflow:auto; text-align:center; -webkit-overflow-scrolling:touch;">
                                            <img src="{img_src}" style="max-width:100%; height:auto; touch-action: pan-x pan-y pinch-zoom !important; border-radius:6px; margin-bottom:8px;" />
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
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
                
                st.markdown("<hr style='margin: 4px 0; border-color: var(--border-main);'>", unsafe_allow_html=True)
