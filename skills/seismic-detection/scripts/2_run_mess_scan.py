#!/usr/bin/env python3
"""Run PALM MFT full scan (template cutting + GPU detection + association).

Usage:
  python 2_run_mess_scan.py \\
    --data-root /path/to/mess_data \\
    --config-dir . \\
    --palm-root /path/to/PALM-master \\
    --time-range 20250331-20250701 \\
    --gpu-index 0 \\
    --segment-days 7

This script calls PALM's own MFT_src modules directly (not via conda run,
which can hang cut_template — see SKILL.md pitfall #4).
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True,
                    help="day-first data root (from 1_prepare_inputs.py)")
    ap.add_argument("--config-dir", required=True,
                    help="directory containing config_<CASE>.py + mess.temp + mess.sta")
    ap.add_argument("--palm-root", required=True,
                    help="PALM checkout root (containing MFT_src/)")
    ap.add_argument("--time-range", required=True,
                    help="YYYYMMDD-YYYYMMDD (exclusive end)")
    ap.add_argument("--gpu-index", type=int, default=0,
                    help="torch GPU index (NOT nvidia-smi index)")
    ap.add_argument("--segment-days", type=int, default=7)
    ap.add_argument("--template-root", default=None,
                    help="reuse existing template root (skip cutting)")
    args = ap.parse_args()

    palm = Path(args.palm_root).resolve()
    cfg_dir = Path(args.config_dir).resolve()
    data_root = Path(args.data_root).resolve()

    # Find config file
    cfg_files = list(cfg_dir.glob("config_*.py"))
    if not cfg_files:
        raise FileNotFoundError(f"No config_*.py in {cfg_dir}")
    cfg_name = cfg_files[0].stem  # e.g. "config_mess"

    # Environment setup
    env = os.environ.copy()
    env["PALM_MFT_CONFIG"] = cfg_name
    env["PYTHONPATH"] = os.pathsep.join([
        str(cfg_dir),
        str(palm / "PAL_src"),
        str(palm / "MFT_src"),
    ])

    mft = palm / "MFT_src"

    # ---- Step 1: Cut templates (skip if --template-root given) ----
    template_root = Path(args.template_root) if args.template_root else \
        cfg_dir / "output" / "mess_templates"
    if not args.template_root or not (template_root / "template_index.npy").exists():
        print("=" * 60)
        print("STEP 1: Cutting templates")
        print("=" * 60)
        subprocess.check_call([
            sys.executable, str(mft / "cut_template.py"),
            "--data_dir", str(data_root),
            "--temp_pha", str(cfg_dir / "mess.temp"),
            "--out_root", str(template_root),
        ], cwd=str(cfg_dir), env=env)

    # ---- Step 2: Segment-wise GPU scan ----
    print("=" * 60)
    print(f"STEP 2: GPU scan ({args.time_range}, {args.segment_days}-day segments)")
    print("=" * 60)

    from obspy import UTCDateTime
    start, end = [UTCDateTime(v) for v in args.time_range.split("-")]
    current = start
    segments = []
    while current < end:
        following = min(current + args.segment_days * 86400, end)
        label = f"{current.strftime('%Y%m%d')}-{following.strftime('%Y%m%d')}"
        segments.append(label)
        current = following

    out_root = cfg_dir / "output" / "mess"
    out_root.mkdir(parents=True, exist_ok=True)

    phase_files = []
    for label in segments:
        catalog_path = out_root / f"catalog_{label}.dat"
        phase_path = out_root / f"phase_{label}.dat"
        phase_files.append(phase_path)
        print(f"\n--- Segment {label} ---")
        subprocess.check_call([
            sys.executable, str(mft / "run_mft_gpu.py"),
            "--gpu_idx", str(args.gpu_index),
            "--data_dir", str(data_root),
            "--time_range", label,
            "--sta_file", str(cfg_dir / "mess.sta"),
            "--temp_root", str(template_root),
            "--temp_pha", str(cfg_dir / "mess.temp"),
            "--out_ctlg", str(catalog_path),
            "--out_pha", str(phase_path),
        ], cwd=str(cfg_dir), env=env)

    # ---- Step 3: Association ----
    print("=" * 60)
    print("STEP 3: Association")
    print("=" * 60)
    subprocess.check_call([
        sys.executable, str(mft / "associate_mft.py"),
        "--det_pha"] + [str(p) for p in phase_files] + [
        "--temp_pha", str(cfg_dir / "mess.temp"),
        "--sta_file", str(cfg_dir / "mess.sta"),
        "--time_range", args.time_range,
        "--out_catalog", str(out_root / "catalog.csv"),
        "--out_phase", str(out_root / "phase.csv"),
        "--out_event", str(out_root / "event.dat"),
        "--out_dt", str(out_root / "dt.cc"),
    ], cwd=str(cfg_dir), env=env)

    print("\n" + "=" * 60)
    print("DONE")
    print(f"  catalog: {out_root / 'catalog.csv'}")
    print(f"  dt.cc:   {out_root / 'dt.cc'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
