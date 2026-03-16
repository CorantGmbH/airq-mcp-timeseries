from datetime import datetime

import pytest

from airq_mcp_timeseries.errors import InvalidTimeRangeError
from airq_mcp_timeseries.models import HistoryQuery, PlotRequest, Selector
from airq_mcp_timeseries.services.normalize import (
    canonicalize_metric_name,
    normalize_history_query,
    normalize_plot_request,
)


def test_canonicalize_metric_name_normalizes_pm_variants() -> None:
    assert canonicalize_metric_name("PM2.5") == "pm2_5"
    assert canonicalize_metric_name("pm2_5") == "pm2_5"
    assert canonicalize_metric_name("Feinstaub PM2.5") == "pm2_5"


def test_normalize_history_query_resolves_aliases_and_timezone(sample_metrics) -> None:
    query = HistoryQuery(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="Feinstaub PM2.5",
        start=datetime(2026, 3, 1, 8, 0, 0),
        end=datetime(2026, 3, 1, 9, 0, 0),
        timezone="Europe/Berlin",
    )

    normalized = normalize_history_query(query, metrics=sample_metrics)

    assert normalized.metric == "pm2_5"
    assert normalized.timezone == "Europe/Berlin"
    assert normalized.start.tzinfo is not None
    assert getattr(normalized.start.tzinfo, "key", None) == "Europe/Berlin"


def test_plot_request_defaults_to_png() -> None:
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2.5",
        start=datetime(2026, 3, 1, 8, 0, 0),
        end=datetime(2026, 3, 1, 9, 0, 0),
    )

    assert request.output_format == "png"


def test_normalize_plot_request_rejects_invalid_ranges() -> None:
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2.5",
        start=datetime(2026, 3, 1, 9, 0, 0),
        end=datetime(2026, 3, 1, 8, 0, 0),
    )

    with pytest.raises(InvalidTimeRangeError):
        normalize_plot_request(request)
