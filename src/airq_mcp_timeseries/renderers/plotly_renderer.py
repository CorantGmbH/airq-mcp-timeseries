"""Plotly renderer implementation."""

from typing import Any

import plotly.graph_objects as go

from airq_mcp_timeseries.errors import UnsupportedOutputFormatError
from airq_mcp_timeseries.models import (
    PlotModel,
    PlotRequest,
    PlotResult,
    get_theme_definition,
)

_MIME_TYPES = {
    "html": "text/html",
    "png": "image/png",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}


async def render_plotly(model: PlotModel, request: PlotRequest) -> PlotResult:
    """Render a plot model with Plotly into the requested output format."""

    figure = _build_figure(model, request)
    output_format = request.output_format

    if output_format == "html":
        payload = figure.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config=_html_config(),
        )
        return PlotResult(
            output_format=output_format,
            mime_type=_MIME_TYPES[output_format],
            payload=payload,
        )

    try:
        payload = figure.to_image(
            format=output_format,
            width=request.style.width,
            height=request.style.height,
            scale=2,
        )
    except Exception as exc:  # pragma: no cover - exercised via monkeypatch in tests
        raise UnsupportedOutputFormatError(
            f"could not render Plotly output as {output_format}: {exc}"
        ) from exc

    return PlotResult(
        output_format=output_format,
        mime_type=_MIME_TYPES[output_format],
        payload=payload,
    )


def _build_figure(model: PlotModel, request: PlotRequest) -> go.Figure:
    theme = get_theme_definition(request.style.theme)
    figure = go.Figure()

    for index, series in enumerate(model.series):
        color = theme.colorway[index % len(theme.colorway)]
        figure.add_trace(
            go.Scatter(
                x=series.x,
                y=series.y,
                mode="lines+markers" if request.style.marker_size > 0 else "lines",
                name=series.label,
                line={"width": request.style.line_width, "color": color},
                marker={"size": request.style.marker_size, "color": color},
                fill="tozeroy" if request.chart_type == "area" else None,
                fillcolor=(
                    _hex_to_rgba(color, request.style.fill_opacity)
                    if request.chart_type == "area"
                    else None
                ),
                hovertemplate=_hover_template(series.unit),
            )
        )

    paper_bgcolor = (
        "rgba(0,0,0,0)" if request.style.transparent_background else theme.paper_bgcolor
    )
    plot_bgcolor = (
        "rgba(0,0,0,0)" if request.style.transparent_background else theme.plot_bgcolor
    )
    figure.update_layout(
        template=theme.template,
        width=request.style.width,
        height=request.style.height,
        title={"text": model.title, "x": 0.02, "xanchor": "left"},
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font={"color": theme.font_color, "size": 14},
        colorway=list(theme.colorway),
        hovermode="x unified" if request.style.unify_hover else "closest",
        margin={"l": 60, "r": 50, "t": 70, "b": 55},
        legend=_legend_config(request.style.legend_position),
    )

    range_selector = _range_selector(request)
    figure.update_xaxes(
        title_text=request.style.x_axis_title,
        showgrid=False,
        showline=True,
        linecolor=theme.axis_line_color,
        rangeslider={
            "visible": request.output_format == "html"
            and request.style.show_range_slider
        },
        rangeselector=range_selector,
        showspikes=request.style.show_spikes,
        spikecolor=theme.axis_line_color,
        spikemode="across",
        spikesnap="cursor",
    )
    figure.update_yaxes(
        title_text=model.y_axis_title,
        showgrid=request.style.show_grid,
        gridcolor=theme.grid_color,
        showline=True,
        linecolor=theme.axis_line_color,
        zeroline=False,
    )
    return figure


def _html_config() -> dict[str, Any]:
    return {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "select2d",
            "lasso2d",
            "autoScale2d",
            "toggleSpikelines",
        ],
    }


def _legend_config(position: str) -> dict[str, Any]:
    if position == "hidden":
        return {"visible": False}
    if position == "bottom":
        return {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "left",
            "x": 0.0,
        }
    return {
        "orientation": "v",
        "yanchor": "top",
        "y": 1.0,
        "xanchor": "left",
        "x": 1.02,
    }


def _range_selector(request: PlotRequest) -> dict[str, Any] | None:
    if request.output_format != "html":
        return None
    if request.style.range_selector == "off":
        return None
    duration_days = max((request.end - request.start).total_seconds() / 86400, 0.0)
    if request.style.range_selector == "auto" and duration_days < 3:
        return None
    return {
        "buttons": [
            {"count": 1, "label": "24h", "step": "day", "stepmode": "backward"},
            {"count": 7, "label": "7d", "step": "day", "stepmode": "backward"},
            {"count": 1, "label": "30d", "step": "month", "stepmode": "backward"},
            {"step": "all", "label": "All"},
        ]
    }


def _hover_template(unit: str | None) -> str:
    suffix = f" {unit}" if unit else ""
    return "%{x}<br>%{y}" + suffix + "<extra>%{fullData.name}</extra>"


def _hex_to_rgba(color: str, opacity: float) -> str:
    color = color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {opacity})"
