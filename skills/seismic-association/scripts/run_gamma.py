#!/usr/bin/env python3
"""Run GaMMA after an explicit default/estimated/user DBSCAN eps choice.

prepare_dbscan_eps.py computes the options before the agent asks the user.
The selected value is preserved in effective_config.json and config_rationale.md.
"""
import argparse
import json
import os
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_dbscan_eps import load_gamma_utils, resolve_selection
from contract_io import load_contract, product_path
from build_gamma_inputs import sha
from gamma_outputs import output_tables


def load_model_cre(path):
    """vel .cre: 'vp_km_s depth_top_km' per line (header line skipped)."""
    rows = [l.split() for l in Path(path).read_text().splitlines()
            if l.strip() and l.strip()[0].isdigit()]
    arr = np.array(rows, dtype=float)
    return arr[:, 0], arr[:, 1]  # velocities, depths


def derive(stations, vp, vs_depths):
    """Derived quantities from upstream data (SKILL.md section 2-A)."""
    from itertools import combinations
    from pyproj import Geod
    coords = stations[["longitude", "latitude"]].to_numpy()
    lat0 = coords[:, 1].mean()
    km_per_deg = 111.32
    dmax = 0.0
    geod = Geod(ellps="WGS84")
    for a, b in combinations(coords, 2):
        d = abs(geod.inv(a[0], a[1], b[0], b[1])[2]) / 1000
        dmax = max(dmax, d)
    return {"D_max_km": round(dmax, 2),
            "n_station_groups": int(len(stations)),
            "model_max_depth_km": float(max(vp[1].max(), vs_depths.max()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True, help="gamma_picks.csv")
    ap.add_argument("--stations", required=True, help="gamma_stations.csv")
    ap.add_argument("--vp-model", required=True)
    ap.add_argument("--vs-model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth-max-km", type=float, required=True)
    ap.add_argument("--margin-km", type=float, default=20.0)
    ap.add_argument("--ncpu", type=int, default=8)
    ap.add_argument("--min-picks", type=int, default=5)
    ap.add_argument("--min-p", type=int, default=3)
    ap.add_argument("--min-s", type=int, default=1)
    ap.add_argument("--min-stations", type=int, default=3)
    ap.add_argument("--max-sigma11", type=float, default=2.0)
    ap.add_argument("--max-sigma22", type=float, default=1.0)
    ap.add_argument("--oversample", type=int, default=5,
                    help="positive integer: pinned GaMMA uses this factor in component-count indexing")
    ap.add_argument("--picking-contract", default=None,
                    help="picking_contract.json path; REQUIRED (fail-closed gate, R6)")
    ap.add_argument("--dbscan-eps-options", required=True, help="prepare_dbscan_eps.py output JSON")
    ap.add_argument("--dbscan-eps-choice", required=True, choices=["default", "estimated", "custom"])
    ap.add_argument("--dbscan-eps-selected-via", required=True, choices=["pipeline_config", "conversation"])
    ap.add_argument("--dbscan-eps", type=float, help="Explicit positive seconds, only for choice=custom")
    ap.add_argument("--prepare-only", action="store_true", help="Write configuration without association")
    args = ap.parse_args()
    if not np.isfinite(args.depth_max_km) or args.depth_max_km <= 0 or not np.isfinite(args.margin_km) or args.margin_km <= 0:
        ap.error("Depth maximum and projected margin must be finite and positive")
    if args.oversample < 1 or args.ncpu < 1:
        ap.error("--oversample and --ncpu must be positive integers")

    # R6 fail-closed: association requires a verified upstream picking contract
    if not args.picking_contract:
        ap.error("GATE: --picking-contract required. Association consumes only verified "
                 "picking output (status READY/PARTIAL).")
    pc, _ = load_contract(args.picking_contract, "picking")
    if pc.get("status") not in ("READY", "PARTIAL"):
        ap.error(f"GATE: picking contract status={pc.get('status')}; refusing to associate.")

    try:
        selection = resolve_selection(args.dbscan_eps_options, args.stations,
                                      args.dbscan_eps_choice, args.dbscan_eps_selected_via,
                                      args.dbscan_eps)
    except (ValueError, KeyError, OSError) as exc:
        ap.error(f"GATE: {exc}")
    gamma_utils = load_gamma_utils()

    # Bind prepared rows to the verified upstream product and the exact tables.
    manifest_path = Path(args.picks).resolve().parent / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source_picks = product_path(args.picking_contract, "picking", "outputs.picks_path")
    if sha(source_picks) != manifest["source_picks"]["sha256"]:
        raise ValueError("Prepared picks do not match the current picking contract")
    for path in (Path(args.picks), Path(args.stations)):
        if sha(path) != manifest["outputs"][path.name]:
            raise ValueError("Prepared input table changed")
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "gamma_events.csv").exists():
        raise ValueError("Association output exists; use a new directory")
    (out / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(out / "logs/gamma.log"), logging.StreamHandler()])
    log = logging.getLogger("association")

    vp_vel, vp_dep = load_model_cre(args.vp_model)
    vs_vel, vs_dep = load_model_cre(args.vs_model)
    if not np.allclose(vp_dep, vs_dep):
        raise SystemExit("P/S velocity models have inconsistent depth layering; aborting "
                         "(this is the only built-in checkpoint -- do not bypass)")
    picks = pd.read_csv(args.picks, parse_dates=["timestamp", "phase_time"])
    stations = pd.read_csv(args.stations)
    required = {"station_id", "instrument_family", "polarity_score", "phase_type", "phase_time",
                "phase_score", "phase_amplitude", "source_pick_index"}
    if required - set(picks):
        raise ValueError("Prepared picks lack downstream metadata: " + str(sorted(required - set(picks))))
    if stations.id.duplicated().any() or not set(picks.id).issubset(set(stations.id)):
        raise ValueError("Pick and station IDs do not match one-to-many")
    if not np.isfinite(picks.amp).all() or not (picks.amp > 0).all():
        raise ValueError("Amplitude must remain finite, positive linear m/s")

    d = derive(stations, (vp_vel, vp_dep), vs_dep)
    d["model_max_depth_km"] = args.depth_max_km
    d["search_depth_basis"] = "explicit regional configuration; layer-top depth is not maximum event depth"
    d["dbscan_eps_options_path"] = selection["options_path"]
    dbscan_eps = selection["value_s"]
    (out / "derived_quantities.json").write_text(json.dumps(d, indent=2))

    # --- projection & config (following docs/example_phasenet.ipynb) ---
    from pyproj import Proj
    longitude_rad = np.radians(stations["longitude"])
    x0 = float(np.degrees(np.arctan2(np.sin(longitude_rad).mean(), np.cos(longitude_rad).mean())))
    y0 = float(stations["latitude"].median())
    proj = Proj(f"+proj=aeqd +lon_0={x0} +lat_0={y0} +units=km")
    stations[["x(km)", "y(km)"]] = stations.apply(
        lambda r: pd.Series(proj(longitude=r.longitude, latitude=r.latitude)), axis=1)
    stations["z(km)"] = stations["elevation_m"].apply(lambda x: -x / 1e3)
    stations.to_csv(out / "gamma_stations.csv", index=False)

    config = {
        "center": (x0, y0),
        "xlim_degree": (2 * stations["longitude"].min() - x0, 2 * stations["longitude"].max() - x0),
        "ylim_degree": (2 * stations["latitude"].min() - y0, 2 * stations["latitude"].max() - y0),
        "use_dbscan": True, "use_amplitude": True, "method": "BGMM",
        "oversample_factor": args.oversample,
        "dbscan_eps": dbscan_eps, "dbscan_min_samples": 3,
        "covariance_prior": [5.0, 5.0],
        "dims": ["x(km)", "y(km)", "z(km)"],
        # DBSCAN uses a scalar velocity for spatial scaling. The layered models
        # remain in eikonal for phase travel times, as in the upstream example.
        "vel": {"p": selection["vp_km_s"], "s": float(vs_vel[0])},
        "eikonal": {"vel": {"z": vp_dep.tolist(), "p": vp_vel.tolist(), "s": vs_vel.tolist()},
                    "h": 0.5,
                    "xlim": None, "ylim": None, "zlim": (0.0, d["model_max_depth_km"])},
        "min_picks_per_eq": args.min_picks, "min_p_picks_per_eq": args.min_p,
        "min_s_picks_per_eq": args.min_s, "min_stations": args.min_stations,
        "max_sigma11": args.max_sigma11, "max_sigma22": args.max_sigma22,
        "ncpu": args.ncpu,
    }
    config["x(km)"] = [float(stations["x(km)"].min() - args.margin_km), float(stations["x(km)"].max() + args.margin_km)]
    config["y(km)"] = [float(stations["y(km)"].min() - args.margin_km), float(stations["y(km)"].max() + args.margin_km)]
    config["xlim_degree"] = [float(stations.longitude.min()), float(stations.longitude.max())]
    config["ylim_degree"] = [float(stations.latitude.min()), float(stations.latitude.max())]
    config["geographic_bounds_role"] = "station extent only; source search uses projected km bounds"
    config["z(km)"] = (0.0, d["model_max_depth_km"])
    config["bfgs_bounds"] = [list(config["x(km)"]), list(config["y(km)"]),
                              list(config["z(km)"]), [None, None]]
    # np.arange has an exclusive end. Cover the complete search box and
    # source-to-station relative depths (including station elevation).
    h = config["eikonal"]["h"]
    config["eikonal"]["xlim"] = [config["x(km)"][0] - h, config["x(km)"][1] + h]
    config["eikonal"]["ylim"] = [config["y(km)"][0] - h, config["y(km)"][1] + h]
    z_needed = config["z(km)"][1] - stations["z(km)"].min()
    config["eikonal"]["zlim"] = [min(0.0, float(np.floor(-stations["z(km)"].max() / h) * h)),
                                  float(np.ceil(z_needed / h) * h + h)]

    # Capture the values actually supplied to GaMMA before it mutates config.
    (out / "effective_config.json").write_text(json.dumps(
        config, indent=2, default=lambda v: v.tolist(), allow_nan=False) + "\n")
    (out / "dbscan_eps_selection.json").write_text(json.dumps(
        selection, indent=2, allow_nan=False) + "\n")

    # --- rationale (mandatory; missing rationale = do not run) ---
    rat = [f"# GaMMA config rationale  ({datetime.now(timezone.utc).isoformat()})",
           f"derived: {json.dumps(d)}", ""]
    rat.append(f"dbscan_eps = {dbscan_eps!r} s | {selection['basis']} | "
               f"choice={selection['choice']}, selected_via={selection['selected_via']}; "
               f"recommended default=10.0 s; estimate={selection['estimate_s']!r} s; "
               f"options={selection['options_path']}")
    for k in ["use_amplitude", "oversample_factor", "covariance_prior", "min_picks_per_eq",
              "min_p_picks_per_eq", "min_s_picks_per_eq", "min_stations",
              "max_sigma11", "max_sigma22"]:
        rat.append(f"{k} = {config[k]} | see SKILL.md section 2-B")
    rat.append(f"vel = {args.vp_model} + {args.vs_model} | user (pipeline config)")
    (out / "config_rationale.md").write_text("\n".join(rat) + "\n")

    if args.prepare_only:
        print(f"Configuration prepared: dbscan_eps={dbscan_eps!r} s; association not started.")
        return

    log.info("effective dbscan_eps=%s; ncpu=%s; picks=%s", dbscan_eps, args.ncpu, len(picks))
    start = time.monotonic()
    previous_cwd = Path.cwd()
    try:
        os.chdir(out)  # native eikonal scratch files stay inside this run
        raw_events, raw_assignments = gamma_utils.association(picks, stations, config, 0, "BGMM") if len(picks) else ([], [])
    finally:
        os.chdir(previous_cwd)
    events, assignments, unassoc = output_tables(raw_events, raw_assignments, picks, proj)
    for name, table in (("gamma_events.csv", events), ("gamma_assignments.csv", assignments), ("gamma_unassociated.csv", unassoc)):
        table.to_csv(out / name, index=False, date_format="%Y-%m-%dT%H:%M:%S.%fZ")
    summary = {"events": len(events), "picks_in": len(picks), "picks_associated": len(assignments),
               "unassociated": len(unassoc), "runtime_s": time.monotonic() - start,
               "dbscan_eps_s": dbscan_eps, "input_manifest": str(manifest_path),
               "input_manifest_sha256": sha(manifest_path), "phase_metadata_preserved": True,
               "magnitude_usable": False}
    (out / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    log.info("summary %s", json.dumps(summary))

    n_assoc = len(assignments)
    print(f"events={len(events)} picks_in={len(picks)} associated={n_assoc} "
          f"rate={n_assoc / max(len(picks), 1):.3f} unassociated={len(unassoc)}")


if __name__ == "__main__":
    main()
