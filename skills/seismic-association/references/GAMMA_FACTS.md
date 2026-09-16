# GaMMA 代码与论文事实核查

核查日期：2026-09-11（振幅接口于 2026-09-13 修正）· 基准：`knowledge/repos/GAMMA@80394dd`（只读钉版）+ `knowledge/library/raw/assets/extracted/zhu-2022-gamma.md`

## 输入格式（docs/example_phasenet.ipynb 实测提取）

- picks CSV → 重命名：`station_id→id, phase_time→timestamp, phase_type→type, phase_score→prob, phase_amplitude→amp`；
- **震相类型小写** `p`/`s`（`calc_time` 用 `vel[x]` 索引，键为小写）；
- **接口输入 `amp` 为线性速度振幅，单位 m/s**。`gamma/utils.py::convert_picks_csv` 内部执行 `log10(amp * 1e2)`，建模特征才是 log10(cm/s)。不要把内部特征与外部输入混淆；适配器不乘 1e6、不提前取对数。缺失/非数值、非有限、非正振幅在适配器中过滤并分类计数，见 `input_filter_stats.json`。
- 振幅数值回归：`scripts/verify_gamma_amplitude.py --gamma-repo knowledge/repos/GAMMA`；包含实际钉版转换函数对拍和旧预取对数路径的阴性对照，不执行事件关联。
- stations CSV：`id, longitude, latitude, elevation_m`；`x(km)/y(km)` 用 aeqd 投影（当前wrapper使用经度圆均值、纬度中位数，兼容跨日期变更线），`z(km) = -elevation_m/1e3`；
- 当前wrapper的区域设置：投影后台站范围按显式 `margin_km` 外扩；搜索深度上界由 `depth_max_km` 指定。经纬度范围只记台站范围，不再作为投影搜索框。该选择属于项目实现，不能冒称原论文规定。

## 代码事实

| # | 事实 | 位置 |
|---|---|---|
| G1 | 入口 `association(picks, stations, config, event_idx0, method="BGMM")`；DBSCAN 时间切段后逐段 BGMM | `gamma/utils.py` |
| G2 | `dbscan_eps` 默认10秒；当前代码在 `(t,x/Vp,y/Vp)` 空间聚类，eps 为邻域半径，不能用最大 S-P 时差作硬下限。PhaseNet 示例用15秒；`estimate_eps()` 是经验候选，由用户选择是否采用 | `docs/README.md`、`docs/example_phasenet.ipynb`、`utils.py::hierarchical_dbscan_clustering/estimate_eps` |
| G3 | 当前wrapper从显式区域配置取得源深度上界；走时网格还覆盖台站高程。分层模型的最深层顶不等于最大事件深度 | `scripts/run_gamma.py` 与 `seismic_ops.py::initialize_eikonal` |
| G4 | 内置震级/振幅衰减为写死的 Picozzi et al. 2018 系数（c0=1.08, c1=0.93, c3=−0.015），区域外不适用 | `seismic_ops.py::calc_amp/calc_mag` |
| G5 | 钉版以 `id + type` 区分仪器组与P/S，按最小到时残差保留每事件每组每震相一条；P/S必须同时保留 | `utils.py::convert_picks_csv/associate` |
| G6 | `ncpu` 自动：`max(1, min(len(clusters)//4, 32, cpu_count-1))` | `utils.py` |
| G7 | `covariance_prior` 文档原话：1D/均匀模型下用大值防劈裂；过大会合并事件 | `docs/README.md` |
| G8 | BGMM 示例 `oversample_factor=5`（README 默认 10）；钉版要求正整数，更大增加候选分量与计算量，不保证更优 | example / README |
| G9 | eikonal 时距表现算（numba，50 次 sweeping 迭代收敛 1e-6）；P/S 分层共用网格 | `seismic_ops.py` |
| G10 | 过滤项：`min_picks_per_eq` / `min_p_picks_per_eq` / `min_s_picks_per_eq` / `min_stations` / `max_sigma11`（s）/ `max_sigma22`（log 振幅）/ `max_sigma12` | `utils.py` |

## 论文事实

- eps 来源核查（2026-09-13）：论文 §4 用 DBSCAN 分段以降低长序列的计算成本，未给“孔径/Vs”或“孔径×(1/Vs−1/Vp)”作为 eps 下限。当前 `estimate_eps()` 使用第二个非零近邻距离的均值和标准差：`1.5*(mean(d2)+2*std(d2))/Vp`；这是原仓库启发式，不是论文中的最优值定理。执行时先推荐10秒、展示估计值，再按当前skill 获取或沿用用户选择。

- BGMM 无监督聚类；到时双曲线 moveout + 振幅随距离衰减联合建模；EM 同时估计位置/发震时刻/震级；
- 合成测试：0.5 s 到时噪声下稳健；振幅信息有贡献；
- Ridgecrest 6 天：vs SCSN 召回 0.94，vs 模板目录 0.61——**小事件召回有限是算法固有能力边界，漏检部分由下游 MESS 补位**；
- 初始化使用过采样。论文所述局限与当前钉版代码实现分别核对；当前去重行为以 G5 为准。

## 当前交接

输入保留原始仪器组、P/S、极性、幅值和源行号；台站表与拾取完整ID一致。返回元组命名为 pick_index/event_index/gamma_score，输出 gm 事件ID、经纬度和深度，以及完整关联拾取。bfgs_bounds 是必需配置；走时网格覆盖搜索框和相对台站深度，避免插值边缘裁切。
