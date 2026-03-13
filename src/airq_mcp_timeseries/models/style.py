"""Plot styling models and theme definitions."""

from dataclasses import dataclass
from typing import Literal

ThemeName = Literal["light", "dark", "airq"]
LegendPosition = Literal["right", "bottom", "hidden"]
RangeSelectorMode = Literal["auto", "off", "compact"]

AIRQ_COLORWAY = (
    "#1273DE",
    "#0E9F6E",
    "#F59E0B",
    "#DC2626",
    "#7C3AED",
    "#0891B2",
)

LIGHT_COLORWAY = AIRQ_COLORWAY
DARK_COLORWAY = (
    "#60A5FA",
    "#34D399",
    "#FBBF24",
    "#F87171",
    "#A78BFA",
    "#22D3EE",
)


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    template: str
    plot_bgcolor: str
    paper_bgcolor: str
    font_color: str
    grid_color: str
    axis_line_color: str
    colorway: tuple[str, ...]


THEMES: dict[ThemeName, ThemeDefinition] = {
    "light": ThemeDefinition(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#111827",
        grid_color="#D9E2EC",
        axis_line_color="#94A3B8",
        colorway=LIGHT_COLORWAY,
    ),
    "dark": ThemeDefinition(
        template="plotly_dark",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0B1220",
        font_color="#E2E8F0",
        grid_color="#334155",
        axis_line_color="#64748B",
        colorway=DARK_COLORWAY,
    ),
    "airq": ThemeDefinition(
        template="plotly_white",
        plot_bgcolor="#F8FBFD",
        paper_bgcolor="#FFFFFF",
        font_color="#15304A",
        grid_color="#DCE7EF",
        axis_line_color="#9FB3C8",
        colorway=AIRQ_COLORWAY,
    ),
}


@dataclass(frozen=True, slots=True)
class PlotStyle:
    theme: ThemeName = "airq"
    width: int = 1200
    height: int = 550
    show_grid: bool = True
    show_range_slider: bool = False
    range_selector: RangeSelectorMode = "auto"
    legend_position: LegendPosition = "right"
    line_width: float = 2.0
    marker_size: int = 0
    fill_opacity: float = 0.15
    unify_hover: bool = True
    show_spikes: bool = False
    transparent_background: bool = False
    title: str | None = None
    y_axis_title: str | None = None
    x_axis_title: str | None = None


def get_theme_definition(theme: ThemeName) -> ThemeDefinition:
    return THEMES[theme]
