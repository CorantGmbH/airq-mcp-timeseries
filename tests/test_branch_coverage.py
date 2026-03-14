from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from airq_mcp_timeseries.errors import (
    CapabilityNotAvailableError,
    EmptySeriesError,
    InvalidTimeRangeError,
    MetricNotAvailableError,
)
from airq_mcp_timeseries.models import (
    CapabilitySet,
    HistoryQuery,
    PlotModel,
    PlotModelSeries,
    PlotRequest,
    PlotResult,
    PlotStyle,
    Selector,
    SeriesPoint,
    SeriesSet,
    TimeSeries,
)
from airq_mcp_timeseries.models.style import get_theme_definition
from airq_mcp_timeseries.renderers import plotly_renderer
from airq_mcp_timeseries.services import history as history_service
from airq_mcp_timeseries.services.downsample import _downsample_points, downsample
from airq_mcp_timeseries.services.normalize import (
    _validate_time_range,
    default_plot_title,
    default_y_axis_title,
    humanize_metric_name,
    normalize_history_query,
    normalize_metric_name,
    normalize_plot_request,
    select_metric_info,
)
from airq_mcp_timeseries.services.plot_model import build_plot_model
from airq_mcp_timeseries.services.resample import (
    _aggregator,
    _parse_iso_datetime,
    auto_interval_seconds,
    resample,
)


def test_normalize_helpers_cover_fallback_and_errors(sample_metrics) -> None:
    assert select_metric_info("unknown", sample_metrics) is None
    assert select_metric_info("co2", None) is None
    assert normalize_metric_name("CO2", None) == "co2"
    assert humanize_metric_name("co2") == "Co2"
    assert humanize_metric_name("pm2_5") == "PM25"
    assert default_plot_title("co2", None) == "Co2"
    assert default_y_axis_title(None, "ppm") == "ppm"

    query = HistoryQuery(
        selector=Selector(devices=["x"]),
        metric="co2",
        start=datetime(2026, 1, 1, 0, 0, 0),
        end=datetime(2026, 1, 1, 1, 0, 0),
        requested_interval_s=0,
    )
    with pytest.raises(InvalidTimeRangeError):
        normalize_history_query(query, default_timezone="UTC")

    request = PlotRequest(
        selector=Selector(devices=["x"]),
        metric="co2",
        start=datetime(2026, 1, 1, 0, 0, 0),
        end=datetime(2026, 1, 1, 1, 0, 0),
        max_points_per_series=0,
    )
    with pytest.raises(InvalidTimeRangeError):
        normalize_plot_request(request)

    with pytest.raises(InvalidTimeRangeError):
        normalize_plot_request(
            PlotRequest(
                selector=Selector(devices=["x"]),
                metric="co2",
                start=datetime(2026, 1, 1, 0, 0, 0),
                end=datetime(2026, 1, 1, 1, 0, 0),
                timezone="Invalid/Timezone",
            )
        )

    aware = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    with pytest.raises(InvalidTimeRangeError):
        _validate_time_range(aware.replace(tzinfo=None), aware)


def test_plot_model_empty_series_raises() -> None:
    request = PlotRequest(
        selector=Selector(devices=["x"]),
        metric="co2",
        start=datetime.now(UTC) - timedelta(hours=1),
        end=datetime.now(UTC),
    )
    empty = SeriesSet(
        metric="co2",
        series=[],
        start=request.start.isoformat(),
        end=request.end.isoformat(),
    )
    with pytest.raises(EmptySeriesError):
        build_plot_model(empty, request)


def test_resample_and_downsample_cover_remaining_branches() -> None:
    start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=UTC)
    long_end = start + timedelta(days=4000)
    assert auto_interval_seconds(start, long_end, target_points=1) > 86400

    series_set = SeriesSet(
        metric="co2",
        series=[
            TimeSeries(
                id="s1",
                label="Series 1",
                unit="ppm",
                points=[
                    SeriesPoint(ts="2026-03-01T00:00:00Z", value=1.0),
                    SeriesPoint(ts="2026-03-01T00:00:10Z", value=None),
                    SeriesPoint(ts="2026-03-01T00:00:20Z", value=3.0),
                    SeriesPoint(ts="2026-03-01T00:00:30Z", value=None),
                ],
            )
        ],
        start="2026-03-01T00:00:00Z",
        end="2026-03-01T00:00:30Z",
    )

    assert resample(series_set, aggregation="raw", interval_s=None) is series_set
    raw_bucketed = resample(series_set, aggregation="raw", interval_s=30)
    assert [point.value for point in raw_bucketed.series[0].points] == [3.0, None]

    mean_bucketed = resample(series_set, aggregation="mean", interval_s=30)
    assert [point.value for point in mean_bucketed.series[0].points] == [2.0, None]
    assert _aggregator("min")([3.0, 1.0]) == 1.0
    assert _aggregator("max")([3.0, 1.0]) == 3.0
    assert _aggregator("median")([1.0, 3.0, 5.0]) == 3.0
    assert _aggregator("raw")([1.0, 5.0]) == 5.0
    assert _parse_iso_datetime("2026-03-01T00:00:00Z").tzinfo is not None

    with pytest.raises(ValueError):
        downsample(series_set, 0)

    none_points = [SeriesPoint(ts=(start + timedelta(seconds=index)).isoformat(), value=None) for index in range(6)]
    none_set = SeriesSet(
        metric="co2",
        series=[TimeSeries(id="n", label="None", unit="ppm", points=none_points)],
        start=none_points[0].ts,
        end=none_points[-1].ts,
    )
    reduced = downsample(none_set, 2)
    assert len(reduced.series[0].points) == 2

    many_points = [
        SeriesPoint(ts=(start + timedelta(seconds=index)).isoformat(), value=float(index)) for index in range(20)
    ]
    many_set = SeriesSet(
        metric="co2",
        series=[TimeSeries(id="m", label="Many", unit="ppm", points=many_points)],
        start=many_points[0].ts,
        end=many_points[-1].ts,
    )
    reduced_many = downsample(many_set, 3)
    assert len(reduced_many.series[0].points) <= 3

    dense_points = [
        SeriesPoint(
            ts=(start + timedelta(seconds=index)).isoformat(),
            value=float((index * 7) % 13),
        )
        for index in range(40)
    ]
    dense_set = SeriesSet(
        metric="co2",
        series=[TimeSeries(id="d", label="Dense", unit="ppm", points=dense_points)],
        start=dense_points[0].ts,
        end=dense_points[-1].ts,
    )
    reduced_dense = downsample(dense_set, 5)
    assert len(reduced_dense.series[0].points) <= 5
    assert reduced_dense.series[0].points[0] == dense_points[0]
    assert reduced_dense.series[0].points[-1] == dense_points[-1]
    assert len(_downsample_points(dense_points, 5)) == 5


def test_renderer_helpers_cover_layout_branches() -> None:
    model = PlotModel(
        metric="co2",
        title="CO2",
        y_axis_title="ppm",
        series=[
            PlotModelSeries(
                id="a",
                label="A",
                unit=None,
                x=["2026-03-01T00:00:00+00:00", "2026-03-04T00:00:00+00:00"],
                y=[1.0, 2.0],
            )
        ],
    )
    request = PlotRequest(
        selector=Selector(devices=["x"]),
        metric="co2",
        start=datetime(2026, 3, 1, tzinfo=UTC),
        end=datetime(2026, 3, 4, tzinfo=UTC),
        chart_type="area",
        output_format="html",
        style=PlotStyle(
            marker_size=4,
            legend_position="bottom",
            range_selector="compact",
            transparent_background=True,
            unify_hover=False,
        ),
    )

    fig = plotly_renderer._build_figure(model, request)
    layout = fig.to_plotly_json()["layout"]
    data = fig.to_plotly_json()["data"]
    assert layout["legend"]["orientation"] == "h"
    assert layout["hovermode"] == "closest"
    assert layout["paper_bgcolor"] == "rgba(0,0,0,0)"
    assert data[0]["fill"] == "tozeroy"
    assert plotly_renderer._legend_config("hidden") == {"visible": False}
    _airq_theme = get_theme_definition("airq")
    assert plotly_renderer._range_selector(request, _airq_theme) is not None
    assert (
        plotly_renderer._range_selector(
            PlotRequest(
                selector=Selector(devices=["x"]),
                metric="co2",
                start=datetime(2026, 3, 1, tzinfo=UTC),
                end=datetime(2026, 3, 2, tzinfo=UTC),
                output_format="html",
                style=PlotStyle(range_selector="auto"),
            ),
            _airq_theme,
        )
        is None
    )
    # _range_selector itself does not check output_format — that is done in
    # _build_figure which passes None for non-HTML.  A 3-day span with "auto"
    # will return a selector dict.
    assert (
        plotly_renderer._range_selector(
            PlotRequest(
                selector=Selector(devices=["x"]),
                metric="co2",
                start=datetime(2026, 3, 1, tzinfo=UTC),
                end=datetime(2026, 3, 4, tzinfo=UTC),
                output_format="png",
            ),
            _airq_theme,
        )
        is not None
    )
    assert (
        plotly_renderer._range_selector(
            PlotRequest(
                selector=Selector(devices=["x"]),
                metric="co2",
                start=datetime(2026, 3, 1, tzinfo=UTC),
                end=datetime(2026, 3, 4, tzinfo=UTC),
                output_format="html",
                style=PlotStyle(range_selector="off"),
            ),
            _airq_theme,
        )
        is None
    )
    assert plotly_renderer._hover_template(None).endswith("<extra>%{fullData.name}</extra>")
    assert plotly_renderer._hex_to_rgba("#ffffff", 0.5) == "rgba(255, 255, 255, 0.5)"


@pytest.mark.asyncio
async def test_history_error_and_branch_coverage(sample_metrics, sample_series_set, monkeypatch) -> None:
    class Provider:
        def __init__(self, capabilities, metrics, series_set):
            self.capabilities = capabilities
            self.metrics = metrics
            self.series_set = series_set

        async def get_capabilities(self):
            return self.capabilities

        async def list_metrics(self, selector=None):
            return self.metrics

        async def get_history(self, query):
            return self.series_set

    query = HistoryQuery(
        selector=Selector(devices=["x"]),
        metric="co2",
        start=datetime.now(UTC) - timedelta(hours=1),
        end=datetime.now(UTC),
        timezone="UTC",
    )
    with pytest.raises(MetricNotAvailableError):
        await history_service.fetch_history(
            Provider(CapabilitySet(historical_values=True), sample_metrics, sample_series_set),
            query,
        )

    metric_mismatch = SeriesSet(
        metric="wrong",
        series=sample_series_set.series,
        start=sample_series_set.start,
        end=sample_series_set.end,
    )
    with pytest.raises(MetricNotAvailableError):
        await history_service.fetch_history(
            Provider(CapabilitySet(historical_values=True), sample_metrics, metric_mismatch),
            HistoryQuery(
                selector=Selector(devices=["x"]),
                metric="pm2.5",
                start=datetime.now(UTC) - timedelta(hours=1),
                end=datetime.now(UTC),
                timezone="UTC",
            ),
        )

    empty = SeriesSet(
        metric="pm2_5",
        series=[],
        start=sample_series_set.start,
        end=sample_series_set.end,
    )
    with pytest.raises(EmptySeriesError):
        await history_service.fetch_history(
            Provider(CapabilitySet(historical_values=True), sample_metrics, empty),
            HistoryQuery(
                selector=Selector(devices=["x"]),
                metric="pm2.5",
                start=datetime.now(UTC) - timedelta(hours=1),
                end=datetime.now(UTC),
                timezone="UTC",
            ),
        )

    with pytest.raises(CapabilityNotAvailableError):
        history_service._ensure_history_capability(
            CapabilitySet(historical_values=True, max_lookback_days=1),
            HistoryQuery(
                selector=Selector(devices=["x"]),
                metric="pm2_5",
                start=datetime.now(UTC) - timedelta(days=5),
                end=datetime.now(UTC),
                timezone="UTC",
            ),
        )

    history_service._ensure_history_capability(
        CapabilitySet(historical_values=True, max_lookback_days=None),
        HistoryQuery(
            selector=Selector(devices=["x"]),
            metric="pm2_5",
            start=datetime.now(UTC) - timedelta(hours=2),
            end=datetime.now(UTC),
            timezone="UTC",
        ),
    )

    assert (
        history_service._requested_interval_for_plot(
            PlotRequest(
                selector=Selector(devices=["x"]),
                metric="co2",
                start=datetime.now(UTC) - timedelta(hours=5),
                end=datetime.now(UTC),
                aggregation="mean",
            )
        )
        is not None
    )

    called = {"resample": 0, "downsample": 0}

    def fake_resample(series_set, interval_s=None, aggregation="raw", target_points=1200):
        called["resample"] += 1
        return series_set

    def fake_downsample(series_set, max_points_per_series):
        called["downsample"] += 1
        return series_set

    async def fake_render(model, request):
        return PlotResult(output_format=request.output_format, mime_type="image/png", payload=b"x")

    monkeypatch.setattr(history_service, "resample", fake_resample)
    monkeypatch.setattr(history_service, "downsample", fake_downsample)
    monkeypatch.setattr(history_service, "render", fake_render)

    result = await history_service.plot_history(
        Provider(CapabilitySet(historical_values=True), sample_metrics, sample_series_set),
        PlotRequest(
            selector=Selector(devices=["x"]),
            metric="pm2.5",
            start=datetime.now(UTC) - timedelta(hours=5),
            end=datetime.now(UTC),
            aggregation="mean",
            output_format="png",
        ),
    )
    assert result.summary is not None
    assert called["resample"] == 1
    assert called["downsample"] == 1
