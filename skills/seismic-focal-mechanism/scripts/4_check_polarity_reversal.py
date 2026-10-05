#!/usr/bin/env python3
"""Cross-validate colocated stations' P polarity; flag systematically reversed groups.

Usage:
  python 4_check_polarity_reversal.py \
    --assignments association/gamma_assignments.csv \
    --stations association_inputs/gamma_stations.csv \
    --polagree OUT/out_polagree.csv \
    --out-json colocated_polarity_check.json

Method:
  For each colocated pair (dual instrument families at the same NET.STA, or
  cross-station pairs within 1 km), take common events where BOTH sides have
  |polarity_score| >= threshold and count sign agreement. Agreement clearly
  below 50% marks a reversed pair; the reversed side is the one with lower
  agreement against the mechanisms (out_polagree pol_accuracy, from a prior
  no-reversal SKHASH run -- pass --polagree to enable arbitration).

  Acceptance gate for the final list (SKILL.md step 4): reversal must RAISE
  the mechanism-agreement rate above 60%. Present the evidence table to the
  user for confirmation before writing reverse.csv.
"""
import argparse
import json
from math import radians, sin, cos, asin, sqrt

import numpy as np
import pandas as pd

try:
    from scipy.stats import binomtest
    def binom_p(k, n):
        return binomtest(k, n, 0.5).pvalue
except ImportError:
    from math import erf, sqrt as msqrt
    def binom_p(k, n):
        z = (k - n / 2) / msqrt(n / 4)
        return max(1e-10, 2 * (1 - 0.5 * (1 + erf(abs(z) / msqrt(2)))))


def hav(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assignments", required=True)
    ap.add_argument("--stations", required=True)
    ap.add_argument("--polagree", default=None,
                    help="out_polagree.csv from a prior no-reversal SKHASH run "
                         "(enables which-side arbitration)")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--conf", type=float, default=0.3,
                    help="both sides' |polarity_score| lower bound")
    ap.add_argument("--min-n", type=int, default=15,
                    help="minimum common events per pair")
    ap.add_argument("--dist-km", type=float, default=1.0,
                    help="colocation distance for cross-station pairs")
    ap.add_argument("--acc-gate", type=float, default=55.0,
                    help="reversed side must have mechanism agreement below this (%)")
    args = ap.parse_args()

    asg = pd.read_csv(args.assignments, dtype={"station_id": str},
                      usecols=["event_id", "station_id", "phase_type",
                               "polarity_score"])
    p = asg[asg["phase_type"] == "P"].copy()
    p["abs"] = p["polarity_score"].abs()
    p = (p[p["abs"] >= args.conf]
         .sort_values("abs", ascending=False)
         .drop_duplicates(["event_id", "station_id"], keep="first"))

    sta = pd.read_csv(args.stations)
    sta["net_sta"] = sta["id"].str.split(".").str[:2].str.join(".")

    pairs = []
    for _, g in sta.groupby("net_sta"):
        ids = sorted(g["id"])
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append((ids[i], ids[j], "same_site_dual"))
    for i in range(len(sta)):
        for j in range(i + 1, len(sta)):
            a, b = sta.iloc[i], sta.iloc[j]
            if a["net_sta"] == b["net_sta"]:
                continue
            if hav(a.latitude, a.longitude, b.latitude, b.longitude) <= args.dist_km:
                a_id, b_id = sorted([a["id"], b["id"]])
                pairs.append((a_id, b_id, "colocated_1km"))

    pol_wide = p.pivot(index="event_id", columns="station_id",
                       values="polarity_score")

    acc = {}
    if args.polagree:
        pa = pd.read_csv(args.polagree)
        pa = pa[pa["source"] == "dl_p"]
        acc = dict(zip(pa["sta_code"], pa["pol_accuracy"]))

    def get_acc(gid):
        net, s, loc, fam = gid.split(".")
        return acc.get(gid, acc.get("%s.%s.%d.%s" % (net, s, int(loc), fam), np.nan))

    rows = []
    for a_id, b_id, kind in pairs:
        if a_id not in pol_wide.columns or b_id not in pol_wide.columns:
            continue
        both = pol_wide[[a_id, b_id]].dropna()
        n = len(both)
        if n < args.min_n:
            continue
        agree = int((np.sign(both[a_id]) == np.sign(both[b_id])).sum())
        frac = agree / n
        rows.append({
            "station_a": a_id, "station_b": b_id, "kind": kind,
            "n_common": n, "agree": agree, "agree_frac": round(frac, 3),
            "binom_p": round(binom_p(agree, n), 6),
            "acc_a_vs_mech": get_acc(a_id), "acc_b_vs_mech": get_acc(b_id),
            "anti": bool(frac < 0.5 and binom_p(agree, n) < 0.05),
        })
    res = pd.DataFrame(rows).sort_values("agree_frac")
    print(res.to_string(index=False))

    flipped = set()
    if args.polagree:
        for _, r in res[res["anti"]].iterrows():
            aa, ab = r["acc_a_vs_mech"], r["acc_b_vs_mech"]
            if pd.isna(aa) or pd.isna(ab):
                continue
            if aa < ab and aa < args.acc_gate:
                flipped.add(r["station_a"])
            elif ab < aa and ab < args.acc_gate:
                flipped.add(r["station_b"])

    print("\nreversed groups (candidates):", sorted(flipped))
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"confidence_threshold": args.conf,
                   "min_common_events": args.min_n,
                   "pairs_checked": res.to_dict("records"),
                   "flipped_groups": sorted(flipped),
                   "note": "Confirm with user, apply the >60% post-reversal "
                           "agreement gate, then write reverse.csv (times "
                           "timezone-aware) before rerunning SKHASH."},
                  f, ensure_ascii=False, indent=2)
    print("saved:", args.out_json)


if __name__ == "__main__":
    main()
