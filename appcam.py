import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Campañas Ambientales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta de colores y estilos ──────────────────────────────────────────────
COLORS = {
    "botellas":  "#2ecc71",   # verde
    "tapas":     "#3498db",   # azul
    "aceite":    "#f39c12",   # naranja
    "tienda":    "#9b59b6",   # morado
    "operacion": "#e74c3c",   # rojo
    "admin":     "#1abc9c",   # turquesa
    "bg":        "#0e1117",
    "card":      "#1c1f26",
    "text":      "#f0f2f6",
}

CAMPAIGN_COLORS = [COLORS["botellas"], COLORS["tapas"], COLORS["aceite"]]

st.markdown("""
<style>
/* Fondo general */
.main { background-color: #0e1117; }

/* Tarjetas métricas personalizadas */
.metric-card {
    background: linear-gradient(135deg, #1c1f26 0%, #252933 100%);
    border-radius: 12px;
    padding: 20px 24px;
    border-left: 4px solid;
    margin-bottom: 8px;
}
.metric-card h3 { margin: 0 0 4px 0; font-size: 13px; color: #8b949e; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
.metric-card h1 { margin: 0; font-size: 32px; font-weight: 700; }
.metric-card p  { margin: 4px 0 0 0; font-size: 12px; color: #8b949e; }

/* Header */
.dashboard-header {
    background: linear-gradient(90deg, #0e1117 0%, #1a2a1a 50%, #0e1117 100%);
    border-bottom: 1px solid #2ecc7133;
    padding: 16px 0 24px 0;
    margin-bottom: 24px;
}
.dashboard-header h1 { font-size: 2rem; font-weight: 800; color: #2ecc71; letter-spacing: -0.02em; margin: 0; }
.dashboard-header p  { color: #8b949e; margin: 4px 0 0 0; font-size: 14px; }

/* Sección título */
.section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #e2e8f0;
    border-left: 3px solid #2ecc71;
    padding-left: 10px;
    margin: 28px 0 12px 0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Badge de actualización */
.update-badge {
    background: #1c2a1c;
    border: 1px solid #2ecc7144;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #2ecc71;
    display: inline-block;
}

/* Tablas */
.dataframe { font-size: 13px !important; }

/* Dividers */
hr { border-color: #2a2d35; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)


# ── Constantes ───────────────────────────────────────────────────────────────
# Solo el ID del sheet (sin /edit?usp=sharing)
SHEET_ID = "157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8"

# URL de exportación CSV pública de Google Sheets
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

CAMPAIGNS = {
    "Botellas con amor": "botellas_kg",
    "Tapas para sanar":  "tapas_kg",
    "Aceite Green Fuel": "aceite_kg",
}

# Map de columna -> etiqueta legible
camp_labels = {v: k for k, v in CAMPAIGNS.items()}


# ── Funciones de carga y limpieza ────────────────────────────────────────────
@st.cache_data(ttl=0)   # ttl=0 → se respeta el botón de refresco manual
def load_data(url: str) -> pd.DataFrame:
    """Descarga y limpia los datos del Google Sheet."""
    df = pd.read_csv(url)

    # ── Renombrar columnas a nombres cortos ──────────────────────────────────
    expected_cols = list(df.columns[:10])
    if len(expected_cols) >= 10:
        col_map = {
            expected_cols[0]:  "marca_temporal",
            expected_cols[1]:  "fecha",
            expected_cols[2]:  "grupo",
            expected_cols[3]:  "area_admin",
            expected_cols[4]:  "nombre_operacion",
            expected_cols[5]:  "area_operacion",
            expected_cols[6]:  "tienda",
            expected_cols[7]:  "botellas_raw",
            expected_cols[8]:  "tapas_raw",
            expected_cols[9]:  "aceite_raw",
        }
        df = df.rename(columns=col_map)
    else:
        mapping_names = [
            "marca_temporal","fecha","grupo","area_admin","nombre_operacion",
            "area_operacion","tienda","botellas_raw","tapas_raw","aceite_raw"
        ]
        for i, col in enumerate(df.columns):
            df = df.rename(columns={col: mapping_names[i]})

    # ── Parsear fechas ───────────────────────────────────────────────────────
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    if "marca_temporal" in df.columns:
        df["marca_temporal"] = pd.to_datetime(df["marca_temporal"], dayfirst=True, errors="coerce")

    # ── Limpiar columnas de campaña ──────────────────────────────────────────
    def parse_campaign(series: pd.Series) -> pd.Series:
        cleaned = series.astype(str).str.strip()
        cleaned = cleaned.replace({"No Participa": np.nan, "nan": np.nan, "": np.nan})
        return pd.to_numeric(cleaned, errors="coerce")

    for raw_col, new_col in [("botellas_raw", "botellas_kg"), ("tapas_raw", "tapas_kg"), ("aceite_raw", "aceite_kg")]:
        if raw_col in df.columns:
            df[new_col] = parse_campaign(df[raw_col])
        else:
            df[new_col] = pd.Series([np.nan] * len(df))

    # ── Flags de participación ───────────────────────────────────────────────
    df["participa_botellas"] = df["botellas_kg"].notna()
    df["participa_tapas"]    = df["tapas_kg"].notna()
    df["participa_aceite"]   = df["aceite_kg"].notna()
    df["participa_alguna"]   = (
        df["participa_botellas"] | df["participa_tapas"] | df["participa_aceite"]
    )

    # ── Normalizar texto ─────────────────────────────────────────────────────
    for col in ["grupo", "area_admin", "area_operacion", "tienda"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"N/A": np.nan, "nan": np.nan})

    # ── Semana ───────────────────────────────────────────────────────────────
    if "fecha" in df.columns:
        df["semana"] = df["fecha"].dt.isocalendar().week.astype("Int64")
    else:
        df["semana"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    return df


def get_entity_label(row: pd.Series) -> str:
    """Devuelve la etiqueta del participante según su grupo."""
    if row.get("grupo") == "Tienda":
        return f"Tienda – {row.get('tienda')}" if pd.notna(row.get("tienda")) else "Tienda"
    elif row.get("grupo") == "Operación":
        nombre = row.get("nombre_operacion") if pd.notna(row.get("nombre_operacion")) else "—"
        area   = row.get("area_operacion")   if pd.notna(row.get("area_operacion"))   else "—"
        return f"{nombre} ({area})"
    elif row.get("grupo") == "Administrativo":
        return f"Admin – {row.get('area_admin')}" if pd.notna(row.get("area_admin")) else "Administrativo"
    return "Otro"


# ── Helpers de gráficas ───────────────────────────────────────────────────────
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


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
  <h1>🌿 Dashboard – Campañas Ambientales</h1>
  <p>Monitoreo en tiempo real · Botellas con Amor · Tapas para Sanar · Aceite Green Fuel</p>
</div>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/recycling.png", width=60)
    st.markdown("## ⚙️ Panel de Control")

    if st.button("🔄  Refrescar datos", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.toast("✅ Datos actualizados correctamente", icon="🌿")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔗 Fuente de datos")
    st.markdown(
        f"[Ver Google Sheet ↗](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)",
        unsafe_allow_html=False,
    )

    st.markdown("---")
    st.markdown("### 🎛️ Filtros")


# ── CARGA DE DATOS ───────────────────────────────────────────────────────────
try:
    with st.spinner("Cargando datos desde Google Sheets…"):
        df = load_data(CSV_URL)
except Exception as e:
    err_msg = str(e)
    if "404" in err_msg or "Not Found" in err_msg:
        st.error(
            "❌ No se pudo cargar el Sheet (HTTP 404). Verifica que:\n"
            "- El ID del Sheet sea correcto.\n"
            "- El Sheet sea público o compartido con 'Cualquiera con el enlace'.\n"
            "- No estés usando una URL con parámetros (/edit?usp=sharing) en lugar del ID.\n\n"
            f"Error técnico: `{err_msg}`"
        )
    else:
        st.error(f"❌ No se pudo cargar el Sheet. Verifica que sea público.\n\n`{err_msg}`")
    st.stop()

if df.empty:
    st.warning("⚠️ El Sheet está vacío.")
    st.stop()


# ── FILTROS EN SIDEBAR ────────────────────────────────────────────────────────
with st.sidebar:
    grupos_disp = sorted(df["grupo"].dropna().unique().tolist()) if "grupo" in df.columns else []
    grupos_sel  = st.multiselect("Grupo de participación", grupos_disp, default=grupos_disp)

    fechas_disp = df["fecha"].dropna() if "fecha" in df.columns else pd.Series(dtype="datetime64[ns]")
    if not fechas_disp.empty:
        fecha_min = fechas_disp.min().date()
        fecha_max = fechas_disp.max().date()
        rango     = st.date_input("Rango de fechas", value=(fecha_min, fecha_max))
        if len(rango) == 2:
            f_ini, f_fin = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
        else:
            f_ini, f_fin = pd.Timestamp(fecha_min), pd.Timestamp(fecha_max)
    else:
        f_ini = f_fin = None

    campañas_sel = st.multiselect(
        "Campañas a mostrar",
        list(CAMPAIGNS.keys()),
        default=list(CAMPAIGNS.keys()),
    )

    st.markdown("---")
    st.markdown(
        f'<div class="update-badge">🕒 Última carga: {datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )


# ── APLICAR FILTROS ───────────────────────────────────────────────────────────
mask = pd.Series([True] * len(df))
if grupos_sel:
    if "grupo" in df.columns:
        mask &= df["grupo"].isin(grupos_sel)
if f_ini and f_fin and "fecha" in df.columns:
    mask &= df["fecha"].between(f_ini, f_fin)
df_f = df[mask].copy()

if df_f.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados.")
    st.stop()


# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Métricas Generales</div>', unsafe_allow_html=True)

total_reg        = len(df_f)
total_part       = df_f["participa_alguna"].sum() if "participa_alguna" in df_f.columns else 0
kg_botellas      = df_f["botellas_kg"].sum() if "botellas_kg" in df_f.columns else 0.0
kg_tapas         = df_f["tapas_kg"].sum() if "tapas_kg" in df_f.columns else 0.0
kg_aceite        = df_f["aceite_kg"].sum() if "aceite_kg" in df_f.columns else 0.0
total_kg         = kg_botellas + kg_tapas + kg_aceite
pct_participacion = round(total_part / total_reg * 100, 1) if total_reg else 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card" style="border-color:#2ecc71">
      <h3>Total Registros</h3>
      <h1 style="color:#2ecc71">{total_reg}</h1>
      <p>respuestas recibidas</p>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-color:#3498db">
      <h3>Participantes activos</h3>
      <h1 style="color:#3498db">{int(total_part)}</h1>
      <p>{pct_participacion}% del total</p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="border-color:#2ecc71">
      <h3>🍶 Botellas con Amor</h3>
      <h1 style="color:#2ecc71">{kg_botellas:.1f} kg</h1>
      <p>{df_f['participa_botellas'].sum() if 'participa_botellas' in df_f.columns else 0} participantes</p>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card" style="border-color:#3498db">
      <h3>🔵 Tapas para Sanar</h3>
      <h1 style="color:#3498db">{kg_tapas:.1f} kg</h1>
      <p>{df_f['participa_tapas'].sum() if 'participa_tapas' in df_f.columns else 0} participantes</p>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card" style="border-color:#f39c12">
      <h3>🛢️ Aceite Green Fuel</h3>
      <h1 style="color:#f39c12">{kg_aceite:.1f} kg</h1>
      <p>{df_f['participa_aceite'].sum() if 'participa_aceite' in df_f.columns else 0} participantes</p>
    </div>""", unsafe_allow_html=True)


# ── FILA 1: Distribución por grupo + Participación por campaña ───────────────
st.markdown('<div class="section-title">👥 Participación por Grupo y Campaña</div>', unsafe_allow_html=True)
r1c1, r1c2 = st.columns([1, 1])

# Donut – participación por grupo
with r1c1:
    if "grupo" in df_f.columns:
        grupo_counts = df_f["grupo"].value_counts().reset_index()
        grupo_counts.columns = ["Grupo", "Registros"]
        fig_donut = px.pie(
            grupo_counts, values="Registros", names="Grupo",
            hole=0.55,
            color="Grupo",
            color_discrete_map={
                "Tienda":        COLORS["tienda"],
                "Operación":     COLORS["operacion"],
                "Administrativo":COLORS["admin"],
            },
            title="Registros por grupo",
        )
        fig_donut.update_traces(textposition="outside", textinfo="percent+label")
        st.plotly_chart(styled_fig(fig_donut), use_container_width=True)
    else:
        st.info("No hay columna 'grupo' en los datos.")

# Barras agrupadas – participación por campaña y grupo
with r1c2:
    camp_cols = [CAMPAIGNS[c] for c in campañas_sel if c in CAMPAIGNS]
    rows = []
    for grupo in df_f["grupo"].dropna().unique() if "grupo" in df_f.columns else []:
        sub = df_f[df_f["grupo"] == grupo]
        for col in camp_cols:
            rows.append({
                "Grupo":    grupo,
                "Campaña":  camp_labels[col],
                "kg":       sub[col].sum() if col in sub.columns else 0,
                "Personas": sub[col].notna().sum() if col in sub.columns else 0,
            })
    df_camp = pd.DataFrame(rows)

    if not df_camp.empty:
        fig_bar = px.bar(
            df_camp, x="Grupo", y="kg", color="Campaña", barmode="group",
            color_discrete_sequence=CAMPAIGN_COLORS,
            title="Kg recolectados por grupo y campaña",
            labels={"kg": "Kg recolectados"},
        )
        fig_bar.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig_bar), use_container_width=True)
    else:
        st.info("No hay datos para mostrar en 'Kg recolectados por grupo y campaña'.")


# ── FILA 2: Tendencia temporal ───────────────────────────────────────────────
st.markdown('<div class="section-title">📅 Evolución Temporal</div>', unsafe_allow_html=True)

camp_cols_sel = [CAMPAIGNS[c] for c in campañas_sel if c in CAMPAIGNS]
if camp_cols_sel and "fecha" in df_f.columns:
    df_time = (
        df_f.groupby("fecha")[camp_cols_sel]
        .sum()
        .reset_index()
        .sort_values("fecha")
    )
    df_time_melt = df_time.melt(id_vars="fecha", value_vars=camp_cols_sel,
                                 var_name="campaña_col", value_name="kg")
    df_time_melt["Campaña"] = df_time_melt["campaña_col"].map(camp_labels)

    fig_line = px.line(
        df_time_melt, x="fecha", y="kg", color="Campaña",
        markers=True,
        color_discrete_sequence=CAMPAIGN_COLORS,
        title="Kg recolectados por día",
        labels={"fecha": "Fecha", "kg": "Kg"},
    )
    fig_line.update_traces(line_width=2.5, marker_size=7)
    st.plotly_chart(styled_fig(fig_line), use_container_width=True)
else:
    st.info("No hay datos de fecha o campañas seleccionadas para la evolución temporal.")


# ── FILA 3: Desglose por área (solo Admin) ────────────────────────────────
st.markdown('<div class="section-title">🏢 Desglose por Área</div>', unsafe_allow_html=True)
r3c1, r3c2 = st.columns(2)

# Administrativo
with r3c1:
    df_admin = df_f[df_f["grupo"] == "Administrativo"].copy() if "grupo" in df_f.columns else pd.DataFrame()
    if not df_admin.empty:
        admin_sum = (
            df_admin.groupby("area_admin")[camp_cols_sel]
            .sum()
            .reset_index()
        )
        admin_melt = admin_sum.melt(id_vars="area_admin", value_vars=camp_cols_sel,
                                    var_name="col", value_name="kg")
        admin_melt["Campaña"] = admin_melt["col"].map(camp_labels)
        admin_melt = admin_melt[admin_melt["kg"] > 0]

        fig_admin = px.bar(
            admin_melt, x="kg", y="area_admin", color="Campaña",
            orientation="h", barmode="stack",
            color_discrete_sequence=CAMPAIGN_COLORS,
            title="Kg recolectados – Áreas Administrativas",
            labels={"area_admin": "Área", "kg": "Kg"},
        )
        fig_admin.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig_admin), use_container_width=True)
    else:
        st.info("No hay registros de Administrativo con los filtros actuales.")

# ── GRÁFICA: Ranking por Grupos Administrativos ────────────────────────
st.markdown('<div class="section-title">🏷️ Ranking por Grupos Administrativos</div>', unsafe_allow_html=True)

# Definición de mapeo de áreas a grupos (según tu especificación)
# Grupo 1 (SGA, SST, Sistemas, Inventarios, comercial)
# Grupo 2 (Finanzas)
# Grupo 3 (RRHH)
# Grupo 4 (Diseño)
# Grupo 5 (Mercadeo)
# Grupo 6 (Tintoreria)
AREA_TO_GROUP_LOWER = {
    "sga": "Grupo 1",
    "sst": "Grupo 1",
    "sistemas": "Grupo 1",
    "inventarios": "Grupo 1",
    "comercial": "Grupo 1",
    "finanzas": "Grupo 2",
    "fiananzas": "Grupo 2",  # por si hay typo
    "rrhh": "Grupo 3",
    "diseño": "Grupo 4",
    "diseno": "Grupo 4",
    "mercadeo": "Grupo 5",
    "tintoreria": "Grupo 6",
    "tintorería": "Grupo 6",
}
st.markdown(
    """
    <div style="font-size:13px;color:#9aa3ad;margin-top:8px;">
      <strong>Áreas por grupo:</strong>
      Grupo 1: (SGA, SST, Sistemas, Inventarios, Comercial) 
      Grupo 2: (Finanzas) Grupo 3: (RRHH)
      Grupo 4: (Diseño) 
      Grupo 5: (Mercadeo)
      Grupo 6: (Tintorería).
    </div>
    """,
    unsafe_allow_html=True,
)


def map_area_to_group(area_value: str) -> str:
    if pd.isna(area_value):
        return "Otros"
    key = str(area_value).strip().lower()
    return AREA_TO_GROUP_LOWER.get(key, "Otros")

if not df_admin.empty and camp_cols_sel:
    df_admin_groups = df_admin.copy()
    df_admin_groups["grupo_admin_custom"] = df_admin_groups["area_admin"].apply(map_area_to_group)

    group_sum = (
        df_admin_groups.groupby("grupo_admin_custom")[camp_cols_sel]
        .sum()
        .reset_index()
    )
    group_sum["total_kg"] = group_sum[camp_cols_sel].sum(axis=1)
    group_sum = group_sum.sort_values("total_kg", ascending=False)

    group_melt = group_sum.melt(id_vars=["grupo_admin_custom", "total_kg"], value_vars=camp_cols_sel,
                                var_name="col", value_name="kg")
    group_melt["Campaña"] = group_melt["col"].map(camp_labels)

    fig_group_rank = px.bar(
        group_melt, x="kg", y="grupo_admin_custom", color="Campaña",
        orientation="h", barmode="stack",
        category_orders={"grupo_admin_custom": group_sum["grupo_admin_custom"].tolist()},
        color_discrete_sequence=CAMPAIGN_COLORS,
        title="Ranking por Grupos Administrativos (kg totales por campaña)",
        labels={"grupo_admin_custom": "Grupo Administrativo", "kg": "Kg"},
    )
    fig_group_rank.update_layout(yaxis=dict(title="Grupo Administrativo"))
    fig_group_rank.update_traces(marker_line_width=0)
    st.plotly_chart(styled_fig(fig_group_rank), use_container_width=True)
else:
    st.info("No hay datos administrativos o campañas seleccionadas para el ranking por grupos.")


# ── FILA 4: Tiendas + Ranking individual ────────────────────────────────────
st.markdown('<div class="section-title">🏪 Tiendas y Ranking Individual</div>', unsafe_allow_html=True)
r4c1, r4c2 = st.columns([1, 1.4])

# Tiendas — Top 10 tiendas por kg
with r4c1:
    df_tienda = df_f[df_f["grupo"] == "Tienda"].copy() if "grupo" in df_f.columns else pd.DataFrame()
    if not df_tienda.empty and camp_cols_sel:
        tienda_sum = (
            df_tienda.groupby("tienda")[camp_cols_sel]
            .sum()
            .reset_index()
        )
        tienda_sum["total_kg"] = tienda_sum[camp_cols_sel].sum(axis=1)
        top_tiendas = tienda_sum.sort_values("total_kg", ascending=False).head(10)

        tienda_melt = top_tiendas.melt(id_vars="tienda", value_vars=camp_cols_sel,
                                       var_name="col", value_name="kg")
        tienda_melt["Campaña"] = tienda_melt["col"].map(camp_labels)

        fig_tienda = px.bar(
            tienda_melt, x="tienda", y="kg", color="Campaña", barmode="group",
            color_discrete_sequence=CAMPAIGN_COLORS,
            title="Kg por Tienda (Top 10 tiendas)",
            labels={"tienda": "Tienda", "kg": "Kg"},
        )
        fig_tienda.update_layout(xaxis={'categoryorder':'total descending'})
        fig_tienda.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig_tienda), use_container_width=True)
    else:
        st.info("No hay registros de Tienda con los filtros actuales.")

# Ranking individual (personas de Operación) — Top 10
with r4c2:
    df_oper2 = df_f[df_f["grupo"] == "Operación"].copy() if "grupo" in df_f.columns else pd.DataFrame()
    if not df_oper2.empty and camp_cols_sel:
        df_oper2["total_kg"] = df_oper2[camp_cols_sel].sum(axis=1)
        ranking = (
            df_oper2.groupby("nombre_operacion")["total_kg"]
            .sum()
            .reset_index()
            .sort_values("total_kg", ascending=False)
            .head(10)
        )
        ranking.columns = ["Persona", "Total kg"]

        fig_rank = px.bar(
            ranking, x="Total kg", y="Persona", orientation="h",
            title="Top 10 personas de Operación (kg totales)",
        )
        fig_rank.update_layout(yaxis=dict(categoryorder="total ascending"))
        fig_rank.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig_rank), use_container_width=True)
    else:
        st.info("No hay datos de Operación para el ranking."

# ── FILA 5: Heatmap de contribución ──────────────────────────────────────────
if camp_cols_sel:
    st.markdown('<div class="section-title">🔥 Mapa de Calor – Contribución por Fecha y Campaña</div>', unsafe_allow_html=True)

    heatmap_data = df_f.groupby("fecha")[camp_cols_sel].sum().T
    heatmap_data.index = [camp_labels[c] for c in heatmap_data.index]
    heatmap_data.columns = [str(d.date()) for d in pd.to_datetime(heatmap_data.columns)]

    fig_heat = px.imshow(
        heatmap_data,
        color_continuous_scale="Greens",
        aspect="auto",
        title="Distribución de kg por día y campaña",
        labels={"x": "Fecha", "y": "Campaña", "color": "Kg"},
    )
    fig_heat.update_xaxes(tickangle=-45)
    st.plotly_chart(styled_fig(fig_heat), use_container_width=True)


# ── TABLA DETALLADA ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗃️ Datos Detallados</div>', unsafe_allow_html=True)

with st.expander("Ver tabla completa de registros", expanded=False):
    display_cols = [
        "fecha", "grupo", "area_admin", "nombre_operacion",
        "area_operacion", "tienda", "botellas_kg", "tapas_kg", "aceite_kg",
    ]
    available_display_cols = [c for c in display_cols if c in df_f.columns]
    st.dataframe(
        df_f[available_display_cols].rename(columns={
            "fecha":            "Fecha",
            "grupo":            "Grupo",
            "area_admin":       "Área Admin",
            "nombre_operacion": "Persona Oper.",
            "area_operacion":   "Área Oper.",
            "tienda":           "Tienda",
            "botellas_kg":      "Botellas (kg)",
            "tapas_kg":         "Tapas (kg)",
            "aceite_kg":        "Aceite (kg)",
        }),
        use_container_width=True,
        height=340,
    )

    csv_export = df_f[available_display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Descargar CSV filtrado",
        csv_export,
        "campanas_ambientales.csv",
        "text/csv",
        use_container_width=True,
    )


# ── RESUMEN ESTADÍSTICO ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">📐 Estadísticas Descriptivas</div>', unsafe_allow_html=True)

with st.expander("Ver estadísticas por campaña"):
    if camp_cols_sel:
        stats = df_f[camp_cols_sel].describe().T
        stats.index = [camp_labels[c] for c in stats.index]
        stats = stats.rename(columns={
            "count": "N participantes", "mean": "Promedio (kg)",
            "std":   "Desv. estándar",  "min":  "Mínimo",
            "25%":   "Q1", "50%": "Mediana", "75%": "Q3", "max": "Máximo",
        })
        st.dataframe(stats.style.format("{:.2f}"), use_container_width=True)
    else:
        st.info("No hay campañas seleccionadas para mostrar estadísticas.")


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#555;font-size:12px'>"
    "🌱 Dashboard Campañas Ambientales · Datos en tiempo real desde Google Sheets · "
    f"Última carga: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>",
    unsafe_allow_html=True,
)
