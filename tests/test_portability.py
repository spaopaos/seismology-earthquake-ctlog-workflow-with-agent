"""Regression checks for actual migration failures; run with the science interpreter."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'contracts'))
from station_identity import native_mapping, resolve_groups
from archive_interface import intervals, within
from runtime_support import verify_vendor

def module(stage,name):
    directory=ROOT/'skills'/('seismic-'+stage)/'scripts'
    sys.path.insert(0,str(directory))
    spec=importlib.util.spec_from_file_location(stage+'_'+name,directory/(name+'.py'))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

class Portability(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.stations=self.root/'stations.csv'
        pd.DataFrame([['AA.SAME.00.HH',-70,-30,100],['BB.SAME.00.HH',-70.1,-30.1,200],
                      ['AA.LONGSTATION.00.HN',-70.2,-30.2,300]],
                     columns=['id','longitude','latitude','elevation_m']).to_csv(self.stations,index=False)
        self.groups=['AA.SAME.00.HH','BB.SAME.00.HH','AA.LONGSTATION.00.HN']
    def tearDown(self): self.temp.cleanup()
    def test_aliases_preserve_network_and_long_codes(self):
        forward,aliases=native_mapping(self.stations,self.groups)
        self.assertEqual(len(set(forward.values())),3)
        self.assertTrue(all(len(x)==5 for x in forward.values()))
        self.assertEqual(aliases[forward[self.groups[1]]]['site_id'],'BB.SAME.00')
    def test_ambiguous_bare_station_is_rejected(self):
        self.stations.write_text('id,longitude,latitude,elevation_m\nSAME,-70,-30,100\n')
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            resolve_groups(self.stations,self.groups[:2])
    def test_ph2dt_does_not_collapse_two_networks(self):
        mod=module('relocation','make_ph2dt_inputs')
        cat=self.root/'cat.csv'; picks=self.root/'picks.csv'
        pd.DataFrame([{'event_id':'gm000001','date':'2020/01/02 00:00','sec':0.0,
                       'latitude_hyp':-30,'longitude_hyp':-70,'depth_km_hyp':5}]).to_csv(cat,index=False)
        pd.DataFrame([{'station_id':g,'event_index':1,'phase_time':'2020-01-02T00:00:03Z',
                       'phase_type':'P','phase_score':0.9} for g in self.groups]).to_csv(picks,index=False)
        def path(*args): return cat if args[1]=='location' else picks
        with patch.object(mod,'product_path',side_effect=path),patch.object(sys,'argv',['convert','--location-dir','location',
             '--assoc-dir','association','--stations',str(self.stations),'--out',str(self.root/'out')]): mod.main()
        rows=(self.root/'out/input/phase.dat').read_text().splitlines()[1:]
        self.assertEqual(len(rows),3)
        self.assertEqual(len({line.split()[0] for line in rows}),3)
    def test_hypoinverse_station_fields_are_fixed_and_reversible(self):
        mod=module('location','make_hypoinverse_inputs')
        cat=self.root/'cat.csv'; picks=self.root/'picks.csv'
        pd.DataFrame([{'event_id':'gm000001','time':'2020-01-02T00:00:00Z','latitude':-30,'longitude':-70}]).to_csv(cat,index=False)
        pd.DataFrame([{'station_id':g,'event_index':1,'phase_time':'2020-01-02T00:00:03Z','instrument_family':g.split('.')[-1],
                       'phase_type':'P','phase_score':0.9,'polarity_score':0.8} for g in self.groups]).to_csv(picks,index=False)
        model=self.root/'p.cre'; model.write_text('MODEL\n5.5 0\n6.0 5\n')
        with patch.object(mod,'product_path',side_effect=lambda *a:cat if a[2]=='outputs.events_path' else picks),patch.object(sys,'argv',
             ['convert','--assoc-dir','association','--stations',str(self.stations),'--vp-model',str(model),'--out',str(self.root/'out')]): mod.main()
        station_lines=(self.root/'out/input/stations.sta').read_text().splitlines()
        self.assertEqual(len(station_lines),3)
        self.assertTrue(all(l[25]=='S' and l[37]=='W' for l in station_lines))
        self.assertEqual(len({l[:5] for l in station_lines}),3)
    def test_interval_validation(self):
        self.assertTrue(within([[2,4]],intervals([[0,5]])))
        self.assertFalse(within([[2,6]],[[0,5]]))
        for value in [[[1,4],[3,5]],[[-1,2]],[[0,8640001]],[[0.0,1]]]:
            with self.assertRaises(ValueError): intervals(value)
    def test_pick_normalization_restores_identity_and_flags_boundaries(self):
        mod=module('picking','normalize_picks')
        archive=self.root/'archive'; archive.mkdir()
        metadata={'group':'ZZ.LONGSTATION..HH','trace_group':'ZZ.DEMO..HH','utc_day':'2020-01-02','usable_3c_intervals':[[2000,4000]]}
        (archive/'metadata.json').write_text(json.dumps(metadata))
        (archive/'daily_manifest.csv').write_text('group,date,status,metadata,file_Z,file_N,file_E\nZZ.LONGSTATION..HH,2020-01-02,READY,metadata.json,z,n,e\n')
        raw=self.root/'raw'; raw.mkdir()
        pd.DataFrame([{'station_id':'ZZ.DEMO..HH','phase_time':'2020-01-02T00:00:'+str(t)+'Z','phase_type':'P',
                       'phase_score':0.8,'phase_polarity':-0.7,'phase_amplitude':1e-6} for t in [10,20,40]]).to_csv(raw/'model.csv',index=False)
        with patch.object(mod,'load_contract',return_value=({'archive_root':'.'},archive/'contract.v2.json')):
            result,receipt=mod.normalize(raw,archive,self.root/'picks.csv')
        self.assertEqual(result.usable_3c.tolist(),[False,True,False])
        self.assertTrue(result.station_id.eq('ZZ.LONGSTATION..HH').all())
        self.assertTrue(result.polarity_score.eq(-0.7).all())
        self.assertTrue(result.amplitude_units.eq('m/s').all())
        self.assertEqual(receipt['outside_usable'],2)
    def test_vendor_change_is_detected_without_git(self):
        import hashlib
        p=self.root/'repo'; p.mkdir(); (p/'module.py').write_text('value=1\n')
        (p/'SOURCE_MANIFEST.json').write_text(json.dumps({'commit':'pinned','files':{'module.py':hashlib.sha256((p/'module.py').read_bytes()).hexdigest()}}))
        self.assertEqual(verify_vendor(p,'pinned'),'pinned')
        (p/'module.py').write_text('value=2\n')
        with self.assertRaises(ValueError): verify_vendor(p,'pinned')
    def test_dateline_aperture_uses_short_geodesic(self):
        import numpy as np
        mod=module('association','run_gamma')
        stations=pd.DataFrame({'longitude':[179.9,-179.9], 'latitude':[-20,-20]})
        derived=mod.derive(stations,(np.array([6.0,6.5]),np.array([0.,10.])),np.array([0.,10.]))
        self.assertLess(derived['D_max_km'],30)
        self.assertGreater(derived['D_max_km'],10)

if __name__=='__main__': unittest.main()
