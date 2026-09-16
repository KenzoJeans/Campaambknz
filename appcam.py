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

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

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
# PALETA DE COLORES — TEMA OSCURO
# ──────────────────────────────────────────────
DARK_BG      = "#0e1117"   # fondo general de la app
DARK_PANEL   = "#161a23"   # fondo de tarjetas / gráficas
DARK_BORDER  = "#26492f"   # bordes verdes sutiles
DARK_TEXT    = "#e5e7eb"   # texto principal
DARK_MUTED   = "#9aa4b2"   # texto secundario
ACCENT_GREEN = "#34d399"   # verde de acento (títulos, resaltados)
GRID_COLOR   = "#2a2f3a"   # líneas de cuadrícula en gráficas

# Verde sólido para el PDF (los tonos "mint" no imprimen bien sobre blanco)
PDF_GREEN       = colors.HexColor("#16a34a")
PDF_GREEN_LIGHT = colors.HexColor("#eef7f0")
PDF_BORDER      = colors.HexColor("#cbd5c9")

# ──────────────────────────────────────────────
# ESTILOS CSS (TEMA OSCURO)
# ──────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* Fondo general de la app y sidebar */
    .stApp {{
        background-color: {DARK_BG};
        color: {DARK_TEXT};
    }}
    [data-testid="stSidebar"] {{
        background-color: #10131a;
        border-right: 1px solid {DARK_BORDER};
    }}
    [data-testid="stSidebar"] * {{
        color: {DARK_TEXT};
    }}

    .main-title {{
        font-family: 'Montserrat', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #34d399, #22c55e, #16a34a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
    }}
    .subtitle {{
        text-align: center;
        color: {DARK_MUTED};
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        font-family: 'Montserrat', sans-serif;
    }}
    .metric-card {{
        background: linear-gradient(135deg, #10241a, #0e3322);
        border: 1px solid {DARK_BORDER};
        border-left: 4px solid {ACCENT_GREEN};
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
    }}
    .metric-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {ACCENT_GREEN};
        font-family: 'Montserrat', sans-serif;
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: {DARK_MUTED};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .section-header {{
        font-family: 'Montserrat', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: {ACCENT_GREEN};
        border-bottom: 2px solid {DARK_BORDER};
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }}
    .stPlotlyChart {{ border-radius: 12px; overflow: hidden; }}
    .filter-badge {{
        background: #0e3322;
        color: {ACCENT_GREEN};
        border: 1px solid {DARK_BORDER};
        border-radius: 20px;
        padding: 0.25rem 0.9rem;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.8rem;
    }}
    /* Tarjetas / expanders / dataframe */
    [data-testid="stExpander"] {{
        background-color: {DARK_PANEL};
        border: 1px solid {DARK_BORDER};
        border-radius: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
URL_OFICIAL = (
    "https://docs.google.com/spreadsheets/d/"
    "157VmpJo9qvuKDmx12yya2E1caGa28HB4Kxd3-EeY_G8/export?format=csv"
)

PALETTE_MULTI  = ["#34d399","#60a5fa","#fbbf24","#f87171","#a78bfa",
                  "#22d3ee","#f472b6","#a3e635","#2dd4bf","#fb923c"]
COLOR_BOTELLAS = "#34d399"
COLOR_TAPAS    = "#60a5fa"
COLOR_ACEITE   = "#fbbf24"

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
    """Limpia una columna de peso (kg) tolerando errores de digitación
    comunes en formularios: comas decimales, puntos de más ('2.4.'),
    espacios, unidades pegadas ('2.4kg'), celdas vacías, etc.
    Cualquier valor que siga sin poder interpretarse como número se
    convierte a 0 en vez de romper la carga de todo el dashboard.
    """
    s = series.fillna("0").astype(str).str.strip()
    s = s.replace(
        ["No Participa", "No participa", "no participa", "", "nan", "None", "NaN"],
        "0",
    )
    s = s.str.replace(" ", "", regex=False)
    s = s.str.replace("kg", "", case=False, regex=False)
    # Formato es-CO: coma como separador decimal
    s = s.str.replace(",", ".", regex=False)
    # Quita puntos sobrantes al inicio/fin (typos como "2.4." o ".2.4")
    s = s.str.strip(".")

    def _un_solo_punto(v: str) -> str:
        if v.count(".") > 1:
            partes = v.split(".")
            v = "".join(partes[:-1]) + "." + partes[-1]
        return v

    s = s.apply(_un_solo_punto)
    return pd.to_numeric(s, errors="coerce").fillna(0)


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


def _parse_dates(series: pd.Series, dayfirst: bool) -> pd.Series:
    """Intenta parsear fechas con una orientación día/mes dada."""
    return pd.to_datetime(series, dayfirst=dayfirst, errors="coerce")


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

    # ── Parsear fecha (CORREGIDO) ──────────────────────────────────
    # "timestamp" viene de la "Marca temporal" de Google Forms, que por
    # defecto usa formato estadounidense M/D/AAAA — NO day-first.
    # "fecha" (si existe como columna manual) suele venir en formato
    # colombiano D/M/AAAA — sí day-first.
    # Usar dayfirst=True para AMBAS columnas (como en el script original)
    # rompía silenciosamente el parseo de la marca temporal de Google
    # Forms para cualquier día <= 12, generando fechas incorrectas y
    # haciendo que el filtro de fechas pareciera "no funcionar".
    fecha_col = "fecha" if "fecha" in df.columns else ("timestamp" if "timestamp" in df.columns else None)
    if fecha_col:
        dayfirst = (fecha_col == "fecha")  # False para "timestamp"
        parsed = _parse_dates(df[fecha_col], dayfirst=dayfirst)

        # Salvaguarda: si con la orientación esperada fallan demasiadas
        # filas, se prueba la orientación contraria y se usa la que
        # logre parsear más fechas válidas.
        tasa_fallo = parsed.isna().mean() if len(parsed) else 0
        if tasa_fallo > 0.3:
            alterna = _parse_dates(df[fecha_col], dayfirst=not dayfirst)
            if alterna.isna().mean() < tasa_fallo:
                parsed = alterna

        df["fecha_dt"] = parsed
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


def apply_dark_theme(fig, height=None, legend_bottom=True):
    """Aplica el tema oscuro consistente a cualquier figura de Plotly."""
    layout_kwargs = dict(
        template="plotly_dark",
        paper_bgcolor=DARK_PANEL,
        plot_bgcolor=DARK_PANEL,
        font=dict(family="Inter", color=DARK_TEXT),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=DARK_TEXT),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=DARK_TEXT),
    )
    if height:
        layout_kwargs["height"] = height
    fig.update_layout(**layout_kwargs)
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(color=DARK_TEXT)))
    return fig


def top_n_df(df_in: pd.DataFrame, col_label: str, col_value: str, top_n: int = 10) -> pd.DataFrame:
    """Devuelve el top-N agregado (descendente) para una etiqueta y una métrica."""
    return (
        df_in.groupby(col_label, as_index=False)[col_value]
        .sum()
        .query(f"{col_value} > 0")
        .sort_values(col_value, ascending=False)
        .head(top_n)
    )


def top10_bar(df_in, col_label, col_value, title, color, top_n=10):
    df_plot = top_n_df(df_in, col_label, col_value, top_n).sort_values(col_value, ascending=True)
    if df_plot.empty:
        fig = go.Figure()
        fig.update_layout(
            title=title + " — Sin datos",
            annotations=[dict(
                text="Sin registros para los filtros actuales",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=13, color=DARK_MUTED),
            )],
        )
        return apply_dark_theme(fig)
    fig = go.Figure(go.Bar(
        x=df_plot[col_value], y=df_plot[col_label], orientation="h",
        marker=dict(color=df_plot[col_value],
                    colorscale=[[0, DARK_BORDER],[1, color]],
                    showscale=False, line=dict(color=DARK_PANEL, width=0.5)),
        text=[f"{v:.1f} kg" for v in df_plot[col_value]],
        textposition="outside",
        textfont=dict(color=DARK_TEXT),
        hovertemplate="%{y}: %{x:.2f} kg<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)),
        xaxis_title="kg recolectados", yaxis_title="",
        margin=dict(l=10, r=70, t=50, b=30),
        height=max(300, top_n * 38),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return apply_dark_theme(fig, height=max(300, top_n * 38))


# ──────────────────────────────────────────────
# EXPORTACIÓN A PDF
# ──────────────────────────────────────────────
def _tabla_pdf(data, col_widths=None):
    """Construye una tabla de reportlab con el estilo verde del dashboard."""
    tabla = Table(data, colWidths=col_widths, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PDF_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PDF_GREEN_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, PDF_BORDER),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def generar_pdf_reporte(df, df_op, df_tienda, df_admin, df_adm_gpo, top_n, filtro_texto):
    """Genera el PDF de métricas de las campañas ambientales y devuelve los bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "TituloVerde", parent=styles["Title"], textColor=PDF_GREEN,
    )
    heading_style = ParagraphStyle(
        "SubtituloVerde", parent=styles["Heading2"], textColor=PDF_GREEN,
        spaceBefore=14, spaceAfter=6,
    )
    normal_style = styles["Normal"]

    elementos = []
    elementos.append(Paragraph("Reporte Campañas Ambientales", titulo_style))
    elementos.append(Paragraph("Botellas con Amor · Tapas para Sanar · Aceite Green Fuel", normal_style))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    elementos.append(Paragraph(filtro_texto, normal_style))
    elementos.append(Spacer(1, 0.4 * cm))

    total_botellas = df["botellas_kg"].sum()
    total_tapas = df["tapas_kg"].sum()
    total_aceite = df["aceite_kg"].sum()
    total_kg = total_botellas + total_tapas + total_aceite

    elementos.append(Paragraph("Resumen General", heading_style))
    kpi_data = [
        ["Métrica", "Valor"],
        ["Participantes", f"{len(df)}"],
        ["Botellas con Amor (kg)", f"{total_botellas:.1f}"],
        ["Tapas para Sanar (kg)", f"{total_tapas:.1f}"],
        ["Aceite Green Fuel (kg)", f"{total_aceite:.1f}"],
        ["Total recolectado (kg)", f"{total_kg:.1f}"],
    ]
    elementos.append(_tabla_pdf(kpi_data, col_widths=[9 * cm, 5 * cm]))

    def _agregar_ranking(titulo, df_in, col_label, col_value):
        elementos.append(Paragraph(titulo, heading_style))
        top_df = top_n_df(df_in, col_label, col_value, top_n)
        if top_df.empty:
            elementos.append(Paragraph("Sin registros para el período seleccionado.", normal_style))
            return
        data = [["#", "Nombre", "kg"]]
        for i, row in enumerate(top_df.itertuples(index=False), start=1):
            nombre = getattr(row, col_label)
            valor = getattr(row, col_value)
            data.append([str(i), str(nombre), f"{valor:.1f}"])
        elementos.append(_tabla_pdf(data, col_widths=[1.5 * cm, 9 * cm, 3.5 * cm]))

    _agregar_ranking(f"Top {top_n} Operadores — Botellas con Amor", df_op, "nombre_persona", "botellas_kg")
    _agregar_ranking(f"Top {top_n} Operadores — Tapas para Sanar", df_op, "nombre_persona", "tapas_kg")
    _agregar_ranking(f"Top {top_n} Tiendas — Botellas con Amor", df_tienda, "tienda", "botellas_kg")
    _agregar_ranking(f"Top {top_n} Tiendas — Tapas para Sanar", df_tienda, "tienda", "tapas_kg")

    df_admin_et = df_admin.copy()
    df_admin_et["etiqueta"] = df_admin_et.apply(
        lambda r: r["nombre_persona"] if r["nombre_persona"] != "N/A" else r["area_admin"], axis=1)
    _agregar_ranking(f"Top {top_n} Administrativos — Botellas con Amor", df_admin_et, "etiqueta", "botellas_kg")
    _agregar_ranking(f"Top {top_n} Administrativos — Tapas para Sanar", df_admin_et, "etiqueta", "tapas_kg")

    if not df_adm_gpo.empty:
        elementos.append(Paragraph("Competencia Interna — Grupos Administrativos", heading_style))
        data = [["Grupo", "Botellas (kg)", "Tapas (kg)", "Total (kg)"]]
        for row in df_adm_gpo.sort_values("total_kg", ascending=False).itertuples(index=False):
            data.append([
                row.nombre_grupo, f"{row.botellas_kg:.1f}", f"{row.tapas_kg:.1f}", f"{row.total_kg:.1f}"
            ])
        elementos.append(_tabla_pdf(data, col_widths=[7 * cm, 2.5 * cm, 2.5 * cm, 2 * cm]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


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
    fechas_validas = df_raw["fecha_dt"].notna()
    mask = (
        fechas_validas &
        (df_raw["fecha_dt"].dt.date >= fecha_inicio) &
        (df_raw["fecha_dt"].dt.date <= fecha_fin)
    )
    df = df_raw[mask].copy()
    sin_fecha = (~fechas_validas).sum()
    badge_txt = (
        f"🗓️ Filtro activo: {fecha_inicio.strftime('%d/%m/%Y')} → "
        f"{fecha_fin.strftime('%d/%m/%Y')} &nbsp;·&nbsp; "
        f"<b>{len(df)}</b> de <b>{len(df_raw)}</b> registros"
    )
    if sin_fecha:
        badge_txt += f" &nbsp;·&nbsp; ⚠️ {sin_fecha} sin fecha válida (excluidos)"
    filtro_texto_pdf = (
        f"Filtro de fecha: {fecha_inicio.strftime('%d/%m/%Y')} – {fecha_fin.strftime('%d/%m/%Y')} "
        f"· {len(df)} de {len(df_raw)} registros"
    )
elif usar_filtro and fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
    df = df_raw.copy()
    badge_txt = "⚠️ Rango de fechas inválido — mostrando todos los registros sin filtrar"
    filtro_texto_pdf = "Rango de fechas inválido — se muestran todos los registros sin filtrar"
else:
    df = df_raw.copy()
    badge_txt = f"📋 Todos los registros: <b>{len(df)}</b>"
    filtro_texto_pdf = f"Todos los registros: {len(df)}"

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
    fig_pie.update_layout(title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)))
    apply_dark_theme(fig_pie, height=380)
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
        title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)),
        xaxis_title="", yaxis_title="kg",
    )
    apply_dark_theme(fig_bg, height=380)
    fig_bg.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.35, font=dict(color=DARK_TEXT)))
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
    fig_camp.update_layout(title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)))
    apply_dark_theme(fig_camp, height=360)
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
    fig_pcamp.update_traces(textposition="outside", textfont=dict(color=DARK_TEXT))
    fig_pcamp.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)),
        showlegend=False, yaxis_title="Personas", xaxis_title="",
    )
    apply_dark_theme(fig_pcamp, height=360)
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
        title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)),
        xaxis_title="Fecha", yaxis_title="kg",
    )
    apply_dark_theme(fig_time, height=320)
    fig_time.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(color=DARK_TEXT)))
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
        title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)),
        xaxis_title="kg recolectados", yaxis_title="",
        margin=dict(l=10, r=60, t=50, b=60),
    )
    apply_dark_theme(fig_gs, height=max(350, len(df_adm_gpo)*55+80))
    fig_gs.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color=DARK_TEXT)))
    st.plotly_chart(fig_gs, use_container_width=True)
else:
    st.info("No hay datos de grupos administrativos en el período seleccionado.")


# ══════════════════════════════════════════════
# 8.1 EXPORTAR REPORTE PDF
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">📄 Exportar Reporte PDF</div>', unsafe_allow_html=True)
st.caption("Genera un PDF con el resumen de KPIs y los rankings actuales (respeta el filtro de fecha activo).")

pdf_bytes = generar_pdf_reporte(df, df_op, df_tienda, df_admin, df_adm_gpo, top_n, filtro_texto_pdf)
st.download_button(
    label="⬇️ Descargar reporte PDF",
    data=pdf_bytes,
    file_name=f"reporte_campanas_ambientales_{date.today().isoformat()}.pdf",
    mime="application/pdf",
    type="primary",
)


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
        color_continuous_scale=[[0, DARK_PANEL], [1, ACCENT_GREEN]],
        aspect="auto",
    )
    fig_heat.update_layout(
        title=dict(font=dict(family="Montserrat", size=14, color=ACCENT_GREEN)),
        coloraxis_colorbar_title="kg",
    )
    apply_dark_theme(fig_heat, height=max(300, len(df_heat)*40+100), legend_bottom=False)
    st.plotly_chart(fig_heat, use_container_width=True)

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
import textwrap

# 2. Renderizar Infografía Estructurada en Bloques (HTML + CSS)
html_flyer = textwrap.dedent(f"""
<style>
    .flyer-container {{
        background-color: #f8fafc;
        border-radius: 16px;
        padding: 25px;
        color: #1e293b;
        font-family: 'Montserrat', sans-serif;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        max-width: 850px;
        margin: 0 auto;
        border: 4px solid #16a34a;
    }}
    .flyer-header {{
        background: linear-gradient(135deg, #059669, #16a34a);
        color: white;
        text-align: center;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    .flyer-header h1 {{
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .flyer-header p {{
        margin: 5px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }}
    .flyer-impact-banner {{
        background-color: #fef3c7;
        border-left: 6px solid #d97706;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-around;
        text-align: center;
    }}
    .impact-stat {{
        font-size: 2rem;
        font-weight: 800;
        color: #b45309;
    }}
    .impact-label {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #78350f;
        text-transform: uppercase;
    }}
    .flyer-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 20px;
    }}
    .flyer-card {{
        border-radius: 12px;
        padding: 18px 12px;
        text-align: center;
        color: white;
    }}
    .card-green {{ background-color: #10b981; }}
    .card-blue {{ background-color: #3b82f6; }}
    .card-amber {{ background-color: #f59e0b; }}
    .card-icon {{ font-size: 2.2rem; margin-bottom: 8px; }}
    .card-title {{ font-size: 0.9rem; font-weight: 700; text-transform: uppercase; }}
    .card-value {{ font-size: 1.8rem; font-weight: 800; margin: 5px 0; }}
    .card-desc {{ font-size: 0.78rem; opacity: 0.95; line-height: 1.2; }}
    .flyer-winners-section {{
        background-color: #e0f2fe;
        border: 2px dashed #0284c7;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }}
    .winners-title {{
        text-align: center;
        color: #0369a1;
        font-size: 1.3rem;
        font-weight: 800;
        margin-bottom: 15px;
        text-transform: uppercase;
    }}
    .winners-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }}
    .winner-box {{
        background: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }}
    .winner-category {{ font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; }}
    .winner-name {{ font-size: 1rem; font-weight: 800; color: #0f172a; margin: 4px 0; }}
    .winner-score {{ font-size: 0.85rem; font-weight: 700; color: #16a34a; }}
    .flyer-footer {{
        background-color: #1e293b;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 600;
    }}
</style>

<div class="flyer-container">
    <div class="flyer-header">
        <h1>🌱 CAMPAÑAS AMBIENTALES 2026</h1>
        <p>¡Nuestras acciones diarias construyen un planeta sostenible!</p>
    </div>

    <div class="flyer-impact-banner">
        <div>
            <div class="impact-stat">{total_kg:.1f} kg</div>
            <div class="impact-label">Total Recolectado</div>
        </div>
        <div style="border-left: 2px solid #fcd34d; height: 40px;"></div>
        <div>
            <div class="impact-stat">{len(df)}</div>
            <div class="impact-label">Héroes Participantes</div>
        </div>
    </div>

    <div class="flyer-grid">
        <div class="flyer-card card-green">
            <div class="card-icon">♻️</div>
            <div class="card-title">Botellas con Amor</div>
            <div class="card-value">{total_botellas:.1f} kg</div>
            <div class="card-desc">Transformados en madera plástica para parques y vivienda social.</div>
        </div>
        <div class="flyer-card card-blue">
            <div class="card-icon">🔵</div>
            <div class="card-title">Tapas para Sanar</div>
            <div class="card-value">{total_tapas:.1f} kg</div>
            <div class="card-desc">Cerca de 100,000 tapitas apoyando tratamientos de salud infantil.</div>
        </div>
        <div class="flyer-card card-amber">
            <div class="card-icon">🛢️</div>
            <div class="card-title">Aceite Green Fuel</div>
            <div class="card-value">{total_aceite:.1f} kg</div>
            <div class="card-desc">Protegimos más de <b>+{agua_protegida_litros:,} L</b> de agua de contaminación.</div>
        </div>
    </div>

    <div class="flyer-winners-section">
        <div class="winners-title">🏆 Cuadro de Honor del Mes</div>
        <div class="winners-grid">
            <div class="winner-box">
                <div class="winner-category">🥇 Planta (Botellas)</div>
                <div class="winner-name">{ganador_botellas_op}</div>
                <div class="winner-score">{ganador_botellas_op_kg:.1f} kg</div>
            </div>
            <div class="winner-box">
                <div class="winner-category">🥇 Planta (Tapas)</div>
                <div class="winner-name">{ganador_tapas_op}</div>
                <div class="winner-score">{ganador_tapas_op_kg:.1f} kg</div>
            </div>
            <div class="winner-box">
                <div class="winner-category">🏬 Tienda Líder</div>
                <div class="winner-name">{ganador_tienda_botellas}</div>
                <div class="winner-score">Top Botellas</div>
            </div>
        </div>
    </div>

    <div class="flyer-footer">
        📢 ¡Suma tus residuos esta semana! Trae tu aceite, tapas y botellas a los puntos ecológicos.
    </div>
</div>
""").strip()

# Renderizar en Streamlit (Alternativamente puedes usar st.html(html_flyer))
st.markdown(html_flyer, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")
st.caption("🌿 Dashboard Campañas Ambientales · Streamlit + Plotly")
