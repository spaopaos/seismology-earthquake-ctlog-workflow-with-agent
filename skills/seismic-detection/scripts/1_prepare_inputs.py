#!/usr/bin/env python3
"""Prepare input files (mess.temp, mess.sta) and day-first symlink tree.

Usage:
  python 1_prepare_inputs.py \\
    --catalog hypodd_catalog.csv \\
    --assignments gamma_assignments.csv \\
    --stations stations.csv \\
    --archive /path/to/NET.STA/LOC.CHA/YEAR/DAY/ \\
    --data-root /path/to/mess_data \\
    --out-dir .

Steps:
  1. Build mess.temp (template phase file, event names = "OT_eventID")
  2. Build mess.sta (station file, 5 columns with gain=1.0, deduplicated)
  3. Build day-first symlink tree for PALM
"""
import argparse
import os
import re
import numpy as np
import pandas as pd
from pathlib import Path


def build_temp(catalog, assignments, out):
    """Build PALM template phase file.

    Event names must be >=14 chars: "YYYYMMDDHHMMSScc_eventID".
    Phase rows: NET.STA, P_ISO, S_ISO (only stations with both P and S).
    """
    asg = assignments.copy()
    asg["net_sta"] = asg.station_id.str.rsplit(".", n=2).str[0]
    asg = asg.sort_values("phase_score").drop_duplicates(
        subset=["event_id", "net_sta", "phase_type"], keep="last")
    piv = asg.pivot_table(
        index=["event_id", "net_sta"], columns="phase_type",
        values="phase_time", aggfunc="first").reset_index()
    both = piv.dropna(subset=["P", "S"])

    lines = []
    n_events = 0
    for r in catalog.itertuples():
        g = both[both.event_id == r.event_id]
        ot = pd.Timestamp(r.origin_time_utc_dd) if hasattr(
            r, "origin_time_utc_dd") else pd.Timestamp(r.origin_time)
        name = "%s%s.%02d_%s" % (
            ot.strftime("%Y%m%d%H%M%S"),
            str(ot.microsecond // 10000).zfill(2),
            (ot.microsecond % 10000) // 100, r.event_id)
        lines.append("%s,%s,%.5f,%.5f,%.3f,%.3f" % (
            name, ot.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "00Z",
            r.latitude, r.longitude, r.depth, getattr(r, "ml", 0.0)))
        n_events += 1
        for p in g.itertuples():
            lines.append("%s,%s,%s" % (p.net_sta, p.P, p.S))
    Path(out).write_text("\n".join(lines) + "\n")
    return n_events


def build_sta(stations, out):
    """Build PALM station file (5 columns, gain=1.0, deduplicated)."""
    lines = []
    seen = set()
    for _, r in stations.iterrows():
        key = "%s.%s" % (r.network, r.station)
        if key in seen:
            continue
        seen.add(key)
        lines.append("%s,%.5f,%.5f,%.1f,1.0" % (
            key, float(r.latitude), float(r.longitude),
            float(r.elevation)))
    Path(out).write_text("\n".join(lines) + "\n")
    return len(lines)


def build_symlinks(archive, data_root):
    """Build day-first symlink tree: data_root/YYYYMMDD/*.SAC -> archive."""
    archive = Path(archive)
    data_root = Path(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    n = 0
    for sta_dir in archive.iterdir():
        if not sta_dir.is_dir():
            continue
        for fam_dir in sta_dir.iterdir():
            if not fam_dir.is_dir():
                continue
            for year_dir in fam_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                for day_dir in year_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    day = day_dir.name
                    dest = data_root / day
                    dest.mkdir(exist_ok=True)
                    for f in day_dir.glob("*.SAC"):
                        link = dest / f.name
                        if not link.exists():
                            link.symlink_to(f.resolve())
                            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", required=True, help="hypoDD catalog CSV")
    ap.add_argument("--assignments", required=True,
                    help="gamma assignments CSV with picks")
    ap.add_argument("--stations", required=True, help="station coords CSV")
    ap.add_argument("--archive", required=True,
                    help="waveform archive root (station-first)")
    ap.add_argument("--data-root", required=True,
                    help="output day-first data root for PALM")
    ap.add_argument("--out-dir", default=".", help="output directory")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    catalog = pd.read_csv(args.catalog)
    assignments = pd.read_csv(args.assignments, dtype={"station_id": str})
    stations = pd.read_csv(args.stations, dtype=str)

    n_ev = build_temp(catalog, assignments, out / "mess.temp")
    n_sta = build_sta(stations, out / "mess.sta")
    n_link = build_symlinks(args.archive, args.data_root)

    print(f"mess.temp: {n_ev} events")
    print(f"mess.sta: {n_sta} stations")
    print(f"symlinks: {n_link} files")

    # Sanity check: station file must be 5 columns
    first = (out / "mess.sta").read_text().split("\n")[0]
    ncol = len(first.split(","))
    if ncol != 5:
        raise ValueError(f"CRITICAL: mess.sta has {ncol} columns, "
                         "must be 5 (with gain). See SKILL.md pitfall #1.")


if __name__ == "__main__":
    main()
