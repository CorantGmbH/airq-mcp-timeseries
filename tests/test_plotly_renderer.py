from datetime import datetime

from airq_mcp_timeseries.models import PlotModel, PlotModelSeries, PlotRequest, Selector
from airq_mcp_timeseries.renderers.matplotlib_renderer import render_matplotlib
from airq_mcp_timeseries.renderers.plotly_renderer import render_plotly


async def test_render_plotly_returns_html() -> None:
    model = PlotModel(
        metric="pm2_5",
        title="Feinstaub PM2.5",
        y_axis_title="ug/m3",
        series=[
            PlotModelSeries(
                id="wohnzimmer",
                label="Wohnzimmer",
                unit="ug/m3",
                x=["2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00"],
                y=[1.0, 2.0],
            )
        ],
    )
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2_5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
        output_format="html",
    )

    result = await render_plotly(model, request)

    assert result.mime_type == "text/html"
    assert isinstance(result.payload, str)
    assert "plotly" in result.payload.lower()


async def test_render_matplotlib_returns_png() -> None:
    model = PlotModel(
        metric="pm2_5",
        title="Feinstaub PM2.5",
        y_axis_title="ug/m3",
        series=[
            PlotModelSeries(
                id="wohnzimmer",
                label="Wohnzimmer",
                unit="ug/m3",
                x=["2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00"],
                y=[1.0, 2.0],
            )
        ],
    )
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2_5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
        output_format="png",
    )

    result = await render_matplotlib(model, request)

    assert result.mime_type == "image/png"
    assert isinstance(result.payload, bytes)
    assert result.payload[:4] == b"\x89PNG"


async def test_render_matplotlib_returns_svg() -> None:
    model = PlotModel(
        metric="pm2_5",
        title="Feinstaub PM2.5",
        y_axis_title="ug/m3",
        series=[
            PlotModelSeries(
                id="wohnzimmer",
                label="Wohnzimmer",
                unit="ug/m3",
                x=["2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00"],
                y=[1.0, 2.0],
            )
        ],
    )
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2_5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
        output_format="svg",
    )

    result = await render_matplotlib(model, request)

    assert result.mime_type == "image/svg+xml"
    assert isinstance(result.payload, bytes)
    assert result.payload.lstrip().startswith(b"<?xml")


async def test_render_matplotlib_returns_webp() -> None:
    model = PlotModel(
        metric="pm2_5",
        title="Feinstaub PM2.5",
        y_axis_title="ug/m3",
        series=[
            PlotModelSeries(
                id="wohnzimmer",
                label="Wohnzimmer",
                unit="ug/m3",
                x=["2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00"],
                y=[1.0, 2.0],
            )
        ],
    )
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2_5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
        output_format="webp",
    )

    result = await render_matplotlib(model, request)

    assert result.mime_type == "image/webp"
    assert isinstance(result.payload, bytes)
    assert result.payload[:4] == b"RIFF"
