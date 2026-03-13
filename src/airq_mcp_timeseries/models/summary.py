"""Summary models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeriesSummary:
    """Store summary statistics for a single series."""

    series_id: str
    count: int
    min_value: float | None
    max_value: float | None
    mean_value: float | None
    missing_fraction: float | None


@dataclass(frozen=True, slots=True)
class SummarySet:
    """Store summary statistics for every series of one metric."""

    metric: str
    summaries: list[SeriesSummary]
