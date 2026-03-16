"""Shared time-series domain layer for air-Q MCP providers."""

# pylint: disable=duplicate-code

from airq_mcp_timeseries.errors import (
    CapabilityNotAvailableError,
    EmptySeriesError,
    InvalidTimeRangeError,
    MetricNotAvailableError,
    TimeSeriesError,
    UnsupportedOutputFormatError,
)
from airq_mcp_timeseries.models import (
    AIRQ_COLORWAY,
    CapabilitySet,
    ChartType,
    ExportFormat,
    ExportResult,
    HistoryQuery,
    MetricInfo,
    OutputFormat,
    PlotModel,
    PlotModelSeries,
    PlotRequest,
    PlotResult,
    PlotStyle,
    Selector,
    SeriesPoint,
    SeriesSet,
    SeriesSummary,
    SummarySet,
    ThemeName,
    TimeSeries,
)
from airq_mcp_timeseries.providers.base import TimeSeriesProvider
from airq_mcp_timeseries.renderers import render, render_matplotlib, render_plotly
from airq_mcp_timeseries.services.downsample import downsample
from airq_mcp_timeseries.services.export import export_history, export_series_set
from airq_mcp_timeseries.services.history import plot_history, summarize_history
from airq_mcp_timeseries.services.plot_model import build_plot_model
from airq_mcp_timeseries.services.resample import auto_interval_seconds, resample
from airq_mcp_timeseries.services.summarize import summarize

__version__ = "0.1.7"

__all__ = [
    "AIRQ_COLORWAY",
    "CapabilityNotAvailableError",
    "CapabilitySet",
    "ChartType",
    "EmptySeriesError",
    "ExportFormat",
    "ExportResult",
    "HistoryQuery",
    "InvalidTimeRangeError",
    "MetricInfo",
    "MetricNotAvailableError",
    "OutputFormat",
    "PlotModel",
    "PlotModelSeries",
    "PlotRequest",
    "PlotResult",
    "PlotStyle",
    "Selector",
    "SeriesPoint",
    "SeriesSet",
    "SeriesSummary",
    "SummarySet",
    "ThemeName",
    "TimeSeries",
    "TimeSeriesError",
    "TimeSeriesProvider",
    "UnsupportedOutputFormatError",
    "auto_interval_seconds",
    "build_plot_model",
    "downsample",
    "export_history",
    "export_series_set",
    "plot_history",
    "render",
    "render_matplotlib",
    "render_plotly",
    "resample",
    "summarize",
    "summarize_history",
]
