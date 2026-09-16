#!/usr/bin/env python3
"""Run EQNet phasenet_plus with the project's checked read path (shim).

Replaces SeismicTraceIterableDataset.read_mseed with read_mseed_checked via
monkey-patch at runtime. Never modifies any installed EQNet code.

Shim removes from the stock reader (see references/EQNET_FACTS.md):
  F1  HN-family "acceleration to velocity" integration (+1 Hz highpass)
  F2  response removal (response_path/response_xml)
  F3  read-time highpass filter
  F4  linear-interpolation resampling (rejects non-100 Hz instead)
and enforces explicit E,N,Z component ordering (F6/F12).
"""
import argparse
import sys
from collections import defaultdict


def read_mseed_checked(self, fname, response_path=None, response_xml=None,
                       highpass_filter=0.0, sampling_rate=100):
    import numpy as np
    import obspy
    import torch

    if response_path is not None or response_xml is not None:
        raise ValueError("response removal is forbidden by the preprocess contract")
    if highpass_filter and highpass_filter > 0.0:
        raise ValueError("read-time highpass is forbidden by the preprocess contract")

    stream = obspy.Stream()
    for tmp in fname.split(","):
        stream += obspy.read(tmp)  # archive files: mseed (v5+) or sac (transitional)
    if len(stream) != 3 or len({tr.id for tr in stream}) != 3:
        raise ValueError("Exactly three distinct component traces are required")
    if len({(str(tr.stats.starttime), tr.stats.npts, float(tr.stats.sampling_rate)) for tr in stream}) != 1:
        raise ValueError("Components must share the same sampling grid and support")
    if len({tr.id[:-1] for tr in stream}) != 1 or {tr.id[-1] for tr in stream} != {"Z", "N", "E"}:
        raise ValueError("Expected one complete E/N/Z instrument group")
    if any(not np.isfinite(tr.data).all() or float(tr.stats.calib) != 1.0 for tr in stream):
        raise ValueError("Nonfinite archive data or non-unit calib")

    for trace in stream:
        sr = float(trace.stats.sampling_rate)
        if abs(sr - sampling_rate) > 1e-6:
            raise ValueError(
                f"{trace.id}: sampling rate {sr} != {sampling_rate}; "
                "refusing EQNet's linear-interpolation resampling (F4)"
            )
        trace.detrend("demean")  # matches stock reader behavior; benign on processed data

    comp2idx = {"E": 0, "N": 1, "Z": 2}  # model consumes E,N,Z; polarity head reads last channel (Z)
    station_ids = defaultdict(list)
    for tr in stream:
        c = tr.id[-1]
        if c not in comp2idx:
            raise ValueError(f"unknown component in {tr.id}")
        station_ids[tr.id[:-1]].append(c)

    station_keys = sorted(station_ids.keys())
    begin_time = min(tr.stats.starttime for tr in stream)
    end_time = max(tr.stats.endtime for tr in stream)
    stream = stream.trim(begin_time, end_time, pad=True, fill_value=0)

    nx = len(station_keys)
    nt = len(stream[0].data)
    data = np.zeros([3, nt, nx], dtype=np.float32)
    for i, sta in enumerate(station_keys):
        for c in station_ids[sta]:
            trace = stream.select(id=sta + c)[0]
            data[comp2idx[c], :, i] = trace.data.astype(np.float32)[:nt]
        # NOTE: the stock HN integration branch (F1) is deliberately absent.

    return {
        "waveform": torch.from_numpy(data),
        "station_id": station_keys,
        "begin_time": begin_time.datetime.isoformat(timespec="milliseconds"),
        "dt_s": 1.0 / sampling_rate,
    }


def main():
    ap = argparse.ArgumentParser(description="PhaseNet+ picking with checked read path")
    ap.add_argument("--eqnet-repo", required=True, help="path to pinned EQNet repo (knowledge/repos/EQNet)")
    ap.add_argument("--expect-commit", default="af94a08a85de4b2c917a1b9429b044e7f38e4c28",
                    help="pinned commit the repo must be at; refuse to run otherwise")
    ap.add_argument("--allow-unpinned", action="store_true",
                    help="override commit check; requires a diff report against the pinned commit "
                         "recorded in the run report (see SKILL.md)")

    ap.add_argument("--data-list", required=True)
    ap.add_argument("--verify-report", default=None,
                    help="verify_report.json from verify_input_roundtrip.py. "
                         "REQUIRED for batch runs (fail-closed gate, R6): "
                         "refuse to pick unverified input paths.")
    ap.add_argument("--pilot", action="store_true",
                    help="small-batch pilot run; verification still recommended but not gated")
    ap.add_argument("--result-path", required=True)
    ap.add_argument("--device", default="cpu", choices=["cuda", "cpu"])
    ap.add_argument("--gpu-idx", default=None,
                    help="comma-separated GPU ids authorized by the user, e.g. '0' or '0,1'; "
                         "maps to CUDA_VISIBLE_DEVICES. Must be given before torch loads.")
    ap.add_argument("--min-prob", type=float, default=0.3)
    ap.add_argument("--subdir-level", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--weights", required=True, help="Local pinned PhaseNet+ checkpoint; network fetching is disabled")
    ap.add_argument("--weights-sha256", default="f1643330e34bffaa4f7e3a5f7dd9205fb4019d76e5b9b6cb598232360d22f384")
    args = ap.parse_args()
    from contract_io import sha256
    from runtime_support import verify_vendor
    if args.allow_unpinned:
        ap.error("Release runners require a validated source manifest")
    verify_vendor(args.eqnet_repo, args.expect_commit)
    if sha256(args.weights) != args.weights_sha256:
        ap.error("Local model checkpoint checksum mismatch")

    # R6 fail-closed: batch runs require a PASS verification report
    if not args.pilot:
        if not args.verify_report:
            ap.error("GATE: batch picking requires --verify-report pointing to a PASS "
                     "verify_report.json (run verify_input_roundtrip.py first). "
                     "Use --pilot only for small exploratory runs.")
        import json as _json
        rep = _json.loads(open(args.verify_report).read())
        if rep.get("status") != "PASS":
            ap.error(f"GATE: verification status={rep.get('status')}; refusing batch run.")

    if args.device == "cuda":
        if args.gpu_idx is None:
            ap.error("--device cuda requires --gpu-idx (user-authorized GPU selection); "
                     "never grab all GPUs by default")
        import os
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_idx  # before any torch import

    sys.path.insert(0, args.eqnet_repo)
    import eqnet.data.seismic_trace as stmod
    stmod.SeismicTraceIterableDataset.read_mseed = read_mseed_checked

    import predict as eqnet_predict  # repo-root predict.py

    cli = [
        "--resume", args.weights,
        "--model", "phasenet_plus",
        "--format", "mseed",
        "--data_list", args.data_list,
        "--result_path", args.result_path,
        "--device", args.device,
        "--min_prob", str(args.min_prob),
        "--subdir_level", str(args.subdir_level),
        "--workers", str(args.workers),
        "--batch_size", "1",
        "--sampling_rate", "100.0",
        "--highpass_filter", "0.0",  # belt-and-braces; shim rejects it anyway (F3)
    ]
    eqnet_args = eqnet_predict.get_args_parser().parse_args(cli)
    import torch
    import argparse as _argparse
    import contextlib
    # Official checkpoint includes argparse.Namespace; allow only that trusted type.
    guard = torch.serialization.safe_globals([_argparse.Namespace]) if hasattr(torch.serialization, "safe_globals") else contextlib.nullcontext()
    with guard:
        eqnet_predict.main(eqnet_args)

    import json
    from pathlib import Path
    # F20: silent output-name collision assertion
    with open(args.data_list) as f:
        n_in = sum(1 for line in f if line.strip())
    import glob
    import os
    n_out = len(glob.glob(os.path.join(args.result_path, "picks_phasenet_plus", "**", "*.csv"),
                         recursive=True))
    print(f"[collision-check] inputs={n_in} outputs={n_out}")
    if n_out != n_in:
        print("COLLISION: output CSV count far below input count; check --subdir_level "
              "and data_list layout before trusting this run", file=sys.stderr)
        sys.exit(2)

    files = sorted(Path(args.result_path).joinpath("picks_phasenet_plus").rglob("*.csv"))
    receipt = {"status": "PASS", "data_list_sha256": sha256(args.data_list),
               "weights_sha256": sha256(args.weights), "device": args.device,
               "files": {str(p.relative_to(args.result_path)): sha256(p) for p in files}}
    Path(args.result_path).joinpath("execution_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")

if __name__ == "__main__":
    main()
