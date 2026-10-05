#!/usr/bin/env python3
"""Parse hypoDD.reloc into a joint catalog CSV with CC tiers.

Usage:
  python 6_parse_joint.py \\
    --reloc output/joint/output/hypoDD.reloc \\
    --strict-catalog hypodd_catalog_ML.csv \\
    --mess-catalog output/mess/catalog.csv \\
    --out joint_relocated_catalog.csv

Note: hypoDD.reloc FIRST column is the cusp ID (not last).
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reloc", required=True)
    ap.add_argument("--strict-catalog", required=True)
    ap.add_argument("--mess-catalog", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cat = pd.read_csv(args.strict_catalog)
    mess = pd.read_csv(args.mess_catalog)
    mess["event_id"] = mess.event_id.astype(int)
    mmap = mess.set_index("event_id")

    rows = []
    for l in open(args.reloc):
        p = l.split()
        if len(p) < 20:
            continue
        cusp = int(p[0])
        lat, lon, dep = float(p[1]), float(p[2]), float(p[3])

        if cusp < 4545:  # adjust this threshold to your catalog size
            src = cat.iloc[cusp]
            eid, kind = src.event_id, "template"
            ml = getattr(src, "ml", None)
            ot = src.origin_time_utc_dd if hasattr(src, "origin_time_utc_dd") else src.origin_time
            cc = float(mmap.loc[cusp, "best_detection_cc"]) \
                if cusp in mmap.index else np.nan
        else:
            m = mmap.loc[cusp]
            eid = f"mess{cusp - 1000000:07d}"
            kind = "mess_new"
            ml = m.magnitude
            ot = m.origin_time
            cc = m.best_detection_cc

        rows.append({
            "event_id": eid, "source": kind, "cusp": cusp,
            "origin_time": ot,
            "latitude_dd": lat, "longitude_dd": lon,
            "depth_model_km_dd": dep,
            "ml": ml, "best_cc": cc,
        })

    fin = pd.DataFrame(rows)
    fin.to_csv(args.out, index=False)

    print(f"Joint catalog: {len(fin)} events")
    print(fin.source.value_counts().to_dict())
    for tier in [0.4, 0.6, 0.8]:
        print(f"  CC>={tier}: {(fin.best_cc >= tier).sum()}")


if __name__ == "__main__":
    main()
