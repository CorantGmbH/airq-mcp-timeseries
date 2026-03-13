from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Sequence

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from airq_mcp_timeseries.models import (  # noqa: E402
    CapabilitySet,
    HistoryQuery,
    MetricInfo,
    Selector,
    SeriesPoint,
    SeriesSet,
    TimeSeries,
)


class FakeProvider:
    def __init__(
        self,
        capabilities: CapabilitySet,
        metrics: Sequence[MetricInfo],
        series_set: SeriesSet,
    ) -> None:
        self._capabilities = capabilities
        self._metrics = list(metrics)
        self._series_set = series_set

    async def get_capabilities(self) -> CapabilitySet:
        return self._capabilities

    async def list_metrics(
        self, selector: Selector | None = None
    ) -> Sequence[MetricInfo]:
        return self._metrics

    async def get_history(self, query: HistoryQuery) -> SeriesSet:
        return replace(self._series_set, metric=query.metric)


@pytest.fixture
def sample_metrics() -> list[MetricInfo]:
    return [
        MetricInfo(
            key="pm2_5",
            label="Feinstaub PM2.5",
            unit="ug/m3",
            aliases=("PM2.5", "PM2_5", "Feinstaub PM2.5"),
        )
    ]


@pytest.fixture
def sample_series_set() -> SeriesSet:
    start = datetime(2026, 3, 1, 0, 0, 0)
    points = [
        SeriesPoint(
            ts=(start + timedelta(minutes=5 * index)).isoformat() + "+00:00",
            value=float(index),
        )
        for index in range(12)
    ]
    return SeriesSet(
        metric="pm2_5",
        series=[
            TimeSeries(id="wohnzimmer", label="Wohnzimmer", unit="ug/m3", points=points)
        ],
        start=points[0].ts,
        end=points[-1].ts,
        source_resolution_s=300,
    )


@pytest.fixture
def historical_capabilities() -> CapabilitySet:
    return CapabilitySet(
        latest_values=True, historical_values=True, max_lookback_days=90
    )


@pytest.fixture
def fake_provider(
    historical_capabilities: CapabilitySet,
    sample_metrics: list[MetricInfo],
    sample_series_set: SeriesSet,
) -> FakeProvider:
    return FakeProvider(historical_capabilities, sample_metrics, sample_series_set)
