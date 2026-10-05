#!/usr/bin/env python3
"""Generate the SKHASH control file and run SKHASH v1.1.

Usage:
  python 5_run_skhash.py --in-dir IN --out-dir OUT \
    [--skhash-root knowledge/repos/SKHASH] \
    [--threshold 0.3] [--reverse-file IN/reverse.csv] [--num-cpus 8]

Defaults follow the Eryuan (Dali, Yunnan) run; region-dependent values
(velocity model via IN/vmodel_layers.txt, polarity threshold, reversal list,
delmax) must be user-confirmed — see SKILL.md step 5.
"""
import argparse
import subprocess
import sys
from pathlib import Path

TEMPLATE = """\\
$dlpfile
{in_dir}/pol_dl.csv

$catfile
{in_dir}/catalog.csv

$stfile
{in_dir}/stations.csv

$ampfile
{in_dir}/amp.csv
{plfile_block}
$vmodel_paths
{in_dir}/vmodel_layers.txt

$outfile1
{out_dir}/out.csv

$outfile2
{out_dir}/out_planes.csv

$outfile_pol_agree
{out_dir}/out_polagree.csv

$outfile_pol_info
{out_dir}/out_polinfo.csv

$ratmin
{ratmin}

$min_polarity_weight
{threshold}

$badfrac
{badfrac}

$badmin
{badmin}

$npolmin
{npolmin}

$nmc
{nmc}

$maxout
{maxout}

$dang
{dang}

$perturb_epicentral_location
True

$azmax
{azmax}

$delmax
{delmax}

$num_cpus
{num_cpus}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-dir", required=True,
                    help="IN/ from 1_build_inputs.py + amp.csv from 3_measure")
    ap.add_argument("--out-dir", required=True, help="SKHASH output directory")
    ap.add_argument("--skhash-root", default=None,
                    help="SKHASH checkout (default: knowledge/repos/SKHASH "
                         "next to this skill's repo root)")
    ap.add_argument("--threshold", type=float, default=0.3,
                    help="min_polarity_weight (region-dependent, user-confirmed)")
    ap.add_argument("--reverse-file", default=None,
                    help="polarity reversal CSV; REQUIRED timezone-aware times "
                         "(e.g. 2025-03-01T00:00:00+00:00) — pandas 3 rejects "
                         "naive/aware mixes")
    ap.add_argument("--ratmin", type=float, default=2)
    ap.add_argument("--badfrac", type=float, default=0.1)
    ap.add_argument("--badmin", type=int, default=2)
    ap.add_argument("--npolmin", type=int, default=8)
    ap.add_argument("--nmc", type=int, default=30)
    ap.add_argument("--maxout", type=int, default=500)
    ap.add_argument("--dang", type=int, default=5)
    ap.add_argument("--azmax", type=int, default=10)
    ap.add_argument("--delmax", type=int, default=120,
                    help="max epicentral distance km (region-dependent)")
    ap.add_argument("--num-cpus", type=int, default=8)
    args = ap.parse_args()

    in_dir = Path(args.in_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    root = Path(args.skhash_root).resolve() if args.skhash_root else \
        Path(__file__).resolve().parents[3] / "knowledge/repos/SKHASH"
    skhash_py = root / "src/SKHASH/SKHASH.py"
    if not skhash_py.is_file():
        raise FileNotFoundError(f"SKHASH not found at {root}; pass --skhash-root")

    if args.reverse_file:
        # trailing newline keeps a blank line before $vmodel_paths, matching
        # the blank-line block separation SKHASH controls use
        plfile_block = "$plfile\n%s\n" % Path(args.reverse_file).resolve()
    else:
        plfile_block = ""

    control = TEMPLATE.format(
        in_dir=in_dir, out_dir=out_dir, plfile_block=plfile_block,
        ratmin=args.ratmin, threshold=args.threshold, badfrac=args.badfrac,
        badmin=args.badmin, npolmin=args.npolmin, nmc=args.nmc,
        maxout=args.maxout, dang=args.dang, azmax=args.azmax,
        delmax=args.delmax, num_cpus=args.num_cpus)
    ctl = out_dir.parent / "control.txt"
    ctl.write_text(control, newline="\n")  # LF endings
    print(f"control file: {ctl}")

    log = (out_dir.parent / "skhash_run.log").open("w")
    print(f"running SKHASH: {skhash_py} control.txt", flush=True)
    result = subprocess.run([sys.executable, str(skhash_py), ctl.name],
                            cwd=str(ctl.parent), stdout=log,
                            stderr=subprocess.STDOUT)
    log.close()
    if result.returncode != 0:
        raise SystemExit(f"SKHASH failed (exit {result.returncode}); "
                         f"see {out_dir.parent / 'skhash_run.log'}")
    n = len(pd_count(out_dir / "out.csv"))
    print(f"SKHASH done: {n} solutions -> {out_dir / 'out.csv'}")


def pd_count(path):
    import pandas as pd
    return pd.read_csv(path)


if __name__ == "__main__":
    main()
