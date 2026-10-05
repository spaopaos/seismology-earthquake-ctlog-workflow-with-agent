#!/usr/bin/env python3
"""Cut the per-event waveform library used for S/P amplitudes and polarity QC.

Usage:
  python 2_cut_event_waveforms.py \
    --archive <standardized archive root> \
    --assignments association/gamma_assignments.csv \
    --catalog relocation/strict/hypodd_catalog.csv \
    --out event_wf --workers 16

Windows (P−8 -> S+15; P only: P−8 -> P+20; S only: S−12 -> S+15).
Copy-only: no filtering, no deconvolution, no normalization; archive zero-pads
are preserved and usable-interval coverage is recorded in the manifest.
SAC headers: reference time = window start (UTC), t0=P, t1=S, o=origin time.

Archive layout required (preprocess stage output):
  daily_manifest.csv          columns: group, date, file_Z, file_N, file_E
  interface_metadata/<group>/<date>.json   usable_3c_intervals [[s,e],...] samples
  waveform files at the paths recorded in daily_manifest.csv
"""
import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from multiprocessing import Pool
from obspy import Trace, Stream, read
from obspy.core import AttribDict

P_PRE_S = 8.0
S_POST_S = 15.0
P_ONLY_POST = 20.0
S_ONLY_PRE = 12.0
SR = 100.0
NPTS_DAY = 8640000
COMPS = ("Z", "N", "E")
COMP_FILES = {"Z": "file_Z", "N": "file_N", "E": "file_E"}

# per-worker globals (spawn-safe: plain data only, set by init_worker)
MANIFEST_IDX = {}
ARCHIVE = "."
OUT_DIR = "."


def day_str(t):
    return pd.Timestamp(t).strftime("%Y-%m-%d")


def samp_idx(t, day00):
    return int(round((pd.Timestamp(t) - day00).total_seconds() * SR))


def build_pairs(catalog, assignments):
    cat = pd.read_csv(catalog)
    keep = set(cat["event_id"])
    asg = pd.read_csv(assignments, dtype={"station_id": str})
    asg = asg[asg["event_id"].isin(keep)].copy()
    asg["t"] = pd.to_datetime(asg["phase_time"])

    # best pick per (event, station, phase): highest phase_score
    asg = asg.sort_values("phase_score").groupby(
        ["event_id", "station_id", "phase_type"], as_index=False).tail(1)
    pairs = asg.pivot(index=["event_id", "station_id"], columns="phase_type",
                      values=["t", "phase_score", "polarity_score",
                              "phase_amplitude", "gamma_score"]).reset_index()
    pairs.columns = ["_".join([str(a) for a in col if str(a) != ""])
                     if isinstance(col, tuple) else col for col in pairs.columns]

    def win(row):
        p, s = row.get("t_P"), row.get("t_S")
        if pd.notna(p) and pd.notna(s):
            return p - pd.Timedelta(seconds=P_PRE_S), s + pd.Timedelta(seconds=S_POST_S)
        if pd.notna(p):
            return p - pd.Timedelta(seconds=P_PRE_S), p + pd.Timedelta(seconds=P_ONLY_POST)
        return s - pd.Timedelta(seconds=S_ONLY_PRE), s + pd.Timedelta(seconds=S_POST_S)

    w = pairs.apply(win, axis=1, result_type="expand")
    pairs["ws"], pairs["we"] = w[0], w[1]
    pairs["ws_day"] = pairs["ws"].map(day_str)
    has_p, has_s = pairs["t_P"].notna(), pairs["t_S"].notna()
    pairs["phase_pair"] = np.where(has_p & has_s, "P_S",
                                   np.where(has_p, "P_only", "S_only"))
    pairs["s_minus_p_s"] = (pairs["t_S"] - pairs["t_P"]).dt.total_seconds()

    cat_cols = {c: c for c in cat.columns}
    out = pairs.merge(cat.rename(columns=cat_cols), on="event_id", how="left")
    out = out.rename(columns={
        "latitude_dd" if "latitude_dd" in out.columns else "latitude": "latitude_dd",
        "longitude_dd" if "longitude_dd" in out.columns else "longitude": "longitude_dd",
        "depth_model_km_dd" if "depth_model_km_dd" in out.columns else "depth": "depth_model_km_dd",
        "origin_time_utc_dd" if "origin_time_utc_dd" in out.columns else "origin_time": "origin_time_utc_dd",
    })
    return out


def load_day_arrays(group, day, meta_cache):
    """Return {comp: (array|None, stla, stlo, stel, relpath)}, usable intervals."""
    row = MANIFEST_IDX.get((group, day))
    if row is None:
        return {c: (None, np.nan, np.nan, np.nan, "") for c in COMPS}, None
    out = {}
    for c in COMPS:
        path = os.path.join(ARCHIVE, row[COMP_FILES[c]])
        try:
            tr = read(path, format="SAC")[0]
        except Exception:
            out[c] = (None, np.nan, np.nan, np.nan, row[COMP_FILES[c]])
            continue
        sac = tr.stats.sac
        out[c] = (np.asarray(tr.data, dtype=np.float32),
                  float(sac.stla), float(sac.stlo),
                  float(getattr(sac, "stel", np.nan)), row[COMP_FILES[c]])
    mkey = (group, day)
    if mkey not in meta_cache:
        mp = os.path.join(ARCHIVE, "interface_metadata", group, day + ".json")
        meta_cache[mkey] = (json.load(open(mp))["usable_3c_intervals"]
                            if os.path.exists(mp) else None)
    return out, meta_cache[mkey]


def process_task(task):
    group, ws_day, plist = task
    day00 = pd.Timestamp(ws_day + "T00:00:00+00:00")
    meta_cache = {}

    day0, use0 = load_day_arrays(group, ws_day, meta_cache)
    next_day = (day00 + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    need_next = any(pd.Timestamp(p["we"]) >= day00 + pd.Timedelta(days=1) for p in plist)
    if need_next:
        day1, use1 = load_day_arrays(group, next_day, meta_cache)
    else:
        day1, use1 = {c: (None, np.nan, np.nan, np.nan, "") for c in COMPS}, None

    rows = []
    net, sta, loc, fam = group.split(".")
    for p in plist:
        i0 = samp_idx(p["ws"], day00)
        i1 = samp_idx(p["we"], day00)
        npts = i1 - i0
        a0, b0 = max(i0, 0), min(i1, NPTS_DAY)
        a1, b1 = max(i1 - NPTS_DAY, 0), i1 - NPTS_DAY

        usable = []
        for off, use in ((0, use0), (NPTS_DAY, use1)):
            if use:
                usable += [(off + s, off + e) for s, e in use]
        win_len = float(npts)
        cov = sum(max(0, min(e, i1) - max(s, i0)) for s, e in usable)
        usable_frac = cov / win_len if win_len > 0 else 0.0

        def in_usable(idx):
            return any(s <= idx < e for s, e in usable)

        hdr_src = None
        outs = {}
        ok = True
        for c in COMPS:
            arr0, stla, stlo, stel, src0 = day0[c]
            arr1 = day1[c][0]
            seg = np.zeros(npts, dtype=np.float32)
            if arr0 is not None and b0 > a0:
                seg[a0 - i0: b0 - i0] = arr0[a0:b0]
            if arr1 is not None and b1 > a1:
                seg[NPTS_DAY - i0 + a1: NPTS_DAY - i0 + b1] = arr1[a1:b1]
            if hdr_src is None and not np.isnan(stla):
                hdr_src = (stla, stlo, stel)
            try:
                chan = fam + c
                tr = Trace(data=seg)
                tr.stats.sampling_rate = SR
                tr.stats.starttime = p["ws"]
                tr.stats.network, tr.stats.station, tr.stats.location = net, sta, loc
                tr.stats.channel = chan
                tr.stats.calib = 1.0
                tr.stats.sac = AttribDict({
                    "t0": (p["t_P"] - p["ws"]).total_seconds() if pd.notna(p["t_P"]) else -12345.0,
                    "t1": (p["t_S"] - p["ws"]).total_seconds() if pd.notna(p["t_S"]) else -12345.0,
                    "o": (pd.Timestamp(p["origin_time_utc_dd"]) - p["ws"]).total_seconds(),
                    "stla": stla, "stlo": stlo, "stel": stel,
                    "kt0": "P pick", "kt1": "S pick", "ko": "origin",
                })
                fn = os.path.join(OUT_DIR, str(p["event_id"]),
                                  "%s.%s.%s.%s.SAC" % (net, sta, loc, chan))
                Stream([tr]).write(fn, format="SAC")
                outs[c] = fn
            except Exception as ex:
                ok = False
                rows.append({"event_id": p["event_id"], "station_id": group,
                             "error": repr(ex)[:200]})
        if not ok:
            continue

        def val(col):
            x = p.get(col)
            return None if x is None or pd.isna(x) else float(x)

        rows.append({
            "event_id": p["event_id"],
            "station_id": group,
            "channel_family": fam,
            "phase_pair": p["phase_pair"],
            "p_time_utc": None if pd.isna(p["t_P"]) else p["t_P"].strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "s_time_utc": None if pd.isna(p["t_S"]) else p["t_S"].strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "s_minus_p_s": None if pd.isna(p["s_minus_p_s"]) else round(float(p["s_minus_p_s"]), 3),
            "polarity_score_p": val("polarity_score_P"),
            "phase_score_p": val("phase_score_P"),
            "phase_score_s": val("phase_score_S"),
            "latitude_dd": float(p["latitude_dd"]),
            "longitude_dd": float(p["longitude_dd"]),
            "depth_model_km_dd": float(p["depth_model_km_dd"]),
            "origin_time_utc_dd": p["origin_time_utc_dd"],
            "window_start_utc": p["ws"].strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "window_end_utc": p["we"].strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "npts": npts,
            "sampling_rate_hz": SR,
            "duration_s": round(win_len / SR, 2),
            "usable_frac": round(usable_frac, 4),
            "p_in_usable": in_usable(samp_idx(p["t_P"], day00)) if pd.notna(p["t_P"]) else None,
            "s_in_usable": in_usable(samp_idx(p["t_S"], day00)) if pd.notna(p["t_S"]) else None,
            "cross_midnight": bool(i1 > NPTS_DAY),
            "padded_zeros": bool((i0 < 0) or (i1 > NPTS_DAY and day1["Z"][0] is None) or (day0["Z"][0] is None)),
            "warn_s_before_p": bool(pd.notna(p["s_minus_p_s"]) and p["s_minus_p_s"] <= 0),
            "src_day_files": ";".join(x for x in [day0["Z"][4], (day1["Z"][4] if need_next else "")] if x),
            "file_Z": os.path.relpath(outs["Z"], OUT_DIR),
            "file_N": os.path.relpath(outs["N"], OUT_DIR),
            "file_E": os.path.relpath(outs["E"], OUT_DIR),
            "error": "",
        })
    return rows


def init_worker(manifest_idx, archive, out_dir):
    global MANIFEST_IDX, ARCHIVE, OUT_DIR
    MANIFEST_IDX = manifest_idx
    ARCHIVE = archive
    OUT_DIR = out_dir


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True, help="standardized archive root")
    ap.add_argument("--assignments", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--out", required=True, help="output waveform library root")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None,
                    help="process only first N group-day tasks (test run)")
    args = ap.parse_args()

    t0 = time.time()
    out_dir = str(Path(args.out).resolve())
    os.makedirs(out_dir, exist_ok=True)

    man = pd.read_csv(os.path.join(args.archive, "daily_manifest.csv"))
    manifest_idx = {(r["group"], r["date"]): r for _, r in man.iterrows()}

    pairs = build_pairs(args.catalog, args.assignments)
    print(f"pairs: {len(pairs)}  events: {pairs['event_id'].nunique()}", flush=True)

    tasks = []
    for (group, ws_day), g in pairs.groupby(["station_id", "ws_day"]):
        tasks.append((group, ws_day, g.to_dict("records")))
    tasks.sort(key=lambda t: (t[1], t[0]))
    if args.limit:
        tasks = tasks[:args.limit]
        print(f"LIMITED test run: first {len(tasks)} tasks", flush=True)
    print(f"group-day tasks: {len(tasks)}", flush=True)

    for ev in pairs["event_id"].unique():
        os.makedirs(os.path.join(out_dir, str(ev)), exist_ok=True)

    all_rows = []
    with Pool(args.workers, initializer=init_worker,
              initargs=(manifest_idx, args.archive, out_dir)) as pool:
        for i, rows in enumerate(pool.imap_unordered(process_task, tasks, chunksize=4)):
            all_rows.extend(rows)
            if (i + 1) % 200 == 0:
                print("  %d/%d tasks, %.1f min elapsed"
                      % (i + 1, len(tasks), (time.time() - t0) / 60), flush=True)

    df = pd.DataFrame(all_rows)
    if len(df) == 0:
        raise SystemExit("no rows produced")
    ok = df[df["error"].fillna("") == ""].copy()
    ok.drop(columns=["error"]).to_csv(
        os.path.join(out_dir, "event_station_manifest.csv"), index=False)

    summary = {
        "events": int(pairs["event_id"].nunique()),
        "pairs_attempted": len(df),
        "pairs_written": len(ok),
        "files_written": len(ok) * 3,
        "window_rule": {"P_S": "P-8s..S+15s", "P_only": "P-8s..P+20s", "S_only": "S-12s..S+15s"},
        "phase_pair_counts": ok["phase_pair"].value_counts().to_dict(),
        "usable_frac_median": float(ok["usable_frac"].median()),
        "runtime_min": round((time.time() - t0) / 60, 1),
    }
    with open(os.path.join(out_dir, "extraction_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
