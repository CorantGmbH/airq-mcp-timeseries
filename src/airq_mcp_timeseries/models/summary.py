"""Summary models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeriesSummary:
    series_id: str
    count: int
    min_value: float | None
    max_value: float | None
    mean_value: float | None
    missing_fraction: float | None


@dataclass(frozen=True, slots=True)
class SummarySet:
    metric: str
    summaries: list[SeriesSummary]
