#!/usr/bin/env python3
"""Generate a labeled interface fixture in physical units, not an observed earthquake dataset."""
import argparse
import csv
import json
import shutil
from pathlib import Path
import numpy as np
from obspy import Trace, UTCDateTime

def build(root):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=False)
    group='ZZ.DEMO..HH'
    date='2020-01-02'
    files={}
    n=8640000
    meta={'group':group,'utc_day':date,'units':'m/s','physical_quantity':'ground_velocity',
          'orientation_verified':True,'orientation_source':'Synthetic Cartesian Z-up/N/E axes specified by generator',
          'response_verified':True,'response_source':'Synthetic velocity arrays generated directly in m/s; no instrument response applied',
          'analysis_band_hz':[1.0,40.0],'group_min_raw_sampling_rate_hz':100.0,
          'usable_3c_intervals':[[2000,58000]],'components':{}}
    for i,c in enumerate('ZNE'):
        data=np.zeros(n,dtype='float32')
        t=np.arange(60000)/100
        # Deterministic finite wave packets; no seismological truth claim.
        data[:60000]=((i+1)*1e-6*np.sin(2*np.pi*3*t)*np.exp(-((t-300)/5)**2)).astype('float32')
        tr=Trace(data,header={'network':'ZZ','station':'DEMO','location':'','channel':'HH'+c,
                              'sampling_rate':100.0,'starttime':UTCDateTime(date),'calib':1.0})
        name=group+c+'.20200102.mseed'
        tr.write(str(root/name),format='MSEED',encoding='FLOAT32')
        files[c]=name
        meta['components'][c]={'data_intervals':[[0,60000]],'usable_intervals':[[2000,58000]]}
    (root/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    with (root/'daily_manifest.csv').open('w',newline='') as f:
        row={'group':group,'date':date,'status':'PARTIAL_DAY','metadata':'metadata.json',**{'file_'+c:p for c,p in files.items()}}
        writer=csv.DictWriter(f,fieldnames=list(row)); writer.writeheader(); writer.writerow(row)
    shutil.copyfile(__file__,root/'processing_script.py')
    for name,value in [('effective_config.json',{'fixture':'synthetic_interface_only','sampling_rate_hz':100}),
                       ('sources.json',{'kind':'synthetic','generator':'processing_script.py','not_observed_data':True}),
                       ('qc.json',{'status':'SYNTHETIC_INTERFACE_FIXTURE','scientific_validation':'NOT_TESTED'})]:
        (root/name).write_text(json.dumps(value,indent=2)+'\n')
    (root/'archive_provenance.json').write_text(json.dumps({'processing_script':'processing_script.py',
        'effective_config':'effective_config.json','source_manifest':'sources.json','qc_summary':'qc.json'},indent=2)+'\n')
    return root

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--out',required=True)
    build(ap.parse_args().out)
