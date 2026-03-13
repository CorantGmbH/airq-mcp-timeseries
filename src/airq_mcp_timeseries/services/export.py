"""Tabular export helpers for time-series data."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO

from openpyxl import Workbook

from airq_mcp_timeseries.errors import UnsupportedOutputFormatError
from airq_mcp_timeseries.models import ExportResult, HistoryQuery, MetricInfo, SeriesSet
from airq_mcp_timeseries.providers.base import TimeSeriesProvider
from airq_mcp_timeseries.services.history import fetch_history
from airq_mcp_timeseries.services.resample import auto_interval_seconds, resample

_EXPORT_MIME_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
_EXPORT_HEADERS = [
    "timestamp",
    "series_id",
    "series_label",
    "metric",
    "metric_label",
    "unit",
    "value",
]


async def export_history(
    provider: TimeSeriesProvider,
    query: HistoryQuery,
    output_format: str = "csv",
) -> ExportResult:
    normalized_query, metric_info, series_set = await fetch_history(provider, query)
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
    return export_series_set(
        processed, output_format=output_format, metric_info=metric_info
    )


def export_series_set(
    series_set: SeriesSet,
    output_format: str,
    metric_info: MetricInfo | None = None,
) -> ExportResult:
    if output_format == "csv":
        payload = _write_csv(series_set, metric_info=metric_info)
    elif output_format == "xlsx":
        payload = _write_xlsx(series_set, metric_info=metric_info)
    else:
        raise UnsupportedOutputFormatError(
            f"unsupported export format: {output_format}"
        )

    return ExportResult(
        output_format=output_format,
        mime_type=_EXPORT_MIME_TYPES[output_format],
        payload=payload,
    )


def _rows(
    series_set: SeriesSet, metric_info: MetricInfo | None
) -> list[list[str | float | None]]:
    metric_label = metric_info.label if metric_info is not None else series_set.metric
    rows: list[list[str | float | None]] = []
    for series in series_set.series:
        for point in series.points:
            rows.append(
                [
                    point.ts,
                    series.id,
                    series.label,
                    series_set.metric,
                    metric_label,
                    series.unit,
                    point.value,
                ]
            )
    return rows


def _write_csv(series_set: SeriesSet, metric_info: MetricInfo | None) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_EXPORT_HEADERS)
    writer.writerows(_rows(series_set, metric_info))
    return buffer.getvalue()


def _write_xlsx(series_set: SeriesSet, metric_info: MetricInfo | None) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    if worksheet is None:  # pragma: no cover - Workbook always creates an active sheet
        raise RuntimeError("workbook did not provide an active worksheet")
    worksheet.title = "timeseries"
    worksheet.append(_EXPORT_HEADERS)
    for row in _rows(series_set, metric_info):
        worksheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()
