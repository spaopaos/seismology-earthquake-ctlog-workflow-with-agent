#!/usr/bin/env python3
"""Swarm-scale long-period InSAR product: full quality network -> HyP3 -> MintPy SBAS.

Usage:
  # 1) search + pair-select a dedicated swarm window on chosen stacks
  python 7_swarm_timeseries.py --action prepare \
    --jobs insar_jobs_merged.json --stacks p33:f502 p99:f1265 \
    --workdir-root insar_swarm

  # 2) submit each stack's quality-selected network (one batch per stack)
  python 7_swarm_timeseries.py --action submit --workdir-root insar_swarm

  # 3) after download (share the autopilot poller), run SBAS per stack
  python 7_swarm_timeseries.py --action analyze --workdir-root insar_swarm

This is InSARHub's standard chain end-to-end (downloader -> Hyp3_S1 ->
Hyp3_Mintpy_SBAS): the time series resolves the swarm-total deformation
AND inter-event transient/aseismic motion, complementing the per-event
coseismic maps. Quota: ~10 credits per pair (20x4); a 15-35 pair network
per stack is typical — confirm the pair count with the user before submit
in interactive mode.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def default_exe():
    return str(Path(sys.executable).with_name("insarhub"))


def stack_dirs(root):
    return sorted(d for d in root.rglob("p*_*")
                  if d.is_dir() and (d / "insarhub_config.json").is_file())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--action", required=True,
                    choices=["prepare", "submit", "analyze"])
    ap.add_argument("--jobs", help="merged-window jobs json (prepare)")
    ap.add_argument("--stacks", nargs="+",
                    help="PATH:FRAME tokens with INTEGER path, e.g. "
                         "33:502 99:1265 (asc + desc recommended)")
    ap.add_argument("--workdir-root", required=True)
    ap.add_argument("--job-id", default="swarm")
    ap.add_argument("--insarhub-exe", default=default_exe())
    args = ap.parse_args()

    root = Path(args.workdir_root)

    if args.action == "prepare":
        if not (args.jobs and args.stacks):
            raise SystemExit("prepare needs --jobs and --stacks")
        doc = json.loads(Path(args.jobs).read_text())
        job = doc["jobs"][0]  # merged window = one cluster
        wd = root / args.job_id
        wd.mkdir(parents=True, exist_ok=True)
        lon1, lat1, lon2, lat2 = job["aoi"]
        cmd = [args.insarhub_exe, "downloader", "-N", "S1_SLC",
               "--AOI", str(lon1), str(lat1), str(lon2), str(lat2),
               "--start", job["start"], "--end", job["end"],
               "-w", str(wd), "--select-pairs",
               "--stacks"] + args.stacks
        print(" ".join(cmd), flush=True)
        subprocess.check_call(cmd)
        for sd in stack_dirs(wd):
            sj = sd / f"stack_{sd.name}.json"
            n = len(json.loads(sj.read_text())["pairs"]) if sj.is_file() else 0
            print(f"  {sd.name}: {n} network pairs (~{n*10} HyP3 credits)")

    elif args.action == "submit":
        for sd in stack_dirs(root):
            cmd = [args.insarhub_exe, "processor", "-N", "Hyp3_S1",
                   "-w", str(sd), "submit"]
            print(" ".join(cmd), flush=True)
            subprocess.check_call(cmd)

    elif args.action == "analyze":
        for sd in stack_dirs(root):
            cmd = [args.insarhub_exe, "analyzer", "-N", "Hyp3_Mintpy_SBAS",
                   "-w", str(sd), "run"]
            print(" ".join(cmd), flush=True)
            subprocess.check_call(cmd)
        print("\nSwarm time-series products: velocity.h5 / timeseries.h5 "
              "under each stack's mintpy output dir")


if __name__ == "__main__":
    main()
