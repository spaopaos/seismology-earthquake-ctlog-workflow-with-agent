---
name: seismic-detection
description: 以 hypoDD 目录全量事件为模板，使用 PALM v5.0 MFT 引擎扫描连续波形，交付 CC≥0.4/0.6/0.8 三档独立事件目录。
---

# 模板匹配检测（PALM MFT，洱源规则）

## 概述

对预处理的连续波形执行多台互相关模板匹配（Match-Expand-Shift-Stack），以 hypoDD 重定位目录的全量事件为模板库，输出三档 CC 目录。后续联合重定位由 `seismic-post-detection-relocation` skill 接管。

## 前置条件

| 输入 | 来源 | 说明 |
|---|---|---|
| hypoDD 目录 CSV | relocation 阶段产出 | 含 event_id, lat, lon, depth, ML |
| 关联拾取 CSV | association 阶段产出 | gamma_assignments.csv |
| 连续波形库 | preprocess 阶段产出 | NET.STA/LOC.CHA/年/日/ 下的三分量速度 SAC |
| PALM ≥v5.0 | github.com/uafgeotools/capuaf 或用户提供 | 含 2_run_mft 启动器 |
| 台站坐标 CSV | preprocess/preprocess 阶段产出 | NET,STA,LOC,CHA,lat,lon,ele |

## 步骤

### 1. 构建模板相文件与台站文件

模板相文件（`mess.temp`）事件行名必须 ≥14 字符，推荐 `"发震时刻_事件ID"` 格式。事件行 6 列：名称, ISO 发震时刻, 纬度, 经度, 深度, 震级。相位行 3 列：`NET.STA, P_ISO, S_ISO`（仅含有 P+S 双拾取的台站）。

台站文件（`mess.sta`）**必须 5 列**：`NET.STA, lat, lon, ele, gain`。gain=1.0（数据已去响应）。按 NET.STA 去重（HH/HN 双位置码台站同坐标，保留一行）。

> ⚠ 4 列台站文件会被 PALM 的 get_sta_dict 路由为 StationXML 解析并**静默返回空站**，导致全部检测无声跳过。

### 2. 建日优先数据目录

PALM 要求 `data_dir/<YYYYMMDD>/<NET.STA>...` 布局。对台站优先的归档建软链树（不复制数据）：

```bash
for sta_dir in archive/*/*/; do
  for day_dir in "$sta_dir"*/; do
    day=$(basename "$day_dir")
    mkdir -p data_root/"$day"
    ln -s "$day_dir"*.SAC data_root/"$day"/
  done
done
```

### 3. 编写 PALM config

在 `2_run_mft/` 下建 `config_<CASE>.py`，关键参数：

```python
class Config(object):
  def __init__(self):
    self.min_snr = 0                  # 无 SNR 门（全量模板）
    self.min_sta = 4
    self.max_sta = 20                 # 按最早 P 截取
    self.temp_win_det = [1., 9.]      # P−1→P+9 s 检测窗
    self.temp_win_p = [0.5, 1.5]      # P 精修窗
    self.temp_win_s = [0.5, 2.5]      # S 精修窗
    self.trig_thres = 0.3             # 单道触发阈
    self.expand_len = 1.              # 峰扩展（~3 km 搜索半径）
    self.det_gap = 5.
    self.samp_rate = 50               # 检测采样率
    self.phase_samp_rate = 100        # 精修/振幅采样率
    self.freq_band = [1., 20.]        # 频带（用户可调）
    self.hypodd_depth_offset_km = 0.0 # 设 0，避免 +5 km 深度伪影
    self.association_origin_time_tolerance_sec = 2.0
    self.association_detection_cc_min = 0.3
    self.association_phase_cc_min = 0.4
    self.channel_priority = ["HH","BH","EH","HN","EN","SH"]
    self.location_priority = ["10","20","01","02","00",""]
```

### 4. 切取模板

```bash
cd 2_run_mft
python 2_cut_templates_<CASE>.py
```

> ⚠ 不要用 `conda run` 包装此步骤（会挂死）。直接 `python` 运行。

### 5. 全量扫描

```bash
python 3.1_run_mft_gpu_<CASE>.py
```

按 7 天段分批，逐段输出 `catalog_YYYYMMDD-YYYYMMDD.dat` + `phase_*.dat`。GPU 满载运行。

### 6. 关联与三档拆分

扫描完成后 PALM 自动运行关联（`associate_mft`），或手动触发：
- 2 s 发震时刻容差合并重复检出
- 输出：`catalog.csv`（独立事件）、`phase.csv`（逐台 CC 精修拾取）、`event.dat`、`dt.cc`

三档拆分：从 `catalog.csv` 按 `best_detection_cc` ≥0.4/0.6/0.8 筛出三份独立 CSV。

### 7. 新事件震级（向用户询问公式）

> ⚠ 此步骤**必须先向用户展示震级计算公式并请用户确认**，不可沿用固定公式。

询问内容：
- 震级计算公式（如 ML = lg(A) + R(Δ) 或其他）
- 量规函数表（R(Δ) 数值表，需用户提供）
- 振幅测量窗口与分量约定
- 多台合成规则（如 ±0.5 剔除再平均）
- 是否需要台站校正值

用户提供公式后再编写计算脚本，从 phase.csv 的逐台 S 振幅出发计算。

### 8. 新事件波形截取

对新事件（非模板自检命中）按 P−8→S+15 窗截取三分量 SAC（与 event_wf 库同规范），30 进程并行。

## 交付

| 产物 | 说明 |
|---|---|
| `catalog.csv` | 全部独立事件（含 best_cc） |
| `catalog_cc04/06/08.csv` | 三档 CC 目录 |
| `phase.csv` | 逐台 CC 精修拾取（含振幅） |
| `event.dat` | hypoDD 格式事件文件 |
| `dt.cc` | 互相关差分走时（联合重定位用） |
| 新事件波形库 | P−8→S+15 三分量 SAC |
| 新事件震级表 | 按用户确认的公式计算 |

## 关键坑（前人已踩，勿再踩）

1. **台站文件 4 列静默空站** → 必须 5 列含 gain
2. **PALM trim_stream 0.5 采样容差** 对日末 23:59:59.990 会全台判空 → 需改 1.5 采样（dataset.py + dataset_gpu.py）
3. **CUDA_VISIBLE_DEVICES 钉 GPU UUID** → torch 设备编号与 nvidia-smi 不同
4. **conda run 包装 cut_template 挂死** → 直跑
5. **associate_mft 要求整数模板 ID** → 发震时刻名需名字→顺序 ID 映射补丁
6. **event.dat 11 字段行** → 需统一为 10 字段，时间 8 位 HHMMSScc
7. **hypoDD.inp dt.cc 行后空行** → 会报 "line 10" 错
