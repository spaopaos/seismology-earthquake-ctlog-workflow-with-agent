# Vendored SKHASH source — provenance and patches

Upstream: SKHASH v1.1 (2025-12-17), U.S. Geological Survey, CC0-1.0.
Homepage: https://code.usgs.gov/esc/skhash/
Source snapshot: `SKHASH-main` zip archive of tag 1.1, unmodified except the
four compatibility patches below (recorded verbatim in `SKHASH_patches.diff`).

The patches make SKHASH v1.1 compatible with numpy>=2 / pandas 3 (the
Eryuan validation environment ran numpy 2.4.6 / pandas 3.0.6). All four are
additive `.astype(str)` / scalar-extraction changes and remain compatible
with older numpy. Validation: the smile / maacama / hash3 bundled examples
produce equivalent results before/after patching; maacama's first-event
solution matches the upstream published result from a numpy<2 environment.

1. `src/SKHASH/functions/fun.py` — numpy 2 forbids implicit scalar
   conversion of length-1 arrays: extract scalars explicitly from
   `sdr_from_vector` return values.
2. `src/SKHASH/functions/in_sp.py` — numeric-looking location codes
   ("00"/"20") are int-coerced on CSV read; cast merge columns to str.
3. `src/SKHASH/functions/in_sta.py` — same int-coercion issue before
   `.str.strip()` on the station table.
4. `src/SKHASH/functions/in_sta.py` (`read_reverse_skhash_file`) — same for
   the polarity-reversal table before sta_code joins.

Known upstream behaviors (kept as-is):

- A single event with zero solutions can raise KeyError `mech_quality` in
  `out.pol_agree`; full-batch runs are unaffected.
- `$plfile` reversal times must be timezone-aware (e.g.
  `2025-03-01T00:00:00+00:00`) to match the UTC catalog times under pandas 3.
- The layered velocity model must be strictly increasing in vp; the skill's
  staircase generator adds +0.001 km/s per 1 km step for this reason.
