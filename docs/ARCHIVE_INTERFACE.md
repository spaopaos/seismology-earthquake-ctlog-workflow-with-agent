# Standardized preprocessing boundary

The agent may write data-specific preprocessing code. This interface is fixed so PhaseNet+ and later tools do not need dataset-specific format conversions.

Store these files under the run's `archive/`:

- `daily_manifest.csv`: one unique `(group,date)` row per station instrument group and UTC day.
- Per-row waveform files and metadata JSON.
- `archive_provenance.json`, actual preprocessing code/config/input mapping and QC.

Required manifest columns: `group,date,status,metadata,file_Z,file_N,file_E`. Paths are relative to the archive root. `group` is `NET.STA.LOC.FAMILY`, with an empty location allowed (`AA.STA..HH`). `date` is `YYYY-MM-DD`. Eligible statuses are READY and PARTIAL_DAY; unavailable rows have an explicit reason/status and are counted as skipped.

Each component is one 100 Hz trace covering the complete UTC day: 8,640,000 samples starting at midnight. Arrays represent band-limited ground velocity in m/s, with calib=1; missing samples are explicitly zero-filled. Preferred format is MiniSEED FLOAT32. SAC is accepted as an explicit compatibility format. Filenames include group and date; commas/newlines are not allowed in filenames consumed by the EQNet data list.

Metadata includes:

```json
{
  "group": "AA.STA..HH",
  "utc_day": "2020-01-02",
  "units": "m/s",
  "physical_quantity": "ground_velocity",
  "orientation_verified": true,
  "orientation_source": "actual source reference and rotation description",
  "response_verified": true,
  "response_source": "actual response epoch/source or verified existing SI-unit provenance",
  "analysis_band_hz": [1.0, 40.0],
  "group_min_raw_sampling_rate_hz": 100.0,
  "usable_3c_intervals": [[2000, 8638000]],
  "components": {
    "Z": {"data_intervals": [[0, 8640000]], "usable_intervals": [[2000, 8638000]]},
    "N": {"data_intervals": [[0, 8640000]], "usable_intervals": [[2000, 8638000]]},
    "E": {"data_intervals": [[0, 8640000]], "usable_intervals": [[2000, 8638000]]}
  }
}
```

This is a format example, not evidence. Set verification flags only after inspecting actual sources. Interval indices are sorted, nonoverlapping, zero-based half-open integer ranges. Usable intervals must lie inside observation support; usable_3c must lie inside each component's usable intervals. The effective upper band must respect the original Nyquist margin; resampling to 100 Hz does not create new bandwidth. Z/1/2 is rotated from verified orientation metadata; changing channel letters is insufficient.

If a long original station code cannot fit MiniSEED headers, use a documented reversible header mapping. Set `trace_group` in the manifest/metadata to the actual `NET.STA.LOC.FAMILY` in file headers while retaining the original full `group`. Picking normalization restores the original identity. Do not silently truncate names.

`archive_provenance.json` references four existing files with paths relative to the archive:

```json
{
  "processing_script": "processing_script.py",
  "effective_config": "effective_config.json",
  "source_manifest": "source_manifest.json",
  "qc_summary": "qc_summary.json"
}
```

The source manifest should identify raw waveforms, response epochs, direction metadata and transforms. Keep response removal/filter/resampling details and real QC plots per the preprocessing skill. The validator checks waveform/metadata consistency and hashes evidence; it cannot establish physical units from sample values alone or prove the source orientation is correct.

Publish with the fixed preprocessing stage. Downstream consumes the resulting `contract.v2.json`. Validation failures are repaired in the producing data-specific code and rerun in a new archive; do not edit checksums to accept changed products.

`examples/build_synthetic_archive.py` generates a clearly labeled interface-only fixture. It is not a raw-observation preprocessing example or scientific ground truth.
