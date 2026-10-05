#!/usr/bin/env python3
"""Collect InSAR coseismic products into an event-mapped manifest.

Usage:
  python 4_collect_products.py --jobs insar_jobs.json \
    --workdir-root insar_work --out insar_products.csv

Scans each job's workdir for HyP3/GUNW products (NetCDF), rasters and
plots, and maps every file to its capture job and (when the pair dates
identify it) the bracketed event. Converted GeoTIFFs are produced with
`insarhub utils h5-to-raster` when MintPy HDF5 outputs exist (time-series
mode); coseismic GUNW NetCDFs already contain unwrapped phase + coherence.
"""
import argparse
import csv
import json
import re
from pathlib import Path

PRODUCT_PATTERNS = {
    "gunw_interferogram": "*.nc",
    "geotiff": "*.tif",
    "plot": "*.png",
    "hdf5": "*.h5",
}


def pair_dates_from_name(name):
    """Extract YYYYMMDD-YYYYMMDD from common product names (GUNW style)."""
    m = re.search(r"(\d{8})[-_tT](\d{8})", name)
    return (m.group(1), m.group(2)) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", required=True, help="insar_jobs.json")
    ap.add_argument("--workdir-root", required=True)
    ap.add_argument("--out", required=True, help="manifest CSV path")
    args = ap.parse_args()

    doc = json.loads(Path(args.jobs).read_text())
    root = Path(args.workdir_root)
    rows = []

    for job in doc["jobs"]:
        wd = root / job["job_id"]
        if not wd.is_dir():
            continue
        for kind, pattern in PRODUCT_PATTERNS.items():
            for f in sorted(wd.rglob(pattern)):
                rel = f.relative_to(root)
                pd = pair_dates_from_name(f.name)
                bracketed = ""
                if pd:
                    d1, d2 = pd
                    for ev in job["events"]:
                        t = ev["origin_time"][:10].replace("-", "")
                        if d1 <= t <= d2:
                            # pair spans the event; clean only if it stays
                            # inside the event bracket
                            b1 = ev["bracket_start"].replace("-", "")
                            b2 = ev["bracket_end"].replace("-", "")
                            clean = (d1 >= b1 and d2 <= b2)
                            bracketed += ev["event_id"] + (
                                ":clean" if clean else ":spans_multiple") + " "
                rows.append({
                    "job_id": job["job_id"],
                    "kind": kind,
                    "file": str(rel),
                    "bytes": f.stat().st_size,
                    "pair_dates": "-".join(pd) if pd else "",
                    "bracketed_events": bracketed.strip(),
                })

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["job_id", "kind", "file", "bytes",
                                          "pair_dates", "bracketed_events"])
        w.writeheader()
        w.writerows(rows)
    print(f"{args.out}: {len(rows)} products")
    for r in rows[:20]:
        print("  ", r["job_id"], r["kind"], r["file"], r["bracketed_events"])
    if len(rows) > 20:
        print(f"   ... and {len(rows) - 20} more")


if __name__ == "__main__":
    main()
