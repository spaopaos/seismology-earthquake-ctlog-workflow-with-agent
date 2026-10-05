#!/usr/bin/env python3
"""Parse SKHASH output into a per-event best-solution catalog + QC summary.

Usage:
  python 6_parse_mechanisms.py \
    --out-dir OUT --catalog-out mechanisms_catalog.csv --qc-out qc_summary.json

Best solution per event: highest prob_mech, then best quality (A>B>C>D).
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True,
                    help="SKHASH output dir (out.csv, out_polagree.csv, ...)")
    ap.add_argument("--catalog-out", required=True)
    ap.add_argument("--qc-out", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    df = pd.read_csv(out_dir / "out.csv")

    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    df["q_ord"] = df["quality"].map(order)
    best = (df.sort_values(["event_id", "prob_mech", "q_ord"],
                           ascending=[True, False, True])
              .groupby("event_id").head(1).drop(columns=["q_ord"]))
    n_sol = df.groupby("event_id").size().rename("n_solutions")
    out = best.merge(n_sol, on="event_id").rename(columns={
        "origin_lat": "latitude_dd", "origin_lon": "longitude_dd",
        "origin_depth_km": "depth_model_km_dd", "time": "origin_time_utc"})
    cols = ["event_id", "strike", "dip", "rake", "quality",
            "fault_plane_uncertainty", "aux_plane_uncertainty",
            "num_p_pol", "num_sp_ratios", "azimuthal_gap", "takeoff_gap",
            "polarity_misfit", "prob_mech", "sta_distribution_ratio",
            "sp_misfit", "mult_solution_flag", "n_solutions",
            "origin_time_utc", "latitude_dd", "longitude_dd",
            "depth_model_km_dd", "horz_uncert_km", "vert_uncert_km"]
    out[[c for c in cols if c in out.columns]].to_csv(
        args.catalog_out, index=False)
    print(f"{args.catalog_out}: {len(out)} events")

    qc = {
        "events_with_solution": int(out["event_id"].nunique()),
        "quality_counts": out["quality"].value_counts().to_dict(),
        "multiple_solution_events": int(out["mult_solution_flag"].sum())
        if "mult_solution_flag" in out else None,
        "median_p_pols": float(out["num_p_pol"].median()),
        "median_sp_ratios": float(out["num_sp_ratios"].median()),
        "note_pol_accuracy_is_percent": True,
        "note_strike_rake_stats": "use CIRCULAR statistics (+/-180 wraparound)",
    }
    polagree = out_dir / "out_polagree.csv"
    if polagree.is_file():
        pa = pd.read_csv(polagree)
        pa_dl = pa[pa["source"] == "dl_p"].sort_values("pol_accuracy")
        qc["stations_below_60pct_pol_accuracy"] = pa_dl[
            pa_dl["pol_accuracy"] < 60][
            [c for c in ("sta_code", "pol_accuracy", "count_total",
                         "weight_pol_accuracy") if c in pa_dl.columns]
        ].to_dict("records")
    with open(args.qc_out, "w", encoding="utf-8") as f:
        json.dump(qc, f, ensure_ascii=False, indent=2)
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
