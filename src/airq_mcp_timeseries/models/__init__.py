"""Domain models for airq_mcp_timeseries."""

from airq_mcp_timeseries.models.capabilities import CapabilitySet
from airq_mcp_timeseries.models.export import ExportFormat, ExportResult
from airq_mcp_timeseries.models.metrics import MetricInfo
from airq_mcp_timeseries.models.plot import (
    PlotModel,
    PlotModelSeries,
    PlotRequest,
    PlotResult,
)
from airq_mcp_timeseries.models.query import (
    Aggregation,
    ChartType,
    HistoryQuery,
    OutputFormat,
    Selector,
)
from airq_mcp_timeseries.models.series import SeriesPoint, SeriesSet, TimeSeries
from airq_mcp_timeseries.models.style import (
    AIRQ_COLORWAY,
    LegendPosition,
    PlotStyle,
    RangeSelectorMode,
    ThemeDefinition,
    ThemeName,
    get_theme_definition,
)
from airq_mcp_timeseries.models.summary import SeriesSummary, SummarySet

__all__ = [
    "AIRQ_COLORWAY",
    "Aggregation",
    "CapabilitySet",
    "ChartType",
    "ExportFormat",
    "ExportResult",
    "HistoryQuery",
    "LegendPosition",
    "MetricInfo",
    "OutputFormat",
    "PlotModel",
    "PlotModelSeries",
    "PlotRequest",
    "PlotResult",
    "PlotStyle",
    "RangeSelectorMode",
    "Selector",
    "SeriesPoint",
    "SeriesSet",
    "SeriesSummary",
    "SummarySet",
    "ThemeDefinition",
    "ThemeName",
    "TimeSeries",
    "get_theme_definition",
]
