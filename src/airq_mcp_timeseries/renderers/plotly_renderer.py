"""Plotly renderer implementation."""

import json
import re
from typing import Any

import plotly.graph_objects as go

from airq_mcp_timeseries.models import (
    PlotModel,
    PlotRequest,
    PlotResult,
    get_theme_definition,
)
from airq_mcp_timeseries.models.style import PlotStyle, ThemeDefinition

_FONT_FAMILY = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


def _resolve_theme(style: PlotStyle) -> ThemeDefinition:
    theme_name = "dark" if style.dark else style.theme
    return get_theme_definition(theme_name)


async def render_plotly(model: PlotModel, request: PlotRequest) -> PlotResult:
    """Render a plot model as interactive HTML with Plotly."""

    figure = _build_figure(model, request)
    raw_html = figure.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config=_html_config(),
    )
    payload = _wrap_html_with_toggle(raw_html, request)
    return PlotResult(
        output_format="html",
        mime_type="text/html",
        payload=payload,
    )


def _build_figure(model: PlotModel, request: PlotRequest) -> go.Figure:
    theme = _resolve_theme(request.style)
    is_html = request.output_format == "html"
    figure = go.Figure()

    for index, series in enumerate(model.series):
        color = theme.colorway[index % len(theme.colorway)]
        figure.add_trace(
            go.Scatter(
                x=series.x,
                y=series.y,
                mode="lines+markers" if request.style.marker_size > 0 else "lines",
                name=series.label,
                line={
                    "width": request.style.line_width,
                    "color": color,
                    "shape": "spline",
                    "smoothing": 1.0,
                },
                marker={"size": request.style.marker_size, "color": color},
                fill="tozeroy" if request.chart_type == "area" else None,
                fillcolor=(_hex_to_rgba(color, request.style.fill_opacity) if request.chart_type == "area" else None),
                hovertemplate=_hover_template(series.unit),
            )
        )

    paper_bgcolor = "rgba(0,0,0,0)" if request.style.transparent_background else theme.paper_bgcolor
    plot_bgcolor = "rgba(0,0,0,0)" if request.style.transparent_background else theme.plot_bgcolor

    figure.update_layout(
        template="none",
        width=request.style.width,
        height=request.style.height,
        title={
            "text": model.title,
            "x": 0.0,
            "xanchor": "left",
            "pad": {"l": 8, "t": 4},
            "font": {"size": 17, "family": _FONT_FAMILY, "color": theme.font_color},
        },
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        font={
            "color": theme.font_color_secondary,
            "size": 12,
            "family": _FONT_FAMILY,
        },
        colorway=list(theme.colorway),
        hovermode="x unified" if request.style.unify_hover else "closest",
        hoverlabel={
            "bgcolor": theme.hoverlabel_bgcolor,
            "font": {
                "color": theme.hoverlabel_font_color,
                "size": 12,
                "family": _FONT_FAMILY,
            },
            "bordercolor": theme.hoverlabel_bordercolor,
        },
        margin={"l": 60, "r": 24, "t": 72, "b": 64},
        legend=_legend_config(request.style.legend_position),
        # Explicit defaults required when template="none"
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"zeroline": False},
    )

    range_selector = _range_selector(request, theme) if is_html else None
    figure.update_xaxes(
        title_text=request.style.x_axis_title,
        showgrid=False,
        showline=False,
        zeroline=False,
        ticks="outside",
        ticklen=3,
        tickcolor=theme.grid_color,
        tickfont={"color": theme.font_color_secondary, "family": _FONT_FAMILY},
        rangeslider={"visible": is_html and request.style.show_range_slider},
        rangeselector=range_selector,
        showspikes=is_html and request.style.show_spikes,
        spikecolor=theme.grid_color,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=1,
        spikedash="solid",
    )
    figure.update_yaxes(
        title_text=model.y_axis_title,
        title_font={"color": theme.font_color_secondary, "family": _FONT_FAMILY},
        showgrid=request.style.show_grid,
        gridcolor=theme.grid_color,
        griddash="dot",
        showline=False,
        zeroline=False,
        ticks="outside",
        ticklen=3,
        tickcolor=theme.grid_color,
        tickfont={"color": theme.font_color_secondary, "family": _FONT_FAMILY},
    )
    return figure


def _html_config() -> dict[str, Any]:
    return {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "select2d",
            "lasso2d",
            "autoScale2d",
            "toggleSpikelines",
        ],
    }


def _legend_config(position: str) -> dict[str, Any]:
    if position == "hidden":
        return {"visible": False}
    if position == "bottom":
        return {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
        }
    return {
        "orientation": "v",
        "yanchor": "top",
        "y": 1.0,
        "xanchor": "left",
        "x": 1.02,
    }


def _range_selector(request: PlotRequest, theme: ThemeDefinition) -> dict[str, Any] | None:
    if request.style.range_selector == "off":
        return None
    duration_days = max((request.end - request.start).total_seconds() / 86400, 0.0)
    if request.style.range_selector == "auto" and duration_days < 3:
        return None
    return {
        "bgcolor": theme.paper_bgcolor,
        "activecolor": _hex_to_rgba(theme.colorway[0], 0.15),
        "bordercolor": theme.grid_color,
        "borderwidth": 1,
        "font": {
            "size": 11,
            "family": _FONT_FAMILY,
            "color": theme.font_color_secondary,
        },
        "buttons": [
            {"count": 1, "label": "24h", "step": "day", "stepmode": "backward"},
            {"count": 7, "label": "7d", "step": "day", "stepmode": "backward"},
            {"count": 1, "label": "30d", "step": "month", "stepmode": "backward"},
            {"step": "all", "label": "All"},
        ],
    }


def _hover_template(unit: str | None) -> str:
    suffix = f" {unit}" if unit else ""
    return "%{x}<br>%{y}" + suffix + "<extra>%{fullData.name}</extra>"


def _hex_to_rgba(color: str, opacity: float) -> str:
    color = color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {opacity})"


# ---------------------------------------------------------------------------
# HTML theme toggle + system color-scheme detection
# ---------------------------------------------------------------------------


def _theme_to_js(theme: ThemeDefinition, fill_opacity: float) -> dict:
    colors = list(theme.colorway)
    return {
        "plot_bgcolor": theme.plot_bgcolor,
        "paper_bgcolor": theme.paper_bgcolor,
        "font_color": theme.font_color,
        "font_color_secondary": theme.font_color_secondary,
        "grid_color": theme.grid_color,
        "axis_line_color": theme.axis_line_color,
        "hl_bg": theme.hoverlabel_bgcolor,
        "hl_fg": theme.hoverlabel_font_color,
        "hl_border": theme.hoverlabel_bordercolor,
        "colorway": colors,
        "fills": [_hex_to_rgba(c, fill_opacity) for c in colors],
        "range_active": _hex_to_rgba(colors[0], 0.15),
    }


def _wrap_html_with_toggle(html: str, request: PlotRequest) -> str:
    """Wrap the Plotly HTML fragment with a dark/light theme toggle button."""
    match = re.search(r'id="([^"]+)"[^>]*class="plotly-graph-div"', html)
    if not match:
        return html

    style = request.style
    is_dark = style.dark or style.theme == "dark"
    light_theme = get_theme_definition("airq")
    dark_theme = get_theme_definition("dark")
    cur_theme = dark_theme if is_dark else light_theme
    div_id = match.group(1)
    js_fn = f"_airqToggle_{div_id.replace('-', '_')}"
    light_js = _theme_to_js(light_theme, style.fill_opacity)
    dark_js = _theme_to_js(dark_theme, style.fill_opacity)

    css = (
        "<style>"
        "body{margin:0;padding:0;"
        f"background:{cur_theme.paper_bgcolor};"
        "transition:background 0.3s}"
        ".airq-chart-wrap{position:relative;display:inline-block;"
        f"background:{cur_theme.paper_bgcolor};"
        "width:100%;transition:background 0.3s}"
        ".airq-theme-btn{"
        "position:absolute;top:8px;right:8px;z-index:100;"
        "width:30px;height:30px;border-radius:6px;"
        f"border:1px solid {cur_theme.grid_color};"
        f"background:{cur_theme.paper_bgcolor};"
        f"color:{cur_theme.font_color};"
        "font-size:14px;cursor:pointer;display:flex;align-items:center;"
        "justify-content:center;opacity:0;transition:opacity 0.2s;"
        "line-height:1;padding:0;box-shadow:0 1px 3px rgba(0,0,0,.12)}"
        ".airq-chart-wrap:hover .airq-theme-btn{opacity:0.75}"
        ".airq-theme-btn:hover{opacity:1!important}"
        "</style>"
    )

    # JS: use explicit T.l (light) and T.d (dark) so toggle logic is always correct
    js = (
        "<script>"
        "(function(){"
        f"var D={json.dumps(div_id)};"
        f"var T={{l:{json.dumps(light_js)},d:{json.dumps(dark_js)}}};"
        f"var dark={json.dumps(is_dark)};"
        "function apply(t,btn){"
        "var el=document.getElementById(D);"
        "if(!el||!el.data)return;"
        "var n=el.data.length,lc=[],fc=[];"
        "for(var i=0;i<n;i++){lc.push(t.colorway[i%t.colorway.length]);fc.push(t.fills[i%t.fills.length]);}"
        "Plotly.relayout(el,{"
        "plot_bgcolor:t.plot_bgcolor,"
        "paper_bgcolor:t.paper_bgcolor,"
        "'font.color':t.font_color_secondary,"
        "'title.font.color':t.font_color,"
        "'yaxis.gridcolor':t.grid_color,"
        "'xaxis.tickcolor':t.grid_color,"
        "'yaxis.tickcolor':t.grid_color,"
        "'hoverlabel.bgcolor':t.hl_bg,"
        "'hoverlabel.font.color':t.hl_fg,"
        "'hoverlabel.bordercolor':t.hl_border,"
        "'xaxis.rangeselector.bgcolor':t.paper_bgcolor,"
        "'xaxis.rangeselector.bordercolor':t.grid_color,"
        "'xaxis.rangeselector.activecolor':t.range_active,"
        "'xaxis.rangeselector.font.color':t.font_color_secondary,"
        "'xaxis.spikecolor':t.axis_line_color});"
        "Plotly.restyle(el,{'line.color':lc,'marker.color':lc,'fillcolor':fc});"
        "var wrap=document.querySelector('.airq-chart-wrap');"
        "if(wrap)wrap.style.background=t.paper_bgcolor;"
        "document.body.style.background=t.paper_bgcolor;"
        "if(btn){"
        "btn.textContent=dark?'\\u2600\\ufe0f':'\\ud83c\\udf19';"
        "btn.title=dark?'Switch to light theme':'Switch to dark theme';"
        "btn.style.borderColor=t.grid_color;"
        "btn.style.background=t.paper_bgcolor;"
        "btn.style.color=t.font_color;}}"
        # Toggle: when dark, switch to light; when light, switch to dark
        f"window[{json.dumps(js_fn)}]=function(btn){{"
        "dark=!dark;"
        "apply(dark?T.d:T.l,btn);};"
        # System preference detection
        "var mq=window.matchMedia('(prefers-color-scheme: dark)');"
        "function syncSys(wantDark){"
        "if(wantDark===dark)return;"
        "dark=wantDark;"
        "var t=dark?T.d:T.l;"
        "var btn=document.querySelector('[data-atid=\"'+D+'\"]');"
        "apply(t,btn);}"
        "mq.addEventListener('change',function(e){syncSys(e.matches);});"
        # Apply on load (Plotly is already rendered at this point)
        "setTimeout(function(){syncSys(mq.matches);},0);"
        "})();"
        "</script>"
    )

    btn_title = "Switch to light theme" if is_dark else "Switch to dark theme"
    btn_label = "\u2600\ufe0f" if is_dark else "🌙"
    toggle_btn = (
        f'<button class="airq-theme-btn" '
        f'data-atid="{div_id}" '
        f'title="{btn_title}" '
        f'onclick="{js_fn}(this)">'
        f"{btn_label}"
        f"</button>"
    )

    return f'<div class="airq-chart-wrap">{css}{html}{toggle_btn}{js}</div>'
