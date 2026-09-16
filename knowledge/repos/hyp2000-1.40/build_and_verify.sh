#!/bin/bash
# 从钉版源码构建 HYPOINVERSE 1.40 并用官方 testone 金标验证。
# 用法: bash build_and_verify.sh [输出二进制路径]
# 基准: knowledge/repos/hyp2000-1.40（USGS 官方源码包，2014-09，最终版）
# 验证: 官方 testone 输入 + 参考输出；.sum/.arc 必须与参考逐字节一致，
#       .prt 仅允许 RUN ON 时间戳与命令文件名两行差异。
# 注意: testone.hyp 的输出文件名与参考输出同名，本脚本在临时目录中把输出
#       重定向到 out/ 后再比对，不覆盖参考。
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$SRC/hyp1.40}"
BUILD=$(mktemp -d); TEST=$(mktemp -d)
trap 'rm -rf "$BUILD" "$TEST"' EXIT

cp -r "$SRC"/source/* "$BUILD"/
cd "$BUILD"
for f in *.f *.for; do
  [ "$f" = "integer.for" ] && continue   # include 文件，非独立编译单元
  gfortran -c -std=legacy -w "$f" -o "${f%.*}.o"
done
gfortran -std=legacy -w *.o -o hyp1.40

cd "$TEST"
cp "$SRC"/testone/* .
mkdir out
sed 's/testone\.prt/out\/testone.prt/; s/testone\.sum/out\/testone.sum/; s/testone\.arc/out\/testone.arc/' \
  testone.hyp > testone_run.hyp
(echo "@testone_run.hyp"; for i in $(seq 1 40); do echo; done; echo "loc"; echo "stop") \
  | "$BUILD/hyp1.40" > run.log 2>&1

ok=1
for f in sum arc; do
  if cmp -s "out/testone.$f" "testone.$f"; then
    echo "GOLDEN PASS: $f 逐字节一致"
  else
    echo "GOLDEN FAIL: $f 与参考不一致"; ok=0
  fi
done
prt_diff=$(diff \
  <(sed 's/-0\.00/ 0.00/g' out/testone.prt | grep -vE "RUN ON|\(F\)|COMMANDS:") \
  <(sed 's/-0\.00/ 0.00/g' testone.prt | grep -vE "RUN ON|\(F\)|COMMANDS:") \
  | grep "^[<>]" | wc -l)
if [ "$prt_diff" -eq 0 ]; then
  echo "GOLDEN PASS: prt 仅时间戳/路径/负零格式差异"
else
  echo "GOLDEN CHECK: prt 有 $prt_diff 行其他差异，请人工核对"; ok=0
fi
[ "$ok" = 1 ] || exit 1

mv "$BUILD/hyp1.40" "$OUT"
echo "BUILD OK -> $OUT"
sha256sum "$OUT"
