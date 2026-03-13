from datetime import datetime, timedelta

from airq_mcp_timeseries.models import SeriesPoint, SeriesSet, TimeSeries
from airq_mcp_timeseries.services.downsample import downsample


def test_downsample_preserves_peaks_and_boundaries() -> None:
    start = datetime(2026, 3, 1, 0, 0, 0)
    points = []
    for index in range(100):
        value = float(index)
        if index == 50:
            value = 1000.0
        points.append(
            SeriesPoint(
                ts=(start + timedelta(minutes=index)).isoformat() + "+00:00",
                value=value,
            )
        )

    series_set = SeriesSet(
        metric="pm2_5",
        series=[TimeSeries(id="wohnzimmer", label="Wohnzimmer", unit="ug/m3", points=points)],
        start=points[0].ts,
        end=points[-1].ts,
        source_resolution_s=60,
    )

    reduced = downsample(series_set, max_points_per_series=20)
    reduced_values = [point.value for point in reduced.series[0].points]

    assert len(reduced.series[0].points) <= 20
    assert reduced_values[0] == 0.0
    assert reduced_values[-1] == 99.0
    assert 1000.0 in reduced_values


def test_downsample_returns_same_points_under_limit(sample_series_set) -> None:
    reduced = downsample(sample_series_set, max_points_per_series=20)

    assert reduced.series[0].points == sample_series_set.series[0].points
