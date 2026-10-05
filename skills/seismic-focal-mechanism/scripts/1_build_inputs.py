#!/usr/bin/env python3
"""Build SKHASH input files (pol_dl.csv, catalog.csv, stations.csv, vmodel).

Usage:
  python 1_build_inputs.py \
    --assignments association/gamma_assignments.csv \
    --catalog relocation/strict/hypodd_catalog.csv \
    --stations association_inputs/gamma_stations.csv \
    --vmodel inputs/velocity_p.cre \
    --out IN

Outputs (skhash $dlpfile/$catfile/$stfile/$vmodel_paths):
  IN/pol_dl.csv         all P polarity scores (threshold applied by SKHASH)
  IN/catalog.csv        events + erh/erz uncertainties
  IN/stations.csv
  IN/vmodel_layers.txt  staircase model (1 km steps, +0.001 km/s strictly increasing)
  IN/vmodel_gradient.txt
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path


def pick(row, *names, default=None):
    for n in names:
        if n in row and pd.notna(row[n]):
            return row[n]
    return default


def load_vmodel(path):
    """Layered P model: 2 columns (vp_km_s, depth_top_km), header line skipped."""
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "*", "%")):
            continue
        parts = line.replace(",", " ").split()
        try:
            vp, d = float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            continue  # header row with column names
        rows.append((d, vp))
    if len(rows) < 2:
        raise ValueError(f"Velocity model {path} must have >=2 layers (vp, depth_top_km)")
    return sorted(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assignments", required=True,
                    help="gamma_assignments.csv with polarity_score")
    ap.add_argument("--catalog", required=True,
                    help="hypoDD catalog CSV (event_id, location, erh/erz)")
    ap.add_argument("--stations", required=True, help="station coords CSV")
    ap.add_argument("--vmodel", required=True,
                    help="layered P model: 2 columns vp, depth_top_km")
    ap.add_argument("--out", default="IN", help="output directory")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- 1) DL polarity file ($dlpfile, skhash format) ----
    cat = pd.read_csv(args.catalog)
    cat_ids = set(cat["event_id"])
    asg = pd.read_csv(args.assignments, dtype={"station_id": str},
                      usecols=lambda c: c in ("event_id", "station_id",
                                              "phase_type", "polarity_score",
                                              "phase_score"))
    asg = asg[asg["event_id"].isin(cat_ids)]
    pol = asg[(asg["phase_type"] == "P") & asg["polarity_score"].notna()].copy()
    parts = pol["station_id"].str.split(".", expand=True)
    pol["network"] = parts[0]
    pol["station"] = parts[1]
    pol["location"] = parts[2]
    pol["channel"] = parts[3]
    pol["p_polarity"] = pol["polarity_score"].astype(float)
    pol[["event_id", "network", "station", "location", "channel",
         "p_polarity", "phase_score"]].to_csv(out / "pol_dl.csv", index=False)
    print(f"pol_dl.csv: {len(pol)} polarities, {pol['event_id'].nunique()} events")

    # ---- 2) event catalog ($catfile) ----
    rows = []
    for _, r in cat.iterrows():
        ot = pick(r, "origin_time_utc_dd", "origin_time", "time")
        ot = pd.Timestamp(ot).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        rows.append({
            "event_id": r["event_id"],
            "time": ot,
            "latitude": pick(r, "latitude_dd", "latitude"),
            "longitude": pick(r, "longitude_dd", "longitude"),
            "depth": pick(r, "depth_model_km_dd", "depth"),
            "horz_uncert_km": pick(r, "erh", "horz_uncert_km", default=0.5),
            "vert_uncert_km": pick(r, "erz", "vert_uncert_km", default=0.5),
        })
    cat_out = pd.DataFrame(rows)
    cat_out.to_csv(out / "catalog.csv", index=False)
    print(f"catalog.csv: {len(cat_out)} events")

    # ---- 3) station table ($stfile) ----
    sta = pd.read_csv(args.stations, dtype=str)
    if "id" in sta.columns:
        parts = sta["id"].str.split(".", expand=True)
        sta_out = pd.DataFrame({
            "network": parts[0], "station": parts[1],
            "location": parts[2], "channel": parts[3],
            "latitude": sta["latitude"].astype(float),
            "longitude": sta["longitude"].astype(float),
            "elevation": sta["elevation_m"].astype(float) if "elevation_m" in sta
            else sta["elevation"].astype(float),
        })
    else:
        sta_out = pd.DataFrame({
            "network": sta["network"], "station": sta["station"],
            "location": sta["location"], "channel": sta["channel"],
            "latitude": sta["latitude"].astype(float),
            "longitude": sta["longitude"].astype(float),
            "elevation": sta["elevation"].astype(float),
        })
    sta_out.to_csv(out / "stations.csv", index=False)
    print(f"stations.csv: {len(sta_out)} groups")

    # ---- 4) velocity model ----
    pairs = load_vmodel(args.vmodel)

    with open(out / "vmodel_gradient.txt", "w") as f:
        f.write("# layered P model as gradient control points\n# depth_km,vp_km_s\n")
        for d, v in pairs:
            f.write("%.2f,%.2f\n" % (d, v))

    # staircase: 1 km steps, +0.001 km/s per step (SKHASH requires
    # strictly increasing vp; approximates constant-velocity layers)
    stair = []
    dv = 0.001
    for i, (d, v) in enumerate(pairs):
        d_next = pairs[i + 1][0] if i + 1 < len(pairs) else 60.0
        edges = np.arange(d, d_next, 1.0)
        if len(edges) == 0 or edges[-1] < d:
            edges = np.array([d])
        for j, e in enumerate(edges):
            stair.append((round(float(e), 3), round(v + dv * j, 5)))
    stair.append((60.0, stair[-1][1] + dv))
    with open(out / "vmodel_layers.txt", "w", newline="\n") as f:
        f.write("# layered P model as staircase approximating constant-velocity layers\n"
                "# 1 km steps, +0.001 km/s per step to keep strictly increasing vp (SKHASH QC)\n"
                "# depth_km,vp_km_s\n")
        for d, v in stair:
            f.write("%.3f,%.5f\n" % (d, v))
    print(f"vmodel_gradient.txt: {len(pairs)} pts; vmodel_layers.txt: {len(stair)} pts")


if __name__ == "__main__":
    main()
