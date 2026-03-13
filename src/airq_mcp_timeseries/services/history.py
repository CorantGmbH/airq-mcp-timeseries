"""History loading and high-level orchestration."""

from dataclasses import replace
from datetime import timedelta
from typing import Sequence

from airq_mcp_timeseries.errors import (
    CapabilityNotAvailableError,
    EmptySeriesError,
    MetricNotAvailableError,
)
from airq_mcp_timeseries.models import (
    CapabilitySet,
    HistoryQuery,
    MetricInfo,
    PlotRequest,
    PlotResult,
    SeriesSet,
    SummarySet,
)
from airq_mcp_timeseries.providers.base import TimeSeriesProvider
from airq_mcp_timeseries.renderers.plotly_renderer import render_plotly
from airq_mcp_timeseries.services.downsample import downsample
from airq_mcp_timeseries.services.normalize import (
    normalize_history_query,
    normalize_plot_request,
    select_metric_info,
    utc_now,
)
from airq_mcp_timeseries.services.plot_model import build_plot_model
from airq_mcp_timeseries.services.resample import auto_interval_seconds, resample
from airq_mcp_timeseries.services.summarize import summarize


async def fetch_history(
    provider: TimeSeriesProvider,
    query: HistoryQuery,
    available_metrics: Sequence[MetricInfo] | None = None,
) -> tuple[HistoryQuery, MetricInfo | None, SeriesSet]:
    metrics = (
        list(available_metrics)
        if available_metrics is not None
        else list(await provider.list_metrics(query.selector))
    )
    normalized = normalize_history_query(query, metrics=metrics)
    metric_info = select_metric_info(normalized.metric, metrics)
    if metrics and metric_info is None:
        raise MetricNotAvailableError(
            f"metric '{query.metric}' is not available for the selected source"
        )

    capabilities = await provider.get_capabilities()
    _ensure_history_capability(capabilities, normalized)

    series_set = await provider.get_history(normalized)
    _validate_series_set(series_set, normalized.metric)
    return normalized, metric_info, series_set


async def summarize_history(
    provider: TimeSeriesProvider,
    query: HistoryQuery,
) -> SummarySet:
    normalized_query, _, series_set = await fetch_history(provider, query)
    processed = series_set
    if (
        normalized_query.aggregation != "raw"
        or normalized_query.requested_interval_s is not None
    ):
        interval_s = normalized_query.requested_interval_s or auto_interval_seconds(
            normalized_query.start,
            normalized_query.end,
        )
        processed = resample(
            series_set,
            interval_s=interval_s,
            aggregation=normalized_query.aggregation,
        )
    return summarize(processed)


async def plot_history(
    provider: TimeSeriesProvider,
    request: PlotRequest,
) -> PlotResult:
    available_metrics = list(await provider.list_metrics(request.selector))
    normalized_request = normalize_plot_request(request, metrics=available_metrics)
    history_query = HistoryQuery(
        selector=normalized_request.selector,
        metric=normalized_request.metric,
        start=normalized_request.start,
        end=normalized_request.end,
        aggregation=normalized_request.aggregation,
        requested_interval_s=_requested_interval_for_plot(normalized_request),
        timezone=normalized_request.timezone,
    )
    _, metric_info, series_set = await fetch_history(
        provider,
        history_query,
        available_metrics=available_metrics,
    )

    processed = series_set
    if (
        normalized_request.aggregation != "raw"
        or history_query.requested_interval_s is not None
    ):
        processed = resample(
            processed,
            interval_s=history_query.requested_interval_s,
            aggregation=normalized_request.aggregation,
            target_points=normalized_request.max_points_per_series,
        )
    processed = downsample(
        processed, max_points_per_series=normalized_request.max_points_per_series
    )
    summary = summarize(processed)
    model = build_plot_model(processed, normalized_request, metric_info=metric_info)
    result = await render_plotly(model, normalized_request)
    return replace(result, summary=summary)


def _requested_interval_for_plot(request: PlotRequest) -> int | None:
    if request.aggregation == "raw":
        return None
    return auto_interval_seconds(
        request.start, request.end, target_points=request.max_points_per_series
    )


def _ensure_history_capability(
    capabilities: CapabilitySet, query: HistoryQuery
) -> None:
    if not capabilities.historical_values:
        raise CapabilityNotAvailableError("provider does not support historical values")
    if capabilities.max_lookback_days is None:
        return
    latest_allowed_start = utc_now().astimezone(query.start.tzinfo) - timedelta(
        days=capabilities.max_lookback_days
    )
    if query.start < latest_allowed_start:
        raise CapabilityNotAvailableError(
            f"provider only supports lookback windows up to {capabilities.max_lookback_days} days"
        )


def _validate_series_set(series_set: SeriesSet, expected_metric: str) -> None:
    if series_set.metric != expected_metric:
        raise MetricNotAvailableError(
            f"provider returned metric '{series_set.metric}' but '{expected_metric}' was requested"
        )
    total_points = sum(len(series.points) for series in series_set.series)
    if not series_set.series or total_points == 0:
        raise EmptySeriesError("provider returned no series points")
