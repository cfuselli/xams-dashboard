from __future__ import annotations

import time
import math
from typing import Any, Dict, Tuple

_CACHE = {}  # type: Dict[int, Tuple[float, Dict[str, Any]]]
_CACHE_TTL = 60


def _to_list(arr, names, field):
    if field in names:
        return arr[field].tolist()
    return []


def _finite(values):
    out = []
    for v in values:
        try:
            fv = float(v)
        except Exception:
            continue
        if math.isfinite(fv):
            out.append(fv)
    return out


def _paired_finite(a, b):
    aa = []
    bb = []
    for x, y in zip(a, b):
        try:
            fx = float(x)
            fy = float(y)
        except Exception:
            continue
        if math.isfinite(fx) and math.isfinite(fy):
            aa.append(fx)
            bb.append(fy)
    return aa, bb


def _is_led_run_doc(doc: Dict[str, Any]) -> bool:
    if not isinstance(doc, dict):
        return False
    mode = str(doc.get("mode") or "").lower()
    xbk = doc.get("xams_bookkeeping") if isinstance(doc.get("xams_bookkeeping"), dict) else {}
    run_class = str(xbk.get("run_class") or "").lower()
    if run_class == "led":
        return True
    if "led" in mode:
        return True
    tags = doc.get("tags") or []
    for t in tags:
        name = (t.get("name") if isinstance(t, dict) else str(t)).lower()
        if "led" in name:
            return True
    return False


def load_event_features(
    run_id: int,
    max_points: int = 120000,
    max_peaks: int = 120000,
    max_waveforms: int = 40,
) -> Dict[str, Any]:
    now = time.time()
    run_id = int(run_id)

    if run_id in _CACHE:
        ts, payload = _CACHE[run_id]
        if now - ts < _CACHE_TTL:
            return payload

    payload = {
        "ok": False,
        "plot_mode": "event",
        "is_led_run": False,
        "drift_time": [],
        "s1_area": [],
        "s2_area": [],
        "x": [],
        "y": [],
        "source": [],
        "peak_source": "",
        "peak_area": [],
        "peak_aft": [],
        "peak_width_50": [],
        "peak_area_width": [],
        "peak_type": [],
        "waveforms": [],
        "led_channel": [],
        "led_area": [],
        "led_amplitude_led": [],
        "led_amplitude_noise": [],
        "led_amplitude_diff": [],
        "reason": "",
    }

    try:
        import amstrax  # type: ignore

        rid = "{:06d}".format(run_id)
        run_doc = amstrax.get_mongo_collection().find_one({"number": run_id}, {"mode": 1, "xams_bookkeeping": 1, "tags": 1, "_id": 0}) or {}
        is_led = _is_led_run_doc(run_doc)
        payload["is_led_run"] = bool(is_led)

        if is_led:
            st_led = amstrax.contexts.xams_led(output_folder="/data/xenon/xams_v2/xams_processed")
            if st_led.is_stored(rid, "led_calibration"):
                led = st_led.get_array(rid, "led_calibration", progress_bar=False)
                if len(led):
                    led = led[: min(len(led), max_points)]
                    names = set(led.dtype.names)
                    area = _finite(_to_list(led, names, "area"))
                    amp_led = _finite(_to_list(led, names, "amplitude_led"))
                    amp_noise = _finite(_to_list(led, names, "amplitude_noise"))
                    ch = []
                    if "channel" in names:
                        ch = [int(c) for c in led["channel"].tolist()[: len(area)]]

                    # align LED/noise arrays
                    amp_led, amp_noise = _paired_finite(amp_led, amp_noise)
                    n = min(len(amp_led), len(amp_noise))
                    amp_diff = [amp_led[i] - amp_noise[i] for i in range(n)]

                    payload.update(
                        {
                            "ok": bool(area or amp_led or ch),
                            "plot_mode": "led",
                            "source": ["led_calibration"],
                            "led_channel": ch,
                            "led_area": area,
                            "led_amplitude_led": amp_led,
                            "led_amplitude_noise": amp_noise,
                            "led_amplitude_diff": amp_diff,
                            "reason": "ok from led_calibration",
                        }
                    )
                else:
                    payload["plot_mode"] = "led"
                    payload["reason"] = "led_calibration exists but empty"
            else:
                payload["plot_mode"] = "led"
                payload["reason"] = "no led_calibration stored in current LED context"

            # Optional waveform sampling from records_led.
            try:
                if st_led.is_stored(rid, "records_led"):
                    rled = st_led.get_array(rid, "records_led", progress_bar=False)
                    if len(rled):
                        rled = rled[: min(len(rled), max_waveforms)]
                        wfs = []
                        for rec in rled:
                            raw = rec["data"].tolist()
                            step = max(1, int(len(raw) / 500))
                            data = raw[::step]
                            dt = int(rec["dt"])
                            ts = [j * dt * step for j in range(len(data))]
                            wfs.append({"area": float(sum(data)), "t_ns": ts, "amp": [float(v) for v in data]})
                        payload["waveforms"] = wfs
            except Exception:
                pass

            _CACHE[run_id] = (now, payload)
            return payload

        st = amstrax.contexts.xams(output_folder="/data/xenon/xams_v2/xams_processed")

        data = {}
        for t in ("event_info", "event_basics", "event_positions", "events"):
            if st.is_stored(rid, t):
                arr = st.get_array(rid, t, progress_bar=False)
                if len(arr):
                    data[t] = arr[: min(len(arr), max_points)]

        if not data:
            payload["reason"] = "no event-level data stored in current context"
        else:
            source = list(data.keys())

            # Drift time: prefer explicit field, else derive from events timing
            drift = []
            for t in ("event_info", "event_basics", "events"):
                arr = data.get(t)
                if arr is None:
                    continue
                names = set(arr.dtype.names)
                if "drift_time" in names:
                    drift = arr["drift_time"].tolist()
                    break
                if "time" in names and "endtime" in names:
                    drift = (arr["endtime"] - arr["time"]).tolist()
                    break

            # S1/S2: event_info or event_basics
            s1 = []
            s2 = []
            for t in ("event_info", "event_basics"):
                arr = data.get(t)
                if arr is None:
                    continue
                names = set(arr.dtype.names)
                s1 = _to_list(arr, names, "s1_area") or _to_list(arr, names, "s1") or _to_list(arr, names, "cs1")
                s2 = _to_list(arr, names, "s2_area") or _to_list(arr, names, "s2") or _to_list(arr, names, "cs2")
                if s1 and s2:
                    break

            # XY: event_positions first, else info/basics if present
            x = []
            y = []
            for t in ("event_positions", "event_info", "event_basics"):
                arr = data.get(t)
                if arr is None:
                    continue
                names = set(arr.dtype.names)
                x = _to_list(arr, names, "x")
                y = _to_list(arr, names, "y")
                if x and y:
                    break

            drift = _finite(drift)
            s1, s2 = _paired_finite(s1, s2)
            x, y = _paired_finite(x, y)

            payload.update(
                {
                    "ok": bool(drift or (s1 and s2) or (x and y)),
                    "drift_time": drift,
                    "s1_area": s1,
                    "s2_area": s2,
                    "x": x,
                    "y": y,
                    "source": source,
                }
            )

            missing = []
            if not drift:
                missing.append("drift_time")
            if not (s1 and s2):
                missing.append("S1/S2")
            if not (x and y):
                missing.append("XY")

            payload["reason"] = "ok from {}{}".format(
                ",".join(source),
                ("; missing " + ", ".join(missing)) if missing else "",
            )

        # Peak basics quick-check fields
        rid = "{:06d}".format(run_id)
        if st.is_stored(rid, "peak_basics"):
            pb = st.get_array(rid, "peak_basics", progress_bar=False)
            if len(pb):
                pb = pb[: min(len(pb), max_peaks)]
                names = set(pb.dtype.names)
                area = _to_list(pb, names, "area")
                aft = _to_list(pb, names, "area_fraction_top")
                width = _to_list(pb, names, "range_50p_area") or _to_list(pb, names, "rise_time")
                ptype = _to_list(pb, names, "type")
                area, aft = _paired_finite(area, aft)
                area2, width = _paired_finite(_to_list(pb, names, "area"), width)
                # keep one type list finite and same length as area/aft pair when possible
                ptype = [int(t) for t in ptype[: len(area)] if isinstance(t, (int, float))]
                payload.update(
                    {
                        "peak_source": "peak_basics",
                        "peak_area": area,
                        "peak_aft": aft,
                        "peak_width_50": width,
                        "peak_area_width": area2,
                        "peak_type": ptype,
                    }
                )

                # Optional tiny waveform sample from first second
                try:
                    if st.is_stored(rid, "peaks") and "time" in names:
                        t0 = int(pb["time"][0])
                        t1 = t0 + int(1e9)
                        p = st.get_array(rid, "peaks", time_range=(t0, t1), progress_bar=False)
                        wfs = []
                        if len(p):
                            # pick top peaks and keep payload manageable
                            order = sorted(range(len(p)), key=lambda i: float(p["area"][i]), reverse=True)[:max_waveforms]
                            for idx in order:
                                pi = p[idx]
                                raw = pi["data"][: int(pi["length"])].tolist()
                                # decimate to avoid huge frontend payload
                                step = max(1, int(len(raw) / 500))
                                data = raw[::step]
                                dt = int(pi["dt"])
                                ts = [j * dt * step for j in range(len(data))]
                                wfs.append({"area": float(pi["area"]), "t_ns": ts, "amp": [float(v) for v in data]})
                        payload["waveforms"] = wfs
                except Exception:
                    pass

    except Exception as e:
        payload["reason"] = "{}".format(e)

    _CACHE[run_id] = (now, payload)
    return payload
