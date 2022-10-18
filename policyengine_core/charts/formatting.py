import plotly.graph_objects as go
from IPython.display import HTML


WHITE = "#FFF"
LIGHTER_BLUE = "#ABCEEB"  # Blue 100.
LIGHT_BLUE = "#49A6E2"  # Blue 500.
BLUE = "#1976D2"  # Blue 700.
DARK_BLUE = "#0F4AA1"  # Blue 900.
GRAY = "#BDBDBD"
DARK_GRAY = "#616161"
LIGHT_GRAY = "#F5F5F5"
LIGHT_GREEN = "#C5E1A5"
DARK_GREEN = "#558B2F"


def format_fig(fig: go.Figure) -> dict:
    """Formats figure with styling and returns as JSON.
    :param fig: Plotly figure.
    :type fig: go.Figure
    :return: Formatted plotly figure as a JSON dict.
    :rtype: dict
    """
    fig.update_xaxes(
        title_font=dict(size=16, color="black"), tickfont={"size": 14}
    )
    fig.update_yaxes(
        title_font=dict(size=16, color="black"), tickfont={"size": 14}
    )
    return fig.update_layout(
        hoverlabel_align="right",
        font_family="Arial, sans-serif",
        font_color="Black",
        title_font_size=20,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(font_family="Arial, sans-serif"),
    )


def display_fig(fig: go.Figure) -> HTML:
    return HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))
