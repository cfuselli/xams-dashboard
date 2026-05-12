from __future__ import annotations

import math
from datetime import datetime
from flask import Flask, jsonify, render_template, request

from backend.events_loader import load_event_features
from backend.loadability import scan_disk_availability
from backend.mongo_service import MongoService
from backend.processing_service import ProcessingService

app = Flask(__name__, template_folder='templates', static_folder='static')

mongo = MongoService()
processing = ProcessingService()


def _serialize_dt(v):
    if isinstance(v, datetime):
        return v.isoformat()
    return v


@app.get('/v2')
def v2_index():
    return render_template('v2/index.html')


@app.get('/api/v2/runs')
def v2_runs():
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(200, max(10, int(request.args.get('page_size', 30))))
    q = (request.args.get('q') or '').strip().lower()
    status = (request.args.get('status') or '').strip().lower()

    runs = mongo.get_runs(page=1, page_size=None)
    rows = []
    for r in runs:
        rows.append({
            'run_id': r.number,
            'mode': r.mode or '',
            'status': r.processing_status or 'unknown',
            'has_raw_records': bool(r.has_raw_records),
            'has_event_info': bool(r.has_events),
            'start': _serialize_dt(r.start),
            'end': _serialize_dt(r.end),
        })

    if status:
        rows = [x for x in rows if str(x['status']).lower() == status]

    if q:
        rows = [x for x in rows if q in str(x['run_id']) or q in x['mode'].lower() or q in str(x['status']).lower()]

    total = len(rows)
    n_pages = max(1, math.ceil(total / page_size))
    page = min(page, n_pages)
    start_i = (page - 1) * page_size

    return jsonify({'page': page, 'page_size': page_size, 'total': total, 'n_pages': n_pages, 'rows': rows[start_i:start_i + page_size]})


@app.get('/api/v2/run/<int:run_id>')
def v2_run(run_id: int):
    d = mongo.get_run_details(run_id)
    if d is None:
        return jsonify({'error': 'run_not_found', 'run_id': run_id}), 404
    ps = d.processing_status or {}
    if not isinstance(ps, dict):
        ps = {'status': str(ps)}
    return jsonify({'run_id': d.number, 'mode': d.mode, 'start': _serialize_dt(d.start), 'end': _serialize_dt(d.end), 'tags': d.tags, 'comments': d.comments, 'processing_status': ps, 'raw_doc': d.raw_doc})


@app.get('/api/v2/run/<int:run_id>/availability')
def v2_availability(run_id: int):
    return jsonify(scan_disk_availability(run_id))


@app.get('/api/v2/run/<int:run_id>/plot-data')
def v2_plot_data(run_id: int):
    max_points = min(150000, max(5000, int(request.args.get('max_points', 80000))))
    return jsonify(load_event_features(run_id=run_id, max_points=max_points))


@app.post('/api/v2/submit')
def v2_submit():
    body = request.get_json(force=True, silent=True) or {}
    run_ids = body.get('run_ids') or []
    targets = body.get('targets') or ['event_basics', 'event_positions', 'event_info']
    out = []
    for rid in run_ids:
        out.append(processing.submit_run(int(rid), target=targets))
    ok = sum(1 for x in out if x.get('submitted'))
    return jsonify({'submitted': ok, 'total': len(out), 'results': out})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8070, debug=False)
