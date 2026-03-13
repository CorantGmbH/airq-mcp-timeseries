"""Time-series data models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    """Represent a single timestamped value in a time series."""

    ts: str
    value: float | None


@dataclass(frozen=True, slots=True)
class TimeSeries:
    """Represent one named series of points returned by a provider."""

    id: str
    label: str
    unit: str | None
    points: list[SeriesPoint]


@dataclass(frozen=True, slots=True)
class SeriesSet:
    """Represent a metric and all matching time series for a query."""

    metric: str
    series: list[TimeSeries]
    start: str
    end: str
    source_resolution_s: int | None = None
