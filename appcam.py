"""
Dashboard - Campañas Ambientales
Botellas con Amor | Tapas para Sanar | Aceite Green Fuel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
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
    .filter-badge {
        background: #dcfce7;
        color: #15803d;
        border: 1px solid #86efac;
        border-radius: 20px;
        padding: 0.25rem 0.9rem;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
URL_OFICIAL = (
    "https://docs.google.com/spreadsheets/d/"
    "157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8/export?format=csv"
)

PALETTE_MULTI  = ["#059669","#2563eb","#d97706","#dc2626","#7c3aed",
                  "#0891b2","#be185d","#65a30d","#0f766e","#c2410c"]
COLOR_BOTELLAS = "#059669"
COLOR_TAPAS    = "#2563eb"
COLOR_ACEITE   = "#d97706"

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
    "Grupo 1": "Grupo 1 (SGA, SST, Inventarios, Comercial)",
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
    return (
        series.replace(["No Participa","No participa","no participa",""], 0)
              .fillna(0)
              .astype(float)
    )


def gs_url_to_csv(url: str) -> str:
    if "export?format=csv" in url:
        return url
    if "/edit#gid=" in url:
        return url.replace("/edit#gid=", "/export?format=csv&gid=")
    if "/edit?usp=sharing" in url:
        return url.replace("/edit?usp=sharing", "/export?format=csv")
    if "/spreadsheets/d/" in url:
        base = url.split("/edit")[0].split("/pub")[0]
        return base.rstrip("/") + "/export?format=csv"
    return url + "/export?format=csv"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        cl = col.lower()
        if "marca temporal" in cl or "timestamp" in cl:
            rename_map[col] = "timestamp"
        elif "fecha" in cl and "marca" not in cl:
            rename_map[col] = "fecha"
        elif "grupo" in cl and "participac" in cl:
            rename_map[col] = "grupo"
        elif "área" in cl or "area" in cl or "administrativo" in cl:
            rename_map[col] = "area_admin"
        elif "nombre" in cl or ("persona" in cl and "operac" in cl):
            rename_map[col] = "nombre_persona"
        elif "tienda" in cl and "pertenece" in cl:
            rename_map[col] = "tienda"
        elif "botellas" in cl:
            rename_map[col] = "botellas_kg"
        elif "tapas" in cl:
            rename_map[col] = "tapas_kg"
        elif "aceite" in cl:
            rename_map[col] = "aceite_kg"
    df = df.rename(columns=rename_map)

    for c in ["grupo","area_admin","nombre_persona","tienda",
              "botellas_kg","tapas_kg","aceite_kg"]:
        if c not in df.columns:
            df[c] = "N/A"

    for c in ["grupo","area_admin","nombre_persona","tienda"]:
        df[c] = df[c].replace(["N/A","n/a","NA","na",None], pd.NA).fillna("N/A")

    df["botellas_kg"] = clean_weight(df["botellas_kg"])
    df["tapas_kg"]    = clean_weight(df["tapas_kg"])
    df["aceite_kg"]   = clean_weight(df["aceite_kg"])
    df["grupo"]       = df["grupo"].str.strip().str.title()
    df["grupo_admin"] = df["area_admin"].map(ADMIN_GRUPOS)

    # Parsear fecha
    fecha_col = "fecha" if "fecha" in df.columns else ("timestamp" if "timestamp" in df.columns else None)
    if fecha_col:
        df["fecha_dt"] = pd.to_datetime(df[fecha_col], dayfirst=True, errors="coerce")
    else:
        df["fecha_dt"] = pd.NaT

    return df


@st.cache_data(show_spinner=False)
def load_from_url(url: str) -> pd.DataFrame:
    csv_url = gs_url_to_csv(url)
    df = pd.read_csv(csv_url)
    return _normalize(df)


@st.cache_data(show_spinner=False)
def load_from_bytes(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    import io
    buf = io.BytesIO(file_bytes)
    df = pd.read_csv(buf) if file_name.endswith(".csv") else pd.read_excel(buf, engine="openpyxl")
    return _normalize(df)


def top10_bar(df_in, col_label, col_value, title, color, top_n=10):
    df_plot = (
        df_in.groupby(col_label, as_index=False)[col_value]
        .sum()
        .query(f"{col_value} > 0")
        .sort_values(col_value, ascending=False)
        .head(top_n)
        .sort_values(col_value, ascending=True)
    )
    if df_plot.empty:
        fig = go.Figure()
        fig.update_layout(
            title=title + " — Sin datos",
            paper_bgcolor="white",
            annotations=[dict(
                text="Sin registros para los filtros actuales",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=13, color="#9ca3af"),
            )],
        )
        return fig
    fig = go.Figure(go.Bar(
        x=df_plot[col_value], y=df_plot[col_label], orientation="h",
        marker=dict(color=df_plot[col_value],
                    colorscale=[[0,"#d1fae5"],[1,color]],
                    showscale=False, line=dict(color="white", width=0.5)),
        text=[f"{v:.1f} kg" for v in df_plot[col_value]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.2f} kg<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        xaxis_title="kg recolectados", yaxis_title="",
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=70, t=50, b=30),
        height=max(300, top_n * 38),
        xaxis=dict(gridcolor="#f0f0f0", showgrid=True),
        yaxis=dict(tickfont=dict(size=11)),
        font=dict(family="Inter"),
    )
    return fig

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.icons8.com/color/96/leaf.png", width=64)
    st.markdown("## 🌿 Campañas Ambientales")
    st.markdown("---")

    # ── Fuente de datos ───────────────────────────────────────────────
    st.markdown("### 📂 Fuente de datos")
    modo = st.radio(
        "Selecciona el modo de carga:",
        ["🔗 Base de datos oficial", "🌐 Otra URL de Google Sheets", "📎 Subir archivo"],
        index=0,
    )

    data_key   = None
    data_bytes = None
    data_fname = None

    if modo == "🔗 Base de datos oficial":
        st.success("✅ Conectado a la base de datos oficial del proyecto.")
        data_key = URL_OFICIAL

    elif modo == "🌐 Otra URL de Google Sheets":
        gs_url = st.text_input(
            "URL de Google Sheets:",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="La hoja debe tener acceso de lectura público o estar publicada en la web.",
        )
        if gs_url.strip():
            data_key = gs_url.strip()
        else:
            st.info("Ingresa la URL para continuar.")

    else:
        uploaded = st.file_uploader("Sube el archivo (CSV o Excel):", type=["csv","xlsx","xls"])
        if uploaded:
            data_bytes = uploaded.getvalue()
            data_fname = uploaded.name
            data_key   = data_fname

    # ── Botón de refresco ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔄 Actualizar datos")
    st.caption("Úsalo cuando se hayan agregado nuevos registros a la fuente.")
    if st.button("↺  Refrescar datos ahora", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.toast("✅ Caché limpiado — recargando datos...", icon="🔄")
        st.rerun()

    # ── Filtro por fecha ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🗓️ Filtro por Fecha")
    usar_filtro = st.checkbox("Activar filtro de fecha", value=False)
    fecha_inicio = fecha_fin = None
    if usar_filtro:
        col_a, col_b = st.columns(2)
        with col_a:
            fecha_inicio = st.date_input("Desde:", value=date(2025, 1, 1), key="fi",
                                         label_visibility="visible")
        with col_b:
            fecha_fin = st.date_input("Hasta:", value=date.today(), key="ff",
                                      label_visibility="visible")
        if fecha_inicio > fecha_fin:
            st.error("⚠️ La fecha de inicio debe ser anterior a la de fin.")

    # ── Opciones de gráficas ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎛️ Opciones de gráficas")
    top_n = st.slider("Posiciones en Rankings:", 5, 20, 10)

    st.markdown("---")
    st.caption("Dashboard · Streamlit + Plotly")


# ══════════════════════════════════════════════
# CABECERA
# ══════════════════════════════════════════════
st.markdown('<div class="main-title">🌿 Dashboard Campañas Ambientales</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Botellas con Amor &nbsp;|&nbsp; Tapas para Sanar &nbsp;|&nbsp; Aceite Green Fuel</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════
# CARGA DE DATOS
# ══════════════════════════════════════════════
if data_key is None:
    st.info("👈 Selecciona una fuente de datos en el panel lateral para comenzar.")
    st.stop()

try:
    with st.spinner("⏳ Cargando datos..."):
        if data_bytes is not None:
            df_raw = load_from_bytes(data_bytes, data_fname)
        else:
            df_raw = load_from_url(data_key)
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.stop()

# ── Aplicar filtro de fecha ───────────────────────────────────────────
if usar_filtro and fecha_inicio and fecha_fin and fecha_inicio <= fecha_fin:
    mask = (
        (df_raw["fecha_dt"].dt.date >= fecha_inicio) &
        (df_raw["fecha_dt"].dt.date <= fecha_fin)
    )
    df = df_raw[mask].copy()
    badge_txt = (
        f"🗓️ Filtro activo: {fecha_inicio.strftime('%d/%m/%Y')} → "
        f"{fecha_fin.strftime('%d/%m/%Y')} &nbsp;·&nbsp; "
        f"<b>{len(df)}</b> de <b>{len(df_raw)}</b> registros"
    )
else:
    df = df_raw.copy()
    badge_txt = f"📋 Todos los registros: <b>{len(df)}</b>"

st.markdown(f'<div class="filter-badge">{badge_txt}</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ No hay datos para el período seleccionado. Ajusta el filtro de fechas.")
    st.stop()

# ── Subconjuntos por grupo ────────────────────────────────────────────
df_op     = df[df["grupo"].str.lower() == "operación"].copy()
df_admin  = df[df["grupo"].str.lower() == "administrativo"].copy()
df_tienda = df[df["grupo"].str.lower() == "tienda"].copy()


# ══════════════════════════════════════════════
# 0. KPIs GENERALES
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Resumen General</div>', unsafe_allow_html=True)

total_botellas = df["botellas_kg"].sum()
total_tapas    = df["tapas_kg"].sum()
total_aceite   = df["aceite_kg"].sum()
total_kg       = total_botellas + total_tapas + total_aceite

cols_kpi = st.columns(5)
for col, (icon, val, label) in zip(cols_kpi, [
    ("👥", f"{len(df)}",             "Participantes"),
    ("♻️", f"{total_botellas:.1f} kg", "Botellas con Amor"),
    ("🔵", f"{total_tapas:.1f} kg",    "Tapas para Sanar"),
    ("🛢️", f"{total_aceite:.1f} kg",  "Aceite Green Fuel"),
    ("⚖️", f"{total_kg:.1f} kg",       "Total Recolectado"),
]):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.8rem">{icon}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 1. % PARTICIPACIÓN POR GRUPOS
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🥧 Participación por Grupos</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    part_grupo = df["grupo"].value_counts().reset_index()
    part_grupo.columns = ["Grupo", "Participantes"]
    fig_pie = px.pie(
        part_grupo, values="Participantes", names="Grupo",
        title="% Participación por Grupo",
        color_discrete_sequence=PALETTE_MULTI, hole=0.42,
    )
    fig_pie.update_traces(
        textposition="outside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Participantes: %{value}<br>%{percent}<extra></extra>",
    )
    fig_pie.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        margin=dict(t=50, b=20), paper_bgcolor="white", height=380,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    df_gkg = df.groupby("grupo")[["botellas_kg","tapas_kg","aceite_kg"]].sum().reset_index()
    df_gkg_m = df_gkg.melt(id_vars="grupo", var_name="Campaña", value_name="kg")
    df_gkg_m["Campaña"] = df_gkg_m["Campaña"].map({
        "botellas_kg":"Botellas con Amor","tapas_kg":"Tapas para Sanar","aceite_kg":"Aceite Green Fuel"
    })
    fig_bg = px.bar(
        df_gkg_m.query("kg > 0"), x="grupo", y="kg", color="Campaña", barmode="group",
        title="Kg recolectados por Grupo y Campaña",
        color_discrete_map={
            "Botellas con Amor":COLOR_BOTELLAS,"Tapas para Sanar":COLOR_TAPAS,"Aceite Green Fuel":COLOR_ACEITE
        }, text_auto=".1f",
    )
    fig_bg.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="kg",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35), height=380,
    )
    st.plotly_chart(fig_bg, use_container_width=True)


# ══════════════════════════════════════════════
# 2. DISTRIBUCIÓN POR CAMPAÑA
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Distribución por Campaña</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    camp_tot = pd.DataFrame({
        "Campaña":["Botellas con Amor","Tapas para Sanar","Aceite Green Fuel"],
        "kg":[total_botellas, total_tapas, total_aceite],
    })
    fig_camp = px.pie(
        camp_tot, values="kg", names="Campaña", title="Distribución de kg por Campaña",
        color_discrete_map={
            "Botellas con Amor":COLOR_BOTELLAS,"Tapas para Sanar":COLOR_TAPAS,"Aceite Green Fuel":COLOR_ACEITE
        }, hole=0.42,
    )
    fig_camp.update_traces(
        textposition="outside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value:.1f} kg (%{percent})<extra></extra>",
    )
    fig_camp.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        paper_bgcolor="white", height=360,
    )
    st.plotly_chart(fig_camp, use_container_width=True)

with c2:
    df_pc = pd.DataFrame({
        "Campaña":["Botellas con Amor","Tapas para Sanar","Aceite Green Fuel"],
        "Participantes":[(df["botellas_kg"]>0).sum(),(df["tapas_kg"]>0).sum(),(df["aceite_kg"]>0).sum()],
    })
    fig_pcamp = px.bar(
        df_pc, x="Campaña", y="Participantes", title="Participantes por Campaña",
        color="Campaña",
        color_discrete_map={
            "Botellas con Amor":COLOR_BOTELLAS,"Tapas para Sanar":COLOR_TAPAS,"Aceite Green Fuel":COLOR_ACEITE
        }, text="Participantes",
    )
    fig_pcamp.update_traces(textposition="outside")
    fig_pcamp.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
        height=360, yaxis_title="Personas", xaxis_title="",
    )
    st.plotly_chart(fig_pcamp, use_container_width=True)


# ══════════════════════════════════════════════
# 3. EVOLUCIÓN TEMPORAL (solo si hay >1 fecha)
# ══════════════════════════════════════════════
if df["fecha_dt"].dropna().dt.date.nunique() > 1:
    st.markdown('<div class="section-header">📅 Evolución Temporal</div>', unsafe_allow_html=True)
    df_time = (
        df.groupby(df["fecha_dt"].dt.date)[["botellas_kg","tapas_kg","aceite_kg"]]
        .sum().reset_index().rename(columns={"fecha_dt":"Fecha"})
    )
    df_tm = df_time.melt(id_vars="Fecha", var_name="Campaña", value_name="kg")
    df_tm["Campaña"] = df_tm["Campaña"].map({
        "botellas_kg":"Botellas con Amor","tapas_kg":"Tapas para Sanar","aceite_kg":"Aceite Green Fuel"
    })
    fig_time = px.line(
        df_tm, x="Fecha", y="kg", color="Campaña", markers=True,
        title="Recolección acumulada por Fecha",
        color_discrete_map={
            "Botellas con Amor":COLOR_BOTELLAS,"Tapas para Sanar":COLOR_TAPAS,"Aceite Green Fuel":COLOR_ACEITE
        },
    )
    fig_time.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="Fecha", yaxis_title="kg", height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    st.plotly_chart(fig_time, use_container_width=True)


# ══════════════════════════════════════════════
# 4. RANKINGS — OPERADORES
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🏭 Rankings — Operadores</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(top10_bar(df_op, "nombre_persona", "botellas_kg",
        f"🥇 Top {top_n} Operadores — Botellas con Amor", COLOR_BOTELLAS, top_n), use_container_width=True)
with c2:
    st.plotly_chart(top10_bar(df_op, "nombre_persona", "tapas_kg",
        f"🥇 Top {top_n} Operadores — Tapas para Sanar", COLOR_TAPAS, top_n), use_container_width=True)


# ══════════════════════════════════════════════
# 5. RANKINGS — TIENDAS
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🏪 Rankings — Tiendas</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(top10_bar(df_tienda, "tienda", "botellas_kg",
        f"🥇 Top {top_n} Tiendas — Botellas con Amor", COLOR_BOTELLAS, top_n), use_container_width=True)
with c2:
    st.plotly_chart(top10_bar(df_tienda, "tienda", "tapas_kg",
        f"🥇 Top {top_n} Tiendas — Tapas para Sanar", COLOR_TAPAS, top_n), use_container_width=True)


# ══════════════════════════════════════════════
# 6. RANKING — ACEITE (TODOS LOS GRUPOS)
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🛢️ Ranking — Aceite Green Fuel (Todos los Grupos)</div>', unsafe_allow_html=True)
df_aceite_all = df.copy()
df_aceite_all["etiqueta"] = df_aceite_all.apply(
    lambda r: r["nombre_persona"] if r["nombre_persona"] != "N/A"
              else (r["area_admin"] if r["area_admin"] != "N/A" else r["tienda"]), axis=1)
st.plotly_chart(top10_bar(df_aceite_all, "etiqueta", "aceite_kg",
    f"🛢️ Top {top_n} — Aceite Green Fuel (Todos los grupos)", COLOR_ACEITE, top_n),
    use_container_width=True)


# ══════════════════════════════════════════════
# 7. RANKINGS — ADMINISTRATIVOS
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🏢 Rankings — Administrativos</div>', unsafe_allow_html=True)
df_admin["etiqueta"] = df_admin.apply(
    lambda r: r["nombre_persona"] if r["nombre_persona"] != "N/A" else r["area_admin"], axis=1)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(top10_bar(df_admin, "etiqueta", "botellas_kg",
        f"🥇 Top {top_n} Administrativos — Botellas con Amor", COLOR_BOTELLAS, top_n), use_container_width=True)
with c2:
    st.plotly_chart(top10_bar(df_admin, "etiqueta", "tapas_kg",
        f"🥇 Top {top_n} Administrativos — Tapas para Sanar", COLOR_TAPAS, top_n), use_container_width=True)


# ══════════════════════════════════════════════
# 8. GRUPOS ADMINISTRATIVOS INTERNOS
#     (Corregido: quitar Aceite y usar solo Botellas + Tapas)
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🏆 Competencia Interna — Grupos Administrativos</div>', unsafe_allow_html=True)

# Agrupar solo los administrativos que tienen mapeo de grupo interno
df_adm_gpo = (
    df_admin[df_admin["grupo_admin"].notna()]
    .groupby("grupo_admin")[["botellas_kg","tapas_kg"]].sum().reset_index()
)

# Calcular total considerando solo botellas + tapas (se elimina aceite del ranking)
df_adm_gpo["total_kg"]     = df_adm_gpo[["botellas_kg","tapas_kg"]].sum(axis=1)
df_adm_gpo["nombre_grupo"] = df_adm_gpo["grupo_admin"].map(GRUPO_NOMBRES)
df_adm_gpo = df_adm_gpo.sort_values("total_kg", ascending=False)

if not df_adm_gpo.empty:
    # Melt solo botellas y tapas
    df_gm = df_adm_gpo.melt(
        id_vars=["nombre_grupo","total_kg"],
        value_vars=["botellas_kg","tapas_kg"],
        var_name="Campaña", value_name="kg"
    )
    df_gm["Campaña"] = df_gm["Campaña"].map({
        "botellas_kg":"Botellas con Amor","tapas_kg":"Tapas para Sanar"
    })
    # Paleta y mapeo solo para las dos campañas
    fig_gs = px.bar(
        df_gm.query("kg > 0"), x="kg", y="nombre_grupo", orientation="h",
        color="Campaña", barmode="stack",
        title="Ranking Grupos Administrativos — Total por Campaña (Botellas + Tapas)",
        color_discrete_map={
            "Botellas con Amor":COLOR_BOTELLAS,"Tapas para Sanar":COLOR_TAPAS
        }, text_auto=".1f",
    )
    fig_gs.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="kg recolectados", yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        height=max(350, len(df_adm_gpo)*55+80),
        margin=dict(l=10, r=60, t=50, b=60),
    )
    st.plotly_chart(fig_gs, use_container_width=True)
else:
    st.info("No hay datos de grupos administrativos en el período seleccionado.")


# ══════════════════════════════════════════════
# 9. MAPA DE CALOR
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🌡️ Mapa de Calor — Área Administrativa vs Campaña</div>', unsafe_allow_html=True)
df_heat = (
    df_admin.groupby("area_admin")[["botellas_kg","tapas_kg","aceite_kg"]].sum()
    .rename(columns={"botellas_kg":"Botellas con Amor","tapas_kg":"Tapas para Sanar","aceite_kg":"Aceite Green Fuel"})
    .query("`Botellas con Amor` + `Tapas para Sanar` + `Aceite Green Fuel` > 0")
)
if not df_heat.empty:
    fig_heat = px.imshow(
        df_heat, text_auto=".1f",
        title="Mapa de Calor — Kg por Área y Campaña",
        color_continuous_scale="Greens", aspect="auto",
    )
    fig_heat.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        paper_bgcolor="white", height=max(300, len(df_heat)*40+100),
        coloraxis_colorbar_title="kg",
    )
    st.plotly_chart(fig_heat, use_container_width=True)


# ══════════════════════════════════════════════
# 10. RADAR — Grupos Administrativos
# ══════════════════════════════════════════════
if len(df_adm_gpo) >= 3:
    st.markdown('<div class="section-header">🕸️ Radar — Grupos Administrativos</div>', unsafe_allow_html=True)
    cats = ["Botellas con Amor","Tapas para Sanar"]
    cr   = ["#059669","#2563eb","#d97706","#dc2626","#7c3aed","#0891b2"]
    fig_r = go.Figure()
    for i, row in df_adm_gpo.iterrows():
        vals = [row["botellas_kg"], row["tapas_kg"]]
        fig_r.add_trace(go.Scatterpolar(
            r=vals+vals[:1], theta=cats+cats[:1],
            fill="toself", name=row["nombre_grupo"],
            line_color=cr[i % len(cr)],
        ))
    fig_r.update_layout(
        polar=dict(radialaxis=dict(visible=True, tickfont=dict(size=9))),
        showlegend=True,
        title=dict(text="Radar de Desempeño — Grupos Administrativos (Botellas + Tapas)",
                   font=dict(family="Montserrat", size=14, color="#1a6b3c")),
        paper_bgcolor="white", height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    st.plotly_chart(fig_r, use_container_width=True)


# ══════════════════════════════════════════════
# 11. TABLA DESCARGABLE
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">📋 Tabla de Datos</div>', unsafe_allow_html=True)
with st.expander("Ver / Descargar tabla completa", expanded=False):
    col_show = [c for c in ["fecha","grupo","area_admin","nombre_persona","tienda",
                             "botellas_kg","tapas_kg","aceite_kg"] if c in df.columns]
    st.dataframe(
        df[col_show].rename(columns={
            "fecha":"Fecha","grupo":"Grupo","area_admin":"Área",
            "nombre_persona":"Persona","tienda":"Tienda",
            "botellas_kg":"Botellas (kg)","tapas_kg":"Tapas (kg)","aceite_kg":"Aceite (kg)",
        }),
        use_container_width=True, height=300,
    )
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=df[col_show].to_csv(index=False).encode("utf-8-sig"),
        file_name="campanas_ambientales_filtrado.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption("🌿 Dashboard Campañas Ambientales · Streamlit + Plotly")
