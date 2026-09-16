#!/usr/bin/env python3
"""Location products -> ph2dt inputs (R1: the ONLY permitted converter).

Reads hyp_catalog.csv (HYPOINVERSE located) + gamma_picks.csv (association)
and writes ph2dt's phase.dat / station.dat:
  event header: # YYYY M D H M SS.SS  lat lon dep mag 0.00 0.00 0.00  evid
  phase line:   STA + 6sp + tt(6.3f, travel time from origin) + 2sp + wt(6.3f) + 3sp + P/S
  station.dat:  STA lat lon  (decimal degrees)
Format follows the palm production template (input/phase.dat sample verified
2026-09-11). Hard assertions throughout.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from contract_io import product_path
from station_identity import native_mapping, save_mapping


def prob_to_weight(p):
    """prob -> continuous weight matching WET 1/.5/.2/.1 codes (0..3)."""
    if p >= 0.5:
        return 1.0
    if p >= 0.4:
        return 0.5
    if p >= 0.3:
        return 0.2
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--location-dir", required=True, help="location_output_v2 (hyp_catalog.csv)")
    ap.add_argument("--assoc-dir", required=True)
    ap.add_argument("--stations", required=True, help="sta lon lat elev (whitespace)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "input").mkdir(parents=True, exist_ok=True)

    cat = pd.read_csv(product_path(args.location_dir, "location", "outputs.catalog_path"))
    picks = pd.read_csv(product_path(args.assoc_dir, "association", "outputs.assignments_path"), parse_dates=["phase_time"])
    picks["phase_time"] = pd.to_datetime(picks["phase_time"], utc=True)
    picks = picks[picks["event_index"] >= 0]

    group_alias, aliases = native_mapping(args.stations, picks.station_id.unique())
    save_mapping(out / "input/station_aliases.json", aliases)
    n_lines = 0
    with open(out / "input" / "phase.dat", "w") as fout:
        for _, e in cat.iterrows():
            eid = int(str(e["event_id"]).replace("gm", ""))
            ot = pd.to_datetime(e["date"] + " " + str(e["sec"]), format="%Y/%m/%d %H:%M %S.%f", errors="coerce")
            if pd.isna(ot):  # date like 2026/01/01 07:23 + sec 43.8
                d, t = e["date"].split()
                ot = pd.to_datetime(f"{d} {t}", format="%Y/%m/%d %H:%M") + pd.Timedelta(seconds=float(e["sec"]))
            ot = ot.tz_localize("UTC") if ot.tzinfo is None else ot.tz_convert("UTC")
            fout.write(
                f"# {ot.year:4d} {ot.month:2d} {ot.day:2d} {ot.hour:2d} {ot.minute:2d} "
                f"{ot.second + ot.microsecond / 1e6:5.2f}  {e['latitude_hyp']:7.4f} "
                f"{e['longitude_hyp']:9.4f}  {e['depth_km_hyp']:6.2f} {0.0:4.2f}  "
                f"0.00  0.00  0.00  {eid:>9}\n"
            )
            sub = picks[picks["event_index"] == eid]
            # 同站台多仪器组（HH/HN）折叠到站级：ph2dt/HypoDD 假设每站每震相一条观测；
            # 保留 prob 最高者（旧 pipeline 同样 fold NET.STA.LOC.CHAN -> NET.STA）
            sub = (sub.assign(_sta=sub["station_id"].map(group_alias))
                      .sort_values("phase_score")
                      .groupby(["_sta", "phase_type"], as_index=False)
                      .last())
            for _, pk in sub.iterrows():
                sta = pk["_sta"]
                tt = (pk["phase_time"] - ot).total_seconds()
                assert -600 < tt < 600, f"travel time {tt}s out of range (event {eid})"
                wt = prob_to_weight(float(pk["phase_score"]))
                if wt == 0.0:
                    continue
                fout.write(f"{sta:<5}{' ' * 6}{tt:6.3f}  {wt:6.3f}   {pk['phase_type']}\n")
                n_lines += 1

    stations = sorted(aliases)
    with open(out / "input" / "station.dat", "w") as f:
        for alias in stations:
            c = aliases[alias]["coordinates"]
            f.write(f"{alias} {c['latitude']} {c['longitude']}\n")

    (out / "input" / "conversion_meta.json").write_text(json.dumps({
        "n_events": len(cat), "n_phase_lines": n_lines,
        "converter_sha256": __import__("hashlib").sha256(
            Path(__file__).read_bytes()).hexdigest()}, indent=2))
    print(f"phase.dat: {len(cat)} events, {n_lines} phase lines; stations: {len(stations)}")


if __name__ == "__main__":
    main()
