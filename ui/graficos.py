# ui/graficos.py
import plotly.graph_objects as go
import pandas as pd

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,22,40,0.6)",
    font=dict(family="DM Sans", color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(10,22,40,0.8)", bordercolor="rgba(56,189,248,0.2)", borderwidth=1),
    xaxis=dict(gridcolor="rgba(56,189,248,0.08)", linecolor="rgba(56,189,248,0.2)", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="rgba(56,189,248,0.08)", linecolor="rgba(56,189,248,0.2)", tickfont=dict(size=10)),
)

def _layout(**kwargs):
    l = {**LAYOUT_BASE}
    l.update(kwargs)
    return l

def grafico_temperaturas(df: pd.DataFrame, cultivo: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["t_max"],   name="T° Máxima", line=dict(color="#f87171", width=1.5)))
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["t_media"], name="T° Media",  line=dict(color="#34d399", width=2)))
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["t_min"],   name="T° Mínima", line=dict(color="#60a5fa", width=1.5)))
    fig.add_hline(y=33, line_dash="dash", line_color="rgba(251,191,36,0.5)",
                  annotation_text="Umbral calor floración", annotation_font_color="#fbbf24", annotation_font_size=10)
    fig.add_hline(y=35, line_dash="dash", line_color="rgba(239,68,68,0.5)",
                  annotation_text="Umbral calor llenado",  annotation_font_color="#ef4444", annotation_font_size=10)
    fig.update_layout(**_layout(
        title=dict(text=f"🌡️ Temperaturas Diarias — {cultivo}", font=dict(color="#e2e8f0", size=14)),
        yaxis_title="°C",
    ))
    return fig

def grafico_lluvia_et0(df: pd.DataFrame, cultivo: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["fecha"], y=df["lluvia"], name="Lluvia diaria",
                         marker_color="rgba(96,165,250,0.6)"))
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["lluvia_acum"], name="Lluvia acumulada",
                             line=dict(color="#3b82f6", width=2.5), yaxis="y2"))
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["et0_acum"], name="ET₀ acumulada",
                             line=dict(color="#fb923c", width=2.5, dash="dash"), yaxis="y2"))
    fig.update_layout(**_layout(
        title=dict(text=f"🌧️ Lluvia vs ET₀ — {cultivo}", font=dict(color="#e2e8f0", size=14)),
        yaxis_title="mm/día",
        yaxis2=dict(title="mm acumulados", overlaying="y", side="right",
                    gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10, color="#94a3b8")),
        barmode="overlay",
    ))
    return fig

def grafico_balance(df: pd.DataFrame, cultivo: str) -> go.Figure:
    colores = ["rgba(96,165,250,0.7)" if b >= 0 else "rgba(239,68,68,0.7)" for b in df["balance"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["fecha"], y=df["balance"], name="Balance", marker_color=colores))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.2)", line_width=1)
    fig.update_layout(**_layout(
        title=dict(text=f"💧 Balance Hídrico Diario — {cultivo}", font=dict(color="#e2e8f0", size=14)),
        yaxis_title="mm",
    ))
    return fig

def grafico_gdc(df: pd.DataFrame, variedad: dict, cultivo: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["gdc_acum"], name="GDC Acumulado",
                             line=dict(color="#34d399", width=3),
                             fill="tozeroy", fillcolor="rgba(52,211,153,0.08)"))
    colores_linea = {"R1":"#fbbf24","R3":"#fb923c","R5":"#f472b6","R7":"#a78bfa","R8":"#a78bfa",
                     "VT":"#fbbf24","H":"#fb923c","IF":"#fbbf24"}
    for etapa, umbral in variedad["gdc"].items():
        if etapa in colores_linea:
            fig.add_hline(y=umbral, line_dash="dot",
                          line_color=colores_linea.get(etapa,"#64748b"), line_width=1,
                          annotation_text=etapa, annotation_position="right",
                          annotation_font_size=10,
                          annotation_font_color=colores_linea.get(etapa,"#94a3b8"))
    fig.update_layout(**_layout(
        title=dict(text=f"📊 GDC Acumulado vs Umbrales — {cultivo}", font=dict(color="#e2e8f0", size=14)),
        yaxis_title="GDC (°C·día)",
    ))
    return fig

def grafico_rinde_comparativo(resultado: dict, cultivo: str) -> go.Figure:
    """Gráfico de barras con rinde estimado, mín y máx"""
    fig = go.Figure()
    etapas   = [d["etapa"] for d in resultado["detalle"]]
    perdidas = [d["perdida_kg"] for d in resultado["detalle"]]
    colores  = ["#ef4444" if p > 300 else "#fbbf24" if p > 100 else "#34d399" for p in perdidas]

    fig.add_trace(go.Bar(x=etapas, y=perdidas, name="Pérdida estimada (kg/ha)",
                         marker_color=colores))
    fig.update_layout(**_layout(
        title=dict(text=f"📉 Pérdidas por Etapa — {cultivo}", font=dict(color="#e2e8f0", size=14)),
        yaxis_title="kg/ha perdidos",
        xaxis_title="Etapa fenológica",
        showlegend=False,
    ))
    return fig
