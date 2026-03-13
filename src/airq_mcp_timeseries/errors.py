"""Custom exceptions for airq_mcp_timeseries."""


class TimeSeriesError(Exception):
    """Base class for all package-specific errors."""


class CapabilityNotAvailableError(TimeSeriesError):
    """Raised when a provider cannot satisfy a requested capability."""


class MetricNotAvailableError(TimeSeriesError):
    """Raised when a metric cannot be resolved for a provider."""


class InvalidTimeRangeError(TimeSeriesError):
    """Raised when the requested time range is invalid."""


class EmptySeriesError(TimeSeriesError):
    """Raised when a provider returns no usable time-series points."""


class UnsupportedOutputFormatError(TimeSeriesError):
    """Raised when a renderer cannot create the requested output format."""
