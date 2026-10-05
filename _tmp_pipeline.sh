#!/bin/bash
# Autopilot: poll HyP3 -> download -> make maps
set -x
export PATH="/home/spaopaos/miniconda3/envs/insarhub/bin:$PATH"
ROOT=/home/spaopaos/insar_test_eryuan
LOG=/home/spaopaos/insar_test_eryuan/autopilot.log

for i in $(seq 1 30); do
  for d in $ROOT/job_001/p135_f503 $ROOT/job_001/p99_f1265 \
           $ROOT/job_002/p33_f507 $ROOT/job_002/p99_f1265; do
    insarhub processor -N Hyp3_S1 -w "$d" refresh >> "$LOG" 2>&1
  done
  # count incomplete jobs across batch files
  N=$(python3 - <<'EOF'
import json, glob
n = 0
for f in glob.glob('/home/spaopaos/insar_test_eryuan/job_*/p*/hyp3_jobs.json'):
    doc = json.load(open(f))
    def count(o):
        if isinstance(o, dict):
            if 'status' in o and isinstance(o['status'], str):
                return 0 if o['status'].upper() in ('SUCCEEDED',) else 1
            return sum(count(v) for v in o.values())
        if isinstance(o, list):
            return sum(count(v) for v in o)
        return 0
    n += count(doc)
print(n)
EOF
)
  echo "poll $i: incomplete=$N" >> "$LOG"
  if [ "$N" = "0" ]; then
    for d in $ROOT/job_001/p135_f503 $ROOT/job_001/p99_f1265 \
             $ROOT/job_002/p33_f507 $ROOT/job_002/p99_f1265; do
      insarhub processor -N Hyp3_S1 -w "$d" download >> "$LOG" 2>&1
    done
    python3 /mnt/d/yunan/ctlog_work/skills/seismic-insar/scripts/6_make_maps.py \
      --jobs $ROOT/insar_jobs.json --workdir-root $ROOT \
      --selected $ROOT/selected_pairs.json \
      --outdir $ROOT/maps >> "$LOG" 2>&1
    echo "AUTOPILOT_DONE" >> "$LOG"
    exit 0
  fi
  sleep 300
done
echo "AUTOPILOT_TIMEOUT_after_30_polls" >> "$LOG"
