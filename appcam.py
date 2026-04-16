import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
from datetime import datetime
from io import StringIO

# ── Configuración de la página ───────────────────────────────────────────────
st.set_page_config(page_title="Campañas Ambientales", page_icon="🌿", layout="wide")

# ── Estilos mínimos ─────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .section-title { font-size:1rem; font-weight:700; color:#e2e8f0; border-left:3px solid #2ecc71; padding-left:10px; margin:18px 0 8px 0; }
    .metric-card { background: linear-gradient(135deg,#1c1f26,#252933); border-radius:10px; padding:12px; color:#e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constantes y colores ────────────────────────────────────────────────────
SHEET_ID = "157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

COLORS = {
    "botellas": "#2ecc71",
    "tapas": "#3498db",
    "aceite": "#f39c12",
    "operacion": "#e74c3c",
    "admin": "#1abc9c",
    "tienda": "#9b59b6",
}
CAMPAIGNS = {
    "Botellas con amor": "botellas_kg",
    "Tapas para sanar": "tapas_kg",
    "Aceite Green Fuel": "aceite_kg",
}
CAMPAIGN_COLORS = [COLORS["botellas"], COLORS["tapas"], COLORS["aceite"]]

# ── Utilidades ──────────────────────────────────────────────────────────────
def normalize_colname(s: str) -> str:
    return str(s).strip().lower()

def find_column_by_keywords(cols, keywords):
    for c in cols:
        cn = normalize_colname(c)
        if all(k in cn for k in keywords):
            return c
    # fallback: return first column that contains any keyword
    for c in cols:
        cn = normalize_colname(c)
        for k in keywords:
            if k in cn:
                return c
    return None

def extract_number_series(s: pd.Series) -> pd.Series:
    """Convierte una serie con valores numéricos o textos como 'No Participa' a float (NaN si no aplica)."""
    # Try direct numeric conversion first
    out = pd.to_numeric(s, errors="coerce")
    # If many NaNs, try to extract numbers from strings
    if out.isna().mean() > 0.2:
        def extract(x):
            if pd.isna(x):
                return np.nan
            x = str(x).strip()
            if x.lower() in ("no participa", "no_participa", "no", "n/a", "nan", ""):
                return np.nan
            m = re.search(r"(-?\d+[.,]?\d*)", x)
            if m:
                return float(m.group(1).replace(",", "."))
            return np.nan
        out = s.apply(extract).astype("float64")
    return out

# ── Cargar y preparar datos ──────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_and_prepare(url: str) -> pd.DataFrame:
    # Read as text to avoid dtype surprises
    df = pd.read_csv(url, dtype=str)
    # strip column names
    df.columns = [str(c).strip() for c in df.columns]
    cols = df.columns.tolist()

    # Detect columns based on the Excel you provided
    date_col = find_column_by_keywords(cols, ["fecha"]) or find_column_by_keywords(cols, ["marca temporal"])
    group_col = find_column_by_keywords(cols, ["indique su grupo", "grupo"])
    area_admin_col = find_column_by_keywords(cols, ["si es administrativo", "area", "área"])
    name_col = find_column_by_keywords(cols, ["si es de operación", "nombre", "indique el nombre"])
    tienda_col = find_column_by_keywords(cols, ["indique la tienda", "tienda"])
    # campaign raw columns
    botellas_col = find_column_by_keywords(cols, ["botellas"])
    tapas_col = find_column_by_keywords(cols, ["tapas"])
    aceite_col = find_column_by_keywords(cols, ["aceite"])

    # Create normalized columns
    # Fecha
    if date_col:
        df["fecha"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    else:
        df["fecha"] = pd.NaT

    # Grupo
    if group_col:
        df["grupo"] = df[group_col].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    else:
        df["grupo"] = np.nan

    # Area admin
    if area_admin_col:
        df["area_admin"] = df[area_admin_col].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    else:
        df["area_admin"] = np.nan

    # Nombre (operación o administrativos que pusieron nombre)
    if name_col:
        df["nombre"] = df[name_col].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    else:
        df["nombre"] = np.nan

    # Tienda
    if tienda_col:
        df["tienda"] = df[tienda_col].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    else:
        df["tienda"] = np.nan

    # Campaign numeric parsing
    df["botellas_kg"] = extract_number_series(df[botellas_col]) if botellas_col else np.nan
    df["tapas_kg"] = extract_number_series(df[tapas_col]) if tapas_col else np.nan
    df["aceite_kg"] = extract_number_series(df[aceite_col]) if aceite_col else np.nan

    # Participation flags
    df["participa_botellas"] = df["botellas_kg"].notna()
    df["participa_tapas"] = df["tapas_kg"].notna()
    df["participa_aceite"] = df["aceite_kg"].notna()
    df["participa_alguna"] = df[["participa_botellas", "participa_tapas", "participa_aceite"]].any(axis=1)

    # Normalize text columns to consistent casing for comparisons
    df["grupo_norm"] = df["grupo"].astype(str).str.strip().str.lower().replace({"nan": np.nan})
    df["area_admin_norm"] = df["area_admin"].astype(str).str.strip().str.lower().replace({"nan": np.nan})
    df["nombre_norm"] = df["nombre"].astype(str).str.strip().replace({"nan": np.nan})
    df["tienda_norm"] = df["tienda"].astype(str).str.strip().replace({"nan": np.nan})

    return df

df = load_and_prepare(CSV_URL)

# ── Sidebar: filtros ────────────────────────────────────────────────────────
st.sidebar.markdown("## 🔎 Filtros")
# grupos disponibles (presented as original strings)
grupos_disp = sorted(df["grupo"].dropna().unique().tolist()) if "grupo" in df.columns else []
grupos_sel = st.sidebar.multiselect("Grupo de participación", grupos_disp, default=grupos_disp)

# fecha range
fechas_disp = df["fecha"].dropna() if "fecha" in df.columns else pd.Series(dtype="datetime64[ns]")
if not fechas_disp.empty:
    fecha_min = fechas_disp.min().date()
    fecha_max = fechas_disp.max().date()
    rango = st.sidebar.date_input("Rango de fechas", value=(fecha_min, fecha_max))
    if isinstance(rango, (list, tuple)) and len(rango) == 2:
        f_ini, f_fin = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
    else:
        f_ini, f_fin = pd.Timestamp(fecha_min), pd.Timestamp(fecha_max)
else:
    f_ini = f_fin = None

campañas_sel = st.sidebar.multiselect("Campañas a mostrar", list(CAMPAIGNS.keys()), default=list(CAMPAIGNS.keys()))
st.sidebar.markdown("---")
st.sidebar.markdown(f"Última carga: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ── Aplicar filtros ──────────────────────────────────────────────────────────
mask = pd.Series(True, index=df.index)
if grupos_sel and "grupo" in df.columns:
    mask &= df["grupo"].isin(grupos_sel)
if f_ini is not None and f_fin is not None and "fecha" in df.columns:
    # inclusive date filter
    mask &= (df["fecha"].dt.date >= f_ini.date()) & (df["fecha"].dt.date <= f_fin.date())
df_f = df[mask].copy()

if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Métricas Generales</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(f'<div class="metric-card"><strong>Total registros</strong><div style="font-size:20px">{len(df_f)}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card"><strong>Participantes activos</strong><div style="font-size:20px">{int(df_f["participa_alguna"].sum())}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-card"><strong>Botellas (kg)</strong><div style="font-size:20px">{df_f["botellas_kg"].sum():.1f}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-card"><strong>Tapas (kg)</strong><div style="font-size:20px">{df_f["tapas_kg"].sum():.1f}</div></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="metric-card"><strong>Aceite (kg)</strong><div style="font-size:20px">{df_f["aceite_kg"].sum():.1f}</div></div>', unsafe_allow_html=True)

# ── Participación por grupo (pie) y por campaña (barras) ────────────────────
st.markdown('<div class="section-title">👥 Participación por Grupo y Campaña</div>', unsafe_allow_html=True)
r1, r2 = st.columns([1, 1])

with r1:
    if "grupo" in df_f.columns:
        grp_counts = df_f["grupo"].value_counts().reset_index()
        grp_counts.columns = ["Grupo", "Registros"]
        fig = px.pie(grp_counts, names="Grupo", values="Registros", hole=0.55,
                     color="Grupo",
                     color_discrete_map={"Tienda": COLORS["tienda"], "Operación": COLORS["operacion"], "Administrativo": COLORS["admin"]},
                     title="Registros por grupo")
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay columna 'grupo' en los datos.")

with r2:
    camp_cols = [CAMPAIGNS[c] for c in campañas_sel if c in CAMPAIGNS]
    rows = []
    for grupo in df_f["grupo"].dropna().unique() if "grupo" in df_f.columns else []:
        sub = df_f[df_f["grupo"] == grupo]
        for col in camp_cols:
            rows.append({"Grupo": grupo, "Campaña": col, "kg": sub[col].sum() if col in sub.columns else 0})
    df_camp = pd.DataFrame(rows)
    if not df_camp.empty:
        order = df_camp.groupby("Grupo")["kg"].sum().sort_values(ascending=False).index.tolist()
        fig = px.bar(df_camp, x="Grupo", y="kg", color="Campaña", barmode="group",
                     category_orders={"Grupo": order},
                     color_discrete_sequence=CAMPAIGN_COLORS, title="Kg por grupo y campaña", labels={"kg": "Kg"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar por campaña y grupo.")

# ── Desglose por área administrativa ────────────────────────────────────────
st.markdown('<div class="section-title">🏢 Desglose por Área Administrativa</div>', unsafe_allow_html=True)
df_admin = df_f[df_f["grupo"].str.lower().fillna("") == "administrativo"].copy()
if not df_admin.empty and camp_cols:
    admin_sum = df_admin.groupby("area_admin")[camp_cols].sum().reset_index()
    admin_melt = admin_sum.melt(id_vars="area_admin", value_vars=camp_cols, var_name="col", value_name="kg")
    admin_melt["Campaña"] = admin_melt["col"].map({v: k for k, v in CAMPAIGNS.items()})
    admin_melt = admin_melt[admin_melt["kg"] > 0]
    if not admin_melt.empty:
        fig = px.bar(admin_melt, x="kg", y="area_admin", color="Campaña", orientation="h", barmode="stack",
                     color_discrete_sequence=CAMPAIGN_COLORS, title="Kg recolectados – Áreas Administrativas")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay registros administrativos con kg > 0.")
else:
    st.info("No hay registros administrativos con los filtros actuales.")

# ── Ranking por Grupos Administrativos (agrupado) ───────────────────────────
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
    key = str(area).strip().lower()
    return AREA_TO_GROUP_LOWER.get(key, "Otros")

if not df_admin.empty and camp_cols:
    df_admin_groups = df_admin.copy()
    df_admin_groups["grupo_admin_custom"] = df_admin_groups["area_admin"].apply(map_area_to_group)
    group_sum = df_admin_groups.groupby("grupo_admin_custom")[camp_cols].sum()
    if not group_sum.empty:
        group_sum = group_sum.reset_index()
        group_sum["total_kg"] = group_sum[camp_cols].sum(axis=1)
        group_sum = group_sum.sort_values("total_kg", ascending=False)
        group_melt = group_sum.melt(id_vars=["grupo_admin_custom", "total_kg"], value_vars=camp_cols, var_name="col", value_name="kg")
        group_melt["Campaña"] = group_melt["col"].map({v: k for k, v in CAMPAIGNS.items()})
        order = group_sum["grupo_admin_custom"].tolist()
        fig = px.bar(group_melt, x="kg", y="grupo_admin_custom", color="Campaña", orientation="h", barmode="stack",
                     category_orders={"grupo_admin_custom": order},
                     color_discrete_sequence=CAMPAIGN_COLORS, title="Ranking por Grupos Administrativos (kg totales)")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para agrupar por grupos administrativos.")
else:
    st.info("No hay datos administrativos o campañas seleccionadas para el ranking por grupos.")

# ── Tiendas y ranking individual de Operación ───────────────────────────────
st.markdown('<div class="section-title">🏪 Tiendas y Ranking Individual</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.4])

with c1:
    df_tienda = df_f[df_f["grupo"].str.lower().fillna("") == "tienda"].copy()
    if not df_tienda.empty and camp_cols:
        tienda_sum = df_tienda.groupby("tienda")[camp_cols].sum().reset_index()
        tienda_sum["total_kg"] = tienda_sum[camp_cols].sum(axis=1)
        top_tiendas = tienda_sum.sort_values("total_kg", ascending=False).head(10)
        tienda_melt = top_tiendas.melt(id_vars="tienda", value_vars=camp_cols, var_name="col", value_name="kg")
        tienda_melt["Campaña"] = tienda_melt["col"].map({v: k for k, v in CAMPAIGNS.items()})
        fig = px.bar(tienda_melt, x="tienda", y="kg", color="Campaña", barmode="group", title="Kg por Tienda (Top 10)")
        fig.update_layout(xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay registros de Tienda con los filtros actuales.")

with c2:
    df_oper = df_f[df_f["grupo"].str.lower().fillna("") == "operación"].copy()
    if not df_oper.empty and camp_cols:
        df_oper["total_kg"] = df_oper[camp_cols].sum(axis=1)
        ranking = df_oper.groupby("nombre")["total_kg"].sum().reset_index().sort_values("total_kg", ascending=False).head(10)
        ranking = ranking[ranking["nombre"].notna()]
        if not ranking.empty:
            ranking_plot = ranking.sort_values("total_kg", ascending=True)
            fig = px.bar(ranking_plot, x="total_kg", y="nombre", orientation="h",
                         labels={"total_kg": "Total kg", "nombre": "Persona"},
                         title="Top 10 personas de Operación (kg totales)")
            fig.update_traces(marker_color=COLORS["operacion"], texttemplate="%{x:.1f}", textposition="outside")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay personas de Operación con registros válidos.")
    else:
        st.info("No hay datos de Operación para el ranking.")

# ── Tres gráficas solicitadas: operativos botellas, operativos tapas, nombres en aceite ─
st.markdown('<div class="section-title">👤 Gráficas por Persona — Operación y Aceite</div>', unsafe_allow_html=True)

# 1) Solo operativos para Botellas (ordenadas desc)
df_oper_bot = df_f[(df_f["grupo"].str.lower().fillna("") == "operación") & (df_f["botellas_kg"].fillna(0) > 0) & df_f["nombre"].notna()].copy()
if not df_oper_bot.empty:
    grp = df_oper_bot.groupby("nombre")["botellas_kg"].sum().reset_index().sort_values("botellas_kg", ascending=False)
    grp_plot = grp.sort_values("botellas_kg", ascending=True)
    fig = px.bar(grp_plot, x="botellas_kg", y="nombre", orientation="h",
                 labels={"botellas_kg": "Kg (Botellas)", "nombre": "Persona"},
                 title="Top Operativos — Botellas (kg)")
    fig.update_traces(marker_color=COLORS["botellas"], texttemplate="%{x:.1f}", textposition="outside")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay operativos con participación en Botellas dentro del rango seleccionado.")

# 2) Solo operativos para Tapas (ordenadas desc)
df_oper_tap = df_f[(df_f["grupo"].str.lower().fillna("") == "operación") & (df_f["tapas_kg"].fillna(0) > 0) & df_f["nombre"].notna()].copy()
if not df_oper_tap.empty:
    grp = df_oper_tap.groupby("nombre")["tapas_kg"].sum().reset_index().sort_values("tapas_kg", ascending=False)
    grp_plot = grp.sort_values("tapas_kg", ascending=True)
    fig = px.bar(grp_plot, x="tapas_kg", y="nombre", orientation="h",
                 labels={"tapas_kg": "Kg (Tapas)", "nombre": "Persona"},
                 title="Top Operativos — Tapas (kg)")
    fig.update_traces(marker_color=COLORS["tapas"], texttemplate="%{x:.1f}", textposition="outside")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay operativos con participación en Tapas dentro del rango seleccionado.")

# 3) Todos con nombre que participaron en Aceite (Operación + Administrativo), excluir Tienda
df_aceite_nombres = df_f[(df_f["aceite_kg"].fillna(0) > 0) & df_f["nombre"].notna() & (df_f["grupo"].str.lower().fillna("") != "tienda")].copy()
if not df_aceite_nombres.empty:
    grp = df_aceite_nombres.groupby("nombre")["aceite_kg"].sum().reset_index().sort_values("aceite_kg", ascending=False)
    grp_plot = grp.sort_values("aceite_kg", ascending=True)
    fig = px.bar(grp_plot, x="aceite_kg", y="nombre", orientation="h",
                 labels={"aceite_kg": "Kg (Aceite)", "nombre": "Persona"},
                 title="Participantes con Nombre — Aceite (Operación + Administrativo)")
    fig.update_traces(marker_color=COLORS["aceite"], texttemplate="%{x:.1f}", textposition="outside")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay participantes con nombre que hayan participado en Aceite dentro del rango seleccionado.")

# ── Tabla detallada y export ─────────────────────────────────────────────────
st.markdown('<div class="section-title">🗃️ Datos Detallados</div>', unsafe_allow_html=True)
display_cols = ["fecha", "grupo", "area_admin", "nombre", "tienda", "botellas_kg", "tapas_kg", "aceite_kg"]
available = [c for c in display_cols if c in df_f.columns]
st.dataframe(
    df_f[available].rename(columns={
        "fecha": "Fecha", "grupo": "Grupo", "area_admin": "Área Admin", "nombre": "Nombre",
        "tienda": "Tienda", "botellas_kg": "Botellas (kg)", "tapas_kg": "Tapas (kg)", "aceite_kg": "Aceite (kg)"
    }),
    use_container_width=True, height=360
)
csv_export = df_f[available].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar CSV filtrado", csv_export, "campanas_filtradas.csv", "text/csv", use_container_width=True)
