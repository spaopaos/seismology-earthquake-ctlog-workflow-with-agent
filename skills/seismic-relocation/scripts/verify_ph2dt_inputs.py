#!/usr/bin/env python3
"""Independent verifier for ph2dt inputs (phase.dat / station.dat) + tooling proof.

Mirrors verify_phase_dat.py (location stage): re-parses independently, checks
structure and semantics against upstream truth, and verifies the converter's
sha256 against the frozen SHA256SUMS.txt manifest (R1 tooling proof).
FAIL blocks run_ph2dt.py (which checks this file exists and is PASS).
"""
import argparse
import hashlib
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
    manifest = Path(__file__).resolve().parent / "SHA256SUMS.txt"
    if manifest.exists():
        expect = {}
        for l in manifest.read_text().splitlines():
            if l.strip():
                h, name = l.split(None, 1)
                expect[name.strip()] = h
        conv = expect.get("make_ph2dt_inputs.py")
        if conv and meta.get("converter_sha256") != conv:
            errors.append("converter hash mismatch: inputs NOT from the frozen script (R1)")
    else:
        warns.append("no SHA256SUMS.txt manifest; tooling proof skipped")

    result = {"status": "FAIL" if errors else "PASS",
              "n_events": n_events, "n_phase_lines": n_phases,
              "phase_dat_sha256": hashlib.sha256(
                  (w / "input" / "phase.dat").read_bytes()).hexdigest(),
              "errors": errors[:50], "warnings": warns}
    out = Path(args.out) if args.out else w / "input" / "ph2dt_input_verification.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({k: result[k] for k in ("status", "n_events", "n_phase_lines")}))
    for e in errors[:10]:
        print("ERR:", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
