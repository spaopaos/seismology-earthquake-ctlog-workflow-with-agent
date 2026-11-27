#!/usr/bin/env bash
# Restore offline runtime assets downloaded from the GitHub Release.
# Usage: scripts/restore_offline_assets.sh /path/to/dir-with-downloaded-assets
# Checks that the downloads are present, rejoins the split runtime archives
# (GitHub caps release assets at 2 GiB), unpacks the native binaries, and
# places the PhaseNet+ checkpoint.
set -euo pipefail

DL="${1:?usage: restore_offline_assets.sh <downloaded-assets-dir>}"
DL="$(cd "$DL" && pwd)"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 1) Check that every downloaded file is present and non-empty.
for f in plam-linux-x86_64.tar.gz.part-01 plam-linux-x86_64.tar.gz.part-02 \
         phasenet_plus-linux-x86_64.tar.gz.part-01 phasenet_plus-linux-x86_64.tar.gz.part-02 \
         phasenet2-linux-x86_64.tar.gz phasenet_plus_v1.pth bin-native-linux-x86_64.tar.gz; do
  [ -s "$DL/$f" ] || { echo "missing or empty download: $DL/$f" >&2; exit 1; }
done

# 2) Rejoin the split runtime archives into runtime_archives/.
mkdir -p runtime_archives assets/weights bin
cat "$DL/plam-linux-x86_64.tar.gz.part-01" "$DL/plam-linux-x86_64.tar.gz.part-02" \
  > runtime_archives/plam-linux-x86_64.tar.gz
cat "$DL/phasenet_plus-linux-x86_64.tar.gz.part-01" "$DL/phasenet_plus-linux-x86_64.tar.gz.part-02" \
  > runtime_archives/phasenet_plus-linux-x86_64.tar.gz
cp "$DL/phasenet2-linux-x86_64.tar.gz" runtime_archives/

# 3) Native binaries (hyp1.40, hypoDD, ph2dt, bundled shared libs) and
#    the PhaseNet+ checkpoint (already verified as downloaded).
tar -xzf "$DL/bin-native-linux-x86_64.tar.gz" -C bin
chmod +x bin/hyp1.40 bin/hypoDD bin/ph2dt
cp "$DL/phasenet_plus_v1.pth" assets/weights/

echo "Offline assets restored."
