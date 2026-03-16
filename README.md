# airq-mcp-timeseries

[![PyPI](https://img.shields.io/pypi/v/airq-mcp-timeseries)](https://pypi.org/project/airq-mcp-timeseries/)
[![Python](https://img.shields.io/pypi/pyversions/airq-mcp-timeseries)](https://pypi.org/project/airq-mcp-timeseries/)
[![License](https://img.shields.io/pypi/l/airq-mcp-timeseries)](LICENSE)
[![Tests](https://github.com/CorantGmbH/airq-mcp-timeseries/actions/workflows/tests.yml/badge.svg)](https://github.com/CorantGmbH/airq-mcp-timeseries/actions/workflows/tests.yml)
[![Publish to PyPI](https://github.com/CorantGmbH/airq-mcp-timeseries/actions/workflows/publish.yml/badge.svg)](https://github.com/CorantGmbH/airq-mcp-timeseries/actions/workflows/publish.yml)
[![pre-commit enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)

Shared time-series domain layer and Plotly renderer for air-Q MCP providers.

This project is not an MCP server. It is the shared package that consolidates
time-series querying, normalization, resampling, summarization and plotting so
that `mcp-airq` and `mcp-airq-cloud` can reuse the same business logic.

## Features

- shared query, series, summary and plotting data models
- source-agnostic `TimeSeriesProvider` protocol
- metric normalization and query validation
- resampling and peak-preserving downsampling
- renderer-independent plot model
- Plotly rendering for HTML plus matplotlib-based PNG, SVG and WebP exports
- CSV and Excel export for processed time-series data
- async high-level orchestration with `plot_history()`, `summarize_history()` and `export_history()`

## Installation

```bash
pip install airq-mcp-timeseries
```

This package now includes `Pillow` as a runtime dependency so WebP rendering
works out of the box.

For development:

```bash
uv sync --frozen --extra dev
uv run pre-commit install
```

## Usage

```python
from datetime import datetime, timedelta

from airq_mcp_timeseries import HistoryQuery, PlotRequest, Selector, export_history, plot_history

request = PlotRequest(
    selector=Selector(devices=["Living Room"]),
    metric="co2",
    start=datetime.now().astimezone() - timedelta(hours=6),
    end=datetime.now().astimezone(),
)

result = await plot_history(provider, request)

export = await export_history(
    provider,
    HistoryQuery(
        selector=request.selector,
        metric=request.metric,
        start=request.start,
        end=request.end,
    ),
    output_format="csv",
)
```

`provider` must implement the shared `TimeSeriesProvider` protocol.

## Development

Run the full local validation stack:

```bash
uv run pre-commit run --all-files
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest --exitfirst -n auto
```

## Release Process

1. Update `version` in `pyproject.toml`.
2. Commit the change and create a matching Git tag such as `v0.1.2`.
3. Publish a GitHub Release from that tag.

The publish workflow validates that the release tag matches
`pyproject.toml`, builds the package and publishes it to PyPI.

## License

Apache License 2.0. See [LICENSE](LICENSE).
