#!/usr/bin/env python3
"""QC + contract generation for GaMMA association.

Stats computed from files, never hand-written. Contract validated against
contracts/association.contract.schema.json. GaMMA magnitudes are marked
unusable (hardcoded Picozzi 2018 coefficients, G4).
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from prepare_dbscan_eps import read_effective_eps
from contract_io import publish_payload, load_contract

SCHEMA = Path(__file__).resolve().parents[3] / "contracts" / "association.contract.schema.json"


def dbscan_contract_params(directory, rationale):
    """Build contract parameters from the actual run, refusing conflicting records."""
    value, selection = read_effective_eps(directory)
    return {"rationale_path": str(rationale), "dbscan_eps_s": value,
            "dbscan_eps_choice": selection["choice"],
            "dbscan_eps_basis": selection["basis"],
            "dbscan_eps_estimate_s": selection["estimate_s"],
            "dbscan_eps_selected_via": selection["selected_via"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="association output dir (gamma_events.csv etc.)")
    ap.add_argument("--out", required=True, help="contract output path")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--picks-contract", required=True, help="upstream picking contract path")
    ap.add_argument("--vp-model", required=True)
    ap.add_argument("--vs-model", required=True)
    ap.add_argument("--ncpu-used", type=int, required=True)
    args = ap.parse_args()

    d = Path(args.dir)
    _, picking_contract = load_contract(args.picks_contract, "picking")
    eps_params = dbscan_contract_params(d, d / "config_rationale.md")
    events = pd.read_csv(d / "gamma_events.csv")
    assigns = pd.read_csv(d / "gamma_assignments.csv")
    unassoc = pd.read_csv(d / "gamma_unassociated.csv")
    rationale = d / "config_rationale.md"
    derived = json.loads((d / "derived_quantities.json").read_text())
    effective = json.loads((d / "effective_config.json").read_text())
    if effective["ncpu"] != args.ncpu_used:
        raise ValueError("Reported CPU count differs from the effective configuration")
    if assigns.duplicated(["event_index", "station_id", "phase_type"]).any():
        raise ValueError("Duplicate event/station-group/phase rows")
    if set(assigns.source_pick_index) & set(unassoc.source_pick_index):
        raise ValueError("Associated and unassociated source rows overlap")

    qc_dir = d / "qc"
    qc_dir.mkdir(exist_ok=True)
    plot_status, plot_error = "PASS", None
    try:
        import matplotlib
        matplotlib.use("agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        if len(events):
            pd.to_datetime(events["time"]).dt.date.value_counts().sort_index().plot(ax=axes[0], kind="bar")
        axes[0].set_title("events per day")
        if "sigma_time" in events:
            events["sigma_time"].hist(ax=axes[1], bins=50)
        axes[1].set_title("sigma_time (s)")
        axes[2].scatter(events["x(km)"], events["y(km)"], s=3)
        axes[2].set_title("event map (km)")
        fig.tight_layout()
        fig.savefig(qc_dir / "association_overview.png", dpi=160)
    except Exception as e:
        plot_status, plot_error = "FAIL", str(e)
        print(f"QC figure incomplete: {e}")
    qc = {"events": len(events), "picks_in": len(assigns) + len(unassoc),
          "assigned": len(assigns), "unassociated": len(unassoc), "plot_status": plot_status,
          "plot_error": plot_error, "dbscan_eps_s": eps_params["dbscan_eps_s"],
          "assigned_p": int(assigns.phase_type.eq("P").sum()), "assigned_s": int(assigns.phase_type.eq("S").sum()),
          "source_rows_disjoint": True, "scientific_status": "NOT_TESTED"}
    (qc_dir / "association_qc.json").write_text(json.dumps(qc, indent=2) + "\n")

    sta_file = d / "gamma_stations.csv"
    sta = pd.read_csv(sta_file) if sta_file.exists() else None
    lat_range = [float(sta["latitude"].min()), float(sta["latitude"].max())] if sta is not None else [None, None]
    lon_range = [float(sta["longitude"].min()), float(sta["longitude"].max())] if sta is not None else [None, None]

    contract = {
        "contract_version": "1.0",
        "stage": "association",
        "software": {"name": "GaMMA", "version": "80394dd"},
        "run_id": args.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(d / "effective_config.json"),
        "upstream": [{"stage": "picking", "contract_path": str(picking_contract),
                      "input_verification": "PASS"}],
        "status": "READY" if len(events) > 0 and plot_status == "PASS" else "PARTIAL",
        "station_source": {"path": str(sta_file.resolve()), "coordinates_verified": sta is not None},
        "region": {"lat_range": lat_range,
                   "lon_range": lon_range,
                   "depth_range_km": [0.0, derived["model_max_depth_km"]]},
        "velocity_model": {"name": Path(args.vp_model).stem, "path": args.vp_model,
                           "source": "user-specified (pipeline config); see config_rationale.md", "s_path": str(Path(args.vs_model).resolve())},
        "params": eps_params,
        "outputs": {"events_path": str(d / "gamma_events.csv"),
                    "assignments_path": str(d / "gamma_assignments.csv"),
                    "event_id_scheme": "gm%06d from native event_index; stable across output sorting"},
        "stats": {"picks_in": int(len(assigns) + len(unassoc)),
                  "picks_associated": int(len(assigns)),
                  "association_rate": round(len(assigns) / max(len(assigns) + len(unassoc), 1), 4),
                  "n_events": int(len(events)),
                  "unassociated_picks_path": str(d / "gamma_unassociated.csv")},
        "magnitude_usable": False,  # G4: hardcoded Picozzi 2018 coefficients
        "qc_path": str(qc_dir),
        "warnings": [],
    }

    contract = publish_payload(contract, args.out, "association")
    print("[contract] schema validation:", contract["validation"]["schema_status"])
    print(f"[contract] -> {args.out}  events={len(events)} rate={contract['stats']['association_rate']}")


if __name__ == "__main__":
    main()
