"""Plot request and result models."""

from dataclasses import dataclass, field
from datetime import datetime

from airq_mcp_timeseries.models.query import (
    Aggregation,
    ChartType,
    OutputFormat,
    Selector,
)
from airq_mcp_timeseries.models.style import PlotStyle
from airq_mcp_timeseries.models.summary import SummarySet


@dataclass(frozen=True, slots=True)
class PlotRequest:
    selector: Selector
    metric: str
    start: datetime
    end: datetime
    chart_type: ChartType = "line"
    aggregation: Aggregation = "raw"
    max_points_per_series: int = 1200
    timezone: str | None = None
    output_format: OutputFormat = "html"
    style: PlotStyle = field(default_factory=PlotStyle)


@dataclass(frozen=True, slots=True)
class PlotModelSeries:
    id: str
    label: str
    unit: str | None
    x: list[str]
    y: list[float | None]


@dataclass(frozen=True, slots=True)
class PlotModel:
    metric: str
    title: str
    y_axis_title: str | None
    series: list[PlotModelSeries]


@dataclass(frozen=True, slots=True)
class PlotResult:
    output_format: OutputFormat
    mime_type: str
    payload: bytes | str
    summary: SummarySet | None = None
