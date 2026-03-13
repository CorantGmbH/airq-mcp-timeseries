"""Summary calculations for series sets."""

from statistics import mean

from airq_mcp_timeseries.models import SeriesSet, SeriesSummary, SummarySet


def summarize(series_set: SeriesSet) -> SummarySet:
    """Compute per-series summary statistics for a series set."""

    summaries = []
    for series in series_set.series:
        values = [point.value for point in series.points if point.value is not None]
        total_count = len(series.points)
        valid_count = len(values)
        summaries.append(
            SeriesSummary(
                series_id=series.id,
                count=valid_count,
                min_value=min(values) if values else None,
                max_value=max(values) if values else None,
                mean_value=mean(values) if values else None,
                missing_fraction=(None if total_count == 0 else (total_count - valid_count) / total_count),
            )
        )
    return SummarySet(metric=series_set.metric, summaries=summaries)
