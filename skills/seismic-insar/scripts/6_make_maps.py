#!/usr/bin/env python3
"""Turn HyP3 GUNW interferograms into LOS deformation maps.

Usage:
  python 6_make_maps.py --jobs insar_jobs.json \
    --workdir-root insar_work --selected selected_pairs.json \
    --outdir maps

Per selected pair: reads the GUNW NetCDF (unwrappedPhase, coherence,
heights, incidenceAngle), converts phase to LOS displacement
(d = -phase * lambda / 4pi, positive = motion TOWARD the satellite,
lambda = 0.0554658 m C-band), masks low coherence (<0.3 by default),
writes a displacement GeoTIFF (EPSG:4326, mm) and a PNG: displacement over
a DEM hillshade with coherence contour, event epicenter marked, title
carrying event/stack/dates/quality. Intermediates (NetCDF) stay in place
for review.
"""
import argparse
import glob
import json
import re
from pathlib import Path

import numpy as np

LAMBDA_C = 0.0554658  # Sentinel-1 C-band wavelength, m


def find_gunw(stack_dir, granules):
    dates = sorted(re.search(r'_(\d{8})T', g).group(1) for g in granules)
    pattern = f"{stack_dir}/**/*{dates[0]}*{dates[1]}*.nc"
    hits = sorted(glob.glob(pattern, recursive=True)) or \
        sorted(glob.glob(f"{stack_dir}/**/*.nc", recursive=True))
    return hits[0] if hits else None


def load_gunw(path):
    from netCDF4 import Dataset
    ds = Dataset(path)
    g = ds.groups['science'].groups['GRIDS']
    data = g.groups['data']
    geo = g.groups['geometry']

    def arr(v):
        a = np.array(data.variables[v][:], dtype=float)
        return np.ma.filled(a, np.nan)
    out = dict(
        unw=arr('unwrappedPhase'), coh=arr('coherence'),
        hgt=np.ma.filled(np.array(geo.variables['heights'][:], dtype=float), np.nan),
        inc=np.ma.filled(np.array(geo.variables['incidenceAngle'][:], dtype=float), np.nan),
        lon=np.array(data.variables['longitude'][:], dtype=float),
        lat=np.array(data.variables['latitude'][:], dtype=float))
    ds.close()
    return out


def shade(h):
    """Simple illumination: gradient-based synthetic shading."""
    gy, gx = np.gradient(h)
    gnorm = np.sqrt(gy**2 + gx**2)
    s = np.clip(1 - (gx * np.cos(np.deg2rad(315)) + gy * np.sin(np.deg2rad(315)))
                / (gnorm + 1e-6) * 0.5, 0, 1)
    return np.nan_to_num(s, nan=0.5)


def process_pair(sel, root, outdir, coh_min):
    stack_dir = root / sel['job_id'] / sel['stack']
    nc = find_gunw(stack_dir, sel['granules'])
    if not nc:
        return None, 'no GUNW netcdf found'
    d = load_gunw(nc)
    disp_mm = -d['unw'] * LAMBDA_C / (4 * np.pi) * 1000.0
    mask = ~(d['coh'] >= coh_min)
    disp_mm[mask] = np.nan
    lon2d, lat2d = (np.meshgrid(np.linspace(d['lon'].min(), d['lon'].max(),
                                            disp_mm.shape[1]),
                                np.linspace(d['lat'].min(), d['lat'].max(),
                                            disp_mm.shape[0]))
                    if d['lon'].ndim == 1 else (d['lon'], d['lat']))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    lim = np.nanpercentile(np.abs(disp_mm), 99.5) or 30.0
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
    ax.pcolormesh(lon2d, lat2d, shade(d['hgt']), cmap='gray', vmin=0, vmax=1,
                  shading='auto')
    im = ax.pcolormesh(lon2d, lat2d, disp_mm, cmap='RdBu', vmin=-lim, vmax=lim,
                       shading='auto')
    cs = ax.contour(lon2d, lat2d, d['coh'], levels=[coh_min], colors='k',
                    linewidths=0.5, linestyles='--')
    ax.plot(sel_event_lon(sel), sel_event_lat(sel), 'k*', ms=18, mec='w')
    plt.colorbar(im, ax=ax, label='LOS displacement (mm; + toward satellite)')
    ax.set_title(f"{sel['event_id']} ML{sel['ml']:.2f} {sel['event_time'][:10]}  "
                 f"{sel['stack']} {sel['direction']}  "
                 f"{sel['d1']}->{sel['d2']} ({sel['dt_days']}d)  [{sel['quality']}]")
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    png = Path(outdir) / f"{sel['job_id']}_{sel['event_id']}_{sel['stack']}.png"
    fig.tight_layout(); fig.savefig(png); plt.close(fig)

    # GeoTIFF via GDAL (rasterio in the insarhub env)
    tif = png.with_suffix('.tif')
    try:
        import rasterio
        from rasterio.transform import from_bounds
        h, w = disp_mm.shape
        transform = from_bounds(lon2d.min(), lat2d.min(), lon2d.max(),
                                lat2d.max(), w, h)
        with rasterio.open(tif, 'w', driver='GTiff', height=h, width=w,
                           count=1, dtype='float32', crs='EPSG:4326',
                           transform=transform, nodata=np.nan) as dst:
            dst.write(disp_mm.astype('float32'), 1)
    except Exception as ex:
        return png, f'geotiff failed ({ex}); png ok'
    return png, 'ok'


_jobs_cache = {}


def sel_event_lon(sel):
    if not _jobs_cache:
        return 99.99
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
                                       args.coh_min)
            print(f"  {s['job_id']} {s['stack']}: {status} -> {png}")
            rows.append((s, png, status))
        except Exception as ex:
            print(f"  {s['job_id']} {s['stack']}: FAILED {ex!r}")
            rows.append((s, None, repr(ex)))
    ok = [r for r in rows if r[1]]
    print(f"\nmaps: {len(ok)}/{len(rows)} -> {outdir}/")


if __name__ == '__main__':
    main()
