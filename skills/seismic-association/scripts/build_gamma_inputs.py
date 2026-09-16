#!/usr/bin/env python3
"""Prepare GaMMA inputs, retaining source identity and downstream phase metadata."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from contract_io import load_contract
from station_identity import resolve_groups


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def station_groups(metadata, groups):
    """Expand physical coordinates to exact NET.STA.LOC.FAMILY pick IDs."""
    if metadata["id"].duplicated().any():
        raise ValueError("Station metadata has duplicate IDs")
    metadata = metadata.set_index("id")
    rows = []
    for group in sorted(groups):
        parts = group.split(".")
        keys = [group]
        if len(parts) >= 2:
            keys.extend([".".join(parts[:2]), parts[1]])
        matches = [key for key in dict.fromkeys(keys) if key in metadata.index]
        if not matches:
            raise ValueError(f"No coordinates for picking group {group}")
        coords = metadata.loc[matches, ["longitude", "latitude", "elevation_m"]].astype(float)
        if not np.isfinite(coords.to_numpy()).all() or (coords.longitude.abs() > 180).any() or (coords.latitude.abs() > 90).any():
            raise ValueError(f"Invalid station coordinates for {group}")
        if len(coords.drop_duplicates()) != 1:
            raise ValueError(f"Conflicting station coordinates for {group}")
        rows.append({"id": group, **coords.iloc[0].to_dict()})
    return pd.DataFrame(rows, columns=["id", "longitude", "latitude", "elevation_m"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picks", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--stations", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--day", help="Optional UTC YYYY-MM-DD subset, retaining original source row indices")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "gamma_picks.csv").exists() or (out / "input_manifest.json").exists():
        raise ValueError("Prepared inputs already exist; use a new directory")
    picks = pd.read_csv(args.picks)
    required = {"station_id", "phase_time", "phase_type", "phase_score", "phase_amplitude"}
    if required - set(picks):
        raise ValueError("Missing picking columns: " + str(sorted(required - set(picks))))
    picks["source_pick_index"] = np.arange(len(picks), dtype=np.int64)
    source_rows = len(picks)
    picks["phase_time"] = pd.to_datetime(picks["phase_time"], utc=True, errors="raise")
    if picks["phase_time"].isna().any():
        raise ValueError("Missing pick timestamps")
    if args.day:
        day = pd.Timestamp(args.day, tz="UTC")
        picks = picks.loc[(picks.phase_time >= day) & (picks.phase_time < day + pd.Timedelta(days=1))].copy()
    n0 = len(picks)
    if "usable_3c" in picks:
        picks = picks.loc[picks.usable_3c.astype(str).str.lower().isin(["true", "1"])].copy()
    excluded_usable = n0 - len(picks)
    a = pd.to_numeric(picks.phase_amplitude, errors="coerce")
    finite = np.isfinite(a)
    reasons = {"missing_or_non_numeric": int(a.isna().sum()),
               "non_finite": int((~finite & a.notna()).sum()),
               "non_positive": int((finite & (a <= 0)).sum())}
    valid = finite & (a > 0)
    picks = picks.loc[valid].copy()
    picks["amp"] = a.loc[valid]
    picks["phase_type"] = picks.phase_type.astype(str).str.upper()
    if not picks.phase_type.isin(["P", "S"]).all():
        raise ValueError("Unsupported phase type")
    scores = pd.to_numeric(picks.phase_score, errors="raise")
    if not np.isfinite(scores).all() or not scores.between(0, 1).all():
        raise ValueError("Invalid phase probabilities")
    if "amplitude_units" in picks and not picks.amplitude_units.eq("m/s").all():
        raise ValueError("Expected velocity amplitude in m/s")
    # Original columns survive, alongside the five GaMMA aliases.
    picks["id"] = picks.station_id
    picks["timestamp"] = picks.phase_time
    picks["type"] = picks.phase_type.str.lower()
    picks["prob"] = scores
    groups = picks.id.unique()
    if not len(groups):
        archive_doc, archive_path = load_contract(args.archive, "preprocess")
        groups = pd.read_csv(archive_path.parent / archive_doc["manifest_path"]).group.unique()
    stations = resolve_groups(args.stations, groups)
    picks.to_csv(out / "gamma_picks.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S.%fZ")
    stations.to_csv(out / "gamma_stations.csv", index=False)
    stats = {"source_rows": source_rows, "input_rows": n0, "day": args.day,
             "excluded_usable_3c": excluded_usable, "excluded_amplitude": sum(reasons.values()),
             "amplitude_reject_reasons": reasons, "output_rows": len(picks),
             "amplitude_units": "m/s", "amplitude_scale": "linear"}
    (out / "input_filter_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    manifest = {"source_picks": {"path": str(Path(args.picks).resolve()), "sha256": sha(args.picks)},
                "station_metadata": {"path": str(Path(args.stations).resolve()), "sha256": sha(args.stations)},
                "archive": str(Path(args.archive).resolve()), "day": args.day,
                "outputs": {name: sha(out / name) for name in ("gamma_picks.csv", "gamma_stations.csv", "input_filter_stats.json")}}
    (out / "input_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"picks={len(picks)}; matching instrument groups={len(stations)}; output={out}")


if __name__ == "__main__":
    main()
