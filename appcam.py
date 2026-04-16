"""
Dashboard - Campañas Ambientales
Botellas con Amor | Tapas para Sanar | Aceite Green Fuel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
from datetime import datetime, date

# ──────────────────────────────────────────────
# CONFIGURACIÓN PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Campañas Ambientales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CONSTANTES / URL POR DEFECTO
# ──────────────────────────────────────────────
DEFAULT_SHEET = "https://docs.google.com/spreadsheets/d/157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8"
# Asegurar formato export CSV
def ensure_csv_export(url: str) -> str:
    if "export?format=csv" in url:
        return url
    if "/edit#gid=" in url:
        return url.replace("/edit#gid=", "/export?format=csv&gid=")
    if "/edit?usp=sharing" in url:
        return url.replace("/edit?usp=sharing", "/export?format=csv")
    return url.rstrip("/") + "/export?format=csv"

DEFAULT_URL = ensure_csv_export(DEFAULT_SHEET)

# ──────────────────────────────────────────────
# ESTILOS CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1a6b3c, #2ecc71, #27ae60);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        font-family: 'Montserrat', sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border: 1px solid #bbf7d0;
        border-left: 4px solid #16a34a;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #15803d;
        font-family: 'Montserrat', sans-serif;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #4b5563;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .section-header {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #1a6b3c;
        border-bottom: 2px solid #bbf7d0;
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }
    .stPlotlyChart { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PALETA DE COLORES
# ──────────────────────────────────────────────
PALETTE_GREEN  = ["#064e3b", "#065f46", "#047857", "#059669", "#10b981",
                  "#34d399", "#6ee7b7", "#a7f3d0", "#d1fae5", "#ecfdf5"]
PALETTE_BLUE   = ["#1e3a5f", "#1e40af", "#1d4ed8", "#2563eb", "#3b82f6",
                  "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe", "#eff6ff"]
PALETTE_MULTI  = ["#059669", "#2563eb", "#d97706", "#dc2626", "#7c3aed",
                  "#0891b2", "#be185d", "#65a30d", "#0f766e", "#c2410c"]
COLOR_BOTELLAS = "#059669"
COLOR_TAPAS    = "#2563eb"
COLOR_ACEITE   = "#d97706"

# ──────────────────────────────────────────────
# MAPEO GRUPOS ADMINISTRATIVOS
# ──────────────────────────────────────────────
ADMIN_GRUPOS = {
    "SGA":        "Grupo 1",
    "SST":        "Grupo 1",
    "Sistemas":   "Grupo 1",
    "Inventarios":"Grupo 1",
    "Comercial":  "Grupo 1",
    "Finanzas":   "Grupo 2",
    "RRHH":       "Grupo 3",
    "Diseno":     "Grupo 4",
    "Diseño":     "Grupo 4",
    "Mercadeo":   "Grupo 5",
    "Tintoreria": "Grupo 6",
    "Tintorería": "Grupo 6",
}
GRUPO_NOMBRES = {
    "Grupo 1": "Grupo 1 (SGA, SST, Sistemas, Inventarios, Comercial)",
    "Grupo 2": "Grupo 2 (Finanzas)",
    "Grupo 3": "Grupo 3 (RRHH)",
    "Grupo 4": "Grupo 4 (Diseño)",
    "Grupo 5": "Grupo 5 (Mercadeo)",
    "Grupo 6": "Grupo 6 (Tintorería)",
}

# ──────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ──────────────────────────────────────────────
def clean_weight(series: pd.Series) -> pd.Series:
    """Convierte 'No Participa' y variantes a 0, luego a float."""
    return (
        series.replace(["No Participa", "No participa", "no participa", ""], 0)
              .fillna(0)
              .astype(float)
    )

def load_data(source) -> pd.DataFrame:
    """Carga y normaliza el DataFrame desde varias fuentes."""
    if isinstance(source, str):           # URL de Google Sheets
        url = source
        url = ensure_csv_export(url)
        df = pd.read_csv(url)
    else:                                  # Archivo subido
        name = source.name
        if name.endswith(".csv"):
            df = pd.read_csv(source)
        else:
            df = pd.read_excel(source, engine="openpyxl")

    # ── Renombrar columnas clave ──────────────────────────────────────
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "marca temporal" in col_lower or "timestamp" in col_lower:
            rename_map[col] = "timestamp"
        elif "fecha" in col_lower and "marca" not in col_lower:
            rename_map[col] = "fecha"
        elif "grupo" in col_lower and "participac" in col_lower:
            rename_map[col] = "grupo"
        elif "área" in col_lower or "area" in col_lower or "administrativo" in col_lower:
            rename_map[col] = "area_admin"
        elif "nombre" in col_lower or ("persona" in col_lower and "operac" in col_lower):
            rename_map[col] = "nombre_persona"
        elif "tienda" in col_lower and "pertenece" in col_lower:
            rename_map[col] = "tienda"
        elif "botellas" in col_lower:
            rename_map[col] = "botellas_kg"
        elif "tapas" in col_lower:
            rename_map[col] = "tapas_kg"
        elif "aceite" in col_lower:
            rename_map[col] = "aceite_kg"
    df = df.rename(columns=rename_map)

    # ── Columnas mínimas necesarias ───────────────────────────────────
    for c in ["grupo", "area_admin", "nombre_persona", "tienda",
              "botellas_kg", "tapas_kg", "aceite_kg"]:
        if c not in df.columns:
            df[c] = "N/A"

    # ── Limpiar N/A textuales ─────────────────────────────────────────
    for c in ["grupo", "area_admin", "nombre_persona", "tienda"]:
        df[c] = df[c].replace(["N/A", "n/a", "NA", "na", None], pd.NA).fillna("N/A")

    # ── Convertir pesos ───────────────────────────────────────────────
    df["botellas_kg"] = clean_weight(df["botellas_kg"])
    df["tapas_kg"]    = clean_weight(df["tapas_kg"])
    df["aceite_kg"]   = clean_weight(df["aceite_kg"])

    # ── Normalizar grupo ──────────────────────────────────────────────
    df["grupo"] = df["grupo"].astype(str).str.strip().str.title()

    # ── Grupo administrativo mapeado ──────────────────────────────────
    df["grupo_admin"] = df["area_admin"].map(ADMIN_GRUPOS)

    # ── Intentar parsear fecha si existe ──────────────────────────────
    if "fecha" in df.columns:
        try:
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        except Exception:
            df["fecha"] = pd.to_datetime(df["fecha"].astype(str), errors="coerce")

    return df

def top10_bar(df_filtered: pd.DataFrame, col_label: str, col_value: str,
              title: str, color: str, top_n: int = 10) -> go.Figure:
    """Crea un gráfico de barras horizontales Top-N."""
    df_plot = (
        df_filtered.groupby(col_label, as_index=False)[col_value]
        .sum()
        .query(f"{col_value} > 0")
        .sort_values(col_value, ascending=False)
        .head(top_n)
        .sort_values(col_value, ascending=True)   # ascendente para barras horiz.
    )
    if df_plot.empty:
        return go.Figure().update_layout(title=title + " — Sin datos")

    fig = go.Figure(go.Bar(
        x=df_plot[col_value],
        y=df_plot[col_label],
        orientation="h",
        marker=dict(
            color=df_plot[col_value],
            colorscale=[[0, "#d1fae5"], [1, color]],
            showscale=False,
            line=dict(color="white", width=0.5),
        ),
        text=[f"{v:.1f} kg" for v in df_plot[col_value]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.2f} kg<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        xaxis_title="kg recolectados",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=60, t=50, b=30),
        height=max(300, top_n * 38),
        xaxis=dict(gridcolor="#f0f0f0", showgrid=True),
        yaxis=dict(tickfont=dict(size=11)),
        font=dict(family="Inter"),
    )
    return fig

# ──────────────────────────────────────────────
# SESSION STATE: controlar carga y recarga
# ──────────────────────────────────────────────
if "data_source" not in st.session_state:
    st.session_state["data_source"] = None
if "df" not in st.session_state:
    st.session_state["df"] = None
if "last_loaded_source" not in st.session_state:
    st.session_state["last_loaded_source"] = None

# ──────────────────────────────────────────────
# SIDEBAR: fuente, filtros y botón de refresco
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/leaf.png", width=70)
    st.markdown("## 🌿 Campañas Ambientales")
    st.markdown("---")
    st.markdown("### 📂 Fuente de datos")

    modo = st.radio("Selecciona el modo de carga:", ["📎 Subir archivo", "🔗 URL Google Sheets"])

    uploaded = None
    gs_url = ""
    if modo == "📎 Subir archivo":
        uploaded = st.file_uploader(
            "Sube el archivo CSV o Excel:",
            type=["csv", "xlsx", "xls"],
            help="Exporta la hoja de cálculo en formato CSV o Excel.",
        )
    else:
        gs_url = st.text_input(
            "URL de Google Sheets:",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="La hoja debe estar publicada (Archivo → Publicar en la web → CSV).",
        )

    st.markdown("---")
    st.markdown("### 🎛️ Filtros")
    top_n = st.slider("Número de posiciones en Rankings:", 5, 20, 10)

    st.markdown("---")
    # Botón de refresco / carga por defecto
    col_a, col_b = st.columns([2, 1])
    with col_a:
        if st.button("🔄 Refrescar datos"):
            # Si hay archivo subido o URL en el input, priorizarlo; si no, usar DEFAULT_URL
            if uploaded is not None:
                st.session_state["data_source"] = uploaded
            elif gs_url and gs_url.strip():
                st.session_state["data_source"] = gs_url.strip()
            else:
                st.session_state["data_source"] = DEFAULT_URL
            # Forzar recarga
            st.session_state["last_loaded_source"] = None
            st.experimental_rerun()
    with col_b:
        if st.button("📥 Cargar por defecto"):
            st.session_state["data_source"] = DEFAULT_URL
            st.session_state["last_loaded_source"] = None
            st.experimental_rerun()

    st.markdown("---")
    st.caption("Dashboard creado con Streamlit + Plotly")

# ──────────────────────────────────────────────
# CABECERA
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">🌿 Dashboard Campañas Ambientales</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Botellas con Amor &nbsp;|&nbsp; Tapas para Sanar &nbsp;|&nbsp; Aceite Green Fuel</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# DETERMINAR DATA_SOURCE A USAR (prioridad: session_state > inputs)
# ──────────────────────────────────────────────
# Preferir lo que ya está en session_state (por botón), si no, tomar lo del sidebar actual
if st.session_state.get("data_source") is None:
    # intentar tomar lo que el usuario dejó en el sidebar (uploaded o gs_url)
    try:
        # 'uploaded' y 'gs_url' vienen del contexto del sidebar
        if 'uploaded' in locals() and uploaded is not None:
            st.session_state["data_source"] = uploaded
        elif 'gs_url' in locals() and gs_url and gs_url.strip():
            st.session_state["data_source"] = gs_url.strip()
        else:
            # No hay nada: no cargar automáticamente, mostrar opción para cargar por defecto
            st.session_state["data_source"] = None
    except Exception:
        st.session_state["data_source"] = None

# Si aún no hay fuente, mostrar mensaje y ofrecer cargar por defecto
if st.session_state["data_source"] is None:
    st.info("👈 Carga un archivo o ingresa la URL de tu Google Sheet en el panel lateral para comenzar. Usa 'Cargar por defecto' para usar la hoja pública.")
    st.stop()

# ──────────────────────────────────────────────
# CARGA DE DATOS (solo si la fuente cambió o no hay df en session_state)
# ──────────────────────────────────────────────
source_to_load = st.session_state["data_source"]
if st.session_state.get("last_loaded_source") != str(source_to_load) or st.session_state["df"] is None:
    try:
        with st.spinner("Cargando y procesando datos..."):
            df = load_data(source_to_load)
            st.session_state["df"] = df
            st.session_state["last_loaded_source"] = str(source_to_load)
    except Exception as e:
        st.error(f"❌ Error al cargar los datos: {e}")
        st.stop()
else:
    df = st.session_state["df"]

# ──────────────────────────────────────────────
# FILTROS ADICIONALES: FECHA y ÁREA ADMINISTRATIVA
# ──────────────────────────────────────────────
df_filtered = df.copy()

# Fecha: si existe columna 'fecha' con valores válidos
if "fecha" in df_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_filtered["fecha"]):
    min_date = df_filtered["fecha"].min().date()
    max_date = df_filtered["fecha"].max().date()
    if pd.isna(min_date) or pd.isna(max_date):
        # si hay NaT, intentar inferir desde strings convertidos
        valid_dates = df_filtered["fecha"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
        else:
            min_date = date.today()
            max_date = date.today()

    st.sidebar.markdown("### 📅 Filtrar por fecha")
    date_range = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    # Asegurar tupla (start, end)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        # convertir a datetime para comparar
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtered = df_filtered[(df_filtered["fecha"] >= start_dt) & (df_filtered["fecha"] <= end_dt)]
    else:
        # si el usuario selecciona un solo día, tratarlo como rango de un día
        single = pd.to_datetime(date_range)
        df_filtered = df_filtered[df_filtered["fecha"].dt.date == single.date()]

else:
    st.sidebar.markdown("### 📅 Filtrar por fecha")
    st.sidebar.info("No se detectó una columna 'fecha' con valores válidos en los datos. El filtro por fecha no está disponible.")

# Área administrativa: multiselect
st.sidebar.markdown("### 🏷️ Filtrar por Área administrativa")
areas = df_filtered["area_admin"].dropna().unique().tolist()
# Normalizar y ordenar
areas = sorted([a for a in areas if a not in [None, "N/A", ""]])
if areas:
    selected_areas = st.sidebar.multiselect("Selecciona áreas (dejar vacío = todas):", options=areas, default=areas)
    if selected_areas:
        df_filtered = df_filtered[df_filtered["area_admin"].isin(selected_areas)]
else:
    st.sidebar.info("No hay valores de 'area_admin' disponibles para filtrar.")

# ──────────────────────────────────────────────
# SUBCONJUNTOS (usar df_filtered)
# ──────────────────────────────────────────────
df_op    = df_filtered[df_filtered["grupo"].str.lower() == "operación"].copy()
df_admin = df_filtered[df_filtered["grupo"].str.lower() == "administrativo"].copy()
df_tienda= df_filtered[df_filtered["grupo"].str.lower() == "tienda"].copy()

# ──────────────────────────────────────────────
# 0. KPIs GENERALES
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Resumen General</div>', unsafe_allow_html=True)

total_participantes = len(df_filtered)
total_botellas      = df_filtered["botellas_kg"].sum()
total_tapas         = df_filtered["tapas_kg"].sum()
total_aceite        = df_filtered["aceite_kg"].sum()
total_kg            = total_botellas + total_tapas + total_aceite

cols_kpi = st.columns(5)
kpis = [
    ("👥", f"{total_participantes}", "Participantes"),
    ("♻️", f"{total_botellas:.1f} kg", "Botellas con Amor"),
    ("🔵", f"{total_tapas:.1f} kg", "Tapas para Sanar"),
    ("🛢️", f"{total_aceite:.1f} kg", "Aceite Green Fuel"),
    ("⚖️", f"{total_kg:.1f} kg", "Total Recolectado"),
]
for col, (icon, val, label) in zip(cols_kpi, kpis):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.8rem">{icon}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 1. TORTA — % Participación por Grupos
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🥧 Participación por Grupos</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1])

with c1:
    part_grupo = df_filtered["grupo"].value_counts().reset_index()
    part_grupo.columns = ["Grupo", "Participantes"]
    fig_pie = px.pie(
        part_grupo,
        values="Participantes",
        names="Grupo",
        title="% Participación por Grupo",
        color_discrete_sequence=PALETTE_MULTI,
        hole=0.42,
    )
    fig_pie.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Participantes: %{value}<br>%{percent}<extra></extra>",
    )
    fig_pie.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=50, b=20),
        paper_bgcolor="white",
        height=380,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    # Kg recolectados por grupo
    df_grupo_kg = df_filtered.groupby("grupo")[["botellas_kg","tapas_kg","aceite_kg"]].sum().reset_index()
    df_grupo_kg_melt = df_grupo_kg.melt(id_vars="grupo", var_name="Campaña", value_name="kg")
    df_grupo_kg_melt["Campaña"] = df_grupo_kg_melt["Campaña"].map({
        "botellas_kg": "Botellas con Amor",
        "tapas_kg":    "Tapas para Sanar",
        "aceite_kg":   "Aceite Green Fuel",
    })
    fig_bar_grupo = px.bar(
        df_grupo_kg_melt.query("kg > 0"),
        x="grupo", y="kg", color="Campaña",
        barmode="group",
        title="Kg recolectados por Grupo y Campaña",
        color_discrete_map={
            "Botellas con Amor": COLOR_BOTELLAS,
            "Tapas para Sanar":  COLOR_TAPAS,
            "Aceite Green Fuel": COLOR_ACEITE,
        },
        text_auto=".1f",
    )
    fig_bar_grupo.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="", yaxis_title="kg",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        height=380,
    )
    st.plotly_chart(fig_bar_grupo, use_container_width=True)

# ──────────────────────────────────────────────
# 2. DISTRIBUCIÓN POR CAMPAÑA
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Distribución por Campaña</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    camp_totales = pd.DataFrame({
        "Campaña": ["Botellas con Amor", "Tapas para Sanar", "Aceite Green Fuel"],
        "kg": [total_botellas, total_tapas, total_aceite],
    })
    fig_camp = px.pie(
        camp_totales, values="kg", names="Campaña",
        title="Distribución de kg por Campaña",
        color_discrete_map={
            "Botellas con Amor": COLOR_BOTELLAS,
            "Tapas para Sanar":  COLOR_TAPAS,
            "Aceite Green Fuel": COLOR_ACEITE,
        },
        hole=0.42,
    )
    fig_camp.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value:.1f} kg (%{percent})<extra></extra>",
    )
    fig_camp.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        paper_bgcolor="white",
        height=360,
    )
    st.plotly_chart(fig_camp, use_container_width=True)

with c2:
    # Participantes por campaña (quiénes SI participan)
    part_b = (df_filtered["botellas_kg"] > 0).sum()
    part_t = (df_filtered["tapas_kg"] > 0).sum()
    part_a = (df_filtered["aceite_kg"] > 0).sum()
    df_part_camp = pd.DataFrame({
        "Campaña": ["Botellas con Amor", "Tapas para Sanar", "Aceite Green Fuel"],
        "Participantes": [part_b, part_t, part_a],
    })
    fig_part_camp = px.bar(
        df_part_camp, x="Campaña", y="Participantes",
        title="Número de Participantes por Campaña",
        color="Campaña",
        color_discrete_map={
            "Botellas con Amor": COLOR_BOTELLAS,
            "Tapas para Sanar":  COLOR_TAPAS,
            "Aceite Green Fuel": COLOR_ACEITE,
        },
        text="Participantes",
    )
    fig_part_camp.update_traces(textposition="outside")
    fig_part_camp.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
        height=360,
        yaxis_title="Personas",
        xaxis_title="",
    )
    st.plotly_chart(fig_part_camp, use_container_width=True)

# ──────────────────────────────────────────────
# 3. RANKINGS — OPERADORES
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🏭 Rankings — Operadores</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    fig_op_bot = top10_bar(
        df_op, "nombre_persona", "botellas_kg",
        f"🥇 Top {top_n} Operadores — Botellas con Amor", COLOR_BOTELLAS, top_n
    )
    st.plotly_chart(fig_op_bot, use_container_width=True)

with c2:
    fig_op_tap = top10_bar(
        df_op, "nombre_persona", "tapas_kg",
        f"🥇 Top {top_n} Operadores — Tapas para Sanar", COLOR_TAPAS, top_n
    )
    st.plotly_chart(fig_op_tap, use_container_width=True)

# ──────────────────────────────────────────────
# 4. RANKINGS — TIENDAS
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🏪 Rankings — Tiendas</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    fig_t_bot = top10_bar(
        df_tienda, "tienda", "botellas_kg",
        f"🥇 Top {top_n} Tiendas — Botellas con Amor", COLOR_BOTELLAS, top_n
    )
    st.plotly_chart(fig_t_bot, use_container_width=True)

with c2:
    fig_t_tap = top10_bar(
        df_tienda, "tienda", "tapas_kg",
        f"🥇 Top {top_n} Tiendas — Tapas para Sanar", COLOR_TAPAS, top_n
    )
    st.plotly_chart(fig_t_tap, use_container_width=True)

# ──────────────────────────────────────────────
# 5. RANKING — ACEITE (TODOS LOS GRUPOS, POR PERSONA)
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🛢️ Ranking — Aceite Green Fuel (Todos los Grupos)</div>', unsafe_allow_html=True)

df_aceite_all = df_filtered.copy()
df_aceite_all["etiqueta"] = df_aceite_all.apply(
    lambda r: r["nombre_persona"] if r["nombre_persona"] != "N/A"
    else (r["area_admin"] if r["area_admin"] != "N/A"
          else r["tienda"]),
    axis=1,
)
fig_aceite = top10_bar(
    df_aceite_all, "etiqueta", "aceite_kg",
    f"🛢️ Top {top_n} — Aceite Green Fuel (Todos los grupos)", COLOR_ACEITE, top_n
)
st.plotly_chart(fig_aceite, use_container_width=True)

# ──────────────────────────────────────────────
# 6. RANKINGS — ADMINISTRATIVOS
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🏢 Rankings — Administrativos</div>', unsafe_allow_html=True)

df_admin["etiqueta"] = df_admin.apply(
    lambda r: r["nombre_persona"] if r["nombre_persona"] != "N/A"
    else r["area_admin"],
    axis=1,
)

c1, c2 = st.columns(2)
with c1:
    fig_adm_bot = top10_bar(
        df_admin, "etiqueta", "botellas_kg",
        f"🥇 Top {top_n} Administrativos — Botellas con Amor", COLOR_BOTELLAS, top_n
    )
    st.plotly_chart(fig_adm_bot, use_container_width=True)

with c2:
    fig_adm_tap = top10_bar(
        df_admin, "etiqueta", "tapas_kg",
        f"🥇 Top {top_n} Administrativos — Tapas para Sanar", COLOR_TAPAS, top_n
    )
    st.plotly_chart(fig_adm_tap, use_container_width=True)

# ──────────────────────────────────────────────
# 7. RANKING — ADMINISTRATIVOS POR GRUPO INTERNO
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🏆 Competencia Interna — Grupos Administrativos</div>', unsafe_allow_html=True)

df_admin_gpo = (
    df_admin[df_admin["grupo_admin"].notna()]
    .groupby("grupo_admin")[["botellas_kg", "tapas_kg", "aceite_kg"]]
    .sum()
    .reset_index()
)
df_admin_gpo["total_kg"]      = df_admin_gpo[["botellas_kg","tapas_kg","aceite_kg"]].sum(axis=1)
df_admin_gpo["nombre_grupo"]  = df_admin_gpo["grupo_admin"].map(GRUPO_NOMBRES)
df_admin_gpo = df_admin_gpo.sort_values("total_kg", ascending=False)

df_gpo_melt = df_admin_gpo.melt(
    id_vars=["nombre_grupo","total_kg"],
    value_vars=["botellas_kg","tapas_kg","aceite_kg"],
    var_name="Campaña", value_name="kg"
)
df_gpo_melt["Campaña"] = df_gpo_melt["Campaña"].map({
    "botellas_kg": "Botellas con Amor",
    "tapas_kg":    "Tapas para Sanar",
    "aceite_kg":   "Aceite Green Fuel",
})

fig_gpo_stack = px.bar(
    df_gpo_melt.query("kg > 0"),
    x="kg", y="nombre_grupo", orientation="h",
    color="Campaña",
    barmode="stack",
    title="Ranking Grupos Administrativos — Total por Campaña",
    color_discrete_map={
        "Botellas con Amor": COLOR_BOTELLAS,
        "Tapas para Sanar":  COLOR_TAPAS,
        "Aceite Green Fuel": COLOR_ACEITE,
    },
    text_auto=".1f",
)
fig_gpo_stack.update_layout(
    title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
    plot_bgcolor="white", paper_bgcolor="white",
    xaxis_title="kg recolectados",
    yaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    height=max(350, len(df_admin_gpo) * 55 + 80),
    margin=dict(l=10, r=60, t=50, b=60),
)
st.plotly_chart(fig_gpo_stack, use_container_width=True)

# ──────────────────────────────────────────────
# 8. MAPA DE CALOR — Participación por Área y Campaña
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">🌡️ Mapa de Calor — Área Administrativa vs Campaña</div>', unsafe_allow_html=True)

df_heat = (
    df_admin.groupby("area_admin")[["botellas_kg","tapas_kg","aceite_kg"]].sum()
    .rename(columns={
        "botellas_kg": "Botellas con Amor",
        "tapas_kg":    "Tapas para Sanar",
        "aceite_kg":   "Aceite Green Fuel",
    })
    .query("(`Botellas con Amor` + `Tapas para Sanar` + `Aceite Green Fuel`) > 0")
)
if not df_heat.empty:
    fig_heat = px.imshow(
        df_heat,
        text_auto=".1f",
        title="Mapa de Calor — Kg recolectados por Área y Campaña",
        color_continuous_scale="Greens",
        aspect="auto",
    )
    fig_heat.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        paper_bgcolor="white",
        height=max(300, len(df_heat) * 40 + 100),
        coloraxis_colorbar_title="kg",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ──────────────────────────────────────────────
# 9. RADAR — Grupos Administrativos
# ──────────────────────────────────────────────
if len(df_admin_gpo) >= 3:
    st.markdown('<div class="section-header">🕸️ Radar — Grupos Administrativos</div>', unsafe_allow_html=True)

    categories = ["Botellas con Amor", "Tapas para Sanar", "Aceite Green Fuel"]
    fig_radar = go.Figure()
    colors_radar = ["#059669","#2563eb","#d97706","#dc2626","#7c3aed","#0891b2"]
    for i, row in df_admin_gpo.iterrows():
        values = [row["botellas_kg"], row["tapas_kg"], row["aceite_kg"]]
        values += values[:1]
        cats   = categories + categories[:1]
        fig_radar.add_trace(go.Scatterpolar(
            r=values, theta=cats,
            fill="toself", name=row["nombre_grupo"],
            line_color=colors_radar[i % len(colors_radar)],
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, tickfont=dict(size=9))),
        showlegend=True,
        title=dict(
            text="Radar de Desempeño — Grupos Administrativos",
            font=dict(family="Montserrat", size=14, color="#1a6b3c")
        ),
        paper_bgcolor="white",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ──────────────────────────────────────────────
# 10. TABLA RESUMEN DESCARGABLE
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Tabla de Datos</div>', unsafe_allow_html=True)

with st.expander("Ver / Descargar tabla completa", expanded=False):
    col_show = [c for c in ["fecha","grupo","area_admin","nombre_persona","tienda",
                             "botellas_kg","tapas_kg","aceite_kg"] if c in df_filtered.columns]
    st.dataframe(
        df_filtered[col_show].rename(columns={
            "fecha": "Fecha", "grupo": "Grupo", "area_admin": "Área",
            "nombre_persona": "Persona", "tienda": "Tienda",
            "botellas_kg": "Botellas (kg)", "tapas_kg": "Tapas (kg)", "aceite_kg": "Aceite (kg)"
        }),
        use_container_width=True,
        height=300,
    )
    csv_bytes = df_filtered[col_show].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Descargar CSV",
        data=csv_bytes,
        file_name="campanas_ambientales.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption("🌿 Dashboard Campañas Ambientales · Desarrollado con Streamlit & Plotly")
