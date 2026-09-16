#!/usr/bin/env python3
"""Generate picking_contract.json from actual picking outputs.

Stats are computed from files, never hand-written. Applies the interval policy
against preprocess metadata usable_3c_intervals (default: flag, do not drop).
Validates against contracts/picking.contract.schema.json.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from contract_io import load_contract, publish_payload
from normalize_picks import normalize

SCHEMA = Path(__file__).resolve().parents[3] / "contracts" / "picking.contract.schema.json"
K_CAP_PER_DAY = 28800  # F18: 10 picks per 30 s per phase -> 86400/30*10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks-dir", required=True, help="result_path containing picks_phasenet_plus/")
    ap.add_argument("--archive", required=True, help="preprocess archive root (for metadata)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--eqnet-commit", required=True)
    ap.add_argument("--weights-sha256", default="")
    ap.add_argument("--device", default="unknown")
    ap.add_argument("--min-prob", type=float, default=0.3)
    ap.add_argument("--mode", default="whole_day", choices=["whole_day", "chunked"])
    ap.add_argument("--chunk-length-s", type=float, default=None)
    ap.add_argument("--chunk-margin-s", type=float, default=None)
    ap.add_argument("--interval-policy", default="picks_outside_usable_3c_flagged")
    ap.add_argument("--verification-report", default=None,
                    help="verify_report.json from verify_input_roundtrip.py; required for PASS")
    ap.add_argument("--qc-path", default=None, help="Existing QC file/directory; missing QC prevents READY")
    args = ap.parse_args()
    upstream, upstream_path = load_contract(args.archive, "preprocess")

    picks_dir = Path(args.picks_dir) / "picks_phasenet_plus"
    normalized_path = Path(args.out).resolve().parent / "picks.csv"
    picks, receipt = normalize(picks_dir, args.archive, normalized_path)

    n_p = int((picks["phase_type"] == "P").sum())
    n_s = int((picks["phase_type"] == "S").sum())
    p_picks = picks[picks["phase_type"] == "P"]
    n_pol = int(p_picks["phase_polarity"].abs().gt(0).sum()) if "phase_polarity" in p_picks else 0

    # K-cap monitor (F18): group-day-phase counts approaching the cap
    picks["day"] = picks["phase_time"].str[:10]
    cap_watch = (picks.groupby(["station_id", "day", "phase_type"]).size()
                 .loc[lambda s: s > K_CAP_PER_DAY * 0.8])

    # input verification state: PASS only with an actual verification report
    ver_status = "NOT_TESTED"
    if args.verification_report:
        rep = json.loads(Path(args.verification_report).read_text())
        ver_status = "PASS" if rep.get("status") == "PASS" else "FAIL"

    contract = {
        "contract_version": "1.0",
        "stage": "picking",
        "software": {"name": "EQNet phasenet_plus", "version": args.eqnet_commit,
                     "weights_sha256": args.weights_sha256},
        "run_id": args.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_path": "",
        "script_path": str(Path(__file__).resolve()),
        "upstream": [{"stage": "preprocess",
                      "contract_path": str(upstream_path),
                      "input_verification": ver_status}],
        "status": "READY" if ver_status == "PASS" and upstream["status"] == "READY" and args.qc_path else "PARTIAL",
        "reader": {"name": "seismic-picking shim (read_mseed_checked)", "version": "v1",
                   "adapted": True,
                   "input_verification": {"status": ver_status,
                                          "method": "known_velocity_array_roundtrip",
                                          "checked_no_rescale_no_integration_no_axis_swap":
                                              ver_status == "PASS"}},
        "component_order": ["E", "N", "Z"],
        "normalization": "model_internal_moving_normalize",
        "model": {"weights": "PhaseNet-Plus-v1/model_99.pth",
                  "weights_sha256": args.weights_sha256},
        "window": {"mode": args.mode, "sampling_rate_hz": 100.0,
                   **({"chunk_length_s": args.chunk_length_s,
                       "chunk_margin_s": args.chunk_margin_s} if args.mode == "chunked" else {})},
        "thresholds": {"min_prob": args.min_prob},
        "interval_policy": args.interval_policy,
        "outputs": {"picks_path": str(normalized_path),
                    "schema": ["station_id", "phase_index", "phase_time", "phase_score",
                               "phase_type", "dt_s", "phase_polarity", "phase_amplitude", "polarity_score",
                               "instrument_family", "usable_3c", "outside_usable", "amplitude_units", "day"],
                    "time_base": "UTC"},
        "coverage": {"station_days_processed": receipt["group_days_processed"],
                     "station_days_skipped": len(receipt["group_days_skipped"]),
                     "skip_reasons": dict(__import__('collections').Counter(r['reason'] for r in receipt['group_days_skipped'])),
                     "skipped_group_days": receipt["group_days_skipped"]},
        "stats": {"n_p": n_p, "n_s": n_s, "n_polarity": n_pol},
        "qc_path": str(Path(args.qc_path).resolve()) if args.qc_path else "",
        "warnings": ([f"K-cap watch: {len(cap_watch)} group-day-phase bins >80% of cap"]
                     if len(cap_watch) else []),
    }

    contract = publish_payload(contract, args.out, "picking")
    print("[contract] schema validation:", contract["validation"]["schema_status"])
    print(f"[contract] -> {args.out}  (n_p={n_p}, n_s={n_s}, n_polarity={n_pol}, "
          f"verification={ver_status})")


if __name__ == "__main__":
    main()
