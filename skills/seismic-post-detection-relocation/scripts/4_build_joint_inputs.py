#!/usr/bin/env python3
"""Build joint hypoDD inputs (dt.ct ID rewrite + dt.cc station rename + event.dat).

Usage:
  python 4_build_joint_inputs.py \\
    --strict-catalog hypodd_catalog_ML.csv \\
    --mess-catalog output/mess/catalog.csv \\
    --mess-event-dat output/mess/event.dat \\
    --mess-dt-cc output/mess/dt.cc \\
    --strict-dt-ct input/dt.ct \\
    --station-aliases input/station_aliases.json \\
    --new-cc-min 0.4 \\
    --outdir output/joint

Produces:
  input/event.dat  (joint, 10 fields, depth offset removed)
  input/dt.ct       (event IDs rewritten to strict row numbers)
  input/dt.cc       (station names rewritten to S%04d aliases)
"""
import argparse
import json
import re
import numpy as np
import pandas as pd
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict-catalog", required=True)
    ap.add_argument("--mess-catalog", required=True)
    ap.add_argument("--mess-event-dat", required=True)
    ap.add_argument("--mess-dt-cc", required=True)
    ap.add_argument("--strict-dt-ct", required=True)
    ap.add_argument("--station-aliases", required=True)
    ap.add_argument("--new-cc-min", type=float, default=0.4)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    out = Path(args.outdir)
    (out / "input").mkdir(parents=True, exist_ok=True)

    cat = pd.read_csv(args.strict_catalog)
    seq_of = {int(ei): seq for seq, ei in enumerate(cat.event_index)}
    mess = pd.read_csv(args.mess_catalog)
    mess["event_id"] = mess.event_id.astype(int)

    # New events above CC threshold
    new_ok = set(mess.loc[
        (mess.event_id >= 1000000) & (mess.best_detection_cc >= args.new_cc_min),
        "event_id"].astype(int))

    # ---- event.dat ----
    DEPTH_OFFSET = 5.0  # PALM hypodd_depth_offset_km default; strip it
    rows = []
    for l in open(args.mess_event_dat):
        p = l.split()
        if len(p) < 10:
            continue
        cusp = int(p[-1])
        p = p[:9] + [p[-1]] if len(p) == 11 else p
        # Time normalization
        t = p[1]
        if not re.fullmatch(r"\d{8}", t):
            if re.fullmatch(r"\d{9,10}", t):
                frac = t[6:]
                cs = min(int(round(int(frac) / 10 ** len(frac) * 100)), 99)
                p[1] = t[:6] + f"{cs:02d}"
        # Depth offset removal (config should have offset=0, but strip anyway)
        p[4] = "%.3f" % (float(p[4]) - DEPTH_OFFSET)
        if cusp < 1000000 or cusp in new_ok:
            rows.append(" ".join(p))
    n_mess = len(rows)
    in_set = {int(r.split()[-1]) for r in rows}

    # Add missing strict templates
    for seq, r in enumerate(cat.itertuples()):
        if seq in in_set:
            continue
        ot = pd.Timestamp(r.origin_time_utc_dd)
        rows.append(
            "%s %s%02d %8.4f %9.4f %7.3f %5.2f 0.00 0.00 0.00 %9d" % (
                ot.strftime("%Y%m%d"), ot.strftime("%H%M%S"),
                ot.microsecond // 10000,
                r.latitude_dd, r.longitude_dd, r.depth_model_km_dd,
                getattr(r, "ml", 0.0), seq))
    (out / "input" / "event.dat").write_text("\n".join(rows) + "\n")
    final_ids = {int(l.split()[-1]) for l in rows}
    print(f"event.dat: {len(rows)} ({n_mess} MESS + {len(rows)-n_mess} strict)")

    # ---- dt.ct (rewrite IDs) ----
    kept = 0
    with open(args.strict_dt_ct) as fi, \
         open(out / "input" / "dt.ct", "w") as fo:
        keep = False
        for l in fi:
            if l.startswith("#"):
                a, b = (int(x) for x in l[1:].split())
                sa, sb = seq_of.get(a, -1), seq_of.get(b, -1)
                keep = sa in final_ids and sb in final_ids
                if keep:
                    fo.write(f"#{sa:9d}{sb:9d}\n")
                    kept += 1
            elif keep and l.strip():
                fo.write(l)
    print(f"dt.ct: {kept} pairs kept")

    # ---- dt.cc (rewrite station names) ----
    al = json.load(open(args.station_aliases))["aliases"]
    by_sta = {}
    for k, v in al.items():
        by_sta.setdefault(v["site_id"].split(".")[1], []).append(k)

    def pick_alias(sta):
        for k in by_sta.get(sta, []):
            if ".HH" in al[k]["groups"][0]:
                return k
        return by_sta.get(sta, [sta])[0]

    n_pairs = n_obs = 0
    with open(args.mess_dt_cc) as fi, \
         open(out / "input" / "dt.cc", "w") as fo:
        keep = False
        for l in fi:
            if l.startswith("#"):
                a, b = int(l.split()[1]), int(l.split()[2])
                keep = a in final_ids and b in final_ids
                if keep:
                    fo.write(l)
                    n_pairs += 1
            elif keep and l.strip():
                p = l.split()
                p[0] = pick_alias(p[0])
                fo.write(" ".join(p) + "\n")
                n_obs += 1
    print(f"dt.cc: {n_pairs} pairs / {n_obs} observations")

    print("\nReady for hypoDD. Write hypoDD.inp with IDAT=3.")


if __name__ == "__main__":
    main()
