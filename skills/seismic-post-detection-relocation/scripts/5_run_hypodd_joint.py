#!/usr/bin/env python3
"""Generate hypoDD.inp for IDAT=3 joint solve, then run (optionally with DAMP scan).

Usage:
  # Single run (uses DAMP from --damp or default 400):
  python 5_run_hypodd_joint.py \\
    --indir output/joint/input \\
    --outdir output/joint/output \\
    --hypodd-bin /path/to/hypoDD \\
    --vp-model velocity_p.cre --vs-model velocity_s.cre --ratio 1.7092 \\
    --damp 400

  # DAMP scan (generates configs, runs all in parallel):
  python 5_run_hypodd_joint.py ... --damp-scan 50,100,200,400,800

  # Then select best DAMP and rerun with --damp <best>

Velocity model: layered .cre files (2 columns: vp/vs km/s, depth_top_km,
header line skipped). TOP/VELP come from the P model; RAT per layer is
vp_i/vs_i (constant --ratio fallback if layer counts mismatch).
"""
import argparse
import os
import subprocess
from pathlib import Path


def load_layers(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "*", "%")):
            continue
        parts = line.replace(",", " ").split()
        try:
            v, d = float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            continue
        rows.append((d, v))
    return sorted(rows)


def model_lines(vp_path, vs_path, ratio):
    vp = load_layers(vp_path)
    top = " ".join("%.2f" % d for d, _ in vp) + " -9"
    velp = " ".join("%.2f" % v for _, v in vp) + " -9"
    if vs_path:
        vs = load_layers(vs_path)
        if len(vs) == len(vp) and all(abs(dp - ds) < 1e-6 for (dp, _), (ds, _) in zip(vp, vs)):
            rat = " ".join("%.6f" % (a / b) for (_, a), (_, b) in zip(vp, vs)) + " -9"
        else:
            rat = ("%.6f " % ratio) * len(vp) + "-9"
    else:
        rat = ("%.6f " % ratio) * len(vp) + "-9"
    return top, velp, rat


TEMPLATE = """hypoDD_2
* joint ct+cc solve (IDAT=3)
* cross-correlation differential times:
{indir}/dt.cc
* catalog differential times:
{indir}/dt.ct
* events:
{indir}/event.dat
* stations:
{indir}/station.dat
* original locations:
{outdir}/hypoDD.loc
* relocations:
{outdir}/hypoDD.reloc
* station information:
{outdir}/hypoDD.sta
* residuals:
{outdir}/hypoDD.res
* source parameters:
{outdir}/hypoDD.src
* IDAT IPHA DIST
  3 3 100.0
* OBSCC OBSCT MINDS MAXDS MAXGAP
  4 6 -999 -999 -999
* ISTART ISOLV IAQ NSET
  2 2 1 4
* NITER WTCCP WTCCS WRCC WDCC WTCTP WTCTS WRCT WDCT DAMP
  4 1.0 0.5 -9 -9 1.0 0.5 6 5 {damp}.0
  8 1.0 0.5 -9 -9 1.0 0.4 4 4 {damp}.0
  12 1.0 0.5 4 4 1.0 0.4 4 4 {damp}.0
  16 1.0 0.5 3 2 1.0 0.3 3 2 {damp}.0
* IMOD
1
* TOP (km), terminated by -9
  {top}
* VELP (km/s), terminated by -9
  {velp}
* RAT (Vp/Vs), terminated by -9
  {rat}
* CID
0
* ID
"""


def write_inp(path, indir, outdir, damp, top, velp, rat):
    text = TEMPLATE.format(indir=indir, outdir=outdir, damp=int(damp),
                           top=top, velp=velp, rat=rat)
    path.write_text(text, newline="\n")  # LF endings, no CRLF


def run_hypodd(inp_path, hypodd_bin, log_path):
    subprocess.check_call(
        [str(hypodd_bin), inp_path.name],
        cwd=str(inp_path.parent),
        stdout=open(log_path, "w"), stderr=subprocess.STDOUT)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--indir", required=True, help="input dir with event.dat, dt.ct, dt.cc")
    ap.add_argument("--outdir", required=True, help="output dir for hypoDD results")
    ap.add_argument("--hypodd-bin", required=True, help="path to hypoDD binary")
    ap.add_argument("--vp-model", required=True, help="layered P model (.cre)")
    ap.add_argument("--vs-model", default=None, help="layered S model (.cre)")
    ap.add_argument("--ratio", type=float, default=1.7,
                    help="constant Vp/Vs fallback for RAT")
    ap.add_argument("--damp", type=float, default=400, help="damping value")
    ap.add_argument("--damp-scan", default=None,
                    help="comma-separated DAMP values, e.g. 50,100,200,400,800")
    args = ap.parse_args()

    indir = Path(args.indir).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    hypodd_bin = Path(args.hypodd_bin).resolve()
    top, velp, rat = model_lines(args.vp_model, args.vs_model, args.ratio)

    if args.damp_scan:
        # Parallel DAMP scan
        damps = [float(d) for d in args.damp_scan.split(",")]
        procs = []
        for d in damps:
            sub_out = outdir.parent / f"output_d{int(d)}"
            sub_out.mkdir(parents=True, exist_ok=True)
            inp = outdir.parent / f"hypoDD_d{int(d)}.inp"
            write_inp(inp, indir, sub_out, d, top, velp, rat)
            log = outdir.parent / f"damp_d{int(d)}.log"
            procs.append((d, inp,
                          subprocess.Popen(
                              [str(hypodd_bin), inp.name],
                              cwd=str(inp.parent),
                              stdout=open(log, "w"),
                              stderr=subprocess.STDOUT)))
        for d, inp, proc in procs:
            proc.wait()
            n = len((outdir.parent / f"output_d{int(d)}" / "hypoDD.reloc")
                    .read_text().splitlines())
            print(f"DAMP={int(d)}: {n} events")
        print("\nDAMP scan complete. Compare solutions and select optimal DAMP,")
        print("then rerun with --damp <best> for final solve.")
    else:
        # Single run
        inp = outdir / "hypoDD.inp"
        write_inp(inp, indir, outdir, args.damp, top, velp, rat)
        log = outdir / "hypoDD.log"
        run_hypodd(inp, hypodd_bin, log)
        n = len((outdir / "hypoDD.reloc").read_text().splitlines())
        print(f"DAMP={int(args.damp)}: {n} events relocated")
        print(f"Output: {outdir / 'hypoDD.reloc'}")


if __name__ == "__main__":
    main()
