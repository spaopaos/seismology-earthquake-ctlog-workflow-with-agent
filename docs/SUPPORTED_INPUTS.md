# Region configuration and supported scope

Raw waveforms can have different layouts and formats as long as the agent can read them using the available tools and establish their sampling, units, response and orientation. Preprocessing and picking do not need a velocity model. Later stages consume fixed standard products.

## Stations

Provide `input/stations.csv` with `id,longitude,latitude,elevation_m`. Coordinates are WGS84; elevation is metres above sea level. Prefer full group IDs (`NET.STA.LOC.FAMILY`), or `NET.STA.LOC`/`NET.STA` when the same coordinates apply unambiguously. Bare station IDs are compatibility inputs and are rejected when they can refer to different network/location identities. Never remove network codes to resolve an error.

The legacy native solvers receive reversible five-character station aliases. `input/station_aliases.json` accompanies native inputs and explains all original group identities. Keep it with `.arc` and ph2dt products. Aliases are run-local, and event IDs are also run-local; use run_id together with event_id when combining independent runs.

## Velocity model

Provide `input/velocity.csv` with `depth_top_km,vp_km_s,vs_km_s`. Layer tops increase strictly from 0 km, Vp and Vs are positive and increase strictly with depth, and Vp>Vs. P/S share layer boundaries. The current HYPOINVERSE CRH path has these capability restrictions; reject low-velocity zones or unsupported model representations with a clear reason instead of changing the model to make the program run.

Depth is positive below sea level. Do not mix depth below topography, ellipsoid heights and sea-level heights. Declare `region.depth_range_km` separately from layer tops, since a half-space has no finite bottom. The default [0,30] km and station-margin 20 km are starting settings to review for the actual study region.

HypoDD takes one P model and a constant Vp/Vs. Derive/check that ratio from current picks (Wadati) and assess the approximation; a depth-varying input ratio is not silently averaged. Record the chosen ratio and basis in pipeline.json.

## Scientific settings and limits

The profile supplies initial GaMMA thresholds, fixed HYPOINVERSE controls and three HypoDD pairing/solver tiers. Their applicability requires current-data QC. The package does not optimize all regions automatically. HYPOINVERSE control changes beyond the exposed POS setting require a maintained explicit runner revision and verification, not runtime source edits by an analysis agent.

MESS consumes only a usable medium HypoDD catalog. It chooses one fixed instrument group per physical network/station and uses that same group in templates and continuous data. Compatible effective preprocessing bands are required. Event positions are inherited from templates, and native event.dat includes the declared PALM depth offset for later solver use; these detections have not been independently located by MESS.

After MESS, `post_detection_relocation` consumes each CC tier separately and jointly solves MESS CC with CT from independently measured PhaseNet+ arrivals (IDAT=3). Only three formal catalogs are delivered. It restores the declared sea-level depth reference, aligns origin times and reversible station identities, preserves CC-only nodes and template references, and repeats the shared spatial DAMP trials. Missing CC or independent CT is UNAVAILABLE rather than a silent single-data-type fallback. See POST_MESS_RELOCATION.md.

Empty association catalogs, no differential observations, inadequate template stations and unavailable DAMP evidence are reported explicitly. The release does not promise a nonempty catalog or final scientific interpretation for every input.
