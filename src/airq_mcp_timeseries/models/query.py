"""Query models and related type aliases."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Aggregation = Literal["raw", "mean", "min", "max", "median"]
ChartType = Literal["line", "area"]
OutputFormat = Literal["html", "png", "svg", "webp"]


@dataclass(frozen=True, slots=True)
class Selector:
    devices: list[str] | None = None
    location: str | None = None
    group: str | None = None


@dataclass(frozen=True, slots=True)
class HistoryQuery:
    selector: Selector
    metric: str
    start: datetime
    end: datetime
    aggregation: Aggregation = "raw"
    requested_interval_s: int | None = None
    timezone: str | None = None
