from datetime import datetime

import pytest

from airq_mcp_timeseries.errors import CapabilityNotAvailableError
from airq_mcp_timeseries.models import (
    CapabilitySet,
    HistoryQuery,
    PlotRequest,
    Selector,
)
from airq_mcp_timeseries.services.history import fetch_history, plot_history


async def test_fetch_history_rejects_missing_history_capability(sample_metrics, sample_series_set) -> None:
    class LocalProvider:
        async def get_capabilities(self) -> CapabilitySet:
            return CapabilitySet(latest_values=True, historical_values=False)

        async def list_metrics(self, selector=None):
            return sample_metrics

        async def get_history(self, query):
            return sample_series_set

    with pytest.raises(CapabilityNotAvailableError):
        await fetch_history(
            LocalProvider(),
            query=HistoryQuery(
                selector=Selector(devices=["Wohnzimmer"]),
                metric="pm2.5",
                start=datetime(2026, 3, 1, 0, 0, 0),
                end=datetime(2026, 3, 1, 1, 0, 0),
            ),
        )


async def test_plot_history_returns_plot_and_summary(fake_provider) -> None:
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="PM2.5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
        output_format="html",
    )

    result = await plot_history(fake_provider, request)

    assert result.summary is not None
    assert result.summary.metric == "pm2_5"
    assert isinstance(result.payload, str)
    assert "plotly" in result.payload.lower()
