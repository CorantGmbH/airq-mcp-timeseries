from datetime import datetime

from airq_mcp_timeseries.models import MetricInfo, PlotRequest, Selector
from airq_mcp_timeseries.services.plot_model import build_plot_model


def test_build_plot_model_uses_metric_metadata(sample_series_set) -> None:
    request = PlotRequest(
        selector=Selector(devices=["Wohnzimmer"]),
        metric="pm2_5",
        start=datetime(2026, 3, 1, 0, 0, 0),
        end=datetime(2026, 3, 1, 1, 0, 0),
    )
    metric = MetricInfo(key="pm2_5", label="Feinstaub PM2.5", unit="ug/m3")

    model = build_plot_model(sample_series_set, request, metric_info=metric)

    assert model.metric == "pm2_5"
    assert model.title == "Feinstaub PM2.5"
    assert model.y_axis_title == "ug/m3"
    assert model.series[0].x[0] == sample_series_set.series[0].points[0].ts
