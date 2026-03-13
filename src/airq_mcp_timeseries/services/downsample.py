"""Peak-preserving downsampling helpers."""

from dataclasses import replace
from math import ceil

from airq_mcp_timeseries.models import SeriesPoint, SeriesSet, TimeSeries


def downsample(series_set: SeriesSet, max_points_per_series: int) -> SeriesSet:
    """Reduce each series while preserving endpoints and local extrema."""

    if max_points_per_series <= 0:
        raise ValueError("max_points_per_series must be greater than zero")
    reduced = [
        TimeSeries(
            id=series.id,
            label=series.label,
            unit=series.unit,
            points=_downsample_points(series.points, max_points_per_series),
        )
        for series in series_set.series
    ]
    return replace(series_set, series=reduced)


def _downsample_points(
    points: list[SeriesPoint], max_points_per_series: int
) -> list[SeriesPoint]:
    """Reduce one list of points while keeping spikes visible."""

    point_count = len(points)
    if point_count <= max_points_per_series:
        return list(points)

    bucket_count = max(max_points_per_series // 2, 1)
    bucket_size = ceil(point_count / bucket_count)
    selected: set[int] = {0, point_count - 1}

    for bucket_start in range(0, point_count, bucket_size):
        bucket_end = min(bucket_start + bucket_size, point_count)
        selected.update(_bucket_indices(points, bucket_start, bucket_end))

    ordered = sorted(selected)
    if len(ordered) > max_points_per_series:  # pragma: no cover
        middle = ordered[1:-1]
        keep_middle = max(max_points_per_series - 2, 0)
        if keep_middle > 0:
            stride = len(middle) / keep_middle
            sampled_middle = [
                middle[min(int(index * stride), len(middle) - 1)]
                for index in range(keep_middle)
            ]
        else:  # pragma: no cover
            sampled_middle = []
        ordered = [ordered[0], *sampled_middle, ordered[-1]]

    unique_ordered: list[int] = []
    for index in ordered:
        if not unique_ordered or unique_ordered[-1] != index:
            unique_ordered.append(index)
    return [points[index] for index in unique_ordered]


def _bucket_indices(
    points: list[SeriesPoint], bucket_start: int, bucket_end: int
) -> set[int]:
    """Return representative point indexes for one bucket."""

    valid = [
        (bucket_start + offset, point.value)
        for offset, point in enumerate(points[bucket_start:bucket_end])
        if point.value is not None
    ]
    if not valid:
        return {bucket_start, bucket_end - 1}
    return {
        min(valid, key=lambda item: item[1])[0],
        max(valid, key=lambda item: item[1])[0],
    }
