"""Time-series data models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    ts: str
    value: float | None


@dataclass(frozen=True, slots=True)
class TimeSeries:
    id: str
    label: str
    unit: str | None
    points: list[SeriesPoint]


@dataclass(frozen=True, slots=True)
class SeriesSet:
    metric: str
    series: list[TimeSeries]
    start: str
    end: str
    source_resolution_s: int | None = None
