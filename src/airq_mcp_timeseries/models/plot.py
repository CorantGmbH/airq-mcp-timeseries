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
# The request object mirrors the public API and keeps fields flat on purpose.
# pylint: disable=too-many-instance-attributes
class PlotRequest:
    """Describe a complete plotting request for one metric."""

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
    """Store renderer-ready x/y arrays for one plotted series."""

    id: str
    label: str
    unit: str | None
    x: list[str]
    y: list[float | None]


@dataclass(frozen=True, slots=True)
class PlotModel:
    """Store the renderer-independent chart representation."""

    metric: str
    title: str
    y_axis_title: str | None
    series: list[PlotModelSeries]


@dataclass(frozen=True, slots=True)
class PlotResult:
    """Return a rendered plot payload and optional computed summary."""

    output_format: OutputFormat
    mime_type: str
    payload: bytes | str
    summary: SummarySet | None = None
