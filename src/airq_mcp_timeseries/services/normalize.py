"""Normalization helpers for metrics, queries and requests."""

import re
from dataclasses import replace
from datetime import UTC, datetime
from typing import Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from airq_mcp_timeseries.errors import InvalidTimeRangeError
from airq_mcp_timeseries.models import HistoryQuery, MetricInfo, PlotRequest

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_PM_METRIC_RE = re.compile(r"pm\s*([0-9]+)(?:[.,_ ]([0-9]+))?", re.IGNORECASE)


def canonicalize_metric_name(metric: str) -> str:
    """Create a stable, comparable metric key."""
    stripped = metric.strip()
    pm_match = _PM_METRIC_RE.search(stripped)
    if pm_match:
        major = pm_match.group(1)
        minor = pm_match.group(2)
        return f"pm{major}_{minor}" if minor else f"pm{major}"
    normalized = _NON_ALNUM_RE.sub("_", stripped.casefold()).strip("_")
    return normalized


def select_metric_info(metric: str, metrics: Sequence[MetricInfo] | None = None) -> MetricInfo | None:
    """Resolve one metric name or alias to its metadata record."""

    if not metrics:
        return None
    alias_map = _metric_alias_map(metrics)
    key = alias_map.get(canonicalize_metric_name(metric))
    if key is None:
        return None
    return next((item for item in metrics if item.key == key), None)


def normalize_metric_name(metric: str, metrics: Sequence[MetricInfo] | None = None) -> str:
    """Resolve a metric to its canonical provider key if possible."""
    info = select_metric_info(metric, metrics)
    if info is not None:
        return info.key
    return canonicalize_metric_name(metric)


def normalize_history_query(
    query: HistoryQuery,
    metrics: Sequence[MetricInfo] | None = None,
    default_timezone: str = "UTC",
) -> HistoryQuery:
    """Normalize a history query and ensure its time range is valid."""

    timezone_name = _resolve_timezone_name(query.timezone, default_timezone)
    zone = _get_timezone(timezone_name)
    start = _coerce_datetime(query.start, zone)
    end = _coerce_datetime(query.end, zone)
    _validate_time_range(start, end)
    if query.requested_interval_s is not None and query.requested_interval_s <= 0:
        raise InvalidTimeRangeError("requested_interval_s must be greater than zero")
    return replace(
        query,
        metric=normalize_metric_name(query.metric, metrics),
        start=start,
        end=end,
        timezone=timezone_name,
    )


def normalize_plot_request(
    request: PlotRequest,
    metrics: Sequence[MetricInfo] | None = None,
    default_timezone: str = "UTC",
) -> PlotRequest:
    """Normalize a plot request and ensure its time range is valid."""

    timezone_name = _resolve_timezone_name(request.timezone, default_timezone)
    zone = _get_timezone(timezone_name)
    start = _coerce_datetime(request.start, zone)
    end = _coerce_datetime(request.end, zone)
    _validate_time_range(start, end)
    if request.max_points_per_series <= 0:
        raise InvalidTimeRangeError("max_points_per_series must be greater than zero")
    return replace(
        request,
        metric=normalize_metric_name(request.metric, metrics),
        start=start,
        end=end,
        timezone=timezone_name,
    )


def humanize_metric_name(metric: str) -> str:
    """Generate a readable fallback label for a metric key."""

    raw = metric.replace("_", " ").strip()
    if raw.lower().startswith("pm") and any(ch.isdigit() for ch in raw):
        return raw.upper().replace(" ", "")
    return raw.title()


def default_plot_title(metric: str, metric_info: MetricInfo | None = None) -> str:
    """Build the default plot title from metric metadata or key."""

    return metric_info.label if metric_info is not None else humanize_metric_name(metric)


def default_y_axis_title(metric_info: MetricInfo | None, fallback_unit: str | None = None) -> str | None:
    """Choose the y-axis title from metric metadata or fallback unit."""

    if metric_info is not None and metric_info.unit:
        return metric_info.unit
    return fallback_unit


def _metric_alias_map(metrics: Sequence[MetricInfo]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for metric in metrics:
        for candidate in (metric.key, metric.label, *metric.aliases):
            aliases[canonicalize_metric_name(candidate)] = metric.key
    return aliases


def _resolve_timezone_name(explicit_timezone: str | None, default_timezone: str) -> str:
    """Choose the effective timezone name for normalization."""

    if explicit_timezone:
        return explicit_timezone
    return default_timezone


def _get_timezone(timezone_name: str) -> ZoneInfo:
    """Load a timezone or raise a package-specific validation error."""

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise InvalidTimeRangeError(f"unknown timezone: {timezone_name}") from exc


def _coerce_datetime(value: datetime, zone: ZoneInfo) -> datetime:
    """Attach or convert a datetime into the target timezone."""

    if value.tzinfo is None:
        return value.replace(tzinfo=zone)
    return value.astimezone(zone)


def _validate_time_range(start: datetime, end: datetime) -> None:
    """Ensure a normalized time range is timezone-aware and ordered."""

    if start.tzinfo is None or end.tzinfo is None:
        raise InvalidTimeRangeError("start and end must be timezone-aware after normalization")
    if end <= start:
        raise InvalidTimeRangeError("end must be after start")


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)
