#!/usr/bin/env python3
"""Export CC-tier catalogs and event.dat format normalizer.

Usage:
  python 3_export_tiers.py --catalog catalog.csv --outdir output/mess

Outputs:
  catalog_cc04.csv / catalog_cc06.csv / catalog_cc08.csv
  event.dat (normalized to 10 fields, 8-digit HHMMSScc time)
"""
import argparse
import re
import pandas as pd
from pathlib import Path

TIERS = [0.4, 0.6, 0.8]


def normalize_event_dat(path):
    """Normalize event.dat: 10 fields, time 8-digit HHMMSScc.

    PALM may write 9~10 digit times or 11 fields — both break hypoDD.
    """
    lines = path.read_text().splitlines()
    out = []
    for l in lines:
        p = l.split()
        if len(p) < 10:
            continue
        cusp = int(p[-1])
        if len(p) == 11:
            p = p[:9] + [p[-1]]
        t = p[1]
        if not re.fullmatch(r"\d{8}", t):
            if re.fullmatch(r"\d{9,10}", t):
                frac = t[6:]
                cs = min(int(round(int(frac) / 10 ** len(frac) * 100)), 99)
                p[1] = t[:6] + f"{cs:02d}"
            else:
                continue
        out.append(" ".join(p))
    path.write_text("\n".join(out) + "\n")
    return len(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", required=True, help="MESS catalog.csv")
    ap.add_argument("--event-dat", required=True, help="MESS event.dat")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cat = pd.read_csv(args.catalog)
    cc = cat.best_detection_cc.to_numpy()

    for tier in TIERS:
        sub = cat[cc >= tier]
        name = f"catalog_cc{str(tier).replace('.', '')}.csv"
        sub.to_csv(outdir / name, index=False)
        print(f"CC>={tier}: {len(sub)} events -> {name}")

    n = normalize_event_dat(Path(args.event_dat))
    print(f"event.dat normalized: {n} events (10 fields, 8-digit time)")


if __name__ == "__main__":
    main()
