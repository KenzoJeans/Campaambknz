import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
from io import StringIO

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Campañas Ambientales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta de colores y estilos ──────────────────────────────────────────────
COLORS = {
    "botellas":  "#2ecc71",
    "tapas":     "#3498db",
    "aceite":    "#f39c12",
    "tienda":    "#9b59b6",
    "operacion": "#e74c3c",
    "admin":     "#1abc9c",
    "bg":        "#0e1117",
    "card":      "#1c1f26",
    "text":      "#f0f2f6",
}

CAMPAIGN_COLORS = [COLORS["botellas"], COLORS["tapas"], COLORS["aceite"]]

st.markdown("""
<style>
.metric-card { background: linear-gradient(135deg, #1c1f26 0%, #252933 100%); border-radius: 12px; padding: 20px 24px; border-left: 4px solid; margin-bottom: 8px; }
.metric-card h3 { margin: 0 0 4px 0; font-size: 13px; color: #8b949e; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
.metric-card h1 { margin: 0; font-size: 32px; font-weight: 700; }
.metric-card p  { margin: 4px 0 0 0; font-size: 12px; color: #8b949e; }
.dashboard-header { background: linear-gradient(90deg, #0e1117 0%, #1a2a1a 50%, #0e1117 100%); border-bottom: 1px solid #2ecc7133; padding: 16px 0 24px 0; margin-bottom: 24px; }
.dashboard-header h1 { font-size: 2rem; font-weight: 800; color: #2ecc71; margin: 0; }
.section-title { font-size: 1rem; font-weight: 700; color: #e2e8f0; border-left: 3px solid #2ecc71; padding-left: 10px; margin: 28px 0 12px 0; text-transform: uppercase; }
.update-badge { background: #1c2a1c; border: 1px solid #2ecc7144; border-radius: 20px; padding: 4px 12px; font-size: 12px; color: #2ecc71; display: inline-block; }
.dataframe { font-size: 13px !important; }
hr { border-color: #2a2d35; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# ── Constantes ───────────────────────────────────────────────────────────────
SHEET_ID = "157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

CAMPAIGNS = {
    "Botellas con amor": "botellas_kg",
    "Tapas para sanar":  "tapas_kg",
    "Aceite Green Fuel": "aceite_kg",
}
camp_labels = {v: k for k, v in CAMPAIGNS.items()}

# ── Utilidades ───────────────────────────────────────────────────────────────
def normalize_text(s):
    if pd.isna(s):
        return ""
    return str(s).strip().lower()

# ── Carga y limpieza ─────────────────────────────────────────────────────────
@st.cache_data(ttl=0)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    # rename heuristics (keeps compatibility)
    expected = list(df.columns[:10])
    mapping = [
        "marca_temporal","fecha","grupo","area_admin","nombre_operacion",
        "area_operacion","tienda","botellas_raw","tapas_raw","aceite_raw"
    ]
    for i, col in enumerate(expected):
        if i < len(mapping):
            df = df.rename(columns={col: mapping[i]})
    # parse dates
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    if "marca_temporal" in df.columns:
        df["marca_temporal"] = pd.to_datetime(df["marca_temporal"], dayfirst=True, errors="coerce")
    # parse campaign numeric
    def parse_campaign(s):
        s = s.astype(str).str.strip()
        s = s.replace({"No Participa": np.nan, "nan": np.nan, "": np.nan})
        return pd.to_numeric(s, errors="coerce")
    for raw, new in [("botellas_raw","botellas_kg"),("tapas_raw","tapas_kg"),("aceite_raw","aceite_kg")]:
        if raw in df.columns:
            df[new] = parse_campaign(df[raw])
        else:
            df[new] = np.nan
    # flags
    df["participa_botellas"] = df["botellas_kg"].notna()
    df["participa_tapas"] = df["tapas_kg"].notna()
    df["participa_aceite"] = df["aceite_kg"].notna()
    df["participa_alguna"] = df[["participa_botellas","participa_tapas","participa_aceite"]].any(axis=1)
    # normalize text columns
    for c in ["grupo","area_admin","area_operacion","tienda","nombre_operacion"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().replace({"N/A": np.nan, "nan": np.nan})
    # semana
    if "fecha" in df.columns:
        df["semana"] = df["fecha"].dt.isocalendar().week.astype("Int64")
    else:
        df["semana"] = pd.Series([pd.NA]*len(df), dtype="Int64")
    return df

# ── Gráfica styling ──────────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e2e8f0"),
    margin=dict(l=20, r=20, t=40, b=20),
)
def styled_fig(fig):
    fig.update_layout(**PLOTLY_THEME)
    fig.update_xaxes(showgrid=True, gridcolor="#2a2d35", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#2a2d35", zeroline=False)
    return fig

# ── Header y sidebar ────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
  <h1>🌿 Dashboard – Campañas Ambientales</h1>
  <p>Monitoreo · Botellas · Tapas · Aceite Green Fuel</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/recycling.png", width=60)
    st.markdown("## ⚙️ Panel de Control")
    if st.button("🔄 Refrescar datos", use_container_width=True):
        st.cache_data.clear()
        st.toast("✅ Datos actualizados", icon="🌿")
        st.experimental_rerun()
    st.markdown("---")
    st.markdown("### 🔗 Fuente de datos")
    st.markdown(f"[Ver Google Sheet ↗](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)", unsafe_allow_html=False)
    st.markdown("---")

# ── Cargar datos ────────────────────────────────────────────────────────────
try:
    with st.spinner("Cargando datos…"):
        df = load_data(CSV_URL)
except Exception as e:
    st.error(f"No se pudo cargar el sheet: {e}")
    st.stop()

if df.empty:
    st.warning("El sheet está vacío.")
    st.stop()

# ── Filtros en sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    grupos_disp = sorted(df["grupo"].dropna().unique().tolist()) if "grupo" in df.columns else []
    grupos_sel = st.multiselect("Grupo de participación", grupos_disp, default=grupos_disp)
    fechas_disp = df["fecha"].dropna() if "fecha" in df.columns else pd.Series(dtype="datetime64[ns]")
    if not fechas_disp.empty:
        fecha_min = fechas_disp.min().date()
        fecha_max = fechas_disp.max().date()
        rango = st.date_input("Rango de fechas", value=(fecha_min, fecha_max))
        if isinstance(rango, (list, tuple)) and len(rango) == 2:
            f_ini, f_fin = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
        else:
            f_ini, f_fin = pd.Timestamp(fecha_min), pd.Timestamp(fecha_max)
    else:
        f_ini = f_fin = None
    campañas_sel = st.multiselect("Campañas a mostrar", list(CAMPAIGNS.keys()), default=list(CAMPAIGNS.keys()))
    st.markdown("---")
    st.markdown(f'<div class="update-badge">🕒 Última carga: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# ── Aplicar filtros ──────────────────────────────────────────────────────────
mask = pd.Series(True, index=df.index)
if grupos_sel and "grupo" in df.columns:
    mask &= df["grupo"].isin(grupos_sel)
if f_ini is not None and f_fin is not None and "fecha" in df.columns:
    mask &= df["fecha"].between(f_ini, f_fin)
df_f = df[mask].copy()
if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Métricas Generales</div>', unsafe_allow_html=True)
total_reg = len(df_f)
total_part = int(df_f["participa_alguna"].sum()) if "participa_alguna" in df_f.columns else 0
kg_botellas = df_f["botellas_kg"].sum() if "botellas_kg" in df_f.columns else 0.0
kg_tapas = df_f["tapas_kg"].sum() if "tapas_kg" in df_f.columns else 0.0
kg_aceite = df_f["aceite_kg"].sum() if "aceite_kg" in df_f.columns else 0.0
pct_part = round(total_part / total_reg * 100, 1) if total_reg else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(f'<div class="metric-card" style="border-color:#2ecc71"><h3>Total Registros</h3><h1 style="color:#2ecc71">{total_reg}</h1></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card" style="border-color:#3498db"><h3>Participantes activos</h3><h1 style="color:#3498db">{total_part}</h1><p>{pct_part}%</p></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-card" style="border-color:#2ecc71"><h3>Botellas</h3><h1 style="color:#2ecc71">{kg_botellas:.1f} kg</h1></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-card" style="border-color:#3498db"><h3>Tapas</h3><h1 style="color:#3498db">{kg_tapas:.1f} kg</h1></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="metric-card" style="border-color:#f39c12"><h3>Aceite</h3><h1 style="color:#f39c12">{kg_aceite:.1f} kg</h1></div>', unsafe_allow_html=True)

# ── Participación por grupo y campaña ────────────────────────────────────────
st.markdown('<div class="section-title">👥 Participación por Grupo y Campaña</div>', unsafe_allow_html=True)
r1c1, r1c2 = st.columns([1,1])

with r1c1:
    if "grupo" in df_f.columns:
        grupo_counts = df_f["grupo"].value_counts().reset_index()
        grupo_counts.columns = ["Grupo","Registros"]
        fig = px.pie(grupo_counts, names="Grupo", values="Registros", hole=0.55,
                     color="Grupo",
                     color_discrete_map={"Tienda":COLORS["tienda"], "Operación":COLORS["operacion"], "Administrativo":COLORS["admin"]},
                     title="Registros por grupo")
        fig.update_traces(textposition="outside", textinfo="percent+label")
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    else:
        st.info("No hay columna 'grupo'.")

with r1c2:
    camp_cols = [CAMPAIGNS[c] for c in campañas_sel if c in CAMPAIGNS]
    rows = []
    for grupo in df_f["grupo"].dropna().unique() if "grupo" in df_f.columns else []:
        sub = df_f[df_f["grupo"] == grupo]
        for col in camp_cols:
            rows.append({"Grupo": grupo, "Campaña": camp_labels[col], "kg": sub[col].sum() if col in sub.columns else 0})
    df_camp = pd.DataFrame(rows)
    if not df_camp.empty:
        fig = px.bar(df_camp, x="Grupo", y="kg", color="Campaña", barmode="group",
                     color_discrete_sequence=CAMPAIGN_COLORS, title="Kg por grupo y campaña", labels={"kg":"Kg"})
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    else:
        st.info("No hay datos para mostrar por campaña y grupo.")

# ── Tendencia temporal ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">📅 Evolución Temporal</div>', unsafe_allow_html=True)
if camp_cols and "fecha" in df_f.columns:
    df_time = df_f.groupby("fecha")[camp_cols].sum().reset_index().sort_values("fecha")
    df_time_melt = df_time.melt(id_vars="fecha", value_vars=camp_cols, var_name="camp", value_name="kg")
    df_time_melt["Campaña"] = df_time_melt["camp"].map(camp_labels)
    fig = px.line(df_time_melt, x="fecha", y="kg", color="Campaña", markers=True,
                  color_discrete_sequence=CAMPAIGN_COLORS, title="Kg recolectados por día")
    fig.update_traces(line_width=2.5, marker_size=6)
    st.plotly_chart(styled_fig(fig), use_container_width=True)
else:
    st.info("No hay datos de fecha o campañas seleccionadas para la evolución temporal.")

# ── Desglose por área administrativa ────────────────────────────────────────
st.markdown('<div class="section-title">🏢 Desglose por Área Administrativa</div>', unsafe_allow_html=True)
df_admin = df_f[df_f["grupo"] == "Administrativo"].copy() if "grupo" in df_f.columns else pd.DataFrame()
if not df_admin.empty and camp_cols:
    admin_sum = df_admin.groupby("area_admin")[camp_cols].sum().reset_index()
    admin_melt = admin_sum.melt(id_vars="area_admin", value_vars=camp_cols, var_name="col", value_name="kg")
    admin_melt["Campaña"] = admin_melt["col"].map(camp_labels)
    admin_melt = admin_melt[admin_melt["kg"] > 0]
    if not admin_melt.empty:
        fig = px.bar(admin_melt, x="kg", y="area_admin", color="Campaña", orientation="h", barmode="stack",
                     color_discrete_sequence=CAMPAIGN_COLORS, title="Kg recolectados – Áreas Administrativas",
                     labels={"area_admin":"Área","kg":"Kg"})
        fig.update_traces(marker_line_width=0)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    else:
        st.info("No hay registros administrativos con kg > 0.")
else:
    st.info("No hay registros administrativos con los filtros actuales.")

# ── Ranking por Grupos Administrativos (custom mapping) ─────────────────────
st.markdown('<div class="section-title">🏷️ Ranking por Grupos Administrativos (agrupado)</div>', unsafe_allow_html=True)

AREA_TO_GROUP_LOWER = {
    "sga": "Grupo 1", "sst": "Grupo 1", "sistemas": "Grupo 1", "inventarios": "Grupo 1", "comercial": "Grupo 1",
    "finanzas": "Grupo 2", "fiananzas": "Grupo 2",
    "rrhh": "Grupo 3",
    "diseño": "Grupo 4", "diseno": "Grupo 4",
    "mercadeo": "Grupo 5",
    "tintoreria": "Grupo 6", "tintorería": "Grupo 6",
}

def map_area_to_group(area):
    if pd.isna(area):
        return "Otros"
    key = normalize_text(area)
    return AREA_TO_GROUP_LOWER.get(key, "Otros")

if not df_admin.empty and camp_cols:
    df_admin_groups = df_admin.copy()
    df_admin_groups["grupo_admin_custom"] = df_admin_groups["area_admin"].apply(map_area_to_group)
    # sum per custom group
    group_sum = df_admin_groups.groupby("grupo_admin_custom")[camp_cols].sum()
    if not group_sum.empty:
        group_sum = group_sum.reset_index()
        group_sum["total_kg"] = group_sum[camp_cols].sum(axis=1)
        group_sum = group_sum.sort_values("total_kg", ascending=False)
        # melt for stacked bar
        group_melt = group_sum.melt(id_vars=["grupo_admin_custom","total_kg"], value_vars=camp_cols, var_name="col", value_name="kg")
        group_melt["Campaña"] = group_melt["col"].map(camp_labels)
        # ensure category order (largest first)
        order = group_sum["grupo_admin_custom"].tolist()
        fig = px.bar(group_melt, x="kg", y="grupo_admin_custom", color="Campaña", orientation="h", barmode="stack",
                     category_orders={"grupo_admin_custom": order},
                     color_discrete_sequence=CAMPAIGN_COLORS,
                     title="Ranking por Grupos Administrativos (kg totales por campaña)",
                     labels={"grupo_admin_custom":"Grupo Administrativo","kg":"Kg"})
        fig.update_traces(marker_line_width=0)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    else:
        st.info("No hay datos para agrupar por grupos administrativos.")
else:
    st.info("No hay datos administrativos o campañas seleccionadas para el ranking por grupos.")

# ── Tiendas y ranking individual (Operación) ─────────────────────────────────
st.markdown('<div class="section-title">🏪 Tiendas y Ranking Individual</div>', unsafe_allow_html=True)
r4c1, r4c2 = st.columns([1,1.4])

with r4c1:
    df_tienda = df_f[df_f["grupo"] == "Tienda"].copy() if "grupo" in df_f.columns else pd.DataFrame()
    if not df_tienda.empty and camp_cols:
        tienda_sum = df_tienda.groupby("tienda")[camp_cols].sum().reset_index()
        tienda_sum["total_kg"] = tienda_sum[camp_cols].sum(axis=1)
        top_tiendas = tienda_sum.sort_values("total_kg", ascending=False).head(10)
        tienda_melt = top_tiendas.melt(id_vars="tienda", value_vars=camp_cols, var_name="col", value_name="kg")
        tienda_melt["Campaña"] = tienda_melt["col"].map(camp_labels)
        fig = px.bar(tienda_melt, x="tienda", y="kg", color="Campaña", barmode="group",
                     color_discrete_sequence=CAMPAIGN_COLORS, title="Kg por Tienda (Top 10)")
        fig.update_layout(xaxis={'categoryorder':'total descending'})
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig), use_container_width=True)
    else:
        st.info("No hay registros de Tienda con los filtros actuales.")

with r4c2:
    df_oper = df_f[df_f["grupo"] == "Operación"].copy() if "grupo" in df_f.columns else pd.DataFrame()
    if not df_oper.empty and camp_cols:
        df_oper["total_kg"] = df_oper[camp_cols].sum(axis=1)
        ranking = df_oper.groupby("nombre_operacion")["total_kg"].sum().reset_index().sort_values("total_kg", ascending=False).head(10)
        ranking = ranking[ranking["nombre_operacion"].notna()]
        if not ranking.empty:
            ranking_plot = ranking.sort_values("total_kg", ascending=True)
            fig = px.bar(ranking_plot, x="total_kg", y="nombre_operacion", orientation="h",
                         labels={"total_kg":"Total kg","nombre_operacion":"Persona"},
                         title="Top 10 personas de Operación (kg totales)")
            fig.update_traces(marker_color=COLORS["operacion"], texttemplate="%{x:.1f}", textposition="outside")
            fig.update_layout(height=420, margin=dict(l=160, r=20, t=40, b=20))
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(styled_fig(fig), use_container_width=True)
        else:
            st.info("No hay personas de Operación con registros válidos.")
    else:
        st.info("No hay datos de Operación para el ranking.")

# ── Nuevas gráficas por persona (ordenadas de mayor a menor) ────────────────
st.markdown('<div class="section-title">👤 Gráficas por Persona — Operación y Aceite</div>', unsafe_allow_html=True)

# 1) Solo operativos para Botellas
df_oper_botellas = df_f[(df_f["grupo"] == "Operación") & (df_f["botellas_kg"].fillna(0) > 0) & df_f["nombre_operacion"].notna()].copy()
if not df_oper_botellas.empty:
    grp = df_oper_botellas.groupby("nombre_operacion")["botellas_kg"].sum().reset_index().sort_values("botellas_kg", ascending=False).head(20)
    grp_plot = grp.sort_values("botellas_kg", ascending=True)
    fig = px.bar(grp_plot, x="botellas_kg", y="nombre_operacion", orientation="h",
                 labels={"botellas_kg":"Kg (Botellas)","nombre_operacion":"Persona"},
                 title="Top Operativos — Botellas (kg)")
    fig.update_traces(marker_color=COLORS["botellas"], texttemplate="%{x:.1f}", textposition="outside")
    fig.update_layout(height=420, margin=dict(l=160, r=20, t=40, b=20))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(styled_fig(fig), use_container_width=True)
else:
    st.info("No hay operativos con participación en Botellas dentro del rango seleccionado.")

# 2) Solo operativos para Tapas
df_oper_tapas = df_f[(df_f["grupo"] == "Operación") & (df_f["tapas_kg"].fillna(0) > 0) & df_f["nombre_operacion"].notna()].copy()
if not df_oper_tapas.empty:
    grp = df_oper_tapas.groupby("nombre_operacion")["tapas_kg"].sum().reset_index().sort_values("tapas_kg", ascending=False).head(20)
    grp_plot = grp.sort_values("tapas_kg", ascending=True)
    fig = px.bar(grp_plot, x="tapas_kg", y="nombre_operacion", orientation="h",
                 labels={"tapas_kg":"Kg (Tapas)","nombre_operacion":"Persona"},
                 title="Top Operativos — Tapas (kg)")
    fig.update_traces(marker_color=COLORS["tapas"], texttemplate="%{x:.1f}", textposition="outside")
    fig.update_layout(height=420, margin=dict(l=160, r=20, t=40, b=20))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(styled_fig(fig), use_container_width=True)
else:
    st.info("No hay operativos con participación en Tapas dentro del rango seleccionado.")

# 3) Todos con nombre que participaron en Aceite (Operación + Administrativo), excluir Tienda
df_aceite_nombres = df_f[(df_f["aceite_kg"].fillna(0) > 0) & df_f["nombre_operacion"].notna() & (df_f["grupo"] != "Tienda")].copy()
if not df_aceite_nombres.empty:
    grp = df_aceite_nombres.groupby("nombre_operacion")["aceite_kg"].sum().reset_index().sort_values("aceite_kg", ascending=False).head(40)
    grp_plot = grp.sort_values("aceite_kg", ascending=True)
    fig = px.bar(grp_plot, x="aceite_kg", y="nombre_operacion", orientation="h",
                 labels={"aceite_kg":"Kg (Aceite)","nombre_operacion":"Persona"},
                 title="Participantes con Nombre — Aceite (Operación + Administrativo)")
    fig.update_traces(marker_color=COLORS["aceite"], texttemplate="%{x:.1f}", textposition="outside")
    fig.update_layout(height=520, margin=dict(l=200, r=20, t=40, b=20))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(styled_fig(fig), use_container_width=True)
else:
    st.info("No hay participantes con nombre que hayan participado en Aceite dentro del rango seleccionado.")

# ── Heatmap de contribución ──────────────────────────────────────────────────
if camp_cols:
    st.markdown('<div class="section-title">🔥 Mapa de Calor – Contribución por Fecha y Campaña</div>', unsafe_allow_html=True)
    heatmap_data = df_f.groupby("fecha")[camp_cols].sum().T
    heatmap_data.index = [camp_labels[c] for c in heatmap_data.index]
    heatmap_data.columns = [str(d.date()) for d in pd.to_datetime(heatmap_data.columns)]
    fig = px.imshow(heatmap_data, color_continuous_scale="Greens", aspect="auto",
                    title="Distribución de kg por día y campaña", labels={"x":"Fecha","y":"Campaña","color":"Kg"})
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(styled_fig(fig), use_container_width=True)

# ── Tabla detallada y export ─────────────────────────────────────────────────
st.markdown('<div class="section-title">🗃️ Datos Detallados</div>', unsafe_allow_html=True)
with st.expander("Ver tabla completa de registros", expanded=False):
    display_cols = ["fecha","grupo","area_admin","nombre_operacion","tienda","botellas_kg","tapas_kg","aceite_kg"]
    available = [c for c in display_cols if c in df_f.columns]
    st.dataframe(df_f[available].rename(columns={
        "fecha":"Fecha","grupo":"Grupo","area_admin":"Área Admin","nombre_operacion":"Persona Oper.","tienda":"Tienda",
        "botellas_kg":"Botellas (kg)","tapas_kg":"Tapas (kg)","aceite_kg":"Aceite (kg)"
    }), use_container_width=True, height=340)
    csv_export = df_f[available].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV filtrado", csv_export, "campanas_ambientales.csv", "text/csv", use_container_width=True)

# ── Estadísticas descriptivas ───────────────────────────────────────────────
st.markdown('<div class="section-title">📐 Estadísticas Descriptivas</div>', unsafe_allow_html=True)
with st.expander("Ver estadísticas por campaña"):
    if camp_cols:
        stats = df_f[camp_cols].describe().T
        stats.index = [camp_labels[c] for c in stats.index]
        st.dataframe(stats, use_container_width=True)
    else:
        st.info("Selecciona al menos una campaña para ver estadísticas.")
