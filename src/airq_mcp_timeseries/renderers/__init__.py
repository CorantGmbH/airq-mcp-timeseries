"""Renderer exports."""

from airq_mcp_timeseries.models import PlotModel, PlotRequest, PlotResult
from airq_mcp_timeseries.renderers.matplotlib_renderer import render_matplotlib
from airq_mcp_timeseries.renderers.plotly_renderer import render_plotly


async def render(model: PlotModel, request: PlotRequest) -> PlotResult:
    """Render a plot model: HTML via Plotly, static formats via matplotlib."""

    if request.output_format == "html":
        return await render_plotly(model, request)
    return await render_matplotlib(model, request)


__all__ = ["render", "render_matplotlib", "render_plotly"]
