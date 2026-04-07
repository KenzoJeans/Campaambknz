import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

st.markdown('<div class="main-header"><h1>🌱 Dashboard — Campañas Ambientales</h1><p>Resumen de recolección por campaña: Botellas, Tapas y Aceite</p></div>', unsafe_allow_html=True)

# ─── Funciones utilitarias ───────────────────────────────────────────────────
def normalize(s: str) -> str:
    return str(s).strip().lower().replace("\n", " ").replace("\r", " ").replace(":", "")

# ─── Cargar y renombrar columnas (renombrado explícito para tu hoja) ───────
@st.cache_data
def load_and_prepare_gsheet(csv_url: str) -> pd.DataFrame:
    # Leer CSV exportado desde Google Sheets
    df = pd.read_csv(csv_url)
    # Mapeo manual basado en los encabezados que compartiste
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
    # Aplicar renombrado solo para columnas presentes
    rename_map = {k: v for k, v in rename_manual.items() if k in df.columns}
    if rename_map:
        df = df.rename(columns=rename_map)
    # Mostrar columnas detectadas (útil para depuración)
    df.columns = [c.strip() for c in df.columns]
    # Normalizar timestamp si existe
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    # Coercionar columnas numéricas (tratando "No" como NaN)
    for col in ["botellas", "tapas", "aceite"]:
        if col in df.columns:
            df[col] = df[col].replace({"No": np.nan, "no": np.nan, "NO": np.nan}).astype(str).str.strip()
            # Convertir valores que contienen texto como "3 con" a números si es posible
            df[col] = df[col].replace(r'[^0-9\.\-]+', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan
    # Campos auxiliares para agregación
    df["_botellas_kg"] = df["botellas"].fillna(0).astype(float)
    df["_tapas_kg"] = df["tapas"].fillna(0).astype(float)
    df["_aceite_kg"] = df["aceite"].fillna(0).astype(float)
    df["total_kg"] = df[["_botellas_kg", "_tapas_kg", "_aceite_kg"]].sum(axis=1)
    return df

# ─── Sidebar: URL y opciones ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Fuente de datos")
    default_url = "https://docs.google.com/spreadsheets/d/1fBG1FJuFwly_k6_HSwtP56eyoMehPAVrJlRbbfR8oGk/export?format=csv"
    gsheet_url = st.text_input("URL export CSV de Google Sheets", value=default_url)
    st.markdown("---")
    st.markdown("### Opciones de visualización")
    show_heatmap = st.checkbox("Mostrar mapa de calor Área × Tipo", value=True)
    show_evolution = st.checkbox("Mostrar evolución temporal (si hay timestamp)", value=True)
    st.markdown("---")
    st.caption("Asegúrate de que la hoja sea accesible: 'Cualquiera con el enlace puede ver'.")

# ─── Cargar datos ───────────────────────────────────────────────────────────
try:
    df = load_and_prepare_gsheet(gsheet_url)
except Exception as e:
    st.error(f"No se pudo leer la hoja: {e}")
    st.stop()

# Mostrar columnas detectadas para confirmar mapeo
st.sidebar.markdown("**Columnas detectadas en la hoja:**")
st.sidebar.write(list(df.columns))

# Validar columnas mínimas
required = ["area"]
missing = [r for r in required if r not in df.columns]
if missing:
    st.error(f"No se detectó la(s) columna(s) requerida(s): {missing}. Revisa los encabezados o ajusta el mapeo.")
    st.stop()

# ─── Preparar agregados y KPIs ──────────────────────────────────────────────
df_displayable = df.copy()
if "timestamp" in df_displayable.columns:
    df_displayable["timestamp_str"] = df_displayable["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")

total_botellas = df["_botellas_kg"].sum()
total_tapas = df["_tapas_kg"].sum()
total_aceite = df["_aceite_kg"].sum()
total_kg = df["total_kg"].sum()
n_registros = len(df)
n_areas = df["area"].nunique()

st.markdown('<div class="section-title">Resumen general</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Registros", f"{n_registros}")
col2.metric("Áreas", f"{n_areas}")
col3.metric("Total recolectado (kg)", f"{total_kg:.1f} kg")
col4.metric("Bot / Tap / Ace (kg)", f"{total_botellas:.1f} / {total_tapas:.1f} / {total_aceite:.1f} kg")

# ─── Recolección por tipo ───────────────────────────────────────────────────
st.markdown('<div class="section-title">Recolección por tipo</div>', unsafe_allow_html=True)
type_totals = pd.DataFrame({
    "tipo": ["Botellas (kg)", "Tapas (kg)", "Aceite (kg)"],
    "kg": [total_botellas, total_tapas, total_aceite]
})
fig_types = px.bar(type_totals, x="tipo", y="kg", text="kg", color="tipo",
                   color_discrete_map={"Botellas (kg)": "#0ea5a4", "Tapas (kg)": "#f59e0b", "Aceite (kg)": "#ef4444"},
                   title="Total recolectado por tipo")
fig_types.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig_types.update_layout(showlegend=False, yaxis_title="Kg", xaxis_title="")
st.plotly_chart(fig_types, use_container_width=True)

# ─── Recolección por área (apilada) ────────────────────────────────────────
st.markdown('<div class="section-title">Recolección por Área (apilada)</div>', unsafe_allow_html=True)
area_agg = df.groupby("area").agg({
    "_botellas_kg": "sum",
    "_tapas_kg": "sum",
    "_aceite_kg": "sum",
}).reset_index().sort_values("_botellas_kg", ascending=False)

if area_agg.empty:
    st.info("No hay datos por área para mostrar.")
else:
    fig_area = go.Figure()
    fig_area.add_trace(go.Bar(name="Botellas (kg)", x=area_agg["area"], y=area_agg["_botellas_kg"], marker_color="#0ea5a4"))
    fig_area.add_trace(go.Bar(name="Tapas (kg)", x=area_agg["area"], y=area_agg["_tapas_kg"], marker_color="#f59e0b"))
    fig_area.add_trace(go.Bar(name="Aceite (kg)", x=area_agg["area"], y=area_agg["_aceite_kg"], marker_color="#ef4444"))
    fig_area.update_layout(barmode="stack", title="Recolección por Área y tipo (kg)", xaxis_title="", yaxis_title="Kg", height=420)
    st.plotly_chart(fig_area, use_container_width=True)

# ─── Evolución temporal ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">Evolución temporal</div>', unsafe_allow_html=True)
if show_evolution and "timestamp" in df.columns and df["timestamp"].notna().any():
    evo = df.set_index("timestamp").resample("D").sum()[["_botellas_kg", "_tapas_kg", "_aceite_kg"]].reset_index()
    evo_melt = evo.melt(id_vars="timestamp", value_vars=["_botellas_kg", "_tapas_kg", "_aceite_kg"],
                        var_name="tipo", value_name="kg")
    tipo_map = {"_botellas_kg": "Botellas", "_tapas_kg": "Tapas", "_aceite_kg": "Aceite"}
    evo_melt["tipo"] = evo_melt["tipo"].map(tipo_map)
    fig_evo = px.line(evo_melt, x="timestamp", y="kg", color="tipo", markers=True, title="Evolución diaria de recolección (kg)")
    fig_evo.update_layout(xaxis_title="Fecha", yaxis_title="Kg", legend_title="Tipo")
    st.plotly_chart(fig_evo, use_container_width=True)
else:
    st.info("No hay marca temporal válida para mostrar evolución temporal o la opción está desactivada.")

# ─── Mapa de calor Área × Tipo ──────────────────────────────────────────────
if show_heatmap:
    st.markdown('<div class="section-title">Mapa de calor: Kg recolectados por Área y Tipo</div>', unsafe_allow_html=True)
    heat = area_agg.set_index("area")[["_botellas_kg", "_tapas_kg", "_aceite_kg"]].fillna(0)
    heat.columns = ["Botellas (kg)", "Tapas (kg)", "Aceite (kg)"]
    if heat.empty:
        st.info("No hay datos para el mapa de calor.")
    else:
        fig_heat = px.imshow(
            heat.values,
            x=heat.columns,
            y=heat.index,
            color_continuous_scale="RdYlGn_r",
            labels=dict(x="Tipo", y="Área", color="Kg"),
            text_auto=".1f",
            aspect="auto",
            title="Mapa de calor: Kg recolectados por Área y Tipo"
        )
        fig_heat.update_layout(height=420, margin=dict(l=120, r=20, t=60, b=60))
        st.plotly_chart(fig_heat, use_container_width=True)

# ─── Tabla detallada (Plotly) ───────────────────────────────────────────────
st.markdown('<div class="section-title">Registros detallados</div>', unsafe_allow_html=True)
display_cols = []
if "timestamp" in df.columns:
    display_cols.append("timestamp")
if "nombre" in df.columns:
    display_cols.append("nombre")
display_cols.append("area")
for c in ["botellas", "tapas", "aceite", "total_kg"]:
    if c in df.columns or c == "total_kg":
        display_cols.append(c)

df_table = df.copy()
if "timestamp" in df_table.columns:
    df_table["timestamp"] = df_table["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")
# Convert numeric columns to string for display
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
st.caption("Dashboard de campañas ambientales — visualización de recolección por Botellas, Tapas y Aceite")

