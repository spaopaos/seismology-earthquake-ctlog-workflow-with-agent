#!/usr/bin/env python3
"""Pre-delivery QA gate for InSAR coseismic products (agent responsibility).

Usage:
  python 8_qa_products.py --jobs insar_jobs.json \
    --workdir-root insar_work --selected selected_pairs.json \
    --region 99.938 100.088 26.18 26.36 \
    --qa-json insar_products_qa.json

Every check a user would perform by eye is automated here; the agent must
NOT deliver maps before this gate passes. Per pair:

  coverage    fraction of the map window with coherence >= coh-min
              (FAIL < 0.05: frame misses the study window or total
              decorrelation -- the p33_f507 trap; WARN < 0.30)
  epicenter   distance from the epicenter to the nearest valid pixel
              (FAIL > 10 km: no data where the science is)
  signal      max |LOS| within 10 km of the epicenter vs far-field
              (20-40 km ring) noise; SNR < 2 -> WARN
              (may be a genuine non-detection: report, do not fail)

Exit code 1 on any FAIL. WARN entries must be stated in the delivery.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parent


def load_m6():
    spec = importlib.util.spec_from_file_location(
        'm6', SKILL / '6_make_maps.py')
    m6 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m6)
    return m6


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jobs', required=True)
    ap.add_argument('--workdir-root', required=True)
    ap.add_argument('--selected', required=True)
    ap.add_argument('--region', nargs=4, type=float,
                    help='study-area map window: W E S N (lon lon lat lat)')
    ap.add_argument('--coh-min', type=float, default=0.3)
    ap.add_argument('--qa-json', default='insar_products_qa.json')
    args = ap.parse_args()

    m6 = load_m6()
    from rasterio.warp import transform as warp_transform

    root = Path(args.workdir_root)
    jobs = json.loads(Path(args.jobs).read_text())['jobs']
    ev = {e['event_id']: e for j in jobs for e in j['events']}
    sel = json.loads(Path(args.selected).read_text())['selection']

    # default window: the job AOI
    region = args.region
    results, n_fail = [], 0
    for s in sel:
        e = ev[s['event_id']]
        w = region or [s_ for s_ in ()] or [
            min(j['aoi'][0] for j in jobs if j['job_id'] == s['job_id']),
            max(j['aoi'][2] for j in jobs if j['job_id'] == s['job_id']),
            min(j['aoi'][1] for j in jobs if j['job_id'] == s['job_id']),
            max(j['aoi'][3] for j in jobs if j['job_id'] == s['job_id'])]
        pdir = m6.find_product_dir(root / s['job_id'] / s['stack'], s['granules'])
        if not pdir:
            results.append(dict(
                name=f"{s['job_id']}_{s['event_id']}_{s['stack']}",
                status='FAIL', reason='product not found/downloaded'))
            n_fail += 1
            print(f"{results[-1]['name']}: FAIL product not found/downloaded")
            continue
        d = m6.load_layers(pdir)
        disp = -d['unw'] * m6.LAMBDA_C / (4 * np.pi) * 1000.0
        valid = d['coh'] >= args.coh_min
        disp[~valid] = np.nan
        t, (h, wpx) = d['transform'], d['shape']

        def rc(lon, lat):
            xs, ys = warp_transform('EPSG:4326', d['crs'], [lon], [lat])
            x, y = xs[0], ys[0]
            col = (x - t.c) / t.a
            row = (y - t.f) / t.e
            return int(np.clip(row, 0, h - 1)), int(np.clip(col, 0, wpx - 1))

        r0, c0 = rc(region[0], region[3])
        r1, c1 = rc(region[1], region[2])
        r0, r1 = sorted((r0, r1))
        c0, c1 = sorted((c0, c1))
        win_valid = valid[r0:r1, c0:c1]
        coverage = float(win_valid.mean()) if win_valid.size else 0.0

        er, ec = rc(e['longitude'], e['latitude'])
        ex, ey = warp_transform('EPSG:4326', d['crs'],
                                [e['longitude']], [e['latitude']])
        px_size = abs(t.a)
        rows, cols = np.mgrid[max(er - 60, 0):er + 60, max(ec - 60, 0):ec + 60]
        near = valid[rows, cols]
        if near.any():
            dist_km = float(np.sqrt(((rows[near] - er) ** 2 + (cols[near] - ec) ** 2)
                                     ).min() * px_size / 1000.0)
        else:
            dist_km = float('inf')

        # signal: max |LOS| within 10 km; noise: 20-40 km ring
        rr, cc = np.mgrid[0:h:1, 0:wpx:1]
        dist_pix = np.sqrt((rr - er) ** 2 + (cc - ec) ** 2) * px_size / 1000.0
        sig_mask = (dist_pix <= 10) & valid
        far_mask = (dist_pix >= 20) & (dist_pix <= 40) & valid
        sig = float(np.nanmax(np.abs(disp[sig_mask]))) if sig_mask.any() else 0.0
        noise = float(np.nanstd(disp[far_mask])) if far_mask.any() else np.nan
        snr = sig / (2 * noise) if noise and noise > 0 else np.nan

        fails, warns = [], []
        if coverage < 0.05:
            fails.append(f'coverage {coverage:.2f}: frame misses the study '
                         'window (re-select next-ranked pair and resubmit)')
        elif coverage < 0.30:
            warns.append(f'coverage only {coverage:.2f}')
        if dist_km > 10 or not np.isfinite(dist_km):
            fails.append(f'no valid pixel within 10 km of epicenter '
                         f'(nearest {dist_km:.1f} km)')
        if np.isfinite(snr) and snr < 2:
            warns.append(f'SNR {snr:.1f}: no significant anomaly near '
                         'epicenter (possible genuine non-detection)')

        status = 'FAIL' if fails else ('WARN' if warns else 'PASS')
        n_fail += status == 'FAIL'
        results.append(dict(
            name=f"{s['job_id']}_{s['event_id']}_{s['stack']}",
            event_id=s['event_id'], direction=s['direction'],
            stack=s['stack'], pair=f"{s['d1']}->{s['d2']}",
            status=status, fails=fails, warns=warns,
            coverage_fraction=round(coverage, 3),
            nearest_valid_km=round(dist_km, 1) if np.isfinite(dist_km) else None,
            signal_mm=round(sig, 1), farfield_noise_mm=round(noise, 1)
            if np.isfinite(noise) else None, snr=round(snr, 1)
            if np.isfinite(snr) else None))
        print(f"{results[-1]['name']}: {status} cov={coverage:.2f} "
              f"nearest={dist_km:.1f}km sig={sig:.1f}mm snr={snr if np.isfinite(snr) else float('nan'):.1f}"
              + (' ' + '; '.join(fails + warns) if fails or warns else ''))

    doc = dict(gate='pre-delivery QA (agent responsibility; user reviews '
                    'science only)', region=region,
               thresholds=dict(coverage_fail=0.05, coverage_warn=0.30,
                               epicenter_km_fail=10, snr_warn=2),
               results=results,
               verdict='FAIL' if n_fail else 'PASS')
    Path(args.qa_json).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
    print(f"\nverdict: {doc['verdict']} -> {args.qa_json}")
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
