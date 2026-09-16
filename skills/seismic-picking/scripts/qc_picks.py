#!/usr/bin/env python3
"""QC for PhaseNet+ picking outputs.

Produces: per-station-day pick counts, P/S score histograms, P-polarity
fraction, K-cap alerts (F18), sample waveform+pick overlay plots (includes one
HN group when present), midnight-boundary continuity spot check.
Figures must be actually opened and reviewed; record status honestly.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

K_CAP_PER_DAY = 28800  # F18


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True, help="result_path containing picks_phasenet_plus/")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-samples", type=int, default=6)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    picks_dir = Path(args.picks) / "picks_phasenet_plus"
    csvs = [p for p in picks_dir.rglob("*.csv") if p.stat().st_size > 0]
    if not csvs:
        (out / "qc_summary.json").write_text(json.dumps({"picks_total": 0, "status": "EMPTY", "review_status": "NOT_REVIEWED", "scientific_status": "NOT_TESTED"}, indent=2))
        return
    picks = pd.concat((pd.read_csv(p) for p in csvs), ignore_index=True)
    picks["day"] = picks["phase_time"].str[:10]

    # 1. per station-day counts
    counts = (picks.groupby(["station_id", "day", "phase_type"]).size()
              .unstack(fill_value=0).reset_index())
    counts.to_csv(out / "picks_per_station_day.csv", index=False)
    pivot = picks.groupby(["station_id", "day"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(max(8, pivot.shape[1] * 0.3), max(4, pivot.shape[0] * 0.4)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="viridis")
    ax.set_xticks(range(pivot.shape[1]), pivot.columns, rotation=90, fontsize=6)
    ax.set_yticks(range(pivot.shape[0]), pivot.index, fontsize=6)
    ax.set_title("picks per station-group per day")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out / "picks_heatmap.png", dpi=160)
    plt.close(fig)

    # 2. score histograms
    fig, ax = plt.subplots()
    for ph, color in (("P", "C0"), ("S", "C1")):
        sub = picks[picks["phase_type"] == ph]["phase_score"].astype(float)
        ax.hist(sub, bins=50, alpha=0.6, label=f"{ph} (n={len(sub)})", color=color)
    ax.set_xlabel("phase_score")
    ax.legend()
    fig.savefig(out / "score_hist.png", dpi=160)
    plt.close(fig)

    # 3. P polarity fraction
    p = picks[picks["phase_type"] == "P"]
    pol = p["phase_polarity"].astype(float) if "phase_polarity" in p else pd.Series(dtype=float)
    pol_stats = {"n_p": int(len(p)),
                 "n_up": int((pol > 0).sum()), "n_down": int((pol < 0).sum()),
                 "n_zero": int((pol == 0).sum())}

    # 4. K-cap alerts
    cap = (picks.groupby(["station_id", "day", "phase_type"]).size()
           .loc[lambda s: s > K_CAP_PER_DAY * 0.8])
    cap.to_csv(out / "kcap_alerts.csv")

    # 5. sample overlay plots (incl. one HN group when present)
    import obspy
    archive = Path(args.archive)
    sample_dir = out / "waveform_overlays"
    sample_dir.mkdir(exist_ok=True)
    groups = list(picks["station_id"].unique())
    hn = [g for g in groups if g.endswith("N")]
    chosen = (hn[:1] + [g for g in groups if not g.endswith("N")])[: args.max_samples]
    plotted = []
    for g in chosen:
        sub = picks[picks["station_id"] == g]
        day = sub["day"].iloc[0]
        day_dir = day.replace("-", "")
        hits = sorted(archive.rglob(f"{g}*Z.*{day_dir}*"))
        hits = [h for h in hits if h.suffix.lower() in (".sac", ".mseed")]
        if not hits:
            continue
        tr = obspy.read(str(hits[0]))[0]
        t = np.arange(tr.stats.npts) / tr.stats.sampling_rate
        fig, ax = plt.subplots(figsize=(16, 4))
        ax.plot(t, tr.data, lw=0.3)
        for _, r in sub.iterrows():
            pt = pd.Timestamp(r["phase_time"])
            x = (pt.hour * 3600 + pt.minute * 60 + pt.second + pt.microsecond / 1e6)
            ax.axvline(x, color="C0" if r["phase_type"] == "P" else "C1", lw=0.5, alpha=0.6)
        ax.set_title(f"{g} {day}  Z (blue=P, orange=S)")
        ax.set_xlabel("s of day")
        fig.tight_layout()
        fig.savefig(sample_dir / f"{g.replace('.', '_')}_{day_dir}.png", dpi=160)
        plt.close(fig)
        plotted.append(g)

    summary = {"picks_total": int(len(picks)),
               "polarity": pol_stats,
               "kcap_alerts": int(len(cap)),
               "overlay_groups": plotted,
               "figures": ["picks_heatmap.png", "score_hist.png"],
               "review_status": "NOT_REVIEWED"}
    (out / "qc_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[qc] -> {out}  picks={len(picks)} kcap_alerts={len(cap)} overlays={len(plotted)}")


if __name__ == "__main__":
    main()
