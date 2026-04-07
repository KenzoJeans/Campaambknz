import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ─── Configuración de la página ─────────────────────────────────────────────
st.set_page_config(
    page_title="Campañas Ambientales — Recolección",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #0f766e 0%, #10b981 100%);
        color: white;
        padding: 1.2rem 1.6rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .main-header h1 { margin: 0; font-size: 1.4rem; font-weight: 600; }
    .section-title { font-size: 1rem; font-weight: 600; color: #0f172a; border-left: 4px solid #10b981; padding-left: 0.6rem; margin: 1rem 0 0.6rem; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-header"><h1>🌱 Dashboard — Campañas Ambientales</h1>'
    '<p>Participación y recolección por Botellas, Tapas y Aceite</p></div>',
    unsafe_allow_html=True
)

# ─── Funciones utilitarias y mapeo explícito ─────────────────────────────────
def safe_read_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

@st.cache_data
def load_and_prepare_gsheet(csv_url: str) -> pd.DataFrame:
    df = safe_read_csv(csv_url)

    # Renombrado explícito según encabezados de la hoja compartida
    rename_manual = {
        "Marca temporal": "timestamp",
        "Marca temporal ": "timestamp",
        "timestamp": "timestamp",
        "Timestamp": "timestamp",
        "Nombre:": "nombre",
        "Nombre": "nombre",
        "Área a la que pertenece:": "area",
        "Área a la que pertenece": "area",
        "Area a la que pertenece:": "area",
        "Area a la que pertenece": "area",
        "Botellas con amor\nSi = Otro (Indique peso kg)": "botellas",
        "Botellas con amor": "botellas",
        "Botellas": "botellas",
        "Tapas para sanar\nSi = Otro (Indique peso kg)": "tapas",
        "Tapas para sanar": "tapas",
        "Tapas": "tapas",
        "Aceite Green Fuel\nSi = Otro (Indique peso kg)": "aceite",
        "Aceite Green Fuel": "aceite",
        "Aceite": "aceite",
    }
    rename_map = {k: v for k, v in rename_manual.items() if k in df.columns}
    if rename_map:
        df = df.rename(columns=rename_map)

    # Normalizar nombres de columnas (quitar espacios extremos)
    df.columns = [c.strip() for c in df.columns]

    # Coercionar columnas numéricas (tratando "No" como NaN)
    for col in ["botellas", "tapas", "aceite"]:
        if col in df.columns:
            # Convertir a string, limpiar y extraer números cuando sea posible
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"No": np.nan, "no": np.nan, "NO": np.nan, "nan": np.nan})
            # Extraer números (por ejemplo "3 con" -> "3")
            df[col] = df[col].replace(r'[^0-9\.\-]+', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan

    # Campos auxiliares para agregación
    df["_botellas_kg"] = df["botellas"].fillna(0).astype(float)
    df["_tapas_kg"] = df["tapas"].fillna(0).astype(float)
    df["_aceite_kg"] = df["aceite"].fillna(0).astype(float)
    df["total_kg"] = df[["_botellas_kg", "_tapas_kg", "_aceite_kg"]].sum(axis=1)

    # Normalizar columna nombre y area si existen
    if "nombre" in df.columns:
        df["nombre"] = df["nombre"].astype(str).str.strip()
    if "area" in df.columns:
        df["area"] = df["area"].astype(str).str.strip()

    return df

# ─── Sidebar: URL y opciones ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Fuente de datos")
    default_url = "https://docs.google.com/spreadsheets/d/1fBG1FJuFwly_k6_HSwtP56eyoMehPAVrJlRbbfR8oGk/export?format=csv"
    gsheet_url = st.text_input("URL export CSV de Google Sheets", value=default_url)
    st.markdown("---")
    st.markdown("### Opciones")
    st.checkbox("Mostrar mapa de calor fijo (Área × Tipo)", value=True, disabled=True)
    st.markdown("---")
    st.caption("Asegúrate de que la hoja sea accesible: 'Cualquiera con el enlace puede ver'.")

# ─── Cargar datos ───────────────────────────────────────────────────────────
try:
    df = load_and_prepare_gsheet(gsheet_url)
except Exception as e:
    st.error(f"No se pudo leer la hoja: {e}")
    st.stop()

# Mostrar columnas detectadas en la barra lateral (útil para depuración)
st.sidebar.markdown("**Columnas detectadas:**")
st.sidebar.write(list(df.columns))

# Validar que exista la columna 'area'
if "area" not in df.columns:
    st.error(f"No se detectó la columna 'area'. Columnas disponibles: {list(df.columns)}")
    st.stop()

# ─── KPIs principales ───────────────────────────────────────────────────────
total_kg = df["total_kg"].sum()
n_registros = len(df)
n_areas = df["area"].nunique()
n_participantes = df["nombre"].nunique() if "nombre" in df.columns else 0

st.markdown('<div class="section-title">Resumen</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros", f"{n_registros}")
c2.metric("Participantes únicos", f"{n_participantes}")
c3.metric("Áreas", f"{n_areas}")
c4.metric("Total recolectado (kg)", f"{total_kg:.1f} kg")

# ─── Gráfica: participación por área (porcentaje de registros) ─────────────
st.markdown('<div class="section-title">Participación por Área</div>', unsafe_allow_html=True)
area_counts = df["area"].value_counts().reset_index()
area_counts.columns = ["area", "count"]
area_counts["pct"] = (area_counts["count"] / area_counts["count"].sum() * 100).round(1)

fig_particip = px.bar(
    area_counts.sort_values("count", ascending=False),
    x="area", y="count",
    text="pct",
    labels={"area": "Área", "count": "N° de registros"},
    title="Participación por Área (n° registros y %)"
)
fig_particip.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_color="#0ea5a4")
fig_particip.update_layout(xaxis_tickangle=-45, height=420)
st.plotly_chart(fig_particip, use_container_width=True)

# ─── Gráfica: ranking por nombre (top contribuidores por kg) ──────────────
st.markdown('<div class="section-title">Ranking por Nombre (kg recolectados)</div>', unsafe_allow_html=True)
if "nombre" in df.columns:
    name_agg = df.groupby("nombre").agg(total_kg=("total_kg", "sum"), registros=("total_kg", "count")).reset_index()
    name_agg = name_agg.sort_values("total_kg", ascending=False)
    # Mostrar top 20 por defecto
    top_n = st.slider("Mostrar top N contribuidores", min_value=5, max_value=50, value=10)
    name_top = name_agg.head(top_n)
    fig_name = px.bar(
        name_top,
        x="total_kg", y="nombre",
        orientation="h",
        text="total_kg",
        labels={"total_kg": "Kg recolectados", "nombre": "Nombre"},
        title=f"Top {top_n} contribuidores por Kg recolectados"
    )
    fig_name.update_traces(texttemplate="%{text:.1f} kg", marker_color="#f59e0b")
    fig_name.update_layout(yaxis=dict(autorange="reversed"), height=420)
    st.plotly_chart(fig_name, use_container_width=True)
else:
    st.info("No hay columna 'nombre' para generar el ranking.")

# ─── Gráfica: cantidad recolectada por campaña (barras) ────────────────────
st.markdown('<div class="section-title">Cantidad recolectada por campaña (kg)</div>', unsafe_allow_html=True)
type_totals = pd.DataFrame({
    "tipo": ["Botellas", "Tapas", "Aceite"],
    "kg": [
        df["_botellas_kg"].sum(),
        df["_tapas_kg"].sum(),
        df["_aceite_kg"].sum()
    ]
})
fig_types_bar = px.bar(
    type_totals, x="tipo", y="kg", text="kg",
    color="tipo",
    color_discrete_map={"Botellas": "#0ea5a4", "Tapas": "#f59e0b", "Aceite": "#ef4444"},
    title="Kg recolectados por campaña"
)
fig_types_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig_types_bar.update_layout(showlegend=False, yaxis_title="Kg", xaxis_title="", height=420)
st.plotly_chart(fig_types_bar, use_container_width=True)

# ─── Gráfica: diagrama de torta (participación por tipo en kg) ───────────
st.markdown('<div class="section-title">Distribución por tipo (torta)</div>', unsafe_allow_html=True)
fig_pie = px.pie(
    type_totals, names="tipo", values="kg",
    color="tipo",
    color_discrete_map={"Botellas": "#0ea5a4", "Tapas": "#f59e0b", "Aceite": "#ef4444"},
    title="Porcentaje de Kg recolectados por tipo",
    hole=0.4
)
fig_pie.update_traces(textinfo="percent+label")
fig_pie.update_layout(height=420)
st.plotly_chart(fig_pie, use_container_width=True)

# ─── Mapa de calor fijo: Área × Tipo (kg) ──────────────────────────────────
st.markdown('<div class="section-title">Mapa de calor (Área × Tipo) — fijo</div>', unsafe_allow_html=True)
area_heat = area_agg.set_index("area")[["_botellas_kg", "_tapas_kg", "_aceite_kg"]].fillna(0)
area_heat.columns = ["Botellas (kg)", "Tapas (kg)", "Aceite (kg)"]
if area_heat.empty:
    st.info("No hay datos para el mapa de calor.")
else:
    fig_heat = px.imshow(
        area_heat.values,
        x=area_heat.columns,
        y=area_heat.index,
        color_continuous_scale="RdYlGn_r",
        labels=dict(x="Tipo", y="Área", color="Kg"),
        text_auto=".1f",
        aspect="auto",
        title="Mapa de calor: Kg recolectados por Área y Tipo"
    )
    fig_heat.update_layout(height=520, margin=dict(l=140, r=20, t=60, b=60))
    st.plotly_chart(fig_heat, use_container_width=True)

# ─── Tabla detallada (Plotly) ───────────────────────────────────────────────
st.markdown('<div class="section-title">Registros detallados</div>', unsafe_allow_html=True)
display_cols = []
if "nombre" in df.columns:
    display_cols.append("nombre")
display_cols.append("area")
for c in ["botellas", "tapas", "aceite", "total_kg"]:
    if c in df.columns or c == "total_kg":
        display_cols.append(c)

df_table = df.copy()
# Format numeric columns for display
for c in ["botellas", "tapas", "aceite", "total_kg"]:
    if c in df_table.columns:
        df_table[c] = df_table[c].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "")

header_vals = [col.capitalize().replace("_", " ") for col in display_cols]
cell_vals = [df_table[col].astype(str).fillna("") .tolist() for col in display_cols]

fig_table = go.Figure(data=[go.Table(
    header=dict(values=header_vals, fill_color="#f1f5f9", align="left"),
    cells=dict(values=cell_vals, fill_color="white", align="left")
)])
fig_table.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=360)
st.plotly_chart(fig_table, use_container_width=True)

# ─── Exportar resumen por área (Excel) ──────────────────────────────────────
@st.cache_data
def to_excel_bytes(df_export: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Registros")
        summary = df.groupby("area").agg(
            registros=("total_kg", "count"),
            total_kg=("total_kg", "sum"),
            botellas_kg=("_botellas_kg", "sum"),
            tapas_kg=("_tapas_kg", "sum"),
            aceite_kg=("_aceite_kg", "sum"),
        ).reset_index()
        summary.to_excel(writer, index=False, sheet_name="Resumen por área")
    return output.getvalue()

excel_bytes = to_excel_bytes(df)
st.download_button("⬇️ Descargar Excel (registros + resumen)", data=excel_bytes,
                   file_name="campanas_recoleccion.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.caption("Dashboard de campañas ambientales — participación por área, ranking por nombre, recolección por campaña y mapa de calor fijo")
