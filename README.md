# XAMS Dashboard

Dash-based run browser and processing trigger UI for XAMS on STBC.

## Features
- Browse runs with status filters
- Inspect run metadata and data products (type/host/location/lineage)
- Check loadability with current local amstrax/strax context
- Submit HTCondor processing jobs to `events` target
- Plot event-level summaries (drift time, S1/S2, XY)

## Quick start (local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Open: http://127.0.0.1:8070

## Environment variables
- `XAMS_MONGO_URI` (default: `mongodb://user:password@127.0.0.1:27017/admin`)
- `XAMS_RUN_DB` (default: `run`)
- `XAMS_RUN_COLLECTION` (default: `runs_gas`)
- `XAMS_PROCESSING_DB` (default: `daq`)
- `XAMS_PROCESSING_COLLECTION` (default: `processing`)
- `XAMS_STBC_AMSTRAX_DIR` (default: `/data/xenon/xams_v2/software/amstrax/amstrax/auto_processing_new`)
- `XAMS_STBC_LOG_DIR` (default: `/data/xenon/xams_v2/logs`)
- `XAMS_STBC_OUTPUT_DIR` (default: `/data/xenon/xams_v2/xams_processed`)
- `XAMS_DASH_HOST` (default: `127.0.0.1`)
- `XAMS_DASH_PORT` (default: `8070`)

## STBC ops
Use scripts in `ops/`:
- `start_dashboard.sh`
- `stop_dashboard.sh`
- `restart_dashboard.sh`
- `status_dashboard.sh`
- `start_autoprocess_online.sh`

Default dashboard URL on STBC (with tunnel):
- `http://127.0.0.1:18070/?run_id=<RUN_ID>`
