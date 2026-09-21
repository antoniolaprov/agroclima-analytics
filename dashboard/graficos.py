import plotly.graph_objects as go

COR_REFERENCIA = "#9a9a96"


def numero(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def estilo(fig: go.Figure, legenda: bool = True) -> go.Figure:
    fig.update_layout(
        showlegend=legenda,
        legend_title_text="",
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        separators=",.",
    )
    return fig


def linha_de_zero(fig: go.Figure) -> go.Figure:
    fig.add_hline(y=0, line_color=COR_REFERENCIA, line_width=1)
    return fig
