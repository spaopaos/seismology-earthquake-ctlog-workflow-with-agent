---
name: seismic-insar
description: 以 InSARHub（Sentinel-1 + HyP3 云端 GAMMA）捕获重定位目录中显著事件（M≥阈值）的同震形变：AOI/时间窗生成、质量评分配对、云端干涉图与 LOS 形变产品交付。
---

# 同震/震群 InSAR 形变捕获（InSARHub / HyP3）

## 概述 — 两类产品

1. **单震同震形变**（`1→6` 号启动器）：从重定位目录筛 M≥阈值事件，逐事件生成干净同震干涉对（全局 bracket），HyP3 云端处理，交付 LOS 形变图
2. **震群长周期时序**（`7_swarm_timeseries.py`，InSARHub 规范链原生形态）：对整个震群时间窗（聚类合并窗）在选定 stack（升降轨各一）上提交**全质量网络**（约 15-45 对/stack），云端批量干涉后跑 MintPy SBAS，交付**震群总形变、速度场与逐期时间序列**——时间序列同时解析震间慢形变/瞬变（无震蠕滑、流体迁移等），与单震产品互补

两类产品共用搜索/配对/处理前三环；额度预算：单震 ~10 credits/对，震群网络每 stack 数百 credits（提交前向用户报告对数与预算）。

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

GUNW NetCDF → LOS 位移（d = −φ·λ/4π，正值朝卫星，C 波段 λ=0.0554658 m）+ 相干性掩膜（<0.3 默认）→ **远场参考化（扣除 15–40 km 环带中位数，GAMMA unw 带整景常数偏移）** → GeoTIFF(mm) + 阴影地形底图 PNG（虚线=相干性等值线，星=震中，标题含事件/stack/日期/质量标记/参考偏移量）+ sidecar `<name>.json`（reference_offset_mm、farfield_px）。

### 6. 交付前 QA 门（`8_qa_products.py`）— **agent 责任，用户只审科学**

用户目视发现的每个缺陷都是 agent 的 QA 空洞。交付任何图件前必跑本门禁（exit 1 即拦截）：

| 检查 | FAIL 阈值 | WARN 阈值 |
|---|---|---|
| 研究窗覆盖（相干性有效像素占比）| < 0.05（帧未覆盖/全失相干，即 p33_f507 陷阱）| < 0.30 |
| 震中最近有效像素距离 | > 10 km | — |
| 近场信号 vs 远场噪声 SNR（参考化后计算）| — | < 2（可能是真未检出，如实报告不拦截）|
| 远场参考化环带像元数 | — | < 200（offset 不可靠，绝对值存疑）|

FAIL → 修复动作（重选次优对重提交/换 stack）；WARN 必须在交付说明中写明。**原则：任何"用户本可目视发现"的问题（空图、错位、缺层、大片饱和黑块）都必须先被这道门拦下。**

### 7. 产品清单（`4_collect_products.py`）

事件 ↔ 干涉对 ↔ 产品路径映射表 `insar_products.csv`。

### 8. 震群长周期时序（`7_swarm_timeseries.py`）— 第二类产品

```bash
# prepare: 合并窗搜索 + 选定 stack（整数 PATH:FRAME 形如 33:502）的质量网络
python 7_swarm_timeseries.py --action prepare --jobs insar_jobs_merged.json \
  --stacks 33:502 99:1265 --workdir-root insar_swarm
# submit: 每 stack 整网一个批次（裸 submit 自动加载 stack json 网络对）
python 7_swarm_timeseries.py --action submit --workdir-root insar_swarm
# analyze: 下载完成后每 stack 跑 MintPy SBAS
python 7_swarm_timeseries.py --action analyze --workdir-root insar_swarm
```

交付：`velocity.h5` / `timeseries.h5` / 累计形变图（每 stack 的 mintpy 输出目录）。
注意：**prepare 后先向用户报告每 stack 网络对数与 credit 预算再 submit**（典型 15-45 对/stack，~10 credits/对）；SBAS 的对网络是 InSARHub 质量评分选定集，勿手工增删（时序反演依赖网络闭合性）；SBAS 层的大气校正（MintPy correct_troposphere，需 CDS）按跨区域决策表判定。

## 跨区域决策点（agent 自主判定或升级询问，不得沿用上一区域的经验值）

| 决策 | 默认 | 判定规则（按证据） | 升级询问条件 |
|---|---|---|---|
| **对流层大气校正** | 出图后判定，不预扣 | 证据三查：①预估信号幅度（Mw/深度 → 峰值 LOS 量级）②图上条纹形态（与地形相关的长波条纹=对流层；紧凑象限斑图=形变）③升降轨一致性（大气在两视角不相关，形变一致）。信号 ≲ 大气噪声量级（湿季/山区/小事件）→ 应用 GACOS 或 PyAPS/ERA5 校正并重出图对比 | 证据不明确、校正凭据缺失（GACOS 注册/CDS API）、事件科学重要性高 |
| **电离层校正** | C 波段关 | 频段规则：电离层延迟 ∝ 1/f²——Sentinel-1 C 波段可忽略；L 波段路径（NISAR_GSLC）或高纬度（极光区）/超长基线 → 开 split-spectrum | 换 L 波段任务或纬度 >60° 时询问用户确认 |
| **ml_min 可探测阈值** | 4.5 起议 | 区域背景：植被覆盖/沙漠/雪盖气候带 + 事件深度分布 → 给出建议值与依据 | 每个新区域首次必须用户确认 |
| **升降轨判定** | 当地太阳时启发式 | 新区域**首次**运行后与 ASF flightDirection 元数据核验一次，不符则修正 | — |
| **相干性阈值 coh-min** | 0.3 | 首批图解缠质量差（掩膜破碎/孤岛）时上调，异常光滑时下调 | 阈值改动需在 manifest 记录理由 |
| **季节窗口解释** | 质量评分自动 | 质量评分里 NDVI/雪/降水权重要结合区域季节解释（雨季/雪季配对质量系统性差） | — |

校正实施程序（agent 判定触发后）：GACOS=按对日期下载改正文件逐像素扣除；PyAPS/ERA5=`insarhub` env 内 MintPy 工具链（需 CDS 凭据）；扣除后重跑 `6_make_maps.py` 出对比图，原始与校正两版**都保留交付**。

## 参数分区

| [REGION-DEPENDENT]（须用户确认或 agent 按跨区域决策表判定） | 默认 |
|---|---|
| 震级阈值 ml_min | 4.5（C 波段植被区可探测下限的经验起点）|
| AOI 缓冲 / pre / post 窗 | 0.3° / 90 天 / 90 天（S1 重访 12 天）|
| 同震对选择 | 策略自动 + 网络图落盘复核 |
| 大气/电离层校正 | 见"跨区域决策点"表（C 波段电离层默认关；对流层出图后按证据判定）|
| 聚类窗口 | 30 天 / 30 km |
| 同震对 bracket 约束 | 逐事件（前一阈值事件 → 后一阈值事件，全局感知）|

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
| `insar_swarm/*/mintpy/` | **第二类产品（人审对象）**：震群 SBAS 速度场 `velocity.h5`、逐期 `timeseries.h5`、累计形变 |

## 关键坑（前人已踩/已确认，勿再踩）

1. **numpy<2 ABI 陷阱**（上游注释里有两处实证崩溃记录）：只在 `insarhub` env 内运行；libgdal-netcdf / rasterio / burst2safe 必须来自 conda-forge，不可 pip 替换
2. **凭据缺失表现**：downloader 搜索直接 401/空结果——先查 `~/.netrc`（格式 `machine urs.earthdata.nasa.gov login USER password PASS`）
3. **HyP3 额度**：8000 credits/月（20x4 looks 每任务 10）；只提交策略选定的对，勿提交整网络
4. **`--pairs` 是逗号分隔单参数**（`REF,SEC`），两参数形式会被拒（"expected 'reference,secondary'"）
5. **workdir 是两层结构** `<root>/<job>/<stack>/`：processor/分析工具按 stack 目录操作，别在 job 层找 config
6. **bracket 必须全局感知**：聚类拆窗后，各窗 bracket 仍须排除其他窗的阈值事件（洱源实证：0417→0710 跨双震曾被误判干净）
7. **升降轨判定是启发式**（过境当地太阳时 ~18h 升/~06h 降）：新区域首次使用与 ASF flightDirection 核验一次；洱源 p33/p135=降轨（晨）、p99=升轨（昏）
8. **帧覆盖陷阱（洱源实证）**：按质量率择优选 stack 不保证帧 footprint 覆盖研究窗——p33_f507 东缘 99.931°E 差 0.007° 未及研究区西界 99.938°E，小图全空。**SBAS 选栈同理（洱源实证 p33_f502：42 对全部提交下载跑完 SBAS 后才发现帧东缘切过震群，震中带全零、整帧 94% 无效——沉没成本 420 credits + 数小时）**。同震路径下载后有 6_make_maps 覆盖校验兜底；**7_swarm_timeseries 的 prepare 在 submit 前就必须对每个候选 stack 用场景足迹/任一产品 tif bounds 核对研究窗覆盖**；覆盖失败 → 换帧重选（如洱源正确选择是 p135_f503 而非 p33_f502）
9. **S1 12 天重访**：震后窗要等首个震后景；两阈值事件同隔内不可分（如实标注）
10. **植被/季节**：雨季（6–9 月）相干性差，质量评分 NDVI/降水权重高；concern 回退对（长基线/跨季）成图质量存疑，图上已带质量标记
11. **产品符号约定**：d = −φ·λ/4π，正值=朝卫星位移（unw_phase 单位弧度）；产品为 UTM 投影 GeoTIFF zip，成图须 CRS 变换与震中窗裁剪。**polar 色标下红端=正=朝卫星——图注文字必须与色标极性一致（副标题曾写反 blue=toward，实为 red=toward）**。绝对符号链可用地震学机制锚定：降轨（朝东看）红/蓝象限应与"右旋 NW 走滑"模板同号（洱源实证 331° 边界 +0.83）
12. **insarhub_config.json 是状态文件**：改参数必须命令行显式传 flag
13. **环境隔离**：启动器跟随 sys.executable 找 insarhub 可执行——必须用 insarhub 环境 python 运行；误用其他环境会失败（已加守卫报错）
14. **WSL I/O**：workdir 放 WSL 文件系统（~/...），勿放 /mnt/d
15. **整景参考偏移（洱源实证）**：GAMMA 解缠产品携带任意常数参考，整景可偏离零点数十 mm（实测远场环带中位数 −49/−29/+38 mm）——不扣除会把大半像元推出对称色标且污染 QA 的 sig/SNR。**标准步骤：成图与 QA 前一律扣除远场环带（15–40 km、相干≥阈）中位数**（`6_make_maps.farfield_offset()`，QA 记录 `reference_offset_mm`；环带 <200 px 时 WARN）**衍生网格同样适用：物理校正/差分等任何加场操作都会重新引入区域偏移，写出前必须再次扣环带（洱源图 15 复发实证：ERA5 Δ场 +20mm 把双极顶进红色饱和区，图面与统计自相矛盾，视觉门禁捕获）**
16. **GMT polar 主色标越界=黑/白**：polar 母 cpt 自带 `B black / F white`——超出对称量程的像元会画成纯黑/纯白，看起来像数据空洞（洱源实证：黑色区域实为超 ±40mm 的像元）。**修复：生成 cpt 后把 B/F 改写为切片端点色（蓝/红）再制图，并在脚本内断言 `B\tblack` 不存在**（clamp_cpt；pygmt 0.17 makecpt 无 overrule_bgfg 参数）
17. **越界显示簇多为整周解缠平台，非瓣峰**（洱源实证）：超出色标的簇若**平顶**（簇内 std≈0、单一量化值如 49.2/52.5mm）且较周边**跳变 +33~+52mm ≈ 1–2 个 C 整周（27.7mm）**，是解缠误差平台——真瓣峰应呈 41→49 的梯度过渡。**显示层（prep_grids）剔除规则（两判据互补，缺一漏抓）：≤8px 小簇 OR（平顶 AND 较环带跳变>20mm）→ 置 NaN**；剔除后四面板越界像元归零
18. **insarhub MintPy 模板默认对流层校正=pyaps/ERA5**：无 `~/.cdsapirc`（CDS 凭据）时 `correct_troposphere` 步骤**静默挂起**（进程 sleeping、无日志输出、无文件更新，洱源实证 30+ 分钟零进展、且复发一次）。**手改 `.mintpy.cfg`/`smallbaselineApp.cfg` 无效**——analyzer 每次 run 都用 `_sync_runtime_cfg()` 按自身配置重写这两个文件（洱源实证：补丁被覆盖、同一坑踩两次）。**正确修法：analyzer 命令行传覆盖旗标** `insarhub analyzer -N Hyp3_Mintpy_SBAS -w <stack> --troposphericDelay_method no run`（配置字段以 `--KEY VALUE` 形式直接挂在 analyzer 层，见 `--list-options`）；p99 实证立即生效。另：analyzer 重启会从 load_data 重走（文件级 Skip，代价小），非断点续跑；批量 SBAS 前必须 df 预检峰值空间（zip×2+HDF5，洱源实证 ENOSPC 事故：WSL 1TB 被打满，工作区迁 /mnt/d 解决）
19. **ISCE3_Burst 相位链接链（S1_Burst→COMPASS→dolphin）四坑（洱源实证全踩）**：(a) **dolphin 0.42 虚拟干涉图只在压缩 SLC 间构建**——日期数 ≤ `pl_ministack_size`（默认 15）时仅 1 个压缩 SLC → `No valid ifg list generation method specified` 空网络报错，洱源 15 日期正中雷区，修=`--pl_ministack_size 5`；(b) **多栈混下载是毒丸**——AOI 搜索会把邻近轨道 burst 一起拉下（t099 仅 2 日期，短栈必触发 (a) 且单 burst 失败全阶段停），处理前清成单一轨道（SAFE 按过境时刻区分：洱源 p135=T2314xx）；(c) submit 的 `--KEY VALUE` 旗标持久写入 insarhub_config.json（复验生效），AOI 也必须显式传（fullBurstID 下载不留 AOI → dem 阶段"could not determine extent"）；(d) 本地 executor 默认 `--max_workers 3`，提到 12 后 37 作业 ~5 分钟烧完；dolphin 位移/velocity 输出**单位是米**。**QA 终判方法**：步长差分图（d(震后)−d(震前)）→ 远场 MAD 定噪声底 → 机制模板相关 → **必须做去斜坡对照**（平面斜坡与双极模板相关可达 0.7+，洱源实证去斜坡后 0.71→0.09）。
20. **升降轨同震图案必须镜像（多视角一致性门，洱源实证）**：S1 右视——升轨卫星在地面西侧（"朝卫星"≈向西位移分量），降轨在东侧（≈向东）。同一双力偶跨升降轨观测，象限图案必须**镜像**：右旋 NW-SE 族降轨=红 NE/蓝 SW、升轨=红 SW/蓝 NE。**同边同色=物理矛盾（至多一边是真）；镜像一致=几何族一致性证据，但不等于检出**（幅度仍须过远场 MAD+去斜坡对照）。洱源 M4.87 三线实证：asc p99 GAMMA(0417-0429) 红SW/蓝NE（corr_desc −0.27）↔ desc p135 GAMMA(0419-0501) 红NE/蓝SW（+0.67）↔ desc p135 burst PL 同窗（+0.76，disc 去斜坡后仍 +0.36），与 CAP/SKHASH 右旋族一致；M4.96 步窗 raw 即 −0.24（噪声级，不构成同族证据）。判读勿凭目视——用图件目录 mirror_check.py（断块中位数+双模板相关，块轴=机制模板法向）；用户观感"两图完全相反"正是镜像的正常表现，勿误判为矛盾。
21. **ERA5 物理大气校正四坑（洱源实证，era5_correct.py 全流程跑通）**：(a) **pyaps3 0.3.7 传输层已死**——它走 ECMWF legacy portal（_token/_email+pygrib），新 CDS（2024 迁移后）必须走新 cdsapi/ecmwf-datastores + `~/.cdsapirc`（url+PAT 两行）；**正解=只调用其物理层** `processor.intP2H/PTV2del`（纯 numpy），数据自行从新 CDS netCDF（h5py 可读，变量 z/t/q/pressure_level/latitude）构造，**lvls 必须一维 (n,) 与每列高度配对**（传 (n,1,1) 广播数组 → interp1d 长度不匹配崩溃）；层序=气压升序（1hPa 在前=高度降序，intP2H 内部 -hx 取单调）。vpr=q·p·α/(1+(α−1)q) Pa（α=Rv/Rd）。(b) **投影因子用 geometry/los_up（LOS 单位矢量垂直分量=cos 入射角，先验 |LOS|=1）**，勿用 local_incidence_angle（那是地形局部角、且只覆盖 burst 足迹）。(c) **符号双锚定**：MintPy tropo_pyaps3 约定 d_corr = d_obs + (slant_sec − slant_ref)、slant=ZTD/cos(inc)；再以数据内经验锚复核——校正必须使 corr(位移, 高程) 显著下降（洱源 +0.91→+0.53；反号 +0.96 恶化）。(d) **校正自身给短窗注入形态噪声**——0.25° 模型梯度残差以模板形态投射（洱源安静窗模板相关 0.01→−0.69 级别变化），**凡校正后判读，零分布/安静窗对照必须在校正后数据上重算**。另：新 CDS 403 "required licences not accepted"=账号未接受数据集许可（只能账号所有者网页点）；批请求（多日期×1 时刻）比逐日期排队快得多；CDS PAT 凭据只放 ~/.cdsapirc 勿入仓库。
