from __future__ import annotations

import json
import os

import dash
from dash import Dash, Input, Output, State, dash_table, dcc, html

from backend.api import create_api_blueprint
from backend.events_loader import load_event_features
from backend.loadability import scan_disk_availability
from backend.mongo_service import MongoService
from backend.plots import make_drift_time_hist, make_s1_s2_hist2d, make_xy_map
from backend.processing_service import ProcessingService


mongo = MongoService()
processing = ProcessingService()

app: Dash = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
server.register_blueprint(create_api_blueprint(mongo, processing))

RUN_TABLE_COLS = [
    {"name": "Run", "id": "run_id"},
    {"name": "Mode", "id": "mode"},
    {"name": "Raw", "id": "has_raw_records"},
    {"name": "Events", "id": "has_events"},
    {"name": "Start", "id": "start"},
    {"name": "End", "id": "end"},
    {"name": "Status", "id": "processing_status"},
]

app.layout = html.Div(
    [
        dcc.Store(id="selected-run-store", data={"run_id": None}),
        dcc.Interval(id="refresh-interval", interval=20_000, n_intervals=0),
        html.H2("XAMS Dashboard"),
        html.Div(
            [
                dcc.Input(id="run-id-input", type="number", placeholder="Run ID", min=0),
                html.Button("Load Run", id="load-run-btn", n_clicks=0),
                html.Button("Process to events", id="process-btn", n_clicks=0),
                html.Button("Refresh Now", id="refresh-now-btn", n_clicks=0),
                html.Span(id="action-status", style={"marginLeft": "12px", "fontWeight": "600"}),
            ],
            style={"display": "flex", "gap": "8px", "alignItems": "center", "flexWrap": "wrap"},
        ),
        html.Hr(),
        html.H4("Recent Runs"),
        dash_table.DataTable(
            id="runs-table",
            columns=RUN_TABLE_COLS,
            data=[],
            row_selectable="single",
            selected_rows=[],
            page_size=15,
            style_cell={"textAlign": "left", "padding": "6px", "fontFamily": "monospace", "fontSize": "12px"},
            style_data_conditional=[
                {"if": {"filter_query": '{processing_status} = "done"'}, "backgroundColor": "#e9f7ef"},
                {"if": {"filter_query": '{processing_status} = "failed"'}, "backgroundColor": "#fdecea"},
                {"if": {"filter_query": '{processing_status} = "running"'}, "backgroundColor": "#fff8e1"},
                {"if": {"filter_query": '{processing_status} = "submitted"'}, "backgroundColor": "#fff8e1"},
            ],
        ),
        html.Hr(),
        html.H4("Run Details"),
        html.Div(id="run-summary", style={"whiteSpace": "pre-wrap", "fontFamily": "monospace", "fontSize": "12px"}),
        html.H4("Data Availability / Loadability (Disk-first)"),
        dash_table.DataTable(
            id="loadability-table",
            page_size=20,
            style_cell={"textAlign": "left", "padding": "6px", "fontFamily": "monospace", "fontSize": "12px"},
        ),
        html.H4("Run Document (JSON)", style={"marginTop": "18px"}),
        dcc.Textarea(id="run-doc-json", style={"width": "100%", "height": "180px", "fontFamily": "monospace"}),
        html.Hr(),
        html.H4("Plots"),
        dcc.Graph(id="drift-fig"),
        dcc.Graph(id="s1s2-fig"),
        dcc.Graph(id="xy-fig"),
    ],
    style={"padding": "16px", "fontFamily": "Arial, sans-serif"},
)


@app.callback(
    Output("runs-table", "data"),
    Output("runs-table", "selected_rows"),
    Input("refresh-interval", "n_intervals"),
    Input("refresh-now-btn", "n_clicks"),
    Input("load-run-btn", "n_clicks"),
    State("selected-run-store", "data"),
)
def refresh_runs(_n, _refresh_clicks, _load_clicks, selected):
    runs = mongo.get_runs(page=1, page_size=40)
    rows = [
        {
            "run_id": r.number,
            "mode": r.mode,
            "has_raw_records": "yes" if r.has_raw_records else "no",
            "has_events": "yes" if r.has_events else "no",
            "start": r.start,
            "end": r.end,
            "processing_status": r.processing_status,
        }
        for r in runs
    ]
    selected_run = (selected or {}).get("run_id")
    selected_rows = []
    if selected_run is not None:
        for i, row in enumerate(rows):
            if int(row["run_id"]) == int(selected_run):
                selected_rows = [i]
                break
    return rows, selected_rows


@app.callback(
    Output("selected-run-store", "data"),
    Output("run-id-input", "value"),
    Input("load-run-btn", "n_clicks"),
    Input("runs-table", "selected_rows"),
    State("run-id-input", "value"),
    State("runs-table", "data"),
    State("selected-run-store", "data"),
)
def choose_run(_load_clicks, selected_rows, typed_run_id, table_data, current):
    if selected_rows and table_data:
        idx = selected_rows[0]
        if 0 <= idx < len(table_data):
            rid = int(table_data[idx]["run_id"])
            return {"run_id": rid}, rid

    if typed_run_id is not None:
        rid = int(typed_run_id)
        return {"run_id": rid}, rid

    if current and current.get("run_id") is not None:
        rid = int(current["run_id"])
        return current, rid

    return {"run_id": None}, None


@app.callback(
    Output("run-summary", "children"),
    Output("loadability-table", "data"),
    Output("loadability-table", "columns"),
    Output("run-doc-json", "value"),
    Output("drift-fig", "figure"),
    Output("s1s2-fig", "figure"),
    Output("xy-fig", "figure"),
    Input("selected-run-store", "data"),
    Input("refresh-interval", "n_intervals"),
)
def render_run(selected, _n):
    run_id = (selected or {}).get("run_id")
    if run_id is None:
        empty = []
        return "Select a run", empty, [], "", make_drift_time_hist({}), make_s1_s2_hist2d({}), make_xy_map({})

    d = mongo.get_run_details(int(run_id))
    if d is None:
        empty = []
        return "Run {} not found".format(run_id), empty, [], "", make_drift_time_hist({}), make_s1_s2_hist2d({}), make_xy_map({})

    availability = scan_disk_availability(int(run_id))
    cols = [{"name": k, "id": k} for k in (availability[0].keys() if availability else ["type", "location", "dataset_dir", "lineage_hash", "n_files", "size_mb", "loadable", "reason"])]

    ps = d.processing_status or {}
    summary = "\n".join(
        [
            "Run: {}".format(d.number),
            "Mode: {}".format(d.mode),
            "Start: {}".format(d.start),
            "End: {}".format(d.end),
            "Status: {} @ {}".format(ps.get("status", "unknown"), ps.get("time")),
            "Tags: {}".format(", ".join([t.get("name", "") for t in d.tags]) if d.tags else "-"),
            "Comments: {}".format(len(d.comments)),
        ]
    )

    event_features = load_event_features(int(run_id))
    if not event_features.get("ok"):
        summary = summary + "\nPlot data: {}".format(event_features.get("reason"))
    doc_json = json.dumps(d.raw_doc, default=str, indent=2)

    return (
        summary,
        availability,
        cols,
        doc_json,
        make_drift_time_hist(event_features),
        make_s1_s2_hist2d(event_features),
        make_xy_map(event_features),
    )


@app.callback(
    Output("action-status", "children"),
    Input("process-btn", "n_clicks"),
    State("selected-run-store", "data"),
    prevent_initial_call=True,
)
def submit_processing(_clicks, selected):
    run_id = (selected or {}).get("run_id")
    if run_id is None:
        return "Select a run first"

    status = mongo.get_job_status(int(run_id))
    if status.get("status") in ("submitted", "running"):
        return "Run {} already {}; not submitting again".format(run_id, status.get("status"))

    d = mongo.get_run_details(int(run_id))
    if d is None:
        return "Run {} not found".format(run_id)

    mode = (d.mode or "").lower()
    tags = [t.get("name", "").lower() for t in d.tags]
    is_led_run = ("led" in mode) or ("led" in tags)
    if is_led_run:
        return "LED run detected. Events are not produced in this mode."

    availability = scan_disk_availability(int(run_id))
    has_events = any((r.get("type") in ("event_info", "events") and r.get("loadable")) for r in availability)
    if has_events:
        return "Events already found on disk; no submission needed"

    out = processing.submit_run(int(run_id), target="event_info")
    if out["submitted"]:
        return "Submitted processing job for run {}".format(run_id)
    if out["returncode"] == 409:
        return "Duplicate click blocked for run {}".format(run_id)
    return "Submission failed (code={})".format(out["returncode"])


if __name__ == "__main__":
    host = os.getenv("XAMS_DASH_HOST", "127.0.0.1")
    port = int(os.getenv("XAMS_DASH_PORT", "8050"))
    app.run(host=host, port=port, debug=False)
