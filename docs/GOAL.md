# XAMS Dashboard Goal

## Mission
Build a production-usable XAMS run dashboard that lives on STBC and provides a fast, reliable path from run selection to event-level visualization, while integrating safely with existing XAMS processing infrastructure.

## What success looks like

1. Operators can find runs quickly (run id, mode, status, time range).
2. For each run, operators can see both:
   - what data physically exists on disk
   - what data is currently loadable in the active AMStrax/strax context.
3. If event-level products are missing, operators can trigger HTCondor processing from the UI.
4. If event-level products are available, operators can immediately inspect core analysis plots.
5. The app can be restarted reliably on STBC (screen + scripts) with predictable behavior.

## Scope for v1/v2 baseline

- Run browser with search/filter/pagination.
- Run detail card with metadata and raw run document view.
- Availability/loadability matrix by data type + lineage context.
- Job submission action targeting `event_basics`, `event_positions`, `event_info`.
- Core plots:
  - Drift-time histogram
  - S1 vs S2 2D histogram
  - XY occupancy map

## Non-goals for initial version

- Full physics analysis framework replacement.
- Rich event-by-event explorer UI.
- Multi-user auth/permissions model.
- Heavy compute in web process (compute stays in batch jobs / AMStrax stack).

## Constraints and operating context

- Existing production ecosystem must be reused (Mongo, AMStrax, Strax, HTCondor, auto-processing scripts).
- Data truth should come from disk/state checks, not only DB metadata fields.
- Dashboard should avoid duplicate processing submissions and provide safe operator feedback.
- Deployment target is STBC interactive node with SSH tunnel access.
