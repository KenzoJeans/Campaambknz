import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO, StringIO
from plotly.subplots import make_subplots
import re
import requests
import time

# ─── Configuración de la página ─────────────────────────────────────────────
st.set_page_config(
    page_title="Campañas Ambientales — Planta y Tiendas",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #1a6b3c 0%, #2e9e5b 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .main-header h1 { margin: 0; font-size: 1.4rem; font-weight: 600; }
    .kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.8rem 1rem; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
    .kpi-label { font-size: 0.75rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { font-size: 1.6rem; font-weight: 600; margin: 0.2rem 0; }
    .section-title { font-size: 1rem; font-weight: 600; color: #1e293b; border-left: 4px solid #2e9e5b; padding-left: 0.6rem; margin: 1rem 0 0.6rem; }
</style>
""", unsafe_allow_html=True)

# ─── IDs por defecto (los que indicaste) ────────────────────────────────────
GSHEET_PLANTA_ID = "1fBG1FJuFwly_k6_HSwtP56eyoMehPAVrJlRbbfR8oGk"
GSHEET_TIENDAS_ID = "1S3q6Gzz-2DAmcdSSBbd5b6P82tb3SGgBexqkObmIG5Q"

def build_export_url(sheet_id: str, gid: str = None) -> str:
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    if gid:
        return f"{base}&gid={gid}"
    return base

# ─── Utilidades ────────────────────────────────────────────────────────────
def normalize_col(c: str) -> str:
    return str(c).strip().lower()

def find_campaign_cols(df_cols):
    mapping = {"botellas": None, "tapas": None, "aceite": None}
    for c in df_cols:
        cn = normalize_col(c)
        if "botella" in cn or "botellas" in cn:
            mapping["botellas"] = c
        if "tapa" in cn or "tapas" in cn:
            mapping["tapas"] = c
        if "aceite" in cn or "green fuel" in cn:
            mapping["aceite"] = c
    return mapping

def extract_numeric_weight(val):
    if pd.isna(val):
        return 0.0
    try:
        return float(val)
    except Exception:
        s = str(val)
        m = re.search(r"(\d+[.,]?\d*)", s)
        if m:
            return float(m.group(1).replace(",", "."))
    return 0.0

# ─── Lectura robusta de Google Sheets (con cache control) ────────────────
@st.cache_data
def load_gsheet_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"Error al descargar CSV. status_code={resp.status_code}. URL: {url}")
    text = resp.text
    if text.lstrip().startswith("<"):
        snippet = text[:1000].replace("\n", " ")
        raise RuntimeError(f"El contenido descargado parece HTML (posible página de login). Fragmento: {snippet}")
    df = pd.read_csv(StringIO(text))
    df.columns = [str(c).strip() for c in df.columns]
    return df

# ─── Sidebar: URL editable y control de recarga ────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 Panel de control — Campañas Ambientales")
    st.markdown("---")
    st.markdown("Si la lectura automática falla, pega aquí la URL de exportación CSV (export?format=csv&gid=...).")
    default_planta_url = build_export_url(GSHEET_PLANTA_ID)
    default_tiendas_url = build_export_url(GSHEET_TIENDAS_ID)
    gsheet_planta_url = st.text_input("URL CSV Planta", value=default_planta_url)
    gsheet_tiendas_url = st.text_input("URL CSV Tiendas", value=default_tiendas_url)
    st.markdown("---")
    st.caption("Asegúrate de que la hoja sea visible para 'Cualquiera con el enlace' o publica la hoja.")
    st.markdown("---")
    if "planta_cache_bust" not in st.session_state:
        st.session_state.planta_cache_bust = ""
    if "tiendas_cache_bust" not in st.session_state:
        st.session_state.tiendas_cache_bust = ""
    if st.button("🔄 Forzar recarga Planta"):
        st.session_state.planta_cache_bust = f"&cache_bust={int(time.time())}"
    if st.button("🔄 Forzar recarga Tiendas"):
        st.session_state.tiendas_cache_bust = f"&cache_bust={int(time.time())}"

# ─── Cargar datos con manejo de errores y mensajes claros ──────────────────
load_errors = []
def try_load(url):
    try:
        df = load_gsheet_csv(url)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

planta_url_effective = gsheet_planta_url + st.session_state.get("planta_cache_bust", "")
tiendas_url_effective = gsheet_tiendas_url + st.session_state.get("tiendas_cache_bust", "")

df_planta_raw, err_p = try_load(planta_url_effective)
if err_p:
    if "gid=" not in gsheet_planta_url:
        try_url = build_export_url(GSHEET_PLANTA_ID, gid="0") + st.session_state.get("planta_cache_bust", "")
        df_planta_raw, err_p2 = try_load(try_url)
        if err_p2:
            load_errors.append(("Planta", err_p2))
        else:
            planta_url_effective = try_url
    else:
        load_errors.append(("Planta", err_p))

df_tiendas_raw, err_t = try_load(tiendas_url_effective)
if err_t:
    if "gid=" not in gsheet_tiendas_url:
        try_url = build_export_url(GSHEET_TIENDAS_ID, gid="0") + st.session_state.get("tiendas_cache_bust", "")
        df_tiendas_raw, err_t2 = try_load(try_url)
        if err_t2:
            load_errors.append(("Tiendas", err_t2))
        else:
            tiendas_url_effective = try_url
    else:
        load_errors.append(("Tiendas", err_t))

if load_errors:
    for source, msg in load_errors:
        st.sidebar.error(f"{source}: {msg}")

# ─── Preparar y limpiar cada dataset (con columna fecha preservada) ───────
def detect_date_column(cols):
    for c in cols:
        cn = normalize_col(c)
        if "marca temporal" in cn or "timestamp" in cn or "fecha" in cn or "date" in cn:
            return c
    return None

def prepare_planta(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = df.columns.tolist()
    date_col = detect_date_column(cols)
    # parse date if exists
    fecha_series = None
    if date_col and date_col in df.columns:
        fecha_series = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    # remove marca temporal column from later heuristics but keep parsed fecha
    df_work = df.copy()
    if date_col:
        # keep original for debugging but drop from columns used to detect name/area
        df_work = df_work.drop(columns=[date_col])
    # Detect name and area
    name_col = None
    area_col = None
    for c in df_work.columns:
        cn = normalize_col(c)
        if "nombre" in cn and name_col is None:
            name_col = c
        if ("área" in cn or "area" in cn or "pertenece" in cn) and area_col is None:
            area_col = c
    remaining = [c for c in df_work.columns if c not in ([name_col] if name_col else []) + ([area_col] if area_col else [])]
    if name_col is None and len(remaining) >= 1:
        name_col = remaining[0]
    if area_col is None and len(remaining) >= 2:
        area_col = remaining[1]
    if area_col is None and len(df_work.columns) > 1:
        area_col = df_work.columns[1]
    camp_map = find_campaign_cols(df.columns)  # use original df columns to find campaign cols
    df_proc = pd.DataFrame()
    df_proc["nombre"] = df[name_col].astype(str).fillna("Sin nombre") if name_col in df.columns else "Sin nombre"
    df_proc["area"] = df[area_col].astype(str).fillna("Sin área") if area_col in df.columns else "Sin área"
    for key, col in camp_map.items():
        if col is not None and col in df.columns:
            df_proc[key] = df[col].apply(extract_numeric_weight)
        else:
            df_proc[key] = 0.0
    df_proc["total_kg"] = df_proc[["botellas", "tapas", "aceite"]].sum(axis=1)
    # attach fecha if parsed
    if fecha_series is not None:
        # align by index
        fecha_series = fecha_series.reset_index(drop=True)
        df_proc = df_proc.reset_index(drop=True)
        if len(fecha_series) == len(df_proc):
            df_proc["fecha"] = fecha_series
        else:
            # if lengths differ, still try to add NaT column
            df_proc["fecha"] = pd.NaT
    else:
        df_proc["fecha"] = pd.NaT
    return df_proc

def prepare_tiendas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = df.columns.tolist()
    date_col = detect_date_column(cols)
    fecha_series = None
    if date_col and date_col in df.columns:
        fecha_series = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    df_work = df.copy()
    if date_col:
        df_work = df_work.drop(columns=[date_col])
    tienda_col = None
    for c in df_work.columns:
        if "tienda" in normalize_col(c):
            tienda_col = c
            break
    if tienda_col is None:
        tienda_col = df_work.columns[0]
    camp_map = find_campaign_cols(df.columns)
    df_proc = pd.DataFrame()
    df_proc["tienda"] = df[tienda_col].astype(str).fillna("Sin tienda")
    for key, col in camp_map.items():
        if col is not None and col in df.columns:
            df_proc[key] = df[col].apply(extract_numeric_weight)
        else:
            df_proc[key] = 0.0
    df_proc["total_kg"] = df_proc[["botellas", "tapas", "aceite"]].sum(axis=1)
    if fecha_series is not None:
        fecha_series = fecha_series.reset_index(drop=True)
        df_proc = df_proc.reset_index(drop=True)
        if len(fecha_series) == len(df_proc):
            df_proc["fecha"] = fecha_series
        else:
            df_proc["fecha"] = pd.NaT
    else:
        df_proc["fecha"] = pd.NaT
    return df_proc

df_planta = prepare_planta(df_planta_raw)
df_tiendas = prepare_tiendas(df_tiendas_raw)

# ─── Interfaz con pestañas ──────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Campañas Ambientales Planta", "Campañas Ambientales Tiendas"])

# ------------------ PESTAÑA 1: PLANTA --------------------------------------
with tab1:
    st.markdown('<div class="main-header"><h1>Campañas Ambientales — Planta</h1></div>', unsafe_allow_html=True)

    if df_planta.empty:
        st.warning("No hay datos disponibles para Planta.")
        st.info("Si la hoja no es pública o requiere login, pega la URL de exportación CSV con gid en la barra lateral.")
    else:
        # Fecha filter using 'fecha' column if available
        if "fecha" in df_planta.columns and df_planta["fecha"].notna().any():
            min_f = df_planta["fecha"].min().date()
            max_f = df_planta["fecha"].max().date()
            rango = st.date_input("Rango de fechas (Planta)", value=(min_f, max_f), min_value=min_f, max_value=max_f)
            if isinstance(rango, (list, tuple)) and len(rango) == 2:
                df_filtered = df_planta[(df_planta["fecha"].dt.date >= rango[0]) & (df_planta["fecha"].dt.date <= rango[1])].copy()
            else:
                df_filtered = df_planta.copy()
        else:
            df_filtered = df_planta.copy()

        areas = sorted(df_filtered["area"].dropna().unique().tolist())
        sel_areas = st.multiselect("Filtrar por Área", options=areas, default=areas)
        dfp = df_filtered[df_filtered["area"].isin(sel_areas)].copy()

        if dfp.empty:
            st.info("No hay registros después de aplicar filtros.")
        else:
            total_kg = dfp["total_kg"].sum()
            grouped_person = dfp.groupby("nombre")["total_kg"].sum()
            n_personas = int(grouped_person.size) if not grouped_person.empty else 0
            avg_kg_por_persona = float(grouped_person.mean()) if n_personas > 0 else 0.0
            n_registros = len(dfp)

            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Total recolectado (kg)</div>'
                f'<div class="kpi-value">{total_kg:.1f} kg</div></div>',
                unsafe_allow_html=True
            )
            col2.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Promedio por persona (kg)</div>'
                f'<div class="kpi-value">{avg_kg_por_persona:.2f}</div></div>',
                unsafe_allow_html=True
            )
            col3.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Personas registradas</div>'
                f'<div class="kpi-value">{n_personas}</div></div>',
                unsafe_allow_html=True
            )
            col4.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Registros</div>'
                f'<div class="kpi-value">{n_registros}</div></div>',
                unsafe_allow_html=True
            )

        # Rankings Top 10 por persona (orden descendente: mayor arriba)
        st.markdown('<div class="section-title">Ranking Top 10 por persona (kg) — Planta</div>', unsafe_allow_html=True)
        campaigns = [("botellas", "Botellas con amor"), ("tapas", "Tapas para sanar"), ("aceite", "Aceite Green Fuel")]
        cols = st.columns(3)
        for i, (key, label) in enumerate(campaigns):
            with cols[i]:
                grp = dfp.groupby("nombre")[key].sum().reset_index().sort_values(key, ascending=False).head(10)
                if grp.empty:
                    st.info(f"No hay datos para {label}")
                else:
                    # ensure descending order with highest at top
                    grp = grp.sort_values(key, ascending=True)  # for horizontal bar, reverse axis
                    fig = px.bar(grp, x=key, y="nombre", orientation="h", text=key,
                                 labels={key: "Kg", "nombre": "Persona"}, title=f"Top 10 personas — {label}")
                    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                    fig.update_layout(height=380, margin=dict(l=80, r=20, t=40, b=20))
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)

        # Rankings Top 10 por área (orden descendente: mayor arriba)
        st.markdown('<div class="section-title">Ranking Top 10 por área (kg) — Planta</div>', unsafe_allow_html=True)
        cols2 = st.columns(3)
        for i, (key, label) in enumerate(campaigns):
            with cols2[i]:
                grp = dfp.groupby("area")[key].sum().reset_index().sort_values(key, ascending=False).head(10)
                if grp.empty:
                    st.info(f"No hay datos para {label}")
                else:
                    grp = grp.sort_values(key, ascending=True)
                    fig = px.bar(grp, x=key, y="area", orientation="h", text=key,
                                 labels={key: "Kg", "area": "Área"}, title=f"Top 10 áreas — {label}")
                    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                    fig.update_layout(height=380, margin=dict(l=80, r=20, t=40, b=20))
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)

        # Heatmap: área vs campañas (suma de kg)
        st.markdown('<div class="section-title">Mapa de calor: Kg recolectados por Área y Campaña — Planta</div>', unsafe_allow_html=True)
        heat_df = dfp.groupby("area")[["botellas", "tapas", "aceite"]].sum().reset_index()
        if heat_df.empty:
            st.info("No hay datos suficientes para el mapa de calor de Planta.")
        else:
            heat_mat = heat_df.set_index("area")[["botellas", "tapas", "aceite"]]
            fig_heat = px.imshow(heat_mat,
                                 labels=dict(x="Campaña", y="Área", color="Kg recolectados"),
                                 x=heat_mat.columns.tolist(),
                                 y=heat_mat.index.tolist(),
                                 color_continuous_scale=["#ef4444", "#f59e0b", "#2e9e5b"],
                                 text_auto=".1f",
                                 aspect="auto",
                                 title="Kg recolectados por Área y Campaña (Planta)")
            fig_heat.update_layout(height=420, margin=dict(l=120, r=20, t=60, b=20))
            st.plotly_chart(fig_heat, use_container_width=True)

        # Pie chart total por campaña
        st.markdown('<div class="section-title">Distribución total (kg) por campaña — Planta</div>', unsafe_allow_html=True)
        totals = {"Botellas": dfp["botellas"].sum(), "Tapas": dfp["tapas"].sum(), "Aceite": dfp["aceite"].sum()}
        pie_df = pd.DataFrame({"campaña": list(totals.keys()), "kg": list(totals.values())})
        fig_pie = px.pie(pie_df, names="campaña", values="kg", title="Kg recolectados por campaña", hole=0.4,
                         color="campaña", color_discrete_map={"Botellas":"#2e9e5b","Tapas":"#f59e0b","Aceite":"#ef4444"})
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Tabla detallada
        st.markdown('<div class="section-title">Registros detallados — Planta</div>', unsafe_allow_html=True)
        df_table = dfp.copy()
        df_table = df_table.rename(columns={"nombre":"Nombre", "area":"Área", "botellas":"Botellas (kg)", "tapas":"Tapas (kg)", "aceite":"Aceite (kg)", "total_kg":"Total (kg)", "fecha":"Fecha"})
        if "Fecha" in df_table.columns:
            df_table["Fecha"] = pd.to_datetime(df_table["Fecha"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(df_table.sort_values("Total (kg)", ascending=False), use_container_width=True, height=320)

# ------------------ PESTAÑA 2: TIENDAS -------------------------------------
with tab2:
    st.markdown('<div class="main-header"><h1>Campañas Ambientales — Tiendas</h1></div>', unsafe_allow_html=True)

    if df_tiendas.empty:
        st.warning("No hay datos disponibles para Tiendas.")
        st.info("Si la hoja no es pública o requiere login, pega la URL de exportación CSV con gid en la barra lateral.")
    else:
        # Fecha filter using 'fecha' column if available
        if "fecha" in df_tiendas.columns and df_tiendas["fecha"].notna().any():
            min_f = df_tiendas["fecha"].min().date()
            max_f = df_tiendas["fecha"].max().date()
            rango_t = st.date_input("Rango de fechas (Tiendas)", value=(min_f, max_f), min_value=min_f, max_value=max_f, key="rango_tiendas")
            if isinstance(rango_t, (list, tuple)) and len(rango_t) == 2:
                df_t_filtered = df_tiendas[(df_tiendas["fecha"].dt.date >= rango_t[0]) & (df_tiendas["fecha"].dt.date <= rango_t[1])].copy()
            else:
                df_t_filtered = df_tiendas.copy()
        else:
            df_t_filtered = df_tiendas.copy()

        tiendas = sorted(df_t_filtered["tienda"].dropna().unique().tolist())
        sel_tiendas = st.multiselect("Filtrar por Tienda", options=tiendas, default=tiendas)
        dft = df_t_filtered[df_t_filtered["tienda"].isin(sel_tiendas)].copy()

        if dft.empty:
            st.info("No hay registros después de aplicar filtros en Tiendas.")
        else:
            total_kg_t = dft["total_kg"].sum()
            grouped_tienda = dft.groupby("tienda")["total_kg"].sum()
            n_tiendas = int(grouped_tienda.size) if not grouped_tienda.empty else 0
            avg_kg_por_tienda = float(grouped_tienda.mean()) if n_tiendas > 0 else 0.0
            n_registros_t = len(dft)

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Total recolectado (kg)</div><div class="kpi-value">{total_kg_t:.1f} kg</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Promedio por tienda (kg)</div><div class="kpi-value">{avg_kg_por_tienda:.2f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="kpi-card"><div class="kpi-label">Tiendas registradas</div><div class="kpi-value">{n_tiendas}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Registros</div><div class="kpi-value">{n_registros_t}</div></div>', unsafe_allow_html=True)

        # Ranking Top 10 por tienda para cada campaña (orden descendente: mayor arriba)
        st.markdown('<div class="section-title">Ranking Top 10 por tienda (kg)</div>', unsafe_allow_html=True)
        campaigns = [("botellas", "Botellas con amor"), ("tapas", "Tapas para sanar"), ("aceite", "Aceite Green Fuel")]
        cols_t = st.columns(3)
        for i, (key, label) in enumerate(campaigns):
            with cols_t[i]:
                grp = dft.groupby("tienda")[key].sum().reset_index().sort_values(key, ascending=False).head(10)
                if grp.empty:
                    st.info(f"No hay datos para {label}")
                else:
                    grp = grp.sort_values(key, ascending=True)
                    fig = px.bar(grp, x=key, y="tienda", orientation="h", text=key,
                                 labels={key: "Kg", "tienda": "Tienda"}, title=f"Top 10 tiendas — {label}")
                    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                    fig.update_layout(height=380, margin=dict(l=80, r=20, t=40, b=20))
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)

        # Heatmap: tienda vs campañas (suma de kg)
        st.markdown('<div class="section-title">Mapa de calor: Kg recolectados por Tienda y Campaña — Tiendas</div>', unsafe_allow_html=True)
        heat_df_t = dft.groupby("tienda")[["botellas", "tapas", "aceite"]].sum().reset_index()
        if heat_df_t.empty:
            st.info("No hay datos suficientes para el mapa de calor de Tiendas.")
        else:
            heat_mat_t = heat_df_t.set_index("tienda")[["botellas", "tapas", "aceite"]]
            fig_heat_t = px.imshow(heat_mat_t,
                                   labels=dict(x="Campaña", y="Tienda", color="Kg recolectados"),
                                   x=heat_mat_t.columns.tolist(),
                                   y=heat_mat_t.index.tolist(),
                                   color_continuous_scale=["#ef4444", "#f59e0b", "#2e9e5b"],
                                   text_auto=".1f",
                                   aspect="auto",
                                   title="Kg recolectados por Tienda y Campaña (Tiendas)")
            fig_heat_t.update_layout(height=420, margin=dict(l=140, r=20, t=60, b=20))
            st.plotly_chart(fig_heat_t, use_container_width=True)

        # Pie chart total por campaña en Tiendas
        st.markdown('<div class="section-title">Distribución total (kg) por campaña — Tiendas</div>', unsafe_allow_html=True)
        totals_t = {"Botellas": dft["botellas"].sum(), "Tapas": dft["tapas"].sum(), "Aceite": dft["aceite"].sum()}
        pie_df_t = pd.DataFrame({"campaña": list(totals_t.keys()), "kg": list(totals_t.values())})
        fig_pie_t = px.pie(pie_df_t, names="campaña", values="kg", title="Kg recolectados por campaña (Tiendas)", hole=0.4,
                           color="campaña", color_discrete_map={"Botellas":"#2e9e5b","Tapas":"#f59e0b","Aceite":"#ef4444"})
        fig_pie_t.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie_t, use_container_width=True)

        # Tabla detallada Tiendas
        st.markdown('<div class="section-title">Registros detallados — Tiendas</div>', unsafe_allow_html=True)
        df_table_t = dft.copy()
        df_table_t = df_table_t.rename(columns={"tienda":"Tienda", "botellas":"Botellas (kg)", "tapas":"Tapas (kg)", "aceite":"Aceite (kg)", "total_kg":"Total (kg)", "fecha":"Fecha"})
        if "Fecha" in df_table_t.columns:
            df_table_t["Fecha"] = pd.to_datetime(df_table_t["Fecha"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(df_table_t.sort_values("Total (kg)", ascending=False), use_container_width=True, height=320)

# ─── Exportar datos procesados (ambas pestañas) ─────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Exportar datos procesados</div>', unsafe_allow_html=True)

@st.cache_data
def to_excel_combined(df1: pd.DataFrame, df2: pd.DataFrame):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not df1.empty:
            df1.to_excel(writer, index=False, sheet_name="Planta")
            resumen1 = df1.groupby("area").agg(n_registros=("nombre","count"), kg_total=("total_kg","sum")).reset_index()
            resumen1.to_excel(writer, index=False, sheet_name="Resumen_Planta")
        if not df2.empty:
            df2.to_excel(writer, index=False, sheet_name="Tiendas")
            resumen2 = df2.groupby("tienda").agg(n_registros=("total_kg","count"), kg_total=("total_kg","sum")).reset_index()
            resumen2.to_excel(writer, index=False, sheet_name="Resumen_Tiendas")
    return output.getvalue()

excel_bytes = to_excel_combined(df_planta, df_tiendas)
st.download_button(label="⬇️ Descargar Excel procesado (Planta + Tiendas)", data=excel_bytes,
                   file_name="campanas_ambientales_procesadas.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.caption("Dashboard adaptado para Campañas Ambientales — Planta y Tiendas. Basado en el diseño original y adaptado a las columnas indicadas.")
