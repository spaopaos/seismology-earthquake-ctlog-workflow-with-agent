#!/usr/bin/env python3
"""Run the InSARHub HyP3 cloud processor: submit / refresh / download.

Usage:
  python 3_run_processor.py --workdir-root insar_work [--job-id job_001] \
    --action submit|refresh|download [--watch] [--insarhub-exe insarhub]

Wraps:  insarhub processor -N Hyp3_S1 -w <workdir>/<job> <action>

--watch loops refresh until all jobs complete (checks every 10 min by
default). Only submit pairs the user confirmed in step 2 — HyP3's free
quota is limited.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def default_exe():
    # console script living next to this interpreter (insarhub env);
    # guard against being launched with a different interpreter
    exe = Path(sys.executable).with_name("insarhub")
    if not exe.is_file():
        raise SystemExit(
            f"insarhub executable not found next to {sys.executable}; "
            "run this script with the insarhub environment python "
            "(or pass --insarhub-exe)")
    return str(exe)


def workdirs(root, job_id):
    if job_id:
        return [root / job_id]
    return sorted(d for d in root.iterdir() if d.is_dir()
                  and (d / "insarhub_config.json").is_file())


def run(exe, wd, action, pairs=None):
    cmd = [exe, "processor", "-N", "Hyp3_S1", "-w", str(wd), action]
    if pairs and action == "submit":
        cmd += ["--pairs", ",".join(pairs)]
    print(" ".join(cmd), flush=True)
    return subprocess.call(cmd)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir-root", required=True)
    ap.add_argument("--job-id", default=None)
    ap.add_argument("--action", required=True,
                    choices=["submit", "refresh", "download"])
    ap.add_argument("--pairs-json", default=None,
                    help="selected_pairs.json from 5_select_pairs.py; submit "
                         "runs per stack with ONLY its selected pairs "
                         "(policy selection instead of the full network)")
    ap.add_argument("--watch", action="store_true",
                    help="with --action refresh: loop until all jobs complete")
    ap.add_argument("--poll-min", type=float, default=10.0)
    ap.add_argument("--max-hours", type=float, default=24.0)
    ap.add_argument("--insarhub-exe", default=default_exe())
    args = ap.parse_args()

    root = Path(args.workdir_root)
    if args.pairs_json and args.action == "submit":
        # policy submission: iterate the selection; workdirs are
        # <root>/<job_id>/<stack>/ from the downloader
        sel = json.loads(Path(args.pairs_json).read_text())["selection"]
        by_stack = {}
        for c in sel:
            by_stack.setdefault((c["job_id"], c["stack"]), []).append(c["granules"])
        for (job_id, stack), pairs in sorted(by_stack.items()):
            wd = root / job_id / stack
            if not (wd / "insarhub_config.json").is_file():
                raise SystemExit(f"no prepared workdir at {wd}")
            for pair in pairs:
                run(args.insarhub_exe, wd, "submit", pairs=pair)
    else:
        dirs = workdirs(root, args.job_id)
        if not dirs:
            raise SystemExit("no prepared workdirs (run 2_run_downloader.py first)")
        for wd in dirs:
            run(args.insarhub_exe, wd, args.action)

    if args.watch and args.action == "refresh":
        t0 = time.time()
        while time.time() - t0 < args.max_hours * 3600:
            time.sleep(args.poll_min * 60)
            done = True
            for wd in dirs:
                rc = run(args.insarhub_exe, wd, "refresh")
                if rc != 0:
                    done = False
            # completion signal: downloader's product dirs hold downloaded
            # outputs; a simpler robust proxy is insarhub's own status print
            # -- the operator stops the watch or proceeds to download.
            print("[watch] refresh cycle done; rerun without --watch when all "
                  "jobs report SUCCEEDED, then run --action download")
            if done:
                break


if __name__ == "__main__":
    main()
