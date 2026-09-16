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
import html as html_lib
from datetime import datetime, date

import streamlit.components.v1 as components
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


# ──────────────────────────────────────────────
# INFOGRAFÍA STORYTELLING (HTML animado)
# ──────────────────────────────────────────────
def generar_infografia_html(df, df_op, df_tienda, filtro_texto):
    """Genera una infografía HTML animada (contadores, barras y podio top 3)
    con los datos filtrados actuales. Autocontenida: se puede incrustar en
    el dashboard con components.html() o descargarse y abrirse en cualquier
    navegador."""
    total_botellas = df["botellas_kg"].sum()
    total_tapas    = df["tapas_kg"].sum()
    total_aceite   = df["aceite_kg"].sum()
    total_kg       = total_botellas + total_tapas + total_aceite
    total_participantes = len(df)

    pct_botellas = (total_botellas / total_kg * 100) if total_kg else 0
    pct_tapas    = (total_tapas / total_kg * 100) if total_kg else 0
    pct_aceite   = (total_aceite / total_kg * 100) if total_kg else 0

    df_op_tot = df_op.copy()
    df_op_tot["total_kg"] = df_op_tot["botellas_kg"] + df_op_tot["tapas_kg"] + df_op_tot["aceite_kg"]
    top3_op = top_n_df(df_op_tot, "nombre_persona", "total_kg", 3)

    df_tienda_tot = df_tienda.copy()
    df_tienda_tot["total_kg"] = df_tienda_tot["botellas_kg"] + df_tienda_tot["tapas_kg"] + df_tienda_tot["aceite_kg"]
    top3_tda = top_n_df(df_tienda_tot, "tienda", "total_kg", 3)

    def _podio_html(top_df, label_col):
        medallas = ["🥇", "🥈", "🥉"]
        max_val = top_df["total_kg"].max() if not top_df.empty else 1
        tarjetas = []
        for i, row in enumerate(top_df.itertuples(index=False)):
            nombre = html_lib.escape(str(getattr(row, label_col)))
            valor = getattr(row, "total_kg")
            alto_pct = max(12, (valor / max_val * 100)) if max_val else 12
            tarjetas.append(f"""
            <div class="podio-item">
                <div class="podio-medalla">{medallas[i]}</div>
                <div class="podio-barra-wrap">
                    <div class="podio-barra" data-height="{alto_pct:.0f}%"></div>
                </div>
                <div class="podio-nombre">{nombre}</div>
                <div class="podio-valor"><span class="counter" data-target="{valor:.1f}" data-decimals="1">0</span> kg</div>
            </div>""")
        if not tarjetas:
            return '<p class="sin-datos">Sin registros suficientes para este ranking.</p>'
        return f'<div class="podio">{"".join(tarjetas)}</div>'

    podio_operadores = _podio_html(top3_op, "nombre_persona")
    podio_tiendas    = _podio_html(top3_tda, "tienda")
    filtro_seguro    = html_lib.escape(filtro_texto)

    html_doc = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800&family=Inter:wght@400;500&display=swap');
  * {{ box-sizing: border-box; }}
  body {{
    margin:0; font-family:'Inter',sans-serif;
    background: linear-gradient(180deg, #0e1117 0%, #10241a 50%, #0e1117 100%);
    color:#e5e7eb;
  }}
  .seccion {{ padding: 2.6rem 1.5rem; text-align:center; }}
  .hero {{ padding: 3rem 1.5rem 1.5rem; }}
  .hero-icono {{ font-size:3.2rem; animation: flotar 3s ease-in-out infinite; }}
  @keyframes flotar {{ 0%,100% {{ transform: translateY(0);}} 50% {{ transform: translateY(-14px);}} }}
  .hero h1 {{
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.9rem;
    background: linear-gradient(135deg,#34d399,#22c55e,#16a34a);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin: .6rem 0 .3rem;
  }}
  .hero p {{ color:#9aa4b2; font-size:.9rem; margin:.2rem 0; }}
  .reveal {{ opacity:0; transform:translateY(30px); transition: all .8s ease; }}
  .reveal.visible {{ opacity:1; transform:none; }}
  .kpis {{ display:flex; flex-wrap:wrap; gap:1rem; justify-content:center; margin-top:1.3rem; }}
  .kpi-card {{
    background: linear-gradient(135deg,#10241a,#0e3322);
    border:1px solid #26492f; border-left:4px solid #34d399;
    border-radius:14px; padding:1.1rem 1.3rem; min-width:135px;
  }}
  .kpi-icono {{ font-size:1.7rem; }}
  .kpi-valor {{ font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.6rem; color:#34d399; }}
  .kpi-label {{ font-size:.72rem; color:#9aa4b2; text-transform:uppercase; letter-spacing:.05em; }}
  .titulo-seccion {{
    font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.25rem;
    color:#34d399; margin-bottom:1.4rem;
  }}
  .barras-campana {{ max-width:520px; margin:0 auto; text-align:left; }}
  .barra-fila {{ margin-bottom:1.2rem; }}
  .barra-fila-label {{ display:flex; justify-content:space-between; font-size:.82rem; margin-bottom:.3rem; }}
  .barra-track {{ background:#161a23; border:1px solid #26492f; border-radius:20px; height:15px; overflow:hidden; }}
  .barra-fill {{ height:100%; width:0; border-radius:20px; transition: width 1.6s cubic-bezier(.22,1,.36,1); }}
  .podio {{ display:flex; gap:1.1rem; justify-content:center; align-items:flex-end; flex-wrap:wrap; max-width:600px; margin:0 auto; }}
  .podio-item {{ width:140px; }}
  .podio-medalla {{ font-size:1.9rem; }}
  .podio-barra-wrap {{ height:110px; display:flex; align-items:flex-end; justify-content:center; margin: .5rem 0; }}
  .podio-barra {{
    width:52px; height:0; border-radius:8px 8px 0 0;
    background: linear-gradient(180deg,#34d399,#16a34a);
    transition: height 1.4s cubic-bezier(.22,1,.36,1);
  }}
  .podio-nombre {{ font-weight:600; font-size:.82rem; }}
  .podio-valor {{ color:#9aa4b2; font-size:.78rem; }}
  .sin-datos {{ color:#9aa4b2; font-size:.85rem; }}
  .cierre {{ padding: 2.6rem 1.5rem 3rem; }}
  .cierre-icono {{ font-size:2.2rem; animation: latir 1.8s ease-in-out infinite; }}
  @keyframes latir {{ 0%,100% {{ transform: scale(1);}} 50% {{ transform: scale(1.15);}} }}
  .footer-nota {{ color:#5f6a78; font-size:.7rem; margin-top:1.6rem; }}
</style>
</head>
<body>

  <section class="seccion hero reveal">
    <div class="hero-icono">🌿</div>
    <h1>Nuestro Impacto Ambiental</h1>
    <p>Botellas con Amor · Tapas para Sanar · Aceite Green Fuel</p>
    <p>{filtro_seguro}</p>
  </section>

  <section class="seccion reveal">
    <div class="titulo-seccion">📊 Lo que hemos logrado juntos</div>
    <div class="kpis">
      <div class="kpi-card">
        <div class="kpi-icono">👥</div>
        <div class="kpi-valor"><span class="counter" data-target="{total_participantes}" data-decimals="0">0</span></div>
        <div class="kpi-label">Participantes</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icono">♻️</div>
        <div class="kpi-valor"><span class="counter" data-target="{total_botellas:.1f}" data-decimals="1">0</span> kg</div>
        <div class="kpi-label">Botellas con Amor</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icono">🔵</div>
        <div class="kpi-valor"><span class="counter" data-target="{total_tapas:.1f}" data-decimals="1">0</span> kg</div>
        <div class="kpi-label">Tapas para Sanar</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icono">🛢️</div>
        <div class="kpi-valor"><span class="counter" data-target="{total_aceite:.1f}" data-decimals="1">0</span> kg</div>
        <div class="kpi-label">Aceite Green Fuel</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icono">⚖️</div>
        <div class="kpi-valor"><span class="counter" data-target="{total_kg:.1f}" data-decimals="1">0</span> kg</div>
        <div class="kpi-label">Total Recolectado</div>
      </div>
    </div>
  </section>

  <section class="seccion reveal">
    <div class="titulo-seccion">🥧 ¿De dónde viene nuestro impacto?</div>
    <div class="barras-campana">
      <div class="barra-fila">
        <div class="barra-fila-label"><span>♻️ Botellas con Amor</span><span>{pct_botellas:.0f}%</span></div>
        <div class="barra-track"><div class="barra-fill" data-width="{pct_botellas:.0f}%" style="background:#34d399;"></div></div>
      </div>
      <div class="barra-fila">
        <div class="barra-fila-label"><span>🔵 Tapas para Sanar</span><span>{pct_tapas:.0f}%</span></div>
        <div class="barra-track"><div class="barra-fill" data-width="{pct_tapas:.0f}%" style="background:#60a5fa;"></div></div>
      </div>
      <div class="barra-fila">
        <div class="barra-fila-label"><span>🛢️ Aceite Green Fuel</span><span>{pct_aceite:.0f}%</span></div>
        <div class="barra-track"><div class="barra-fill" data-width="{pct_aceite:.0f}%" style="background:#fbbf24;"></div></div>
      </div>
    </div>
  </section>

  <section class="seccion reveal">
    <div class="titulo-seccion">🏭 Los héroes del reciclaje — Operadores</div>
    {podio_operadores}
  </section>

  <section class="seccion reveal">
    <div class="titulo-seccion">🏪 Los héroes del reciclaje — Tiendas</div>
    {podio_tiendas}
  </section>

  <section class="seccion cierre reveal">
    <div class="cierre-icono">🌍</div>
    <p>Gracias por cuidar el planeta, un residuo a la vez.</p>
    <div class="footer-nota">Generado automáticamente · Dashboard Campañas Ambientales</div>
  </section>

<script>
  document.addEventListener('DOMContentLoaded', function() {{
    var observer = new IntersectionObserver(function(entries) {{
      entries.forEach(function(entry) {{
        if (entry.isIntersecting) {{
          entry.target.classList.add('visible');
          entry.target.querySelectorAll('.counter').forEach(function(counter) {{
            if (counter.dataset.animated) return;
            counter.dataset.animated = "true";
            var target = parseFloat(counter.dataset.target);
            var decimals = parseInt(counter.dataset.decimals || "0", 10);
            var duration = 1400;
            var start = null;
            function step(ts) {{
              if (!start) start = ts;
              var progress = Math.min((ts - start) / duration, 1);
              var eased = 1 - Math.pow(1 - progress, 3);
              var value = target * eased;
              counter.textContent = value.toLocaleString('es-CO', {{minimumFractionDigits: decimals, maximumFractionDigits: decimals}});
              if (progress < 1) requestAnimationFrame(step);
            }}
            requestAnimationFrame(step);
          }});
          entry.target.querySelectorAll('.barra-fill').forEach(function(bar) {{
            bar.style.width = bar.dataset.width;
          }});
          entry.target.querySelectorAll('.podio-barra').forEach(function(bar) {{
            bar.style.height = bar.dataset.height;
          }});
        }}
      }});
    }}, {{threshold: 0.2}});
    document.querySelectorAll('.reveal').forEach(function(el) {{ observer.observe(el); }});
  }});
</script>
</body>
</html>
"""
    return html_doc


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
# 8.2 INFOGRAFÍA AUTOMÁTICA (STORYTELLING)
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">✨ Infografía Storytelling</div>', unsafe_allow_html=True)
st.caption("Infografía animada generada automáticamente con los datos filtrados actuales — ideal para compartir.")

html_infografia = generar_infografia_html(df, df_op, df_tienda, filtro_texto_pdf)
components.html(html_infografia, height=1900, scrolling=True)

st.download_button(
    label="⬇️ Descargar infografía (HTML animado)",
    data=html_infografia.encode("utf-8"),
    file_name=f"infografia_campanas_ambientales_{date.today().isoformat()}.html",
    mime="text/html",
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

st.markdown("---")
st.caption("🌿 Dashboard Campañas Ambientales · Streamlit + Plotly")
