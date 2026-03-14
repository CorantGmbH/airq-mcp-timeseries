"""Matplotlib renderer for static image output (PNG, SVG, WebP)."""

from __future__ import annotations

import io
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from airq_mcp_timeseries.errors import UnsupportedOutputFormatError
from airq_mcp_timeseries.models import PlotModel, PlotRequest, PlotResult
from airq_mcp_timeseries.models.style import PlotStyle, ThemeDefinition, get_theme_definition

_MIME_TYPES = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}

_FONT_FAMILY = "sans-serif"


def _resolve_theme(style: PlotStyle) -> ThemeDefinition:
    theme_name = "dark" if style.dark else style.theme
    return get_theme_definition(theme_name)


def _parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


async def render_matplotlib(model: PlotModel, request: PlotRequest) -> PlotResult:
    """Render a PlotModel to PNG/SVG/WebP using matplotlib."""

    output_format = request.output_format
    if output_format not in _MIME_TYPES:
        raise UnsupportedOutputFormatError(f"matplotlib renderer does not support '{output_format}'")

    style = request.style
    theme = _resolve_theme(style)

    dpi = 100
    fig, ax = plt.subplots(
        figsize=(style.width / dpi, style.height / dpi),
        dpi=dpi,
    )

    fig.set_facecolor(theme.paper_bgcolor)
    ax.set_facecolor(theme.plot_bgcolor)

    for index, series in enumerate(model.series):
        color = theme.colorway[index % len(theme.colorway)]
        dates = [_parse_dt(ts) for ts in series.x]
        values = series.y

        marker = "o" if style.marker_size > 0 else None
        markersize = style.marker_size if style.marker_size > 0 else None

        ax.plot(
            dates,  # type: ignore[arg-type]
            values,  # type: ignore[arg-type]
            color=color,
            linewidth=style.line_width,
            marker=marker,
            markersize=markersize,
            label=series.label,
            zorder=2,
        )

        if request.chart_type == "area":
            ax.fill_between(
                dates,  # type: ignore[arg-type]
                values,  # type: ignore[arg-type]
                alpha=style.fill_opacity,
                color=color,
                zorder=1,
            )

    # Title
    ax.set_title(
        model.title,
        fontsize=14,
        fontfamily=_FONT_FAMILY,
        color=theme.font_color,
        loc="left",
        pad=12,
    )

    # Axes labels
    if model.y_axis_title:
        ax.set_ylabel(
            model.y_axis_title,
            fontsize=11,
            fontfamily=_FONT_FAMILY,
            color=theme.font_color_secondary,
        )
    if style.x_axis_title:
        ax.set_xlabel(
            style.x_axis_title,
            fontsize=11,
            fontfamily=_FONT_FAMILY,
            color=theme.font_color_secondary,
        )

    # Grid
    ax.grid(
        visible=style.show_grid,
        color=theme.grid_color,
        linestyle=":",
        linewidth=0.8,
        alpha=0.8,
    )

    # Axis styling
    ax.tick_params(
        axis="both",
        colors=theme.font_color_secondary,
        labelsize=10,
        direction="out",
        length=3,
    )
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Date formatting
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    # Legend
    if style.legend_position == "hidden":
        pass
    elif style.legend_position == "bottom":
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.12),
            ncol=len(model.series),
            frameon=False,
            fontsize=10,
            labelcolor=theme.font_color_secondary,
        )
    else:  # right
        ax.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            frameon=False,
            fontsize=10,
            labelcolor=theme.font_color_secondary,
        )

    fig.tight_layout()

    # Render to bytes
    buf = io.BytesIO()
    save_format = "png" if output_format == "webp" else output_format
    fig.savefig(
        buf,
        format=save_format,
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
        transparent=style.transparent_background,
    )
    plt.close(fig)
    buf.seek(0)
    payload = buf.getvalue()

    if output_format == "webp":
        try:
            from PIL import Image as PILImage

            png_buf = io.BytesIO(payload)
            img = PILImage.open(png_buf)
            webp_buf = io.BytesIO()
            img.save(webp_buf, format="WEBP", quality=90)
            webp_buf.seek(0)
            payload = webp_buf.getvalue()
        except ImportError:
            raise UnsupportedOutputFormatError(
                "webp output requires the 'Pillow' package: pip install Pillow"
            ) from None

    return PlotResult(
        output_format=output_format,
        mime_type=_MIME_TYPES[output_format],
        payload=payload,
    )
