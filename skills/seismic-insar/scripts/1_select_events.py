#!/usr/bin/env python3
"""Select significant catalog events and build InSAR coseismic capture jobs.

Usage:
  python 1_select_events.py \
    --catalog joint_relocated_catalog.csv \
    --ml-min 4.5 --buffer-deg 0.3 --pre-days 90 --post-days 90 \
    --cluster-days 30 --cluster-km 30 \
    --out insar_jobs.json

Events at/above the magnitude threshold are clustered in time+space; each
cluster shares ONE Sentinel-1 search window (same frame/stack) but every
event gets its own bracketing requirement: a coseismic pair is clean only
if it brackets that event ALONE, i.e. the pair's dates must lie inside
[previous threshold event, next threshold event]. Two threshold events
inside the same 12-day revisit interval are flagged inseparable (InSAR
pairs cannot isolate either signal).

Region-dependent values (--ml-min / --buffer-deg / window lengths) must be
user-confirmed; see the skill's parameter table.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

S1_REVISIT_DAYS = 12


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def pick(df, *names):
    for n in names:
        if n in df.columns:
            return n
    raise ValueError(f"catalog needs one of {names}; has {list(df.columns)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--ml-min", type=float, default=4.5)
    ap.add_argument("--buffer-deg", type=float, default=0.3)
    ap.add_argument("--pre-days", type=int, default=90)
    ap.add_argument("--post-days", type=int, default=90)
    ap.add_argument("--cluster-days", type=int, default=30)
    ap.add_argument("--cluster-km", type=float, default=30.0)
    ap.add_argument("--out", default="insar_jobs.json")
    args = ap.parse_args()

    cat = pd.read_csv(args.catalog)
    t_col = pick(cat, "origin_time", "origin_time_utc_dd", "time")
    lat_col = pick(cat, "latitude_dd", "latitude", "lat")
    lon_col = pick(cat, "longitude_dd", "longitude", "lon")
    ml_col = pick(cat, "ml", "ML", "magnitude")
    cat["_t"] = pd.to_datetime(cat[t_col], format="ISO8601", utc=True,
                               errors="coerce")

    sel = cat[(cat[ml_col] >= args.ml_min) & cat["_t"].notna()].copy()
    sel = sel.sort_values("_t")
    print(f"events above ML {args.ml_min}: {len(sel)} of {len(cat)}")
    if sel.empty:
        Path(args.out).write_text(json.dumps({"jobs": []}, indent=2) + "\n")
        print("no events selected; empty job list written")
        return

    # greedy space-time clustering (one search window per cluster)
    clusters = []
    for _, r in sel.iterrows():
        placed = False
        for c in clusters:
            dt = abs((r["_t"] - c["t_max"]).total_seconds()) / 86400.0
            d = haversine_km(r[lat_col], r[lon_col], c["lat"], c["lon"])
            if dt <= args.cluster_days and d <= args.cluster_km:
                c["events"].append(r)
                c["t_max"] = max(c["t_max"], r["_t"])
                c["t_min"] = min(c["t_min"], r["_t"])
                placed = True
                break
        if not placed:
            clusters.append({"events": [r], "t_min": r["_t"], "t_max": r["_t"],
                             "lat": r[lat_col], "lon": r[lon_col]})
    for c in clusters:
        c["lat"] = float(np.mean([e[lat_col] for e in c["events"]]))
        c["lon"] = float(np.mean([e[lon_col] for e in c["events"]]))

    jobs = []
    # GLOBAL bracket awareness: an event's clean bracket must exclude EVERY
    # other threshold event, including events in other clusters/windows --
    # a pair spanning two windows' events carries both signals.
    all_events = sorted(sel.to_dict('records'), key=lambda e: e['_t'])
    for i, c in enumerate(clusters, 1):
        events = sorted(c["events"], key=lambda e: e["_t"])
        pre_start = c["t_min"] - pd.Timedelta(days=args.pre_days)
        post_end = c["t_max"] + pd.Timedelta(days=args.post_days)

        ev_out = []
        for k, e in enumerate(events):
            prev_t = pre_start
            next_t = post_end
            for other in all_events:
                if other["_t"] == e["_t"]:
                    continue
                if other["_t"] < e["_t"] and other["_t"] > prev_t:
                    prev_t = other["_t"]
                if other["_t"] > e["_t"] and other["_t"] < next_t:
                    next_t = other["_t"]
            bracket = [prev_t.strftime("%Y-%m-%d"), next_t.strftime("%Y-%m-%d")]
            gap_before = (e["_t"] - prev_t).total_seconds() / 86400.0
            gap_after = (next_t - e["_t"]).total_seconds() / 86400.0
            # inseparable when a NEIGHBORING THRESHOLD EVENT (not the search
            # window edge) sits within one revisit
            k_all = [j for j, o in enumerate(all_events)
                     if o["_t"] == e["_t"]][0]
            neighbor_before = k_all > 0 and (
                e["_t"] - all_events[k_all - 1]["_t"]).total_seconds() / 86400.0 <= S1_REVISIT_DAYS
            neighbor_after = k_all + 1 < len(all_events) and (
                all_events[k_all + 1]["_t"] - e["_t"]).total_seconds() / 86400.0 <= S1_REVISIT_DAYS
            ev_out.append({
                "event_id": str(e.get("event_id", "")),
                "origin_time": e["_t"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "latitude": float(e[lat_col]), "longitude": float(e[lon_col]),
                "ml": float(e[ml_col]),
                # a CLEAN coseismic pair for this event must have one scene
                # inside [bracket_start, event) and one inside
                # (event, bracket_end]; brackets already exclude every other
                # threshold event, cluster-mate or not
                "bracket_start": bracket[0],
                "bracket_end": bracket[1],
                "clean_pair_possible": bool(
                    (e["_t"] - prev_t).total_seconds() / 86400.0 >= 1
                    and (next_t - e["_t"]).total_seconds() / 86400.0 >= 1),
                "inseparable_with_neighbor": bool(neighbor_before or neighbor_after),
            })

        jobs.append({
            "job_id": f"job_{i:03d}",
            "aoi": [round(c["lon"] - args.buffer_deg, 4),
                    round(c["lat"] - args.buffer_deg, 4),
                    round(c["lon"] + args.buffer_deg, 4),
                    round(c["lat"] + args.buffer_deg, 4)],
            "start": pre_start.strftime("%Y-%m-%d"),
            "end": post_end.strftime("%Y-%m-%d"),
            "n_events": len(events),
            "max_ml": float(max(e[ml_col] for e in events)),
            "events": sorted(ev_out, key=lambda e: -e["ml"]),
        })

    doc = {
        "catalog": str(Path(args.catalog).resolve()),
        "parameters": {k: getattr(args, k.replace("-", "_"))
                       for k in ("ml-min", "buffer-deg", "pre-days",
                                 "post-days", "cluster-days", "cluster-km")},
        "note": "One search window per cluster, but PAIRS ARE PER-EVENT: a "
                "coseismic pair is clean only inside an event's bracket. "
                "Review brackets + pair network with the user before "
                "submitting to HyP3; see SKILL.md step 2.",
        "jobs": jobs,
    }
    Path(args.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(jobs)} capture window(s) -> {args.out}")
    for j in jobs:
        print(f"  {j['job_id']}: {j['n_events']} events (max ML {j['max_ml']:.2f}), "
              f"AOI {j['aoi']}, {j['start']}..{j['end']}")
        for e in j["events"]:
            flag = "" if e["clean_pair_possible"] and not e["inseparable_with_neighbor"] \
                else "  <-- CHECK: " + ("inseparable with neighbor "
                                       if e["inseparable_with_neighbor"]
                                       else "bracket too tight")
            print(f"    {e['event_id']} ML{e['ml']:.2f} {e['origin_time']} "
                  f"bracket {e['bracket_start']}..{e['bracket_end']}{flag}")


if __name__ == "__main__":
    main()

