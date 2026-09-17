"""Joint-lite provenance, input gates and pinned native CC+CT smoke."""
import csv
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'skills/seismic-post-detection-relocation/scripts'))
_RUNTIME = Path(tempfile.mkdtemp(prefix='joint-lite-runtime-'))/'runtime.local.json'
_RUNTIME.write_text(json.dumps({'science_python': sys.executable}))
os.environ['SEISFLOW_RUNTIME'] = str(_RUNTIME)
import bootstrap
from prepare_inputs import (LABELS, build_master, prepare_tier, corrected_cc, load_ct_reuse)
from verify_inputs import verify_joint_lite_inputs
from hypodd_inputs import check_bundle, differentials, verify_joint_receipt
from run_stage import solve_tier
from runtime_support import digest
from station_identity import native_mapping
from run_hypodd import iter_lines, cc_iter_lines, trial_context


def table(path, rows, fields=None):
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def sha(path):
    return digest(path)


def fixture(root, reverse_reference=False):
    """Analytic homogeneous travel times; MESS outputs plus a first-round medium-tier CT source."""
    root = Path(root); adapter = root/'adapter'; adapter.mkdir()
    settings = json.loads((ROOT/'configs/pipeline.example.json').read_text())['post_detection_relocation']
    settings['damping_trials'] = [20, 50, 100]
    locations = [(10*math.cos(i*math.pi/4), 10*math.sin(i*math.pi/4)) for i in range(8)]
    stations = []
    groups = {}
    for i, (east, north) in enumerate(locations):
        physical = f'AA.X{i}'
        group = physical+'..HH'; groups[physical] = group
        stations.append({'id': group, 'longitude': 103+east/(111.195*math.cos(math.radians(30))),
                         'latitude': 30+north/111.195, 'elevation_m': 0})
    station_path = root/'stations.csv'; table(station_path, stations)
    alias_by_group, _ = native_mapping(station_path, groups.values())
    view = adapter/'continuous_manifest.json'; view.write_text(json.dumps({'selected_groups': groups}))
    snapshot = adapter/'source_snapshot.json'; snapshot.write_text(json.dumps({'view_sha256': sha(view)}))
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    ids = [1, 2, 3, 4, 5, 9]
    origins = {eid: base+timedelta(seconds=eid*60+.125 if eid != 9 else 540.123) for eid in ids}
    xyz = {eid: ((eid-3)*.05, .06*math.sin(eid), 5+.04*math.cos(eid)) for eid in ids}
    travel = {}
    for eid in ids:
        x, y, z = xyz[eid]
        for i, (east, north) in enumerate(locations):
            distance = math.sqrt((x-east)**2+(y-north)**2+z*z)
            for phase, speed in (('P', 6.), ('S', 3.5)):
                travel[eid, i, phase] = distance/speed
    templates = []
    for eid in ids:
        templates.append(f'{eid}_20220101_{eid},{origins[eid].isoformat()},30.0,103.0,5.15,0.0\n')
        for i in range(8):
            tp, ts = [(origins[eid]+timedelta(seconds=travel[eid, i, phase])).isoformat() for phase in ('P', 'S')]
            templates.append(f'AA.X{i},{tp},{ts}\n')
    template_path = adapter/'templates.temp'; template_path.write_text(''.join(templates))
    scan_path = adapter/'scan_manifest.json'; scan_path.write_text(json.dumps({'hypodd_depth_offset_km': 5.}))
    rows = [{'event_id': eid, 'origin_time': origins[eid].isoformat(), 'latitude': 30., 'longitude': 103.,
             'depth_km': 5.15, 'best_detection_cc': .9, 'self_detection': 0, 'status': 'new',
             'known_match_method': 'none', 'location_method': 'template_inherited'} for eid in ids if eid != 9]
    # First-round medium tier: ph2dt dt.ct over the same network, hash-tied to its solver evidence.
    associated_rows = list(rows)
    if reverse_reference:
        associated_rows.append({**rows[0], 'event_id': 9, 'best_detection_cc': .39,
                                'origin_time': (origins[9]+timedelta(seconds=.01)).isoformat()})
    associated_path = adapter/'catalog.csv'; table(associated_path, associated_rows)
    tier_dir = root/'round1'/'medium'; (tier_dir/'input').mkdir(parents=True); (tier_dir/'qc').mkdir(parents=True)
    event_lines = []
    for eid in ids:
        t = origins[eid]
        event_lines.append(f'{t:%Y%m%d} {t:%H%M%S}{t.microsecond//10000:02d} 30.0 103.0 5.15 0 0 0 0 {eid}\n')
    (tier_dir/'input/event.dat').write_text(''.join(event_lines))
    (tier_dir/'input/station.dat').write_text(''.join(
        f"{alias} {next(s for s in stations if s['id'] == group)['latitude']:.7f} "
        f"{next(s for s in stations if s['id'] == group)['longitude']:.7f}\n"
        for group, alias in sorted(alias_by_group.items())))
    ct = []
    for eid in ids[:-1]:
        ct.append(f'# {eid} 9\n')
        for i in range(8):
            for phase in ('P', 'S'):
                ct.append(f"{alias_by_group['AA.X'+str(i)+'..HH']} {travel[eid, i, phase]:.6f} "
                          f"{travel[9, i, phase]:.6f} 0.9 {phase}\n")
    (tier_dir/'input/dt.ct').write_text(''.join(ct))
    (tier_dir/'qc/damping_selection.json').write_text(json.dumps(
        {'context': {'input_sha256': {name: sha(tier_dir/'input'/name)
                                      for name in ('dt.ct', 'event.dat', 'station.dat')}}}))
    ct_reuse = {'dt_ct_path': tier_dir/'input/dt.ct', 'event_dat_path': tier_dir/'input/event.dat',
                'station_dat_path': tier_dir/'input/station.dat',
                'selection_path': tier_dir/'qc/damping_selection.json', 'tier_dir': tier_dir}
    documents = {}; catroot = root/'catalogs'; catroot.mkdir()
    for label in LABELS:
        directory = catroot/label; directory.mkdir()
        table(directory/'catalog.csv', rows)
        lines = []
        for eid in ids:
            t = origins[eid]
            lines.append(f'{t:%Y%m%d} {t:%H%M%S}{t.microsecond//10000:02d} 30.0 103.0 10.15 0 0 0 0 {eid}\n')
        (directory/'event.dat').write_text(''.join(lines))
        (directory/'reference_events.json').write_text(json.dumps({'event_ids': [9]}))
        cc = []
        for eid in ids[:-1]:
            reverse = reverse_reference and eid == 1
            cc.append(f'# 9 1 0.0\n' if reverse else f'# {eid} 9 0.0\n')
            for i in range(8):
                for phase in ('P', 'S'):
                    dt = travel[eid, i, phase]-travel[9, i, phase]
                    cc.append(f'X{i} {(-dt-.01) if reverse else dt:.7f} 0.9 {phase}\n')
        (directory/'dt.cc').write_text(''.join(cc))
        documents[label] = {'outputs': {'detections_path': 'catalog.csv',
                            'event_path': 'event.dat', 'dt_cc_path': 'dt.cc', 'reference_events_path': 'reference_events.json'},
            'artifacts': {key: {'path': str(path)} for key, path in
              [('source_templates', template_path), ('source_template_source_snapshot', snapshot),
               ('source_scan_manifest', scan_path), ('source_catalog', associated_path)]}}
    vp = root/'vp.cre'; vp.write_text('SYNTHETIC HOMOGENEOUS\n6.0 0.0\n')
    return build_master(catroot, documents, station_path, ct_reuse), settings, vp


class JointLiteRelocation(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='joint-lite-test-'))
    def tearDown(self):
        if not os.environ.get('SEISFLOW_KEEP_TEST_RUNS'):
            shutil.rmtree(self.root)

    def test_origin_correction_order_and_cross_minute(self):
        old_a = '2022-01-01T00:00:59.999Z'; old_b = '2022-01-01T00:03:00.003Z'
        new_a = '2022-01-01T00:01:00.000Z'; new_b = '2022-01-01T00:03:00.000Z'
        self.assertAlmostEqual(corrected_cc(.25, old_a, old_b, new_a, new_b), .246)
        self.assertAlmostEqual(corrected_cc(-.25, old_b, old_a, new_b, new_a), -.246)

    def test_ct_reuse_is_verbatim_and_hash_tied(self):
        master, settings, _ = fixture(self.root)
        inp = self.root/'input'; prepare_tier(master, 'cc_0p4', inp, settings)
        receipt = verify_joint_lite_inputs(inp)
        self.assertEqual(receipt['measured']['counts']['cc'], 80)
        self.assertEqual(receipt['measured']['counts']['ct'], 80)
        source = json.loads((inp/'source_files.json').read_text())['reused_dt_ct_path']
        self.assertEqual((inp/'dt.ct').read_text(), Path(source).read_text())
        self.assertEqual(json.loads((inp/'events.json').read_text())['9']['role'], 'template_reference')
        self.assertTrue(all(e['depth_km'] == 5.15 for e in master['events'].values() if e['role'] != 'first_round_catalog'))
        verify_joint_receipt(inp)  # runner-side receipt gate
        # Any rewrite of the reused dt.ct must fail verification.
        tampered = Path(source).read_text().replace('0.9 P', '0.8 P', 1)
        (inp/'dt.ct').write_text(tampered)
        with self.assertRaisesRegex(ValueError, 'byte-identical'):
            verify_joint_lite_inputs(inp)
        (inp/'dt.ct').write_text(Path(source).read_text())
        # A tampered adapted CC value must fail independent re-derivation.
        before = (inp/'dt.cc').read_text()
        (inp/'dt.cc').write_text(before.replace('0.9000', '0.8000', 1))
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            verify_joint_lite_inputs(inp)

    def test_ct_source_hash_tie_is_enforced(self):
        master, settings, _ = fixture(self.root)
        tier_dir = self.root/'round1'/'medium'
        before = (tier_dir/'input/dt.ct').read_text()
        (tier_dir/'input/dt.ct').write_text(before.replace('0.9 P', '0.8 P', 1))
        with self.assertRaisesRegex(ValueError, 'differs from its verified solver evidence'):
            build_master(self.root/'catalogs', _documents(self.root), self.root/'stations.csv', {
                'dt_ct_path': tier_dir/'input/dt.ct', 'event_dat_path': tier_dir/'input/event.dat',
                'station_dat_path': tier_dir/'input/station.dat',
                'selection_path': tier_dir/'qc/damping_selection.json', 'tier_dir': tier_dir})
        (tier_dir/'input/dt.ct').write_text(before)

    def test_empty_reused_ct_does_not_fall_back(self):
        _, settings, vp = fixture(self.root)
        tier_dir = self.root/'round1'/'medium'
        (tier_dir/'input/dt.ct').write_text('')
        (tier_dir/'qc/damping_selection.json').write_text(json.dumps(
            {'context': {'input_sha256': {name: sha(tier_dir/'input'/name)
                                          for name in ('dt.ct', 'event.dat', 'station.dat')}}}))
        ct_reuse = {'dt_ct_path': tier_dir/'input/dt.ct', 'event_dat_path': tier_dir/'input/event.dat',
                    'station_dat_path': tier_dir/'input/station.dat',
                    'selection_path': tier_dir/'qc/damping_selection.json', 'tier_dir': tier_dir}
        master = build_master(self.root/'catalogs', _documents(self.root), self.root/'stations.csv', ct_reuse)
        with self.assertRaisesRegex(ValueError, 'CC AND CT'):
            solve_tier(self.root/'no_ct', master, 'cc_0p4', settings, vp, 6/3.5, 1.)
        self.assertFalse((self.root/'no_ct/output').exists())

    def test_no_nine_catalog_axis_and_both_weights_required(self):
        _, settings, _ = fixture(self.root)
        self.assertEqual(LABELS, ('cc_0p4', 'cc_0p6', 'cc_0p8'))
        self.assertNotIn('tiers', settings)
        from hypodd_inputs import joint_schedule
        doc = {**settings, 'ct_source': 'first_round_reuse'}
        good = self.root/'good.json'; good.write_text(json.dumps(doc))
        self.assertEqual(joint_schedule(good)['ct_source'], 'first_round_reuse')
        broken = json.loads(json.dumps(doc)); broken['iterations'][0]['wtccp'] = -9
        path = self.root/'bad.json'; path.write_text(json.dumps(broken))
        with self.assertRaisesRegex(ValueError, 'positive'):
            joint_schedule(path)
        self.assertIn('-9', iter_lines(50))  # first-round catalog schedule remains supported
        self.assertIn('0.5', cc_iter_lines(50))  # copied PALM single-block CC-only schedule

    def test_native_joint_solve_and_stale_cc_rejection(self):
        master, settings, vp = fixture(self.root)
        directory = self.root/'joint'
        state = solve_tier(directory, master, 'cc_0p4', settings, vp, 6/3.5, 1.)
        self.assertEqual(state['status'], 'READY', state)
        final = json.loads((directory/'qc/final_run.json').read_text())
        self.assertGreater(final['used_event_observation_counts']['cc'], 0)
        self.assertGreater(final['used_event_observation_counts']['ct'], 0)
        self.assertEqual(final['data_mode'], 'cc_ct')
        self.assertEqual(len(check_bundle(directory/'input')['per_event']), 6)
        # Reference event 9 survives the union and is actually solved.
        self.assertIn(9, [int(l.split()[0]) for l in (directory/'output/hypoDD.reloc').read_text().splitlines() if l.strip()])
        # Compare the recovered relative geometry against independently specified truth.
        import numpy as np
        native = [l.split() for l in (directory/'output/hypoDD.reloc').read_text().splitlines() if l.strip()]
        truth = np.array([[(int(f[0])-3)*.05, .06*math.sin(int(f[0])), 5+.04*math.cos(int(f[0]))] for f in native])
        recovered = np.array([[(float(f[2])-103)*111.195*math.cos(math.radians(30)),
                               (float(f[1])-30)*111.195, float(f[3])] for f in native])
        error = np.linalg.norm((truth-truth.mean(axis=0))-(recovered-recovered.mean(axis=0)), axis=1)
        self.assertLess(float(np.median(error)), .02)  # <20 m on this analytic regional fixture
        # A stale adapted CC bundle must fail the runner-side receipt gate.
        before = (directory/'input/dt.cc').read_text()
        (directory/'input/dt.cc').write_text(before.replace('0.9000', '0.8000', 1))
        with self.assertRaisesRegex(ValueError, 'changed|differs'):
            verify_joint_receipt(directory/'input')

    def test_native_missing_ct_and_duplicate_cc_are_rejected(self):
        directory = self.root/'native'; directory.mkdir()
        (directory/'event.dat').write_text('20220101 00000000 30 103 5 0 0 0 0 1\n20220101 00010000 30 103 5 0 0 0 0 2\n')
        (directory/'station.dat').write_text('S0001 30 103\n')
        (directory/'dt.cc').write_text('# 1 2 0\nS0001 0.01 0.9 P\n')
        (directory/'dt.ct').write_text('')
        with self.assertRaisesRegex(ValueError, 'CC AND CT'):
            check_bundle(directory)
        (directory/'dt.cc').write_text('# 1 2 0\nS0001 0.01 0.9 P\n# 2 1 0\nS0001 -0.01 0.9 P\n')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            differentials(directory/'dt.cc', 'cc')

    def test_three_native_catalogs_publish_valid_contract(self):
        from publish_results import publish
        from pipeline_contracts import schema_errors, inspect_artifacts
        master, settings, vp = fixture(self.root)
        out = self.root/'post'; out.mkdir()
        states = {label: solve_tier(out/label, master, label, settings, vp, 6/3.5, 1.) for label in LABELS}
        self.assertTrue(all(state['status'] == 'READY' for state in states.values()), states)
        # Stub only the already-validated upstream contracts; native computation above is real.
        parents = {}
        for label in LABELS:
            path = self.root/'catalogs'/label/'contract.v2.json'
            path.write_text(json.dumps({'stage': 'detection', 'contract_version': '2.1',
                            'outputs': {'detections_path': 'catalog.csv'}}))
            parents[label] = path
        loc = self.root/'location.json'; rel = self.root/'relocation.json'
        loc.write_text(json.dumps({'stage': 'location', 'contract_version': '2.0'}))
        rel.write_text(json.dumps({'stage': 'relocation', 'contract_version': '2.0'}))
        (out/'effective_parameters.json').write_text(json.dumps(settings))
        publish(out, master, states, parents, loc, rel, vp, 'synthetic-publication-test')
        doc = json.loads((out/'contract.v2.json').read_text())
        self.assertEqual(schema_errors(doc), [])
        self.assertEqual(inspect_artifacts(doc, out), [])
        self.assertEqual(doc['status'], 'READY')
        self.assertEqual(set(doc['outputs']['catalogs']), set(LABELS))
        self.assertEqual(doc['stats']['tier_counts'], dict.fromkeys(LABELS, 5))
        self.assertEqual(doc['times']['ct_source'], 'first_round_reuse')
        for label in LABELS:
            with (out/label/'catalog.csv').open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual({int(r['event_id']) for r in rows}, {1, 2, 3, 4, 5})
            self.assertTrue(all(r['location_method'] == 'hypodd_cc_ct' for r in rows))
            self.assertTrue(all(r['method'] == 'joint_lite_cc_ct' for r in rows))

    def test_cc_first_event_can_be_a_below_threshold_template_reference(self):
        master, settings, vp = fixture(self.root, reverse_reference=True)
        state = solve_tier(self.root/'reference_first', master, 'cc_0p4', settings, vp, 6/3.5, 1.)
        self.assertEqual(state['status'], 'READY', state)
        audit = json.loads((self.root/'reference_first/input/cc_adaptation.json').read_text())
        reference = next(row for row in audit if row['a'] == 9)
        self.assertTrue(reference['source_origin_a'].endswith('00:09:00.133000+00:00'))


def _documents(root):
    """Rebuild detection document stubs for direct build_master calls."""
    docs = {}
    for label in LABELS:
        directory = root/'catalogs'/label
        docs[label] = {'outputs': {'detections_path': 'catalog.csv', 'event_path': 'event.dat',
                        'dt_cc_path': 'dt.cc', 'reference_events_path': 'reference_events.json'},
            'artifacts': {key: {'path': str(path)} for key, path in
              [('source_templates', root/'adapter/templates.temp'),
               ('source_template_source_snapshot', root/'adapter/source_snapshot.json'),
               ('source_scan_manifest', root/'adapter/scan_manifest.json'),
               ('source_catalog', root/'adapter/catalog.csv')]}}
    return docs


if __name__ == '__main__':
    unittest.main()
