# XAMS Dashboard Implementation Plan

## 1. Repository and layering

Create and maintain a standalone repo (`xams-dashboard`) with clear separation:

1. `backend/`
   - Mongo services
   - run normalization
   - disk availability/loadability checks
   - processing submission wrappers
   - event feature loading for plots
2. `v2/`
   - Flask app and API routes
   - custom frontend (HTML/CSS/JS)
3. `ops/`
   - start/stop/restart/status scripts
   - environment bootstrapping and screen management
4. `tests/`
   - parser, loadability and submission behavior checks

## 2. Runtime architecture

- UI server runs as a light Flask app.
- Heavy processing is never done inline in request handlers.
- Processing is triggered by submitting jobs to existing HTCondor/auto-processing flow.
- UI is accessed via SSH tunnel to STBC port.

## 3. Data model and endpoint plan

Core endpoints:

1. `GET /api/runs`
   - paginated run rows
   - search + status filter
   - quick availability flags (`raw`, `event_info`)
2. `GET /api/run/<run_id>`
   - normalized run details + processing status + raw rundoc
3. `GET /api/run/<run_id>/availability`
   - disk-first availability/loadability report by data type
4. `GET /api/run/<run_id>/plot-data`
   - extracted arrays for drift, S1/S2, XY plots
5. `POST /api/submit`
   - batch submission wrapper for chosen runs + targets
   - duplicate-safe logic (skip when requested targets already loadable)

## 4. Loadability logic

For each run:

1. inspect storage-backed data presence,
2. identify product type and lineage-related metadata,
3. evaluate loadability in current AMStrax context,
4. return both loadable and non-loadable entries with reasons.

This avoids false positives from stale/incomplete DB data entries alone.

## 5. Processing integration plan

- Use existing XAMS processing script path and Condor submission style.
- Default target set for "process to events" workflow:
  - `event_basics`
  - `event_positions`
  - `event_info`
- Add server-side guard:
  - if all requested targets are already loadable, return `skipped` and do not submit.

## 6. UX plan

Runs panel:

- row click selects active run and loads details/plots,
- checkboxes support batch processing selection,
- explicit `Show Selected` action clarifies loading behavior.

Details panel:

- mode, timing, tags, comments, processing status,
- expandable raw JSON for debugging.

Availability panel:

- type, lineage, current lineage, loadable, n_files, size, reason.

Plots panel:

- drift histogram,
- S1 vs S2 density,
- XY map,
- bin controls + color-scale options.

## 7. Ops/deployment plan

- `ops/start_dashboard.sh`: launch screen session (`xams_dashboard`) on fixed port.
- `ops/stop_dashboard.sh`: stop process cleanly.
- Use `/data/xenon/xams_v2/setup.sh` and `.xams_config` conventions.
- Verify health with API probes after restart.

## 8. Next iteration (v3) plan

1. multi-run compare mode,
2. stronger job monitoring UI,
3. richer controls (cuts/rebin presets/export),
4. improved visual polish and workflow guidance,
5. persisted UI state across refreshes/navigation.
