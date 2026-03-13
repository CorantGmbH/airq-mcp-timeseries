"""Provider protocol for time-series sources."""

from typing import Protocol, Sequence

from airq_mcp_timeseries.models import (
    CapabilitySet,
    HistoryQuery,
    MetricInfo,
    Selector,
    SeriesSet,
)


class TimeSeriesProvider(Protocol):
    """Protocol implemented by concrete time-series providers."""

    async def get_capabilities(self) -> CapabilitySet:
        """Return provider capabilities."""
        raise NotImplementedError  # pragma: no cover

    async def list_metrics(self, selector: Selector | None = None) -> Sequence[MetricInfo]:
        """List metrics that can be queried for the given selector."""
        raise NotImplementedError  # pragma: no cover

    async def get_history(self, query: HistoryQuery) -> SeriesSet:
        """Load historical time-series data for the given query."""
        raise NotImplementedError  # pragma: no cover
