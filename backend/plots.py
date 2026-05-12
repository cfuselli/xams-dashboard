from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def _safe_array(values, n=1000):
    if values is None:
        return np.array([])
    arr = np.array(values)
    if arr.size == 0:
        return arr
    if arr.size > n:
        idx = np.linspace(0, arr.size - 1, n).astype(int)
        return arr[idx]
    return arr


def make_drift_time_hist(events: dict) -> go.Figure:
    drift = _safe_array(events.get("drift_time"))
    if drift.size == 0:
        return go.Figure().update_layout(title="Drift Time (no data)")
    fig = px.histogram(x=drift, nbins=80, labels={"x": "Drift time"}, title="Drift Time")
    return fig


def make_s1_s2_hist2d(events: dict) -> go.Figure:
    s1 = _safe_array(events.get("s1_area"))
    s2 = _safe_array(events.get("s2_area"))
    n = min(len(s1), len(s2))
    if n == 0:
        return go.Figure().update_layout(title="S1 vs S2 (no data)")
    fig = px.density_heatmap(x=s1[:n], y=s2[:n], nbinsx=80, nbinsy=80, title="S1 vs S2 area")
    return fig


def make_xy_map(events: dict) -> go.Figure:
    x = _safe_array(events.get("x"))
    y = _safe_array(events.get("y"))
    n = min(len(x), len(y))
    if n == 0:
        return go.Figure().update_layout(title="XY Position (no data)")
    fig = px.density_heatmap(x=x[:n], y=y[:n], nbinsx=80, nbinsy=80, title="XY position map")
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig
