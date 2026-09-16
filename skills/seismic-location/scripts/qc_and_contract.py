#!/usr/bin/env python3
"""Parse the anchored H71 comma summary and publish a reproducible location handoff."""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from contract_io import load_contract, product_path, publish_payload


def read_summary(path):
    rows = []
    with Path(path).open() as stream:
        for line in csv.reader(stream):
            if not line or not line[0].strip() or "DATE" in line[0]:
                continue
            if len(line) < 16:
                raise ValueError("Invalid H71 summary row")
            row = {"date": line[0].strip(), "sec": float(line[1]),
                   "latitude_hyp": float(line[2]), "longitude_hyp": float(line[3]),
                   "depth_km_hyp": float(line[4]), "num": int(line[8]), "gap": float(line[9]),
                   "dmin": float(line[10]), "rms": float(line[11]), "erh": float(line[12]),
                   "erz": float(line[13]), "qasr": line[14].strip(), "event_index": int(line[15])}
            if not np.isfinite([row[k] for k in ("sec", "latitude_hyp", "longitude_hyp", "depth_km_hyp", "rms", "erh", "erz")]).all():
                raise ValueError("Nonfinite native location")
            row["event_id"] = f"gm{row['event_index']:06d}"
            row["q"] = row["qasr"][:1]
            row["rmk2"] = row["qasr"][1:2]
            rows.append(row)
    return pd.DataFrame(rows, columns=["event_id", "event_index", "date", "sec", "latitude_hyp", "longitude_hyp",
        "depth_km_hyp", "num", "gap", "dmin", "rms", "erh", "erz", "qasr", "q", "rmk2"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--assoc-dir", required=True)
    ap.add_argument("--stations", required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    work = Path(args.workdir).resolve()
    _, association = load_contract(args.assoc_dir, "association")
    initial = pd.read_csv(product_path(association, "association", "outputs.events_path"))
    located = read_summary(work / "output/run.sum")
    if located.event_id.duplicated().any() or not set(located.event_id).issubset(set(initial.event_id)):
        raise ValueError("Native location IDs do not match association")
    columns = {"latitude": "latitude_gamma", "longitude": "longitude_gamma", "depth_km": "depth_km_gamma"}
    located = located.merge(initial[["event_id", *columns]].rename(columns=columns), on="event_id", validate="one_to_one")
    located.to_csv(work / "hyp_catalog.csv", index=False)
    rejected = initial.loc[~initial.event_id.isin(located.event_id), ["event_id"]].copy()
    rejected["reason"] = "no_native_solution_in_summary"
    rejected.to_csv(work / "rejected_events.csv", index=False)
    qc_dir = work / "qc"
    qc_dir.mkdir(exist_ok=True)
    qc = {"events_in": len(initial), "located": len(located), "rejected": len(rejected),
          "rms_median_s": float(located.rms.median()) if len(located) else None,
          "erh_median_km": float(located.erh.median()) if len(located) else None,
          "erz_median_km": float(located.erz.median()) if len(located) else None,
          "depth_weak_remark_count": int(located.rmk2.eq("-").sum()),
          "convergence_remark_count": int(located.rmk2.eq("#").sum()),
          "scientific_status": "NOT_TESTED"}
    (qc_dir / "location_qc.json").write_text(json.dumps(qc, indent=2, allow_nan=False) + "\n")
    import matplotlib
    matplotlib.use("agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].scatter(located.longitude_hyp, located.latitude_hyp, c=located.depth_km_hyp, s=8)
    axes[0].set(xlabel="Longitude", ylabel="Latitude", title="Native locations")
    axes[1].hist(located.depth_km_hyp, bins=20)
    axes[1].set(xlabel="Depth (km)", ylabel="Events", title="Reported depths; uncertainty requires review")
    fig.tight_layout()
    fig.savefig(qc_dir / "location.png", dpi=140)
    plt.close(fig)
    payload = {"contract_version": "1.0", "stage": "location", "run_id": args.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "software": {"name": "HYPOINVERSE", "version": "1.40"},
        "upstream": [{"stage": "association", "contract_path": str(association), "input_verification": "PASS"}],
        "status": "READY" if len(located) else "PARTIAL", "qc_path": str(qc_dir),
        "inputs": {"stations": str(Path(args.stations).resolve())},
        "outputs": {"catalog": str(work / "hyp_catalog.csv"), "rejected_list": str(work / "rejected_events.csv"),
                    "arc": str(work / "output/run.arc"), "sum": str(work / "output/run.sum"), "prt": str(work / "output/run.prt")},
        "stats": {"located": len(located), "rejected": len(rejected), "events_in": len(initial),
                  "reject_reasons": {"no_native_solution_in_summary": len(rejected)}},
        "warnings": ["Native solutions and residuals do not establish depth accuracy; inspect uncertainty and remark codes."]}
    contract = publish_payload(payload, work / "contract.v2.json", "location")
    print(json.dumps({"qc": qc, "validation": contract["validation"]}))


if __name__ == "__main__":
    main()
