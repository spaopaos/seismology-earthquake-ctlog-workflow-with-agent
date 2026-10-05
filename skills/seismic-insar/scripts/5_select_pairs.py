#!/usr/bin/env python3
"""Automatically select coseismic pairs by policy (agent-driven stage).

Usage:
  python 5_select_pairs.py --jobs insar_jobs.json \
    --workdir-root insar_work [--per-direction 1] \
    [--prefer-both-directions] [--allow-concern] \
    --out selected_pairs.json

Policy (deterministic, recorded in the output):
  1. candidate = pair whose dates bracket exactly one threshold event AND
     lie inside that event's bracket window (clean);
  2. quality = healthy (InSARHub pair_quality DB); concern pairs only when
     --allow-concern, or with --prefer-both-directions when a look
     direction would otherwise be empty (flagged in the output);
  3. rank by temporal baseline (shortest first), tie-break by the stack's
     healthy-fraction;
  4. keep --per-direction best pairs per look direction (ascending/
     descending from the acquisition local solar time: ~18h ascending,
     ~06h descending).

Look-direction heuristic is generic (local solar time from stack UTC hours
and the AOI longitude); for a new region verify against ASF metadata once.
"""
import argparse
import json
import re
from pathlib import Path


def gdate(g):
    m = re.search(r'_(\d{8})T(\d{2})', g)
    return (m.group(1), int(m.group(2))) if m else ('', 0)


def look_direction(granules, lon):
    """Ascending if local solar time ~18h, descending if ~06h."""
    hours = [gdate(g)[1] + lon / 15.0 for g in granules if gdate(g)[1]]
    local = sum(hours) / len(hours) % 24
    return 'ascending' if 13 <= local < 23 and abs(local - 18) < 6 else 'descending'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jobs', required=True)
    ap.add_argument('--workdir-root', required=True)
    ap.add_argument('--per-direction', type=int, default=1)
    ap.add_argument('--prefer-both-directions', action='store_true', default=True)
    ap.add_argument('--no-prefer-both-directions', dest='prefer_both_directions',
                    action='store_false')
    ap.add_argument('--allow-concern', action='store_true')
    ap.add_argument('--out', default='selected_pairs.json')
    args = ap.parse_args()

    doc = json.loads(Path(args.jobs).read_text())
    root = Path(args.workdir_root)
    selection = []

    for job in doc['jobs']:
        lon = sum(job['aoi'][0::2]) / 2
        stacks = []
        for sd in sorted((root / job['job_id']).iterdir()):
            sj = sd / f'stack_{sd.name}.json'
            if not sj.is_file():
                continue
            sdoc = json.loads(sj.read_text())
            qdb = sd / '.insarhub_pair_quality_db.json'
            status = json.loads(qdb.read_text()).get('status', {}) if qdb.is_file() else {}
            n_h = sum(1 for v in status.values() if v == 'healthy')
            stacks.append(dict(
                stack=sd.name, pairs=sdoc['pairs'],
                scene_hours=[gdate(g)[1] for g in sdoc['scenes'] if gdate(g)[1]],
                healthy_frac=n_h / max(len(status), 1),
                status=status))
        if not stacks:
            continue

        for ev in job['events']:
            evt = ev['origin_time'][:10].replace('-', '')
            b1 = ev['bracket_start'].replace('-', '')
            b2 = ev['bracket_end'].replace('-', '')
            cands = []
            for st in stacks:
                direction = look_direction(
                    [g for g in st['pairs'][0]] if st['pairs'] else [], lon) \
                    if st['pairs'] else '?'
                for pair in st['pairs']:
                    d1, d2 = sorted(gdate(g)[0] for g in pair)
                    if not (d1 <= evt <= d2 and d1 >= b1 and d2 <= b2):
                        continue
                    q = st['status'].get(f'{pair[0]}:{pair[1]}',
                                         st['status'].get(f'{pair[1]}:{pair[0]}', '?'))
                    dt = (int(d2) - int(d1)) // 1
                    from datetime import date
                    dt = (date(int(d2[:4]), int(d2[4:6]), int(d2[6:]))
                          - date(int(d1[:4]), int(d1[4:6]), int(d1[6:]))).days
                    cands.append(dict(
                        stack=st['stack'], direction=direction, quality=q,
                        d1=d1, d2=d2, dt_days=dt,
                        healthy_frac=st['healthy_frac'], granules=list(pair)))
            # policy ranking
            def key(c):
                penalty = (c['quality'] != 'healthy')
                return (penalty, c['dt_days'], -c['healthy_frac'], c['stack'])
            chosen = []
            for direction in ('ascending', 'descending'):
                pool = sorted([c for c in cands if c['direction'] == direction], key=key)
                if not pool:
                    continue
                take = pool[:args.per_direction]
                for c in take:
                    if c['quality'] != 'healthy' and not args.allow_concern:
                        if not (args.prefer_both_directions and not any(
                                x['direction'] == direction and x['quality'] == 'healthy'
                                for x in cands)):
                            continue  # strict: skip concern without fallback right
                    c = dict(c, job_id=job['job_id'], event_id=ev['event_id'],
                             event_time=ev['origin_time'], ml=ev['ml'])
                    chosen.append(c)
            selection += chosen

    out = {
        'policy': {
            'clean_bracket': 'one event alone inside [bracket_start, bracket_end]',
            'quality': 'healthy preferred; concern only to fill an empty look direction'
                       ' when prefer_both_directions is set (flagged)',
            'rank': 'temporal baseline asc, then stack healthy fraction, then name',
            'per_direction': args.per_direction,
            'look_direction': 'local solar time ~18h ascending / ~06h descending '
                              '(heuristic; verify vs ASF metadata on first use)'},
        'selection': selection,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(f'selected {len(selection)} pairs -> {args.out}')
    for c in selection:
        flag = '' if c['quality'] == 'healthy' else '  [CONCERN-fallback]'
        print(f"  {c['job_id']} {c['event_id']} {c['direction']:10s} "
              f"{c['stack']:12s} {c['d1']}->{c['d2']} ({c['dt_days']}d) "
              f"{c['quality']}{flag}")


if __name__ == '__main__':
    main()
