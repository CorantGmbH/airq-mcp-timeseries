from datetime import datetime, timedelta

from airq_mcp_timeseries.models import (
    HistoryQuery,
    Selector,
    SeriesPoint,
    SeriesSet,
    TimeSeries,
)
from airq_mcp_timeseries.services.history import summarize_history
from airq_mcp_timeseries.services.summarize import summarize


def test_summarize_calculates_basic_statistics() -> None:
    start = datetime(2026, 3, 1, 0, 0, 0)
    points = [
        SeriesPoint(ts=start.isoformat() + "+00:00", value=1.0),
        SeriesPoint(ts=(start + timedelta(minutes=5)).isoformat() + "+00:00", value=None),
        SeriesPoint(ts=(start + timedelta(minutes=10)).isoformat() + "+00:00", value=3.0),
    ]
    series_set = SeriesSet(
        metric="pm2_5",
        series=[TimeSeries(id="wohnzimmer", label="Wohnzimmer", unit="ug/m3", points=points)],
        start=points[0].ts,
        end=points[-1].ts,
    )

    summary = summarize(series_set)
    item = summary.summaries[0]

    assert item.count == 2
    assert item.min_value == 1.0
    assert item.max_value == 3.0
    assert item.mean_value == 2.0
    assert item.missing_fraction == 1 / 3


async def test_summarize_history_applies_resampling(fake_provider) -> None:
    query = HistoryQuery(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2.5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
        aggregation="mean",
        requested_interval_s=900,
        timezone="UTC",
    )

    summary = await summarize_history(fake_provider, query)

    assert summary.metric == "pm2_5"
    assert summary.summaries[0].count == 4
