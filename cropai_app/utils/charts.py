from __future__ import annotations

import json
import urllib.request
from functools import lru_cache
from typing import Any

import plotly.graph_objects as go


def _to_json(fig: go.Figure) -> dict:
    return fig.to_plotly_json()


def yield_gauge(predicted: float, crop_max: float) -> dict:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=max(0, float(predicted)),
            number={"suffix": " kg/ha", "font": {"size": 28}},
            gauge={
                "axis": {"range": [0, max(1, crop_max)]},
                "bar": {"color": "#1B5E20"},
                "steps": [
                    {"range": [0, crop_max * 0.33], "color": "#ffebee"},
                    {"range": [crop_max * 0.33, crop_max * 0.66], "color": "#fff8e1"},
                    {"range": [crop_max * 0.66, crop_max], "color": "#e8f5e9"},
                ],
            },
        )
    )
    fig.update_layout(
        margin=dict(l=12, r=12, t=12, b=42),
        paper_bgcolor="white",
        annotations=[dict(text="Yield Gauge", x=0.5, y=-0.06, xref="paper", yref="paper", showarrow=False, font={"size": 13})],
    )
    return _to_json(fig)


def input_radar(user_vals: list[float], optimal_vals: list[float], labels: list[str]) -> dict:
    fig = go.Figure()
    user = user_vals + [user_vals[0]]
    opt = optimal_vals + [optimal_vals[0]]
    theta = labels + [labels[0]]
    fig.add_trace(
        go.Scatterpolar(
            r=user,
            theta=theta,
            fill="toself",
            name="User values",
            fillcolor="rgba(76,175,80,0.40)",
            line=dict(color="#1B5E20", width=2),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=opt,
            theta=theta,
            fill="toself",
            name="Optimal range",
            fillcolor="rgba(120,120,120,0.20)",
            line=dict(color="#6b7280", width=2, dash="dash"),
        )
    )
    fig.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 1]}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.03, "x": 1, "xanchor": "right"},
        margin={"l": 16, "r": 16, "t": 12, "b": 44},
        paper_bgcolor="white",
        annotations=[dict(text="Input Health Radar", x=0.5, y=-0.08, xref="paper", yref="paper", showarrow=False, font={"size": 13})],
    )
    return _to_json(fig)


def npk_bar(n: float, p: float, k: float, n_opt: float, p_opt: float, k_opt: float) -> dict:
    xs = ["N", "P", "K"]
    vals = [float(n), float(p), float(k)]
    opt = [float(n_opt), float(p_opt), float(k_opt)]
    colors: list[str] = []
    for v, o in zip(vals, opt):
        diff = abs(v - o) / max(1.0, o)
        if diff <= 0.15:
            colors.append("#2e7d32")
        elif diff <= 0.40:
            colors.append("#f59e0b")
        else:
            colors.append("#d32f2f")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=xs,
            y=vals,
            marker_color=colors,
            name="Your NPK",
            hovertemplate="%{x}: %{y:.1f} kg/ha<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=opt,
            mode="markers+lines",
            line={"dash": "dash", "color": "#374151"},
            marker={"size": 9, "color": "#374151"},
            name="Optimal midpoint",
            hovertemplate="Optimal %{x}: %{y:.1f} kg/ha<extra></extra>",
        )
    )
    fig.update_layout(
        margin={"l": 16, "r": 16, "t": 12, "b": 44},
        yaxis_title="kg/ha",
        paper_bgcolor="white",
        annotations=[dict(text="NPK vs Optimal", x=0.5, y=-0.08, xref="paper", yref="paper", showarrow=False, font={"size": 13})],
    )
    return _to_json(fig)


def batch_category_donut(counts: dict[str, int]) -> dict:
    order = [("Low", "#d32f2f"), ("Medium", "#f59e0b"), ("High", "#2e7d32")]
    labels, values, colors = [], [], []
    for lbl, col in order:
        v = int(counts.get(lbl, 0))
        labels.append(lbl)
        values.append(max(0, v))
        colors.append(col)
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker={"colors": colors},
            textinfo="label+percent",
            insidetextorientation="radial",
        )
    )
    fig.update_layout(title={"text": "Yield Category Distribution", "x": 0.5}, margin={"l": 10, "r": 10, "t": 48, "b": 8})
    return _to_json(fig)


def batch_yield_histogram(yields: list[float], national_avg: float, crop_name: str) -> dict:
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=yields, marker={"color": "#4CAF50"}, nbinsx=min(35, max(8, len(yields) // 3))))
    fig.add_vline(x=float(national_avg), line_dash="dash", line_color="#d32f2f")
    fig.add_annotation(
        x=float(national_avg),
        y=1,
        yref="paper",
        text=f"National avg ({crop_name})",
        showarrow=False,
        yanchor="bottom",
    )
    fig.update_layout(
        title={"text": "Predicted Yield Distribution", "x": 0.5},
        xaxis_title="Predicted yield in kg/ha",
        yaxis_title="Number of fields",
        margin={"l": 48, "r": 16, "t": 48, "b": 46},
    )
    return _to_json(fig)


def batch_crop_avg_bar(crop_rows: list[tuple[str, float, float, float, int]]) -> dict:
    rows = sorted(crop_rows, key=lambda x: x[1], reverse=True)
    crops = [r[0] for r in rows]
    avgs = [r[1] for r in rows]
    mins = [r[2] for r in rows]
    maxs = [r[3] for r in rows]
    counts = [r[4] for r in rows]
    shades = []
    for i in range(max(1, len(crops))):
        t = i / max(1, len(crops) - 1)
        shades.append(f"rgba(27,94,32,{0.38 + 0.58 * t})")
    fig = go.Figure(
        go.Bar(
            x=avgs,
            y=crops,
            orientation="h",
            marker={"color": shades[: len(crops)]},
            customdata=list(zip(mins, maxs, counts)),
            hovertemplate="<b>%{y}</b><br>Avg: %{x:.1f} kg/ha<br>Min: %{customdata[0]:.1f}<br>Max: %{customdata[1]:.1f}<br>Fields: %{customdata[2]}<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": "Average Yield by Crop", "x": 0.5},
        xaxis_title="Average yield (kg/ha)",
        margin={"l": 120, "r": 20, "t": 48, "b": 44},
    )
    return _to_json(fig)


@lru_cache(maxsize=1)
def _load_india_geojson() -> dict[str, Any] | None:
    url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97dde1875a7d7f72e69ee/raw/e388c4cae20aa53cb5099210a864ccf6336c61c38/india_states.geojson"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CropYieldAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def india_state_yield_map(state_avg: dict[str, float], state_counts: dict[str, int]) -> dict:
    geojson = _load_india_geojson()
    if not geojson or not geojson.get("features"):
        return _state_yield_bar_fallback(state_avg, state_counts)

    sample = geojson["features"][0].get("properties", {})
    id_key = next((k for k in ("ST_NM", "NAME_1", "state", "name") if k in sample), "ST_NM")
    locations: list[str] = []
    zvals: list[float] = []
    counts: list[int] = []

    state_by_norm = {str(k).strip().lower(): (k, v) for k, v in state_avg.items()}
    for feat in geojson["features"]:
        props = feat.get("properties") or {}
        name = str(props.get(id_key, "")).strip()
        if not name:
            continue
        key = name.lower()
        val = None
        cnt = 0
        if key in state_by_norm:
            orig, val = state_by_norm[key]
            cnt = int(state_counts.get(orig, 0))
        else:
            for s_norm, (orig, sval) in state_by_norm.items():
                if s_norm in key or key in s_norm:
                    val = sval
                    cnt = int(state_counts.get(orig, 0))
                    break
        if val is not None:
            locations.append(name)
            zvals.append(float(val))
            counts.append(cnt)

    if not locations:
        return _state_yield_bar_fallback(state_avg, state_counts)

    fig = go.Figure(
        go.Choropleth(
            geojson=geojson,
            locations=locations,
            z=zvals,
            featureidkey=f"properties.{id_key}",
            colorscale=[[0, "#FFF9C4"], [0.5, "#81C784"], [1, "#1B5E20"]],
            marker_line_color="white",
            marker_line_width=0.5,
            colorbar_title="kg/ha",
            customdata=counts,
            hovertemplate="<b>%{location}</b><br>Avg yield: %{z:.1f} kg/ha<br>Fields: %{customdata}<extra></extra>",
        )
    )
    fig.update_geos(fitbounds="locations", visible=False, showcountries=False, showcoastlines=False, projection_type="mercator")
    fig.update_layout(title={"text": "Average Yield by State", "x": 0.5}, margin={"l": 0, "r": 0, "t": 48, "b": 0}, height=420)
    return _to_json(fig)


def _state_yield_bar_fallback(state_avg: dict[str, float], state_counts: dict[str, int]) -> dict:
    items = sorted(state_avg.items(), key=lambda x: x[1], reverse=True)
    fig = go.Figure(
        go.Bar(
            x=[v for _, v in items],
            y=[k for k, _ in items],
            orientation="h",
            marker={"color": "#4CAF50"},
            customdata=[state_counts.get(k, 0) for k, _ in items],
            hovertemplate="%{y}<br>Avg: %{x:.1f} kg/ha<br>Fields: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": "Average Yield by State (fallback view)", "x": 0.5},
        xaxis_title="Average yield (kg/ha)",
        margin={"l": 140, "r": 20, "t": 48, "b": 40},
        height=max(360, len(items) * 22),
    )
    return _to_json(fig)
