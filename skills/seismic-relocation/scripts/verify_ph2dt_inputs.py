#!/usr/bin/env python3
"""Independent verifier for ph2dt inputs (phase.dat / station.dat) + tooling proof.

Mirrors verify_phase_dat.py (location stage): re-parses independently, checks
structure and semantics against upstream truth, and verifies the converter's
against upstream truth (structure, counts, phase types).
FAIL blocks run_ph2dt.py (which checks this file exists and is PASS).
"""
import argparse

import json
import sys
from pathlib import Path

import pandas as pd

from contract_io import product_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--location-dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    w = Path(args.workdir)

    errors, warns = [], []
    cat = pd.read_csv(product_path(args.location_dir, "location", "outputs.catalog_path"))
    n_events_upstream = len(cat)

    n_events = n_phases = 0
    tt_bad = 0
    with open(w / "input" / "phase.dat") as f:
        for line in f:
            if line.startswith("#"):
                n_events += 1
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    tt = float(parts[1])
                    if not -600 < tt < 600:
                        tt_bad += 1
                except ValueError:
                    errors.append(f"bad phase line: {line[:40]!r}")
                if parts[-1] not in ("P", "S"):
                    errors.append(f"bad phase type in: {line[:40]!r}")
                n_phases += 1
    if n_events != n_events_upstream:
        errors.append(f"events {n_events} != upstream {n_events_upstream}")
    if tt_bad:
        errors.append(f"{tt_bad} phase lines with |travel time| > 600 s")

    sta = (w / "input" / "station.dat").read_text().splitlines()
    if len(sta) < 3:
        warns.append(f"only {len(sta)} stations in station.dat")

    meta = json.loads((w / "input" / "conversion_meta.json").read_text())
    result = {"status": "FAIL" if errors else "PASS",
              "n_events": n_events, "n_phase_lines": n_phases,
              "errors": errors[:50], "warnings": warns}
    out = Path(args.out) if args.out else w / "input" / "ph2dt_input_verification.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({k: result[k] for k in ("status", "n_events", "n_phase_lines")}))
    for e in errors[:10]:
        print("ERR:", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
