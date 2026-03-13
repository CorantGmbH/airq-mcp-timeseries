from datetime import datetime, timedelta

from airq_mcp_timeseries.models import SeriesPoint, SeriesSet, TimeSeries
from airq_mcp_timeseries.services.resample import auto_interval_seconds, resample


def test_auto_interval_seconds_snaps_to_friendly_bucket() -> None:
    start = datetime(2026, 3, 1, 0, 0, 0)
    end = start + timedelta(days=30)

    assert auto_interval_seconds(start, end, target_points=1200) == 3600


def test_resample_mean_groups_points_into_time_buckets() -> None:
    start = datetime(2026, 3, 1, 0, 0, 0)
    points = [
        SeriesPoint(
            ts=(start + timedelta(minutes=5 * index)).isoformat() + "+00:00",
            value=float(index),
        )
        for index in range(12)
    ]
    series_set = SeriesSet(
        metric="pm2_5",
        series=[
            TimeSeries(id="wohnzimmer", label="Wohnzimmer", unit="ug/m3", points=points)
        ],
        start=points[0].ts,
        end=points[-1].ts,
        source_resolution_s=300,
    )

    resampled = resample(series_set, interval_s=900, aggregation="mean")

    assert [point.value for point in resampled.series[0].points] == [
        1.0,
        4.0,
        7.0,
        10.0,
    ]
    assert resampled.source_resolution_s == 900
