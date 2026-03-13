"""Resampling helpers."""

from collections import defaultdict
from dataclasses import replace
from datetime import datetime
from math import ceil
from statistics import mean, median
from typing import Callable

from airq_mcp_timeseries.models import Aggregation, SeriesPoint, SeriesSet, TimeSeries

_FRIENDLY_INTERVALS = (
    1,
    5,
    10,
    15,
    30,
    60,
    120,
    300,
    600,
    900,
    1800,
    3600,
    7200,
    14400,
    21600,
    43200,
    86400,
)


def auto_interval_seconds(
    start: datetime, end: datetime, target_points: int = 1200
) -> int:
    duration_s = max((end - start).total_seconds(), 1.0)
    safe_target = min(max(target_points, 100), 4000)
    raw_interval = max(duration_s / safe_target, 1.0)
    for interval in _FRIENDLY_INTERVALS:
        if interval >= raw_interval:
            return interval
    return ceil(raw_interval / 86400) * 86400


def resample(
    series_set: SeriesSet,
    interval_s: int | None = None,
    aggregation: Aggregation = "raw",
    target_points: int = 1200,
) -> SeriesSet:
    if aggregation == "raw" and interval_s is None:
        return series_set
    start = _parse_iso_datetime(series_set.start)
    end = _parse_iso_datetime(series_set.end)
    bucket_size = interval_s or auto_interval_seconds(
        start, end, target_points=target_points
    )
    resampled = [
        TimeSeries(
            id=series.id,
            label=series.label,
            unit=series.unit,
            points=_resample_points(series.points, bucket_size, aggregation),
        )
        for series in series_set.series
    ]
    return replace(
        series_set,
        series=resampled,
        source_resolution_s=bucket_size,
    )


def _resample_points(
    points: list[SeriesPoint], interval_s: int, aggregation: Aggregation
) -> list[SeriesPoint]:
    buckets: dict[int, list[SeriesPoint]] = defaultdict(list)
    timezone = None
    for point in points:
        dt = _parse_iso_datetime(point.ts)
        timezone = timezone or dt.tzinfo
        epoch = int(dt.timestamp())
        bucket_epoch = epoch - (epoch % interval_s)
        buckets[bucket_epoch].append(point)

    aggregate = _aggregator(aggregation)
    result: list[SeriesPoint] = []
    for bucket_epoch in sorted(buckets):
        bucket_points = buckets[bucket_epoch]
        values = [point.value for point in bucket_points if point.value is not None]
        if aggregation == "raw":
            value = next(
                (
                    point.value
                    for point in reversed(bucket_points)
                    if point.value is not None
                ),
                None,
            )
        elif values:
            value = aggregate(values)
        else:
            value = None
        bucket_dt = datetime.fromtimestamp(bucket_epoch, tz=timezone)
        result.append(SeriesPoint(ts=bucket_dt.isoformat(), value=value))
    return result


def _aggregator(aggregation: Aggregation) -> Callable[[list[float]], float]:
    if aggregation == "mean":
        return mean
    if aggregation == "min":
        return min
    if aggregation == "max":
        return max
    if aggregation == "median":
        return median
    return lambda values: values[-1]


def _parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
