"""Normalize pinned GaMMA return values into complete downstream tables."""
import numpy as np
import pandas as pd

EVENT_COLUMNS = ["time", "sigma_time", "sigma_amp", "cov_time_amp", "gamma_score",
                 "num_picks", "num_p_picks", "num_s_picks", "event_index", "x(km)", "y(km)", "z(km)"]


def output_tables(raw_events, raw_assignments, picks, projection):
    events = pd.DataFrame(raw_events) if len(raw_events) else pd.DataFrame(columns=EVENT_COLUMNS)
    events = events.drop(columns=["magnitude"], errors="ignore")
    assignments = pd.DataFrame(raw_assignments, columns=["pick_index", "event_index", "gamma_score"])
    if assignments.pick_index.duplicated().any():
        raise ValueError("GaMMA assigned a pick more than once")
    if not set(assignments.pick_index).issubset(set(picks.index)):
        raise ValueError("GaMMA returned unknown pick indices")
    if events.event_index.duplicated().any() or not set(assignments.event_index).issubset(set(events.event_index)):
        raise ValueError("Duplicate or unknown event IDs")
    if len(events):
        events["longitude"], events["latitude"] = projection(events["x(km)"].to_numpy(), events["y(km)"].to_numpy(), inverse=True)
    else:
        events["longitude"], events["latitude"] = pd.Series(dtype=float), pd.Series(dtype=float)
    events["depth_km"] = events["z(km)"]
    events["event_index"] = events.event_index.astype("int64")
    events["event_id"] = events.event_index.map(lambda n: f"gm{n:06d}")
    events = events.sort_values(["time", "event_index"]).reset_index(drop=True)

    all_picks = picks.copy()
    all_picks["pick_index"] = all_picks.index
    all_picks = all_picks.merge(assignments, on="pick_index", how="left", validate="one_to_one", sort=False)
    all_picks["event_index"] = all_picks.event_index.fillna(-1).astype("int64")
    all_picks["event_id"] = all_picks.event_index.map(lambda n: f"gm{n:06d}" if n >= 0 else "")
    associated = all_picks.loc[all_picks.event_index >= 0].copy()
    # Pinned GaMMA already deduplicates station-group + phase, by travel-time
    # residual. Do not remove S just because the same event/station has a P.
    if associated.duplicated(["event_index", "station_id", "phase_type"]).any():
        raise ValueError("Repeated event/station-group/phase returned by GaMMA")
    for _, event in events.iterrows():
        group = associated.loc[associated.event_index == event.event_index]
        counts = (len(group), int(group.phase_type.eq("P").sum()), int(group.phase_type.eq("S").sum()))
        expected = (int(event.num_picks), int(event.num_p_picks), int(event.num_s_picks))
        if counts != expected:
            raise ValueError(f"GaMMA event {event.event_id} pick counts disagree with assignments")
    aliases = ["id", "timestamp", "type", "prob", "amp"]
    associated = associated.drop(columns=aliases, errors="ignore")
    unassociated = all_picks.loc[all_picks.event_index < 0].drop(columns=aliases, errors="ignore")
    if len(associated) + len(unassociated) != len(picks):
        raise ValueError("Pick accounting does not close")
    return events, associated, unassociated
