from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from typing import cast

import pytest
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from airq_mcp_timeseries.errors import UnsupportedOutputFormatError
from airq_mcp_timeseries.models import ExportResult, HistoryQuery, Selector
from airq_mcp_timeseries.services.export import export_history, export_series_set


def test_export_series_set_writes_csv(sample_metrics, sample_series_set) -> None:
    result = export_series_set(sample_series_set, output_format="csv", metric_info=sample_metrics[0])

    assert result == ExportResult(
        output_format="csv",
        mime_type="text/csv; charset=utf-8",
        payload=result.payload,
    )
    assert isinstance(result.payload, str)
    lines = result.payload.strip().splitlines()
    assert lines[0] == "timestamp,series,metric,unit,value"
    assert "Wohnzimmer,Feinstaub PM2.5,ug/m3,0.0" in lines[1]


def test_export_series_set_writes_xlsx(sample_metrics, sample_series_set) -> None:
    result = export_series_set(sample_series_set, output_format="xlsx", metric_info=sample_metrics[0])

    assert result.output_format == "xlsx"
    assert result.mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert isinstance(result.payload, bytes)

    workbook = load_workbook(filename=BytesIO(result.payload))
    worksheet = cast(Worksheet, workbook.active)
    rows = list(worksheet.iter_rows(values_only=True))
    workbook.close()

    assert rows[0] == (
        "timestamp",
        "series",
        "metric",
        "unit",
        "value",
    )
    assert rows[1][1:] == (
        "Wohnzimmer",
        "Feinstaub PM2.5",
        "ug/m3",
        0,
    )


@pytest.mark.asyncio
async def test_export_history_resamples_when_requested(sample_metrics, sample_series_set) -> None:
    class Provider:
        async def get_capabilities(self):
            from airq_mcp_timeseries.models import CapabilitySet

            return CapabilitySet(latest_values=True, historical_values=True)

        async def list_metrics(self, selector=None):
            return sample_metrics

        async def get_history(self, query):
            return sample_series_set

    query = HistoryQuery(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="PM2.5",
        start=datetime(2026, 3, 1, tzinfo=UTC),
        end=datetime(2026, 3, 1, 1, 0, 0, tzinfo=UTC),
        aggregation="mean",
        requested_interval_s=1800,
    )

    result = await export_history(Provider(), query, output_format="csv")

    assert isinstance(result.payload, str)
    lines = result.payload.strip().splitlines()
    assert len(lines) == 3
    assert lines[1].endswith(",2.5")
    assert lines[2].endswith(",8.5")


def test_export_series_set_rejects_unknown_format(sample_series_set) -> None:
    with pytest.raises(UnsupportedOutputFormatError):
        export_series_set(sample_series_set, output_format="json")
