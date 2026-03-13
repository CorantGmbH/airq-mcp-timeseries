"""Build renderer-independent plot models."""

from airq_mcp_timeseries.errors import EmptySeriesError
from airq_mcp_timeseries.models import (
    MetricInfo,
    PlotModel,
    PlotModelSeries,
    PlotRequest,
    SeriesSet,
)
from airq_mcp_timeseries.services.normalize import (
    default_plot_title,
    default_y_axis_title,
)


def build_plot_model(
    series_set: SeriesSet,
    request: PlotRequest,
    metric_info: MetricInfo | None = None,
) -> PlotModel:
    """Convert a processed series set into a renderer-neutral plot model."""

    if not series_set.series:
        raise EmptySeriesError("cannot build a plot model from an empty series set")

    common_units = {series.unit for series in series_set.series if series.unit}
    fallback_unit = next(iter(common_units), None) if len(common_units) == 1 else None
    title = request.style.title or default_plot_title(series_set.metric, metric_info)
    y_axis_title = request.style.y_axis_title or default_y_axis_title(metric_info, fallback_unit)

    plot_series = [
        PlotModelSeries(
            id=series.id,
            label=series.label,
            unit=series.unit,
            x=[point.ts for point in series.points],
            y=[point.value for point in series.points],
        )
        for series in series_set.series
    ]
    return PlotModel(
        metric=series_set.metric,
        title=title,
        y_axis_title=y_axis_title,
        series=plot_series,
    )
