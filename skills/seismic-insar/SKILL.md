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

## 步骤

### 1. 事件筛选与任务生成（`1_select_events.py`）

- 阈值：ML ≥ `--ml-min`（**用户确认**，默认 4.5）
- 时空聚类：Δt ≤ `--cluster-days`（默认 30 天）且 Δd ≤ `--cluster-km`（默认 30 km）的事件共享**一个搜索窗**（同一 S1 帧栈，避免重复搜索）
- **配对按事件拆**：每事件有独立 bracket（前一阈值事件之后 → 后一阈值事件之前）；**干净同震对 = 一景在 bracket 内事件前、一景在事件后**。跨越两个事件的对是叠加信号，不可当任一事件的同震图
- 两事件落在同一 12 天重访间隔内 → 标记 `inseparable_with_neighbor`（InSAR 无法分离，如实交付）
- 每任务：AOI = 簇质心 ± `--buffer-deg`（默认 0.3°），搜索窗 = 首事件前 `--pre-days`（默认 90 天）至 末事件后 `--post-days`（默认 90 天）
- 输出 `insar_jobs.json`（人可读可改）

### 2. 场景搜索与配对（`2_run_downloader.py`）— **决策点**

```bash
insarhub downloader -N S1_SLC --AOI lon1 lat1 lon2 lat2 \
  --start YYYY-MM-DD --end YYYY-MM-DD -w <workdir> --select-pairs
```

配对由基线 + 质量评分（NDVI/雪盖/降水/地表覆盖）自动打分。**必须把配对网络图与评分表给用户目视确认**：同震对 = 震前最佳 × 震后最佳（跨度大、季节差异大的对相干性差）。确认后才进入步骤 3。

### 3. 云端干涉图（`3_run_processor.py`）

```bash
insarhub processor -N Hyp3_S1 -w <workdir> submit    # 提交选定对
insarhub processor -N Hyp3_S1 -w <workdir> refresh   # 轮询状态（--watch 持续）
insarhub processor -N Hyp3_S1 -w <workdir> download  # 完成后下载
```

HyP3 免费额度有限——**只提交用户确认的同震对**，不要提交整条基线网络。

### 4. 产品收集（`4_collect_products.py`）

扫描各任务 workdir：GUNW/干涉图清单、LOS 位移与相干性栅格（`insarhub utils h5-to-raster` 转 GeoTIFF）、事件↔产品映射表 `insar_products.csv`。

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

## 交付

| 产物 | 说明 |
|---|---|
| `insar_jobs.json` | 捕获任务（AOI/时间窗/事件清单）|
| 配对网络 + 评分 | 每任务 PNG/CSV（downloader 产出）|
| GUNW 干涉图产品 | HyP3 下载（含 unwrapped/corr）|
| LOS 形变 GeoTIFF | h5-to-raster 转换 |
| `insar_products.csv` | 事件 ↔ 干涉对 ↔ 产品路径映射 |

## 关键坑（前人已踩/已确认，勿再踩）

1. **numpy<2 ABI 陷阱**（上游注释里有两处实证崩溃记录）：只在 `insarhub` env 内运行；libgdal-netcdf / rasterio / burst2safe 必须来自 conda-forge，不可 pip 替换
2. **凭据缺失表现**：downloader 搜索直接 401/空结果——先查 `~/.netrc`（格式 `machine urs.earthdata.nasa.gov login USER password PASS`）
3. **HyP3 额度**：同震模式每窗只提交 1–3 对，别把整网络丢上去
4. **S1 重访 12 天**：震后窗要等首个震后景才有同震对；紧急时可先缩短 post 窗出首对，后续补
5. **植被/季节**：云南雨季（6–9 月）相干性差，质量评分 NDVI/降水权重高；跨季对慎选
6. **M~5 信号 mm–cm 级**：对流层延迟可同量级——重要事件开 PyAPS 校正并用多对交叉验证
7. **insarhub_config.json 是状态文件**：改参数必须命令行显式传 flag，静默沿用旧值
8. **WSL I/O**：workdir 放 WSL 文件系统（~/...），勿放 /mnt/d（慢且符号链接行为怪）
