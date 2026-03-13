"""Plot styling models and theme definitions."""

from dataclasses import dataclass
from typing import Literal

ThemeName = Literal["light", "dark", "airq"]
LegendPosition = Literal["right", "bottom", "hidden"]
RangeSelectorMode = Literal["auto", "off", "compact"]

AIRQ_COLORWAY = (
    "#0EA5E9",  # sky-500
    "#10B981",  # emerald-500
    "#F59E0B",  # amber-500
    "#EF4444",  # red-500
    "#8B5CF6",  # violet-500
    "#06B6D4",  # cyan-500
)

LIGHT_COLORWAY = AIRQ_COLORWAY
DARK_COLORWAY = (
    "#38BDF8",  # sky-400
    "#34D399",  # emerald-400
    "#FBBF24",  # amber-400
    "#F87171",  # red-400
    "#A78BFA",  # violet-400
    "#22D3EE",  # cyan-400
)


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    """Define the colors and Plotly template for one visual theme."""

    template: str
    plot_bgcolor: str
    paper_bgcolor: str
    font_color: str
    font_color_secondary: str
    grid_color: str
    axis_line_color: str
    hoverlabel_bgcolor: str
    hoverlabel_font_color: str
    hoverlabel_bordercolor: str
    colorway: tuple[str, ...]


THEMES: dict[ThemeName, ThemeDefinition] = {
    "light": ThemeDefinition(
        template="none",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#374151",
        font_color_secondary="#6B7280",
        grid_color="#E5E7EB",
        axis_line_color="#D1D5DB",
        hoverlabel_bgcolor="#FFFFFF",
        hoverlabel_font_color="#374151",
        hoverlabel_bordercolor="#E5E7EB",
        colorway=LIGHT_COLORWAY,
    ),
    "dark": ThemeDefinition(
        template="none",
        plot_bgcolor="#0D1117",
        paper_bgcolor="#0D1117",
        font_color="#C9D1D9",
        font_color_secondary="#8B949E",
        grid_color="#2D333B",
        axis_line_color="#3D444D",
        hoverlabel_bgcolor="#161B22",
        hoverlabel_font_color="#C9D1D9",
        hoverlabel_bordercolor="#30363D",
        colorway=DARK_COLORWAY,
    ),
    "airq": ThemeDefinition(
        template="none",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#1F2937",
        font_color_secondary="#6B7280",
        grid_color="#E5E7EB",
        axis_line_color="#D1D5DB",
        hoverlabel_bgcolor="#FFFFFF",
        hoverlabel_font_color="#1F2937",
        hoverlabel_bordercolor="#E5E7EB",
        colorway=AIRQ_COLORWAY,
    ),
}


@dataclass(frozen=True, slots=True)
# The public plotting API intentionally exposes these knobs directly.
# pylint: disable=too-many-instance-attributes
class PlotStyle:
    """Collect visual configuration options for plot rendering."""

    theme: ThemeName = "airq"
    dark: bool = False
    width: int = 1200
    height: int = 550
    show_grid: bool = True
    show_range_slider: bool = False
    range_selector: RangeSelectorMode = "auto"
    legend_position: LegendPosition = "bottom"
    line_width: float = 2.0
    marker_size: int = 0
    fill_opacity: float = 0.15
    unify_hover: bool = True
    show_spikes: bool = True
    transparent_background: bool = False
    title: str | None = None
    y_axis_title: str | None = None
    x_axis_title: str | None = None


def get_theme_definition(theme: ThemeName) -> ThemeDefinition:
    """Return the theme configuration for the requested theme name."""

    return THEMES[theme]
