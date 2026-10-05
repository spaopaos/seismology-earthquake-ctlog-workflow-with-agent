#!/usr/bin/env python3
"""Run InSARHub scene search + pair selection for coseismic capture jobs.

Usage:
  python 2_run_downloader.py --jobs insar_jobs.json \
    --workdir-root insar_work [--job-id job_001] [--insarhub-exe insarhub]

Per job this wraps (HyP3 cloud path -- no local SLC download):
  insarhub downloader -N S1_SLC --AOI lon1 lat1 lon2 lat2 \
      --start YYYY-MM-DD --end YYYY-MM-DD -w <workdir>/<job> --select-pairs

The pair network and quality scores must be reviewed with the user before
step 3 submits anything to HyP3 (free quota is limited).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def default_exe():
    # console script living next to this interpreter (insarhub env)
    return str(Path(sys.executable).with_name("insarhub"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", required=True, help="insar_jobs.json")
    ap.add_argument("--workdir-root", required=True)
    ap.add_argument("--job-id", default=None,
                    help="run a single job (default: all)")
    ap.add_argument("--insarhub-exe", default=default_exe())
    ap.add_argument("--download", action="store_true",
                    help="ALSO download SLCs locally (NOT needed for HyP3; "
                         "use only when switching to a local processor)")
    args = ap.parse_args()

    doc = json.loads(Path(args.jobs).read_text())
    root = Path(args.workdir_root)
    todo = [j for j in doc["jobs"] if not args.job_id or j["job_id"] == args.job_id]
    if not todo:
        raise SystemExit(f"no matching job (job-id={args.job_id})")

    for j in todo:
        workdir = root / j["job_id"]
        workdir.mkdir(parents=True, exist_ok=True)
        lon1, lat1, lon2, lat2 = j["aoi"]
        cmd = [args.insarhub_exe, "downloader", "-N", "S1_SLC",
               "--AOI", str(lon1), str(lat1), str(lon2), str(lat2),
               "--start", j["start"], "--end", j["end"],
               "-w", str(workdir), "--select-pairs"]
        if args.download:
            cmd += ["--download", "-O"]
        print("\n== " + " ".join(cmd), flush=True)
        subprocess.check_call(cmd)

        cfgs = sorted(workdir.glob("p*/insarhub_config.json"))
        if not cfgs:
            print(f"WARNING: no per-stack insarhub_config.json under {workdir}; "
                  "check downloader output")
    print("\nNext: review the pair network with the user, then "
          "3_run_processor.py --action submit")


if __name__ == "__main__":
    main()
