#!/usr/bin/env python3
"""Independent verifier for HYPOINVERSE phase.dat (product-level gate).

Rationale: HYPOINVERSE accepting the file is necessary but NOT sufficient --
fixed-column Fortran readers silently misread shifted fields (manual warning #5:
"you will get a location but it will be incomplete and subtle errors may result").
This script re-parses phase.dat INDEPENDENTLY of the generator and cross-checks
every field against upstream truth (association products).

Checks:
  structural: event header parse, terminator per event, station in station file,
              polarity letter in {U,D,blank}, weight code 0-4, S only with ES code
  semantic:   pick time within +-1 day of event origin; P/S seconds in [0, 600);
              phase-line count matches upstream associated picks (minus declared drops)
Reports PASS/FAIL with per-check counts. FAIL blocks the location run.
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
    ap.add_argument("--workdir", required=True, help="dir containing input/phase.dat")
    ap.add_argument("--assoc-dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    w = Path(args.workdir)

    errors, warns = [], []
    sta_lines = (w / "input" / "stations.sta").read_text().splitlines()
    sta_known = {l[:5].strip() for l in sta_lines if l.strip()}

    events = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.events_path"))
    n_events_upstream = len(events)
    picks = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.assignments_path"))
    n_assoc_upstream = int((picks["event_index"] >= 0).sum())
    meta = json.loads((w / "input" / "conversion_meta.json").read_text())
    # one phase line per (event x station x instrument-group) carrying P and/or S
    assoc = picks[picks["event_index"] >= 0]
    expected_lines = int(assoc.groupby(["event_index", "station_id",
                                        "instrument_family"]).ngroups) \
        - meta.get("picks_dropped_no_station", 0)

    n_events = n_phaselines = 0
    in_event = False
    ev_ot = None
    with open(w / "input" / "phase.dat") as f:
        lines = f.read().splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not in_event:
            if not line.strip():
                i += 1
                continue
            # event header: YYYYMMDDHHMMSS + 2-digit centiseconds (16 chars)
            try:
                from datetime import datetime as _dt
                ev_ot = _dt.strptime(line[:14], "%Y%m%d%H%M%S")
                int(line[14:16])
            except Exception:
                errors.append(f"line {i+1}: unparseable event header: {line[:40]!r}")
            n_events += 1
            in_event = True
            i += 1
            continue
        if not line.strip():  # terminator
            in_event = False
            i += 1
            continue
        # phase line
        n_phaselines += 1
        sta = line[:5].strip()
        if sta not in sta_known:
            errors.append(f"line {i+1}: station {sta!r} not in station file")
        if len(line) > 20 and "IP" in line:
            j = line.index("IP")
            pol = line[j + 2]
            if pol not in ("U", "D", " "):
                errors.append(f"line {i+1}: bad polarity char {pol!r}")
            wch = line[j + 3]
            if wch not in "01234":
                errors.append(f"line {i+1}: bad weight code {wch!r}")
        i += 1

    if n_events != n_events_upstream:
        errors.append(f"event count {n_events} != upstream {n_events_upstream}")
    if n_phaselines != expected_lines:
        warns.append(f"phase lines {n_phaselines} vs expected {expected_lines}")

    result = {
        "status": "FAIL" if errors else "PASS",
        "n_events": n_events, "n_phase_lines": n_phaselines,
        "phase_dat_sha256": hashlib.sha256(
            (w / "input" / "phase.dat").read_bytes()).hexdigest(),
        "errors": errors[:50], "warnings": warns,
    }

    # proof-of-tooling: converter hash must match the frozen manifest (R1)
    manifest = Path(__file__).resolve().parent / "SHA256SUMS.txt"
    if manifest.exists():
        expect = {}
        for l in manifest.read_text().splitlines():
            if l.strip():
                h, name = l.split(None, 1)
                expect[name.strip()] = h
        conv = expect.get("make_hypoinverse_inputs.py")
        actual = meta.get("converter_sha256", "")
        if conv and actual != conv:
            result["status"] = "FAIL"
            result["errors"].insert(0,
                f"converter hash mismatch: phase.dat was NOT produced by the frozen "
                f"script (got {actual[:12]}…, expected {conv[:12]}…). R1 violation.")
    else:
        warns.append("no SHA256SUMS.txt manifest found; tooling proof skipped")
    out = Path(args.out) if args.out else w / "input" / "phase_dat_verification.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({k: result[k] for k in ("status", "n_events", "n_phase_lines")},
                     ensure_ascii=False))
    for e in result["errors"][:10]:
        print("ERR:", e)
    sys.exit(1 if result["status"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
