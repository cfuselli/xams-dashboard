# XAMS Dashboard Status

_Date: 2026-05-12_

## Current state summary

The dashboard is in a working baseline state with real STBC deployment and core workflow operational:

1. browse/select runs,
2. inspect run metadata,
3. inspect availability/loadability,
4. submit missing event-level processing,
5. view core event-level plots.

## Completed work

### Architecture

- Flask app with custom frontend is the default dashboard service.
- Preserved backend service layering for data access, loadability, submission, and plotting.

### Data and loadability

- Shifted availability logic to disk-first checks.
- Added loadability reporting in active context.
- Added visibility for non-loadable artifacts with reason fields.

### Processing workflow

- Wired UI processing action to existing HTCondor submission flow.
- Default target chain now includes:
  - `event_basics`
  - `event_positions`
  - `event_info`
- Added duplicate-submission protection:
  - if selected targets are already loadable, submission is skipped server-side.

### Plotting

- Drift-time plot works.
- S1-S2 and XY plots now load from event-level arrays when available.
- Added adjustable bin controls.

### UX updates

- Added search and status filtering in run list.
- Improved pagination behavior.
- Added URL persistence for selected run id.
- Clarified interaction model:
  - click row to load run,
  - checkbox for batch submit,
  - `Show Selected` button for explicit load action.

### Operations

- STBC deployment scripts are in place for default start/stop.
- Dashboard process runs in screen (`xams_dashboard`) on port `8070`.
- Accessible by SSH tunnel.

## Issues found and resolved

1. Empty/unstable run list behavior in earlier iterations.
2. Processing button appearing inactive, then producing repeated submissions.
3. Data availability relying too much on DB hints.
4. Event plots empty despite partial availability claims.
5. Ambiguous UX between "submit" and "show" actions.

All above have targeted fixes in the current baseline.

## Known limitations / open items

1. Overall UI can still be made more polished and feature-rich.
2. Multi-run visualization/compare mode is not complete yet.
3. Job lifecycle monitoring in UI can be deeper (queue/running/done timelines).
4. More advanced analysis interactions (cuts, classes, custom rebin/export) are pending.

## Deployment notes

- Runtime environment should come from XAMS stack setup scripts.
- Config should follow `.xams_config` conventions used by existing processing flow.
- Dashboard is intentionally lightweight; compute remains in batch jobs.
