from __future__ import annotations

import os

import dash
from dash import Dash, Input, Output, State, dash_table, dcc, html

from backend.api import create_api_blueprint
from backend.loadability import assess_loadability
from backend.mongo_service import MongoService
from backend.plots import make_drift_time_hist, make_s1_s2_hist2d, make_xy_map
from backend.processing_service import ProcessingService


mongo = MongoService()
processing = ProcessingService()

app: Dash = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
server.register_blueprint(create_api_blueprint(mongo, processing))

app.layout = html.Div(
    [
        html.H2("XAMS Dashboard v1"),
        html.Div([
            dcc.Input(id="run-id-input", type="number", placeholder="Run ID", min=0),
            html.Button("Load Run", id="load-run-btn", n_clicks=0),
            html.Button("Process to events", id="process-btn", n_clicks=0),
            html.Span(id="action-status", style={"marginLeft": "12px"}),
        ], style={"display": "flex", "gap": "8px", "alignItems": "center"}),
        html.Hr(),
        html.H4("Recent Runs"),
        dash_table.DataTable(id="runs-table", page_size=15),
        html.Hr(),
        html.Div(id="run-summary"),
        html.H4("Data Availability / Loadability"),
        dash_table.DataTable(id="loadability-table", page_size=20),
        html.Hr(),
        html.H4("Plots"),
        dcc.Graph(id="drift-fig"),
        dcc.Graph(id="s1s2-fig"),
        dcc.Graph(id="xy-fig"),
    ],
    style={"padding": "18px", "fontFamily": "sans-serif"},
)


@app.callback(Output("runs-table", "data"), Output("runs-table", "columns"), Input("load-run-btn", "n_clicks"))
def refresh_runs(_):
    runs = mongo.get_runs(page=1, page_size=30)
    rows = [
        {
            "run_id": r.number,
            "mode": r.mode,
            "start": r.start,
            "end": r.end,
            "processing_status": r.processing_status,
        }
        for r in runs
    ]
    cols = [{"name": k, "id": k} for k in (rows[0].keys() if rows else ["run_id", "mode", "start", "end", "processing_status"])]
    return rows, cols


@app.callback(
    Output("run-summary", "children"),
    Output("loadability-table", "data"),
    Output("loadability-table", "columns"),
    Output("drift-fig", "figure"),
    Output("s1s2-fig", "figure"),
    Output("xy-fig", "figure"),
    Input("load-run-btn", "n_clicks"),
    State("run-id-input", "value"),
)
def load_run(_clicks, run_id):
    if run_id is None:
        empty = []
        return "Select a run", empty, [], make_drift_time_hist({}), make_s1_s2_hist2d({}), make_xy_map({})

    d = mongo.get_run_details(int(run_id))
    if d is None:
        empty = []
        return f"Run {run_id} not found", empty, [], make_drift_time_hist({}), make_s1_s2_hist2d({}), make_xy_map({})

    loadability = assess_loadability(d)
    columns = [{"name": k, "id": k} for k in (loadability[0].keys() if loadability else ["type", "host", "location", "lineage_hash", "loadable", "reason"])]

    # v1: event plotting source is optional and best-effort from rundoc-side quick fields
    events = d.raw_doc.get("event_summary", {}) if isinstance(d.raw_doc.get("event_summary"), dict) else {}
    summary = html.Div([
        html.P(f"Run {d.number} | Mode: {d.mode}"),
        html.P(f"Start: {d.start} | End: {d.end}"),
        html.P(f"Processing status: {(d.processing_status or {}).get('status', 'unknown')}")
    ])

    return summary, loadability, columns, make_drift_time_hist(events), make_s1_s2_hist2d(events), make_xy_map(events)


@app.callback(
    Output("action-status", "children"),
    Input("process-btn", "n_clicks"),
    State("run-id-input", "value"),
    prevent_initial_call=True,
)
def submit_processing(_clicks, run_id):
    if run_id is None:
        return "Set run id first"

    status = mongo.get_job_status(int(run_id))
    if status.get("status") in ("submitted", "running"):
        return f"Run {run_id} already {status.get('status')}; not submitting again"

    d = mongo.get_run_details(int(run_id))
    if d is None:
        return f"Run {run_id} not found"

    has_loadable_events = any(r["type"] == "events" and r["loadable"] for r in assess_loadability(d))
    if has_loadable_events:
        return "Loadable events already present; no job submitted"

    out = processing.submit_run(int(run_id), target="events")
    if out["submitted"]:
        return f"Submitted processing job for run {run_id}"
    if out["returncode"] == 409:
        return f"Skipped duplicate submit for run {run_id} (cooldown)"
    return f"Submission failed (code={out['returncode']})"


if __name__ == "__main__":
    host = os.getenv("XAMS_DASH_HOST", "127.0.0.1")
    port = int(os.getenv("XAMS_DASH_PORT", "8050"))
    app.run(host=host, port=port, debug=False)
