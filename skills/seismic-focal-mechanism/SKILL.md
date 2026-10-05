---
name: seismic-focal-mechanism
description: 以 PhaseNet+ 加权初动极性 + 实测 S/P 振幅比驱动 SKHASH v1.1 网格搜索，产出 A/B/C/D 分级震源机制目录，含反极性台识别验证与圆统计规则。
---

# 震源机制反演（SKHASH，洱源规则）

## 概述

对 relocation 阶段目录事件，用 PhaseNet+ 深度学习初动极性（连续置信分数 −1~+1，加权使用）+ 事件波形实测 S/P 振幅比，SKHASH v1.1 网格搜索断层面解，按 HASH（Hardebeck & Shearer 2002）原版判据分 A/B/C/D 四级。极性直接来自 picking 阶段的 PhaseNet+ 输出，无需人工逐台读初动。

## 前置条件

| 输入 | 来源 | 说明 |
|---|---|---|
| hypoDD 目录 CSV | relocation 阶段产出 | 含 event_id, lat/lon/depth + erh/erz（作扰动幅度） |
| gamma_assignments.csv | association 阶段产出 | P 相 `polarity_score` 列（PhaseNet+ 加权极性） |
| 连续波形归档 | preprocess 阶段产出 | 100 Hz m/s 三分量，含 daily_manifest.csv |
| 台站坐标 CSV | preprocess/association 产出 | `id,latitude,longitude,elevation_m` 或分列格式 |
| P 波层状速度模型 | 区域输入 | 分层 Vp-深度表；**必须向用户确认，不可默认套用** |
| SKHASH v1.1 | knowledge/repos/SKHASH | 已含 numpy≥2/pandas3 兼容四补丁，勿换 pip 版 |

## 步骤

### 1. 构建输入（`1_build_inputs.py`）

从 assignments/catalog/stations/vmodel 生成 SKHASH `IN/`：
- `pol_dl.csv`（$dlpfile）：P 相极性分数**全量写入**（阈值由控制文件施加，不在生成时过滤）
- `catalog.csv`（$catfile）：事件位置 + erh/erz（ISO8601 Z 时间）
- `stations.csv`（$stfile）、`vmodel_layers.txt`（阶梯版：1 km 步长，每步 +0.001 km/s 严格递增）+ `vmodel_gradient.txt`

### 2. 事件波形库（`2_cut_event_waveforms.py`）

窗口（须用户确认）：P−8 s → S+15 s；仅 P：P−8 → P+20；仅 S：S−12 → S+15。
只切不改（不滤波/不去响应/不归一化），补零段原样保留，manifest 记录可用区间覆盖率 usable_frac。SAC 头：t0=P、t1=S、o=发震时刻。并行 worker 按 CPU 核数。

### 3. S/P 振幅（`3_measure_sp_amplitudes.py`）

仅取 `phase_pair==P_S 且 usable_frac==1` 的对：
- 噪声窗 [P−5, P−1]：Z 与 max(|N|,|E|)
- P 窗 [P+0.02, P+1.0]：|Z| 最大值
- S 窗 [S+0.02, S+1.0]：水平最大值
- SNR 门控（ratmin）与比值计算交给 SKHASH；此处只交四列原始振幅

### 4. 反极性台检查（`4_check_polarity_reversal.py`）— **决策点**

强震动仪器族（如 HN）常整族硬件反号。两轮判据：
1. **共址独立证据**：同台双仪器族（HH/HN）或坐标 ≤1 km 跨台对，共同事件极性符号一致率 <~35%（正常 74%+）判反号候选
2. **机制一致率跳升验证**：对候选跑一轮无反转 SKHASH 后，取 out_polagree 的极性准确率低的一侧反转；反转后一致率须跳升至 >60% 才采纳

**反转台名单必须向用户展示证据表并确认后**写入 reverse.csv（列：network,station,location,channel,start_time,end_time）。
剩余一致率 50% 出头的台属 DL 极性噪声而非系统反号，**停止迭代防过拟合**。

### 5. 运行 SKHASH（`5_run_skhash.py`）

生成控制文件并运行（先无反转版 → 步骤 4 → 加反转表重跑）。

参数分区：

| [REGION-DEPENDENT]（须用户确认） | 洱源默认 |
|---|---|
| 极性阈值 min_polarity_weight | 0.3（HASH"仅冲动型初动"的等价映射） |
| 速度模型 | CRUST1.0 区域 4 层 |
| delmax（最大震中距 km） | 120 |
| num_cpus | 8 |
| 反转台名单 | 迭代确认后填写 |

| [FIXED]（方法常量） | 值 |
|---|---|
| badfrac | 0.1（H&S 2002 默认；0.15 试验对 A 无增益） |
| npolmin / badmin | 8 / 2 |
| nmc / maxout / dang / azmax | 30 / 500 / 5° / 10° |
| ratmin | 2 |
| max_agap / max_pgap / qbadfrac | 90° / 60° / 0.3（SKHASH 默认） |
| 振幅/波形窗口 | 见步骤 2/3 |

### 6. 整理目录（`6_parse_mechanisms.py`）

每事件最优解（prob_mech 降序 + 质量升序取首个）+ n_solutions → `mechanisms_catalog.csv`；`qc_summary.json` 汇总质量分档、极性准确率 <60% 的可疑台清单。

## 交付

| 产物 | 说明 |
|---|---|
| `mechanisms_catalog.csv` | 逐事件最优解 + 全套诊断量（strike/dip/rake, quality, misfit, 概率, 台站数, gap…）+ hypoDD 位置参考 |
| `qc_summary.json` | 质量分档统计 + 可疑极性台清单 |
| `OUT/` | SKHASH 原生输出（out.csv 每解一行、out_polagree、out_polinfo） |
| `colocated_polarity_check.json` | 反极性判定的证据表 |
| 事件波形库 | P−8→S+15 三分量 SAC + manifest（下游震级/模板复用） |

## 结果统计规则

strike/rake **必须用圆统计**（±180° 双节面折返会把线性均值带偏），dip 用线性统计。
A 级判据是 HASH 原版，不可为凑 A 数改动；只能通过数据质量控制（阈值、反转台）迭代。

## 关键坑（前人已踩，勿再踩）

1. **上游 SKHASH v1.1 不兼容 numpy≥2 / pandas 3** → 用仓库副本（已打 4 补丁：fun.py 标量提取、in_sp/in_sta 的 location 码 str 化×3）；补丁对旧版 numpy 同样兼容
2. **$plfile 反转表时间必须带时区**（如 `2025-03-01T00:00:00+00:00`），naive/aware 混比 pandas 3 直接拒绝
3. **阶梯速度模型必须严格递增** → 每 km +0.001 km/s 步进，否则 SKHASH QC 拒绝
4. **大事件 ≠ 好机制**：强震动使近台初动置信崩塌（振幅 6–10× A 级事件）、出射角空隙 >60° 被直接拒解，属预期行为，不要为此放宽全局阈值
5. **strike/rake 线性均值被 ±180° 折返误导** → 圆统计
6. **反极性台迭代必须带闸门**（反转后一致率 >60% 跳升），否则把 DL 噪声当反号翻转台会过拟合
7. **单事件零解时上游 out.pol_agree 抛 KeyError**（已知 bug，全量运行不受影响）
8. **WSL 重负载 vmmem 满时 `wsl` 命令可 E_UNEXPECTED** → 长扫描前查内存，必要时分批
