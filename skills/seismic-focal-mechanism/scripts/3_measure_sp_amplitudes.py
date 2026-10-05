#!/usr/bin/env python3
"""Measure S/P amplitude inputs for SKHASH ($ampfile, skhash format).

Usage:
  python 3_measure_sp_amplitudes.py --wf-root event_wf --out IN/amp.csv

Measurement conventions (Eryuan defaults):
  noise     : [P-5, P-1] s, Z and max(|N|,|E|)
  amp_p     : [P+0.02, P+1.0] s, max |Z|
  amp_s     : [S+0.02, S+1.0] s, max(|N|,|E|)
SNR gating (ratmin) and the ratio are computed by SKHASH; only the four raw
amplitude columns are delivered here. Only P_S pairs with usable_frac==1
(entire window inside usable intervals) are measured.
"""
import argparse
import os
import numpy as np
import pandas as pd
from obspy import read


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wf-root", required=True,
                    help="event waveform library (from 2_cut_event_waveforms.py)")
    ap.add_argument("--manifest", default=None,
                    help="manifest CSV (default <wf-root>/event_station_manifest.csv)")
    ap.add_argument("--out", required=True, help="output amp.csv path")
    ap.add_argument("--noise-pre-s", type=float, default=5.0)
    ap.add_argument("--noise-end-s", type=float, default=1.0)
    ap.add_argument("--sig-lag-s", type=float, default=0.02)
    ap.add_argument("--sig-len-s", type=float, default=1.0)
    args = ap.parse_args()

    wf = args.wf_root
    man_path = args.manifest or os.path.join(wf, "event_station_manifest.csv")
    man = pd.read_csv(man_path)
    sel = man[(man["phase_pair"] == "P_S") & (man["usable_frac"] >= 0.9999)
              & (~man["warn_s_before_p"])].copy()
    print(f"candidate P_S pairs: {len(sel)} of {len(man)}")

    rows = []
    for i, (_, r) in enumerate(sel.iterrows()):
        out = measure_row(r, wf, args)
        if out is not None:
            rows.append(out)
        if (i + 1) % 2000 == 0:
            print("  %d/%d" % (i + 1, len(sel)), flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"written: {args.out} {len(df)} rows")
    if len(df):
        print(df[["snr_p", "snr_s", "sp_ratio_raw"]].describe().to_string())
        print("snr_p>=3 & snr_s>=3:",
              int(((df["snr_p"] >= 3) & (df["snr_s"] >= 3)).sum()))


def measure_row(r, wf, args):
    sr = 100.0
    ws = pd.Timestamp(r["window_start_utc"]).value / 1e9

    def idx(t):
        return int(round((pd.Timestamp(t).value / 1e9 - ws) * sr))

    tP, tS = pd.Timestamp(r["p_time_utc"]), pd.Timestamp(r["s_time_utc"])
    trs = {}
    for comp, f in (("Z", r["file_Z"]), ("N", r["file_N"]), ("E", r["file_E"])):
        tr = read(os.path.join(wf, f), format="SAC")[0]
        trs[comp] = np.asarray(tr.data)
    n0, n1 = idx(tP) - int(args.noise_pre_s * sr), idx(tP) - int(args.noise_end_s * sr)
    p0, p1 = idx(tP) + int(args.sig_lag_s * sr), idx(tP) + int(args.sig_len_s * sr)
    s0, s1 = idx(tS) + int(args.sig_lag_s * sr), idx(tS) + int(args.sig_len_s * sr)
    n = len(trs["Z"])
    for a, b in ((n0, n1), (p0, p1), (s0, s1)):
        if a < 0 or b > n:
            return None
    noise_p = float(np.abs(trs["Z"][n0:n1]).max())
    noise_s = float(max(np.abs(trs["N"][n0:n1]).max(), np.abs(trs["E"][n0:n1]).max()))
    amp_p = float(np.abs(trs["Z"][p0:p1]).max())
    amp_s = float(max(np.abs(trs["N"][s0:s1]).max(), np.abs(trs["E"][s0:s1]).max()))
    if not all(np.isfinite([noise_p, noise_s, amp_p, amp_s])):
        return None
    if noise_p <= 0 or noise_s <= 0 or amp_p <= 0 or amp_s <= 0:
        return None
    net, sta, loc, fam = str(r["station_id"]).split(".")
    return {
        "event_id": r["event_id"],
        "network": net, "station": sta, "location": loc, "channel": fam,
        "noise_p": noise_p, "noise_s": noise_s, "amp_p": amp_p, "amp_s": amp_s,
        "snr_p": amp_p / noise_p, "snr_s": amp_s / noise_s,
        "sp_ratio_raw": amp_s / amp_p,
        "polarity_score_p": r.get("polarity_score_p"),
        "usable_frac": r["usable_frac"],
        "s_minus_p_s": r["s_minus_p_s"],
        "file_Z": r["file_Z"],
    }


if __name__ == "__main__":
    main()
