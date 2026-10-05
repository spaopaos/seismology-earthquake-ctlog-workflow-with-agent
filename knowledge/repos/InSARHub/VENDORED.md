# Vendored InSARHub source — provenance

Upstream: InSARHub v0.4.2 (tag `v0.4.2`, commit `1139737`, "0.4.2 release"),
Jiawei Li et al., Colorado State University, MIT license.
Homepage: https://github.com/jldz9/InSARHub ; docs: https://jldz9.github.io/InSARHub/

Vendored scope: `src/` (the `insarhub` package), `test/`, `recipe/`,
`scripts/`, `docker/`, root packaging files (`pyproject.toml`,
`environment.yml`), the JOSS-style paper (`paper.md`/`paper.bib`), and the
documentation markdown (`docs/quickstart`, `docs/advanced`) without image
assets. Upstream repository documentation media (~42 MB) and `.github` CI
configuration are excluded; nothing else is modified.

## Environment

InSARHub requires a dedicated environment (Python 3.11–3.12, numpy<2.0,
GDAL>=3.8) that is incompatible with the pinned seismic environments. Create
it from the included `environment.yml` (env name `insarhub`), then install
this vendored source without re-solving dependencies:

```bash
conda env create -f environment.yml
conda run -n insarhub pip install --no-deps -e .
```

The upstream `environment.yml` comments document two confirmed ABI traps —
do not "simplify" them away: (1) `libgdal-netcdf` must stay, or the solver
pulls scipy/mintpy needing numpy>=2 and silently breaks against the
numpy<2.0 pin; (2) `rasterio`/`burst2safe` must come from conda-forge, not
pip, to keep the libproj/proj.db stack consistent with GDAL.

## Cloud credentials (HyP3 path)

Free accounts, configured in `~/.netrc` and `~/.cdsapirc` (see
`docs/quickstart/api_setup.md`): NASA Earthdata (scene search, DEM, orbits,
HyP3 job submission), Copernicus Data Space (orbits), Copernicus Climate
Data Store (PyAPS tropospheric correction).

## Known behaviors

- No modifications were applied to the vendored source; compatibility
  patches, if ever needed, must be recorded here with diffs.
- The web GUI (React frontend) is part of `src/insarhub/app` but is not
  required: the CLI (`insarhub downloader/processor/analyzer`) covers the
  workflow used by the `seismic-insar` skill.
