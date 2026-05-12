from __future__ import annotations

import time
from typing import Any, Dict, Tuple

_CACHE = {}  # type: Dict[int, Tuple[float, Dict[str, Any]]]
_CACHE_TTL = 60


def load_event_features(run_id: int, max_points: int = 120000) -> Dict[str, Any]:
    now = time.time()
    run_id = int(run_id)

    if run_id in _CACHE:
        ts, payload = _CACHE[run_id]
        if now - ts < _CACHE_TTL:
            return payload

    payload = {
        "ok": False,
        "drift_time": [],
        "s1_area": [],
        "s2_area": [],
        "x": [],
        "y": [],
        "reason": "",
    }

    try:
        import amstrax  # type: ignore

        st = amstrax.contexts.xams(output_folder="/data/xenon/xams_v2/xams_processed")
        rid = "{:06d}".format(run_id)
        if not st.is_stored(rid, "events"):
            payload["reason"] = "events not stored in current context"
            _CACHE[run_id] = (now, payload)
            return payload

        arr = st.get_array(rid, "events", progress_bar=False)
        if len(arr) == 0:
            payload["reason"] = "events array empty"
            _CACHE[run_id] = (now, payload)
            return payload

        n = min(len(arr), max_points)
        arr = arr[:n]
        names = set(arr.dtype.names)

        def col(name):
            if name in names:
                return arr[name].tolist()
            return []

        payload.update(
            {
                "ok": True,
                "drift_time": col("drift_time"),
                "s1_area": col("s1_area"),
                "s2_area": col("s2_area"),
                "x": col("x"),
                "y": col("y"),
                "reason": "ok",
            }
        )
    except Exception as e:
        payload["reason"] = "{}".format(e)

    _CACHE[run_id] = (now, payload)
    return payload
