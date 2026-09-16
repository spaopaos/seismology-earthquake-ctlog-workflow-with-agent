# 预处理结果可视化与质检交付（v4）

这是运行时必须执行的 QC 规范，不是已经产生的观测报告。默认开启；仅汇总事实、发现明显问题，不调频带、不做参数扫描、不自动判定某台站科学上“好/坏”。归档检查、QC交付状态、图件审阅状态与下游模型验证是四件不同的事。

## 1. 执行入口、依赖与不变项

在初始索引时准备QC数据源与抽样计划，在实际信号处理时保留少量中间片段，完成归档回读后生成全批次图表。不要等处理结束才发现无法获得原始覆盖或中间物理量。

优先复用并检查已有QC脚本；没有则在`processing/`编写可复用脚本，读取真实索引、处理记录、每日元数据和归档。用现有NumPy/SciPy/Matplotlib，CSV/JSON可用标准库；不强制pandas、Cartopy、GMT或在线底图，不安装/升级依赖。不假定某个QC命令已经存在。

本次增加QC不改变1–40 Hz目标频带、100 Hz输出、m/s单位、pre_filt低频0.01/0.02 Hz、water level、旋转、merge/trim或任何已确定的有效区间规则。绘图不得重新滤波、改变归档振幅、覆盖原始数据或自动排除不美观的台站。

## 2. 统计单位与可用性：先定义，再画图

### 2.1 站、仪器组与时间范围

- `station_id=NET.STA`；`group_id=NET.STA.LOC.FAMILY`。一个站有多套仪器，计为一个台站、多个仪器组；不能把三条通道计为三个台站。
- `group_day`表示一个仪器组在一个UTC日的处理单元。所有汇总均标明统计的是台站、组、组日、通道还是连续段。
- 以输入阶段保存的请求范围/实际处理清单为基准，不只扫描成功输出目录。必须保留失败、缺响应、缺分量、已确认无输入和未完成检查的行。
- 用户明确给出时间范围时，在该范围内建立所选组的日期网格；未限定时，以本次选中资料的整体最早至最晚UTC日期作为总览范围，并注明是资料派生范围。中间无记录日期仅出现在QC中，不要求生成虚假波形文件。
- 有明确部署起止资料时，部署外标记`NOT_EXPECTED`；仅凭没找到文件不能推断台站未部署。完全在请求范围外用`OUTSIDE_REQUEST`。这两个状态不是缺测，也不纳入请求覆盖率分母。
- 仅请求一天中的一部分时，仍报告整日归档覆盖率，另报告请求区间覆盖率；不能把请求外的补齐部分写成传感器故障。

### 2.2 三种覆盖信息不可混用

| 信息 | 数据来源 | 含义 |
|---|---|---|
| 原始观测覆盖 | 处理前索引、实际掩码、无效值和去重记录 | 记录中真正具有输入支持的部分；已知填补点不算观测 |
| 派生数据覆盖 | 每分量`data_intervals` | 本版输出中有实际处理数据支持的样本，不包括归档补零 |
| 可用覆盖 | 每分量`usable_intervals`及`usable_3c_intervals` | 按现有处理和边界规则保留的可用样本，不代表科学精度已经验证 |

原始轴方向尚未确定或原生是Z/1/2时，原始单轴覆盖按实际轴标签保存，不能把1/2覆盖直接写进N/E字段；N/E对应原始字段留空并注明轴基。已确认属于同一传感器的三轴原始共同时间可单独求交集，与最终旋转后的3C可用时间分开。

所有输出可用性在100 Hz普通UTC日网格上按去重后的半开整数区间`[i0,i1)`计算，范围为`[0,8640000)`。重叠区间先求并集，不重复累计。原始覆盖映射到该网格时沿用Skill第4-D节的实际首末样本支持规则；这是共同网格覆盖，不是改写原始采样率。

设`I_Z,I_N,I_E`为三分量可用区间，`n(I)`为区间总样本数：

```text
C_Z = n(I_Z) / 8640000，N/E同理
I_3c = I_Z ∩ I_N ∩ I_E
C_3c_day = n(I_3c) / 8640000
C_3c_requested = n(I_3c ∩ I_requested) / n(I_requested)
```

三分量共同覆盖必须求交集，不能取三个覆盖率的平均值或最小值。例：Z全天、N前12小时、E后12小时，每分量覆盖为100%、50%、50%，但三分量共同覆盖为0%。

**0与未知必须区分。** 已完成索引并确认没有某分量时，原始该分量覆盖为0；存在波形但响应失败、未生成输出时，派生覆盖字段为`null`并保留原因，而不是伪造为已计算的0。下游可交付时长可以明确计为0，使用另一个字段`delivered_usable_3c_seconds`，不能以它冒充已处理数据覆盖率。空白JSON值使用`null`，CSV空值必须有状态说明。

不能用`data != 0`计算覆盖。真实零值仍可有效，非零边界异常也未必可用。只扫描补齐后的SAC文件头，会看到整日文件跨度，不能以此声称整日都有观测。

## 3. 必须生成的总览图

默认PNG、160 dpi，每个逻辑图单独成图，不做拥挤的多图拼版。标题说明统计对象、UTC范围；保留可读取字体、单位、图例和真实分母。需要多页时输出`_p001.png`等，不能只画前几十个台站而不交代遗漏。

| 图件 | 文件名 | 规定内容与检查目标 |
|---|---|---|
| 逐组逐日可用性 | `availability_heatmap.png` | 横轴UTC日期，纵轴group_id；颜色值为已计算的`C_3c_day`，固定0–100%。缺响应、缺分量、未计算、无输入、请求外等用独立符号/图例，不能与真正0%混色。保留对应原始与单分量覆盖表。 |
| 台站分布 | `station_map.png` | 所有具有可信坐标的组，包括失败组；默认用符号区分处理结果、用文字/标记注明`BAND_LIMITED`，不在同图强塞多个数值配色。标题给出去重台站数、仪器组数和缺坐标数。 |
| 原始采样率分布 | `sampling_rate_hist.png` | 按“通道＋采样率/响应有效epoch”去重后分类计数；同一epoch的多个输入文件只计一次。标题明确不是台站数；真实采样变化分别记录，未知值另列。不能只画输出统一100 Hz。 |
| 三分量完整性 | `component_completeness.png` | 输入三轴完整/缺1轴/缺2轴/全缺/未知/不适用，以及输出3C是否形成，必须区分。三个分量都出现过但没有时间交集，不能归为共同连续3C。具体组合在CSV中保留。 |
| 缺口汇总 | `gap_statistics.png` | 默认逐组显示至少一轴原始缺测的总时长，另列无法计算者。各轴缺口个数、最长内部缺口、首尾缺口及边界剔除时长写表；不把处理失败算成观测缺口。 |
| 实际频带汇总 | `effective_band_summary.png` | 按真正发布的group_day统计实际频带类别，区分1–40、1–20、1–16、1–8及其他真实值；候选/失败配置不能算成已执行。未发布单元另列数量和原因。 |

### 3.1 台站地图要求

只采用已核实元数据中的经纬度和epoch，拒绝缺失/SAC未定义值；真实经纬度为0可以有效，但不能用0作缺失填补。台站搬迁或同组坐标有不同有效期时分期显示并标注，不能平均成一个不存在的位置。不得通过抖动真实坐标来分开重叠仪器，可用标签或附表说明。

已有Cartopy及本地底图时可使用；否则用明确标注的经纬度散点图，不自行下载底图或安装依赖。不能画不存在的断层或震中。局地区域可做明确的纵横比例调整；范围过大、极区或跨180°时应采用适当现有投影或说明简图限制，不用未经支持的距离比例尺。

有部分坐标缺失时照常画其余台站，遗漏名单进`station_summary.csv`和报告。所有坐标缺失时不伪造地图，登记`BLOCKED_INPUT`及原因；整体QC交付为部分完成，不能说地图已生成。

### 3.2 缺口统计要求

在明确统计范围内，对每轴原始有效支持求补集；区分内部缺口、首部、尾部与完全无输入。`gap_statistics.csv`记录日网格等效秒数、最长内部缺口和个数。无输出但原始支持已知时仍可统计输入缺口；输入本身未完成检查时为空，不填0。

站/组层面的“三分量共同缺测”使用三轴缺测区间的并集（即至少一轴缺测），不能相加三轴时长并称为台站缺测时长。跨日缺口合并需有相邻日索引依据；只有逐日表时只报告“最长日内缺口”，不能称全时段最长连续缺口。

保守覆盖裁切、旋转所需交集、边界警戒剔除和归档首尾补零均分开标记，不把它们全部归因为仪器断流。对于极小的重采样尾部支持差异，记录为网格/支持限制，不推断设备故障。

## 4. 波形、频谱与响应抽样：少量，但必须基于实际数据

### 4.1 抽样计划

开始批处理前，根据索引按“原始采样率类别、响应输入物理类型、是否需要旋转”选择代表组。默认最多6个基线组：依稳定排序优先覆盖新的类别，每类先1个；类别超出预算时在报告列出未覆盖类别，不称为全覆盖。再按真实异常记录最多选3例边界/缺口/异常振幅案例；没有对应异常就不造例子。

优先选择首个具有足够连续可用内部区间的UTC日，频谱片段目标600 s、波形显示窗目标120 s，均从同一实际处理段的可用内部选择。足够长时取所选可用段中心；不足则用实际长度并记录，PSD少于20 s则不计算。用户指定检查窗口优先，但不能越过真实覆盖。

异常图优先查看实际缺口边缘与午夜邻域，标明真实数据、补零和边界警戒；没有相应前后数据时显示缺失，不外推。全部样本选择写入`sample_selection.csv`，记录选择理由、输入/处理段、时间、配置与未生成原因。

### 4.2 在本次处理过程中保留快照

对选中组在正确的处理阶段保留小段快照与元数据：原始计数、去响应后而未分析带通的原轴速度、完成带通/重采样/对齐但旋转前的原轴速度，以及最终输出ZNE。快照取自真正计算后的长段，仅截取展示窗口；不为画图重新对截短的120 s原始数据去趋势/taper/去响应并冒充原流程中间结果。

采用压缩NPZ或现有等效格式，分别保存每阶段的相对时间数组、数值、有效性及通道/方向/单位/实际采样率；时间原点用明确UTC字符串保留。NPZ不使用需要pickle读取的对象数组。所保留快照和实际脚本路径写入`sample_selection.csv`。

中间快照不存在的历史归档，不得伪造。可以仅画真实原始与最终结果，并明确缺少中间阶段；若授权重做诊断，应在副本中按原完整处理段、缓冲与配置执行并标为诊断重放，不覆写原产物、不算作历史快照。QC状态按实际缺失情况报告。

### 4.3 波形图

每个样本在`waveform_examples/<sample_id>/`保存单独图：`raw_<axis>.png`、`response_velocity_<axis>.png`、`filtered_velocity_<axis>.png`及`final_Z.png/final_N.png/final_E.png`（能生成的真实阶段）。原生理想ZNE时可少量合并同一物理分量的两条m/s曲线；不同单位或轴方向的曲线不能直接叠加比较。

原始计数纵轴为counts，校正后为m/s；不要使用双纵轴把计数和速度强行叠加，不计算其峰值比作为去响应正确率。原轴1/2与旋转后的N/E不应一一当作相同轴。所有图标明同一UTC窗口、阶段、通道/方向、采样率和有效带通，采样时间使用实际值。

缺口和不可用边界以遮罩/说明区分；展示时不能把缺口两侧连成连续曲线。保存波形的符号、尺度与极值；需要减少绘制点时用明确标注的min/max包络，数值统计仍用有效原分辨率样本。不得裁剪峰值、平滑掉异常或修改归档。只有明确标为显示用归一化的附图可归一化，不覆盖物理量图。

### 4.4 PSD图

对同一代表窗口中不跨缺口的有效连续记录，用Welch PSD，默认`segment_seconds=10`、50%重叠、Hann窗、`detrend='constant'`、`scaling='density'`、单边、`average='mean'`；按该阶段实际fs计算nperseg，不对所有阶段假定100 Hz。显式生成窗数组，避免依赖软件版本的窗默认值。

可参考以下计算片段（输入必须已裁为一个全有效连续片段；不是整日补零数组）：

```python
import numpy as np
from scipy.signal import get_window, welch


def diagnostic_psd(x, fs):
    """Return a PSD for a finite real, contiguous, physically identified trace."""
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("无效采样率")
    if np.ma.isMaskedArray(x) and np.ma.getmaskarray(x).any():
        raise ValueError("不能对含缺口片段计算PSD")
    if np.iscomplexobj(x):
        raise ValueError("本规范只接受实数地震波形")
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("PSD需要一维、有限、连续的有效样本")
    nperseg = int(round(10.0 * float(fs)))
    if nperseg < 2 or len(x) < max(2 * nperseg, int(np.ceil(20.0 * fs))):
        raise ValueError("有效时长不足，记录PSD未生成，不用补零凑长度")
    window = get_window("hann", nperseg, fftbins=True)
    return welch(x, fs=float(fs), window=window, nperseg=nperseg,
                 noverlap=nperseg // 2, nfft=nperseg, detrend="constant",
                 return_onesided=True, scaling="density", average="mean")
```

`raw_<axis>_psd.png`的单位为counts²/Hz；`velocity_<axis>_psd.png`中可对照同一物理轴的带通前后速度PSD，单位为(m/s)²/Hz。与旋转相关的情况在原轴上做带通前后PSD比较，最终ZNE按独立图说明；不得把1轴PSD与N轴PSD当成只受滤波影响的同一信号。

频率使用对数坐标时不画0 Hz点，PSD为0的点在绘图副本掩蔽并记录，不添加任意噪声底。显示所计算的可见频率范围并标注实际带通和原始奈奎斯特边界；100 Hz输出的高频端没有能量，不自动认定处理失败，需看原始采样率和实际配置。10 s窗频率间隔约0.1 Hz，不能声称此PSD验证了0.01/0.02 Hz过渡或长周期响应。

这是选定记录窗的PSD，不自动叫“噪声PSD”或台站长期噪声评价。不要对已去响应的归档再调用会去响应/转换物理量的路径生成PPSD，也不直接与单位不同的标准加速度噪声模型叠加。

### 4.5 响应诊断与数量级说明

沿用v3首次接入每种显著不同响应类型时的诊断要求：保存实际原始段的去响应频域诊断，标明响应来源与epoch、输出VEL、pre_filt和water level。可以在实际调用中保存诊断，或在同配置的原始数据副本上做单独诊断；不能对m/s数据再次反卷积。

`response_status.csv`统计是否唯一匹配、是否覆盖整段、是否执行去响应、阶段有限值及警告。没有NaN/Inf只能说明数值有限，不是响应科学正确的证明。振幅过大、平直、尖峰或疑似削顶只作为检查线索，不使用跨台站统一振幅门槛把地震信号删掉。任何数值阈值若来自用户协议须记录，不临时“调到好看”。

## 5. 数据表、元数据和下游摘要

全部数据表按`assets/qc_table_columns.json`的字段约定生成（它是列定义模板，不是已经生成的CSV）。每张图须能对应其数值表、配置及绘图脚本；不只保存PNG。至少包括：

| 表/文件 | 行粒度及用途 |
|---|---|
| `station_summary.csv` | group_id＋位置epoch；源坐标、状态、输入采样率集合、已执行频带和地图遗漏原因 |
| `availability.csv` | group_day；原始、派生、单分量与共同覆盖、请求分母、已交付可用时长、状态 |
| `sampling_rate_epochs.csv` | 去重通道采样epoch；原始率、有效时间、原文件来源，不重复计每个碎文件 |
| `component_completeness.csv` | group_day；输入轴组合、时间交集、输出轴及失败原因 |
| `gap_statistics.csv` | group_day＋source/output＋axis；原始缺测、内部缺口、首尾缺口、支持裁除及边界剔除分别记录 |
| `effective_band_summary.csv` | 实际已发布频带类别；group_day数量；对应逐日明细来自manifest |
| `response_status.csv` | 原始通道处理段；响应唯一性、覆盖和执行状态 |
| `archive_integrity.csv` | 请求group_day；三文件、网格、数值、单位、calib/scale、方向、有效区间和零填充的实际回读检查 |
| `sample_selection.csv` | 抽样案例；选择理由、窗口、阶段/图件实际路径、未生成原因 |
| `qc_artifacts.json` | 每项图/表的生成状态、来源、路径、异常原因；不存在的文件路径为null |
| `visual_review.json` | 图件打开审阅记录、审阅者类型、结论/问题；未审阅保持NOT_REVIEWED |
| `qc_summary.json`与`qc_summary.md` | 机器可读统计与简短人读报告；从真实表和检查结果生成，不从聊天记忆填写数字 |

`archive_integrity.csv`不能只检查文件存在。按Skill回读实际三分量SAC和metadata，检查起点、末点、采样间隔容差、精确点数、数组有限、单位/方向/calib、有效区间边界、应补零索引和真实已填值。不应把恒为0的伪分量计为成功。失败组也需保留一行，未运行的检查列为空并写原因。

日元数据仍保存在各日波形目录，QC表只引用它们，不另建一套相互冲突的metadata。在输出根目录的`qc/`中提供QC摘要，下游读取约定可增加这些相对路径，但不得把`model_input_verification.status`从NOT_TESTED自动变成通过。

## 6. 生成、审阅及完成条件

### 6.1 自动生成之后还要查看

先从真实记录生成表，再生成图，再验证文件可以打开、PNG非空、表内数字和图示一致。Agent有图像查看工具时，应实际打开所有总览图，并审阅生成的抽样图；没有图像查看能力时，保留`NOT_REVIEWED`，告诉用户还需视觉检查，不能假称已经看过。

审阅重点是坐标/日期/单位与图例是否正确，是否遗漏失败台站、把补零画成完整覆盖、把不同单位叠加、截掉异常或缩小到不可读。发现数据问题记录到对应组日，要求明确依据后才重处理；缺少底图/图形依赖不自动更改波形。

### 6.2 状态必须分开

- 归档状态继续使用已有READY/PARTIAL_DAY/FAILED等，不为出图失败擅自删除已检查波形。
- 单项QC状态：`GENERATED`、`NOT_APPLICABLE`、`BLOCKED_INPUT`、`FAILED`；未启动为`NOT_RUN`。每项附理由和实际路径。
- `qc_generation_status=COMPLETE`仅表示适用的图表已生成并检查，且不适用项有可核查理由；缺输入/依赖造成的应有图未生成则为PARTIAL，公共QC错误使报告不可信则为FAILED。COMPLETE不表示所有台站均成功或科学质量良好。
- `visual_review.status`独立使用`NOT_REVIEWED`、`PARTIAL_REVIEW`、`AGENT_REVIEWED`或`HUMAN_REVIEWED`；只按真正的查看行为记录，不假定人已确认。审阅发现问题时另列findings，不能用REVIEWED充当质量通过。
- 模型输入验证沿用原状态，没有测试仍为NOT_TESTED。QC图不能替代PhaseNet+读取测试。

如全部处理失败，仍应交付能由输入与失败记录支持的地图/原始覆盖/状态表，真实说明“没有可用归档”。没有输出使最终波形图不适用时可以NOT_APPLICABLE，但不能因此宣布预处理成功。原本应有的原始/中间材料丢失用BLOCKED_INPUT，不以NOT_APPLICABLE规避。

任何失败表或缺项必须保留。不存在的观测不画“示意结果图”，不调用生成式图像工具制作QC，不把模板中的空值或例子作为真实统计。

### 6.3 人读总结顺序

`qc_summary.md`先给处理与QC真实状态，再给台站/组/日期范围和数量、覆盖与缺项、原始采样率及实际频带、图表路径、抽样检查所见与未覆盖类型，最后列阻止下游使用的问题及仍需人工查看的图。数值均与JSON/CSV一致；不输出自动科学好坏评分或“所有台站都可靠”的结论。

## 7. 输出目录

```text
<output_root>/qc/
  station_map.png
  availability_heatmap.png
  sampling_rate_hist.png
  component_completeness.png
  gap_statistics.png
  effective_band_summary.png
  station_summary.csv
  availability.csv
  sampling_rate_epochs.csv
  component_completeness.csv
  gap_statistics.csv
  effective_band_summary.csv
  response_status.csv
  archive_integrity.csv
  sample_selection.csv
  waveform_examples/<sample_id>/*.png
  spectrum_examples/<sample_id>/*.png
  response_examples/*.png
  snapshots/<sample_id>.npz
  snapshots/<sample_id>.json
  qc_artifacts.json
  visual_review.json
  qc_summary.json
  qc_summary.md
```

大数据默认热图每页不超过50组、90日，统计图过长按50组分页，图间使用相同标度且全部页列入qc_artifacts；不要求逐站日画全波形。默认上限6个基线样本、3个异常样本是本版交付预算，可按明确用户要求覆盖，不能称为代表了全部观测。

## 8. 技术依据与项目约定

以上抽样预算、图件目录、指标命名和完成状态是本项目定义，不是论文要求或软件官方推荐的QC阈值。API事实参考以下官方文档；2026-09-10核对，执行以本地版本为准，不自动升级。

- ObsPy scan根据输入记录跨度汇总数据覆盖；本项目已补零归档必须另外消费真实有效区间，不能只扫描输出文件头。
  https://docs.obspy.org/packages/autogen/obspy.imaging.scripts.scan.html
- SciPy Welch以分段谱平均估计PSD；density的单位是输入单位平方/Hz。本规范显式选择Hann、窗口长度等，不依赖版本默认。
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html
- ObsPy remove_response提供实际反卷积的诊断图；使用原始计数及所选响应，不对已校正产品重复执行。
  https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.remove_response.html
