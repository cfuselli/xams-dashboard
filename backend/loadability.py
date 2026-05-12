from __future__ import annotations

from typing import Any

from .models import RunDetails


TARGET_TYPES = ("raw_records", "peaks", "events")


def assess_loadability(run_details: RunDetails) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for e in run_details.data_entries:
        if e.data_type not in TARGET_TYPES:
            continue

        # v1 heuristic: entries produced by amstrax with lineage hash are considered candidate-loadable.
        # Full strax context validation can be plugged in later.
        loadable = bool(e.lineage_hash and e.location)
        reason = "lineage+location present" if loadable else "missing lineage and/or location"

        rows.append(
            {
                "type": e.data_type,
                "host": e.host,
                "location": e.location,
                "lineage_hash": e.lineage_hash,
                "amstrax_version": e.amstrax_version,
                "loadable": loadable,
                "reason": reason,
            }
        )

    return sorted(rows, key=lambda r: (r["type"], r.get("lineage_hash") or ""))
