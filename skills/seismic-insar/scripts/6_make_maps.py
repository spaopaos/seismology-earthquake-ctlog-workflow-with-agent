#!/usr/bin/env python3
"""Turn HyP3 INSAR_GAMMA products into LOS deformation maps.

Usage:
  python 6_make_maps.py --jobs insar_jobs.json \
    --workdir-root insar_work --selected selected_pairs.json \
    --outdir maps

Per selected pair: locates the downloaded product zip (extracting it if
needed), reads unw_phase / corr / dem GeoTIFFs, converts phase to LOS
displacement (d = -phase * lambda / 4pi in mm, positive = motion TOWARD
the satellite; lambda = 0.0554658 m C-band), masks low coherence, and
writes a displacement GeoTIFF plus a PNG: displacement over a DEM hillshade
with coherence contour, event epicenter marked, title carrying
event/stack/dates/quality. Intermediates (zip + extracted dir) stay in
place for review.
"""
import argparse
import json
import re
import zipfile
from pathlib import Path

import numpy as np

LAMBDA_C = 0.0554658  # Sentinel-1 C-band wavelength, m


def find_product_dir(stack_dir, granules):
    """Locate (and extract if needed) the product dir for this pair."""
    dates = sorted(re.search(r'_(\d{8})T', g).group(1) for g in granules)
    cands = [d for d in stack_dir.rglob('extracted/*')
             if d.is_dir() and dates[0] in d.name and dates[1] in d.name]
    if cands:
        return sorted(cands)[0]
    for z in sorted(stack_dir.rglob('*.zip')):
        if dates[0] in z.name and dates[1] in z.name:
            dest = z.parent / 'extracted' / z.stem
            if not dest.exists():
                dest.mkdir(parents=True)
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(dest)
            inner = [d for d in dest.iterdir() if d.is_dir()]
            return (inner[0] if inner else dest)
    return None


def layer(pdir, suffix):
    hits = sorted(pdir.rglob(f'*{suffix}.tif'))
    return hits[0] if hits else None


def load_layers(pdir):
    import rasterio
    out = {}
    with rasterio.open(layer(pdir, 'unw_phase')) as src:
        out['unw'] = src.read(1).astype(float)
        out['transform'] = src.transform
        out['crs'] = src.crs
        out['shape'] = (src.height, src.width)
    with rasterio.open(layer(pdir, 'corr')) as src:
        out['coh'] = src.read(1).astype(float)
    h = layer(pdir, 'dem')
    if h:
        with rasterio.open(h) as src:
            out['hgt'] = src.read(1).astype(float)
    return out


def shade(h):
    gy, gx = np.gradient(np.nan_to_num(h))
    g = np.sqrt(gy**2 + gx**2)
    return np.clip(1 - (gx * np.cos(np.deg2rad(315))
                        + gy * np.sin(np.deg2rad(315))) / (g + 1e-6) * 0.5, 0, 1)


def process_pair(sel, root, outdir, coh_min, crop_km):
    stack_dir = root / sel['job_id'] / sel['stack']
    pdir = find_product_dir(stack_dir, sel['granules'])
    if not pdir:
        return None, 'no product zip found'
    d = load_layers(pdir)
    disp_mm = -d['unw'] * LAMBDA_C / (4 * np.pi) * 1000.0
    disp_mm[~(d['coh'] >= coh_min)] = np.nan

    # products are projected (typically UTM, metres): warp the event into
    # the product CRS and crop a readable window around the epicenter
    from rasterio.warp import transform as warp_transform
    ex, ey = warp_transform('EPSG:4326', d['crs'],
                            [sel_event_lon(sel)], [sel_event_lat(sel)])
    ex, ey = ex[0], ey[0]
    t = d['transform']
    h, w = d['shape']
    px = abs(t.a)
    r0 = max(int((ey + crop_km * 1000 - t.f) / t.e), 0)
    r1 = min(int((ey - crop_km * 1000 - t.f) / t.e), h)
    c0 = max(int((ex - crop_km * 1000 - t.c) / t.a), 0)
    c1 = min(int((ex + crop_km * 1000 - t.c) / t.a), w)
    if r1 <= r0 or c1 <= c0:  # event outside footprint; keep full frame
        r0, r1, c0, c1 = 0, h, 0, w
    win = (r0, r1, c0, c1)
    disp = disp_mm[r0:r1, c0:c1]
    coh = d['coh'][r0:r1, c0:c1]
    hgt = d.get('hgt')
    base = shade(hgt[r0:r1, c0:c1] if hgt is not None
                 else np.zeros_like(disp))
    xs = (t.c + t.a * (np.arange(c0, c1) + 0.5) - ex) / 1000.0  # km rel. event
    ys = (t.f + t.e * (np.arange(r0, r1) + 0.5) - ey) / 1000.0
    lon2d, lat2d = np.meshgrid(xs, ys)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    lim = np.nanpercentile(np.abs(disp), 99) or 30.0
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
    ax.pcolormesh(lon2d, lat2d, base, cmap='gray', vmin=0, vmax=1, shading='auto')
    im = ax.pcolormesh(lon2d, lat2d, disp, cmap='RdBu', vmin=-lim, vmax=lim,
                       shading='auto')
    try:
        ax.contour(lon2d, lat2d, coh, levels=[coh_min], colors='k',
                   linewidths=0.4, linestyles='--')
    except Exception:
        pass
    ax.plot(0, 0, 'k*', ms=18, mec='w')
    plt.colorbar(im, ax=ax, label='LOS displacement (mm; + toward satellite)')
    ax.set_title(f"{sel['event_id']} ML{sel['ml']:.2f} {sel['event_time'][:10]}  "
                 f"{sel['stack']} {sel['direction']}  "
                 f"{sel['d1']}->{sel['d2']} ({sel['dt_days']}d)  [{sel['quality']}]\n"
                 f"axes: km from epicenter ({sel_event_lon(sel):.3f}, "
                 f"{sel_event_lat(sel):.3f}); CRS {d['crs']}")
    ax.set_xlabel('Easting (km)')
    ax.set_ylabel('Northing (km)')
    ax.set_aspect('equal')
    png = Path(outdir) / f"{sel['job_id']}_{sel['event_id']}_{sel['stack']}.png"
    fig.tight_layout()
    fig.savefig(png)
    plt.close(fig)

    tif = png.with_suffix('.tif')
    try:
        import rasterio
        from rasterio.windows import Window
        with rasterio.open(layer(pdir, 'unw_phase')) as src:
            window = Window(c0, r0, c1 - c0, r1 - r0)
            wtransform = src.window_transform(window)
            wcrs = src.crs
        with rasterio.open(tif, 'w', driver='GTiff', height=r1 - r0,
                           width=c1 - c0, count=1, dtype='float32',
                           crs=wcrs, transform=wtransform,
                           nodata=np.nan) as dst:
            dst.write(disp.astype('float32'), 1)
    except Exception as ex:
        return png, f'geotiff failed ({ex}); png ok'
    return png, 'ok'


_jobs_cache = {}


def sel_event_lon(sel):
    return _jobs_cache.get(sel['job_id'], {}).get('lon', 99.99)


def sel_event_lat(sel):
    return _jobs_cache.get(sel['job_id'], {}).get('lat', 26.27)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jobs', required=True)
    ap.add_argument('--workdir-root', required=True)
    ap.add_argument('--selected', required=True)
    ap.add_argument('--outdir', default='maps')
    ap.add_argument('--coh-min', type=float, default=0.3)
    ap.add_argument('--crop-km', type=float, default=40.0,
                    help='map half-window around the epicenter')
    args = ap.parse_args()

    for job in json.loads(Path(args.jobs).read_text())['jobs']:
        lons = [e['longitude'] for e in job['events']]
        lats = [e['latitude'] for e in job['events']]
        _jobs_cache[job['job_id']] = dict(lon=float(np.mean(lons)),
                                          lat=float(np.mean(lats)))
    sel = json.loads(Path(args.selected).read_text())['selection']
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in sel:
        try:
            png, status = process_pair(s, Path(args.workdir_root), outdir,
                                       args.coh_min, args.crop_km)
            print(f"  {s['job_id']} {s['stack']}: {status} -> {png}")
            rows.append((s, png, status))
        except Exception as ex:
            print(f"  {s['job_id']} {s['stack']}: FAILED {ex!r}")
            rows.append((s, None, repr(ex)))
    ok = [r for r in rows if r[1]]
    print(f"\nmaps: {len(ok)}/{len(rows)} -> {outdir}/")


if __name__ == '__main__':
    main()
