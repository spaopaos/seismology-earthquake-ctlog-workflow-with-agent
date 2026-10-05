---
name: seismic-insar
description: 以 InSARHub（Sentinel-1 + HyP3 云端 GAMMA）捕获重定位目录中显著事件（M≥阈值）的同震形变：AOI/时间窗生成、质量评分配对、云端干涉图与 LOS 形变产品交付。
---

# 同震 InSAR 形变捕获（InSARHub / HyP3）

## 概述

从重定位目录筛选达到震级阈值的事件（时空聚类合并震群），生成 AOI 与震前/震后时间窗，经 InSARHub（vendored v0.4.2，`knowledge/repos/InSARHub`）搜索 Sentinel-1 SLC、按质量评分选择同震干涉对，提交 ASF HyP3 云端（GAMMA）生成干涉图，交付 LOS 形变栅格，与 `seismic-focal-mechanism` 机制解联合解读。

定位是**目录的形变学交叉验证**：M≥~4.5 浅源事件在植被区的 C 波段可探测性有限，捕获失败本身也是科学结论（深度/震级约束），要如实报告。

## 前置条件

| 输入 | 来源 | 说明 |
|---|---|---|
| 重定位目录 CSV | relocation / post_detection_relocation 产出 | 含 event_id, origin_time, lat/lon, ML（列名自适应）|
| insarhub 环境 | conda env `insarhub`（Python 3.11–3.12, numpy<2, GDAL≥3.8）| 官方 environment.yml；与地震学环境完全隔离，勿混装 |
| InSARHub v0.4.2 | knowledge/repos/InSARHub（MIT，vendored）| `conda run -n insarhub pip install --no-deps -e .` 安装 |
| EarthData 凭据 | `~/.netrc`（machine urs.earthdata.nasa.gov）| 免费注册；场景搜索/DEM/轨道/HyP3 提交必需 |
| CDSE / CDS 凭据 | `~/.netrc` / `~/.cdsapirc` | 轨道更早可得 / PyAPS 大气校正（可选）|

## 步骤（默认全自动；人只审最终形变图）

> 交互模式：config 置 `require_manual_review=true` 恢复两道人工闸门（任务单审阅、配对网络审阅）。默认自动模式下，选对由确定性策略完成（见步骤 3），**全部中间产物落盘备查**（stack json、质量库、selected_pairs.json、hyp3_jobs.json 批次状态、GUNW NetCDF、图件）。

### 1. 事件筛选与任务生成（`1_select_events.py`）

- 阈值：ML ≥ `--ml-min`（**用户确认**，默认 4.5）
- 时空聚类：Δt ≤ `--cluster-days`（默认 30 天）且 Δd ≤ `--cluster-km`（默认 30 km）的事件共享**一个搜索窗**（同一 S1 帧栈，避免重复搜索）
- **配对按事件拆 + bracket 全局感知**：每事件的 bracket =（前一个阈值事件 → 后一个阈值事件），**跨窗事件也计入**——跨两事件的干涉对是叠加信号，不是任何一个事件的同震图（洱源实证：42 天间隔双震拆两窗后，须防另一窗事件混入 bracket）
- 两事件落在同一 12 天重访间隔内 → 标记 `inseparable_with_neighbor`
- 每任务：AOI = 簇质心 ± `--buffer-deg`（默认 0.3°），搜索窗 = 首事件前 `--pre-days`（默认 90 天）至 末事件后 `--post-days`（默认 90 天）

### 2. 场景搜索与配对（`2_run_downloader.py`）

```bash
insarhub downloader -N S1_SLC --AOI lon1 lat1 lon2 lat2 \
  --start YYYY-MM-DD --end YYYY-MM-DD -w <workdir>/<job> --select-pairs
```

质量评分（基线/NDVI/雪盖/降水/地表覆盖）自动判健康/关注；产出每 stack 的 `network_*.png`（绿=健康、橙=关注）+ 质量库存档。

### 3. 策略选对（`5_select_pairs.py`）— 自动决策点

确定性策略，输出 `selected_pairs.json`（含策略全文备查）：
1. 候选 = 干净 bracket（单跨一个阈值事件）
2. 质量 = healthy；concern 仅在"某升降方向完全无 healthy"时作**标记回退**（`--prefer-both-directions`）
3. 排序 = 时间基线最短 → stack 健康率 → 名称
4. 每升降方向取 `--per-direction`（默认 1）对；升降属性由过境当地太阳时启发式判定（~18h 升 / ~06h 降，**新区域首次使用需对 ASF 元数据核验一次**）

### 4. 云端干涉图（`3_run_processor.py --pairs-json`）

```bash
insarhub processor -N Hyp3_S1 -w <workdir>/<job>/<stack> submit --pairs REF,SEC
```

**只提交策略选定的对**（`--pairs g1,g2` 逗号分隔）；HyP3 免费额度 8000 credits/月，20x4 looks 每任务 10 credits。refresh 轮询 → download 下载 GUNW。

### 5. 形变图（`6_make_maps.py`）

GUNW NetCDF → LOS 位移（d = −φ·λ/4π，正值朝卫星，C 波段 λ=0.0554658 m）+ 相干性掩膜（<0.3 默认）→ GeoTIFF(mm) + 阴影地形底图 PNG（虚线=相干性等值线，星=震中，标题含事件/stack/日期/质量标记）。

### 6. 产品清单（`4_collect_products.py`）

事件 ↔ 干涉对 ↔ 产品路径映射表 `insar_products.csv`。

## 参数分区

| [REGION-DEPENDENT]（须用户确认） | 默认 |
|---|---|
| 震级阈值 ml_min | 4.5（C 波段植被区可探测下限的经验值）|
| AOI 缓冲 / pre / post 窗 | 0.3° / 90 天 / 90 天（S1 重访 12 天）|
| 同震对选择（网络确认）| 质量评分自动 + 用户目视 |
| 大气校正（PyAPS/CDS）| 默认关；小信号事件建议开 |
| 聚类窗口 | 30 天 / 30 km |
| 同震对 bracket 约束 | 逐事件（前一阈值事件 → 后一阈值事件）|

| [FIXED] | 值 |
|---|---|
| 引擎 | HyP3 云端（GAMMA），`Hyp3_S1` 网络 |
| 数据 | Sentinel-1 SLC（ASF），S1 单帧栈 |
| 断点语义 | insarhub_config.json 工作目录状态，重跑显式传 flag 覆盖 |

## 交付（人审的最终层 = 形变图）

| 产物 | 说明 |
|---|---|
| `maps/*.png` + `*.tif` | **人审对象**：LOS 形变图（阴影地形底图+相干性掩膜+震中）与 GeoTIFF |
| `selected_pairs.json` | 策略选对结果 + 策略全文（审计轨迹）|
| `insar_jobs.json` | 捕获任务（AOI/时间窗/全局 bracket）|
| `network_*.png` + 质量库 | 每 stack 配对网络与评分（中间层复核）|
| `hyp3_jobs.json` + GUNW NetCDF | HyP3 批次状态与原始干涉产品（中间层复核）|
| `insar_products.csv` | 事件 ↔ 干涉对 ↔ 产品路径映射 |

## 关键坑（前人已踩/已确认，勿再踩）

1. **numpy<2 ABI 陷阱**（上游注释里有两处实证崩溃记录）：只在 `insarhub` env 内运行；libgdal-netcdf / rasterio / burst2safe 必须来自 conda-forge，不可 pip 替换
2. **凭据缺失表现**：downloader 搜索直接 401/空结果——先查 `~/.netrc`（格式 `machine urs.earthdata.nasa.gov login USER password PASS`）
3. **HyP3 额度**：8000 credits/月（20x4 looks 每任务 10）；只提交策略选定的对，勿提交整网络
4. **`--pairs` 是逗号分隔单参数**（`REF,SEC`），两参数形式会被拒（"expected 'reference,secondary'"）
5. **workdir 是两层结构** `<root>/<job>/<stack>/`：processor/分析工具按 stack 目录操作，别在 job 层找 config
6. **bracket 必须全局感知**：聚类拆窗后，各窗 bracket 仍须排除其他窗的阈值事件（洱源实证：0417→0710 跨双震曾被误判干净）
7. **升降轨判定是启发式**（过境当地太阳时 ~18h 升/~06h 降）：新区域首次使用与 ASF flightDirection 核验一次；洱源 p33/p135=降轨（晨）、p99=升轨（昏）
8. **S1 12 天重访**：震后窗要等首个震后景；两阈值事件同隔内不可分（如实标注）
9. **植被/季节**：雨季（6–9 月）相干性差，质量评分 NDVI/降水权重高；concern 回退对（长基线/跨季）成图质量存疑，图上已带质量标记
10. **GUNW 符号约定**：d = −φ·λ/4π，正值=朝卫星位移；成图前确认 unwrappedPhase 单位是弧度
11. **insarhub_config.json 是状态文件**：改参数必须命令行显式传 flag
12. **WSL I/O**：workdir 放 WSL 文件系统（~/...），勿放 /mnt/d
