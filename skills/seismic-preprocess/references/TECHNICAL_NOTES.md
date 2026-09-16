# 技术依据与默认策略说明（v4；保留v3处理依据）

本文件用于核对接口语义，不要求每次运行都重新检索所有网页。记录日期：2026-09-10。实际执行以用户安装的版本为准；不为追赶文档版本自动升级科研环境。

## 1. 本次确定的目标与新补全的默认

用户确定的目标：现有 Conda/ObsPy 环境；去响应到速度；目标分析频带 1–40 Hz；PhaseNet/PhaseNet+ 输入准备为 100 Hz；输出按台站、三分量、逐日归档；只进行必要配置与基础检查，不做精细参数寻优。

v2按用户要求将响应预滤波低频角降低为0.01、0.02 Hz，并要求显式merge(fill_value=0)；v3保留这两项要求。本 Skill 的当前配置为：Hann 5%且单端上限20 s；Butterworth corners=4、双向；pre_filt=(0.01,0.02,45,48)及低采样率收缩公式。

既有初始协议另明确：water_level=None；日边界真实缓冲60 s；连续段两端20 s使用警戒区；每日三份SAC加元数据；默认单任务。上述项目均是本项目初始协议选择，不是文献证明的普适最佳参数。存在已验证的用户协议时允许明确覆盖，并保存实际采用值。

20 s警戒区不能严格界定响应反卷积或IIR滤波的全部非局部影响；它用于避免把最邻近处理边缘的样本直接作为可靠输入。显著异常仍需诊断，不能因满足这项规则就保证波形无边界误差。

降低pre_filt低频角不改变后续1–40 Hz分析带通，也不把最终归档变成宽频带长周期数据。不得因此自动放宽有效区间或宣称去响应在所有仪器上都更优。其余taper、water level、缓冲与边界规则在此次定向修改中保持不变。

旧研究案例使用过的1–20 Hz、其他低频预滤波角或water level，不应静默代替本次新Skill的1–40 Hz目标与明确规则。

## 2. Skill格式和读取方式

OpenAI官方文档说明，Skill以目录中的SKILL.md为入口，文件头包含name与description；可以另带参考文件、模板和脚本。仓库级目录为`.agents/skills/`，Codex CLI可通过`/skills`或`$技能名`调用。

来源：https://developers.openai.com/codex/skills
（检查时官方跳转至 https://learn.chatgpt.com/docs/build-skills ）

本交付是操作指令与配置模板，不是已经实现并通过真实数据测试的完整处理器。

## 3. 基础处理、响应及滤波

- 去趋势的`linear`明确表示最小二乘线性拟合，不等于`simple`的首尾连线。
  https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.detrend.html
- `Trace.taper`的百分比与最大时长同时给出时取较短限制；百分比描述单端。
  https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.taper.html
- `remove_response(output="VEL")`输出m/s。该函数默认自行去均值并taper；外部已执行时关闭重复操作。文档指出，目标物理量不是传感器原生量时，water level可能压制目标频段，并给出`None + pre_filt`的替代方式。
  https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.remove_response.html
- pre_filt为四角频率余弦窗，f2到f3为平坦区；它不等同于之后的Butterworth分析带通。
  同上。
- `zerophase=True`执行正、反向滤波，不是再另调用一次带通。
  https://docs.obspy.org/packages/autogen/obspy.signal.filter.bandpass.html

本Skill不会从上述接口文档推导出1–40 Hz对所有地震、仪器或模型均最佳。它是本项目明确的默认分析目标。

## 4. 采样率与时间轴

- PhaseNet官方说明默认采样率为100 Hz。EQNet实际预测入口也提供sampling_rate、高通和响应相关设置。下游必须核对所用权重和实际读取器，不将本项目1–40 Hz协议称为官方强制频带。
  https://github.com/AI4EPS/PhaseNet
  https://raw.githubusercontent.com/AI4EPS/EQNet/main/predict.py
- SciPy `resample_poly`使用上采样、低通FIR和下采样实现采样率转换。
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html
- ObsPy插值可以通过starttime与npts将数据采样到指定网格，但不会外推；降采样需事先做好抗混叠处理。`time_shift`只改元数据，不能用来伪造真实对齐。
  https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.interpolate.html
- ObsPy裁剪会选取上下端样本。为得到普通UTC日的8,640,000个100 Hz样本，应使用半开时间约定或明确的最后样本，不同时保留两个相邻午夜。
  https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.trim.html

0.8/0.9/0.96的奈奎斯特余量是工程规则；不代表已经恢复缺失高频、不代替抗混叠滤波，也不验证低采样率数据的模型精度。

## 5. 合并、缺口与方向

- ObsPy `Stream.merge`按同一Trace ID合并；fill_value控制缺口填充值，method还涉及重叠处理。不能把填零等同于解决冲突重叠。
  https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.merge.html
- 三轴到ZNE的转换需要每个分量的azimuth/dip，且输入应有相同长度和采样时间。Z/1/2并不允许简单改名代替旋转。
  https://docs.obspy.org/packages/autogen/obspy.signal.rotate.rotate2zne.html
- Stream的`->ZNE`旋转会按共同覆盖区间组织数据；因此使用前后必须保留有效区间，而不把被裁掉的其他分量观测默认为存在。
  https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.rotate.html

本项目要求先处理有效连续段、统一采样率和时间网格，再逐输出通道显式执行`merge(method=0, fill_value=0)`，填充内部缺口；随后`trim(..., pad=True, fill_value=0)`补齐日首尾。两项操作均不得省略。method控制重叠处理，因此数值冲突必须在merge之前发现并按既定策略暂停，不能借助填零隐藏冲突。

这不是将Z/N/E三轴合为一个信号，也不允许先给原始缺口补零后整日去响应。缺口与边缘依据输入覆盖和处理记录确定，不靠结果数组中的0来识别。

## 6. 为什么SAC需要额外单位说明

SAC头定义中，`IDEP=IVEL`表示速度nm/s，而本流程数组按ObsPy定义保持m/s。不能不改变数值就将二者混用。

本协议以`kuser0=VEL_M_S`和每日metadata.json明确物理量，IDEP不冒充nm/s。下游以本项目明确的单位字段为准。SAC的有限精度头还需要按名义采样网格检查，不能强求float32的0.01逐位等于实数0.01。

来源：https://docs.obspy.org/packages/autogen/obspy.io.sac.header.html

这是一种明确的项目内SAC使用约定，不应被当作任意第三方程序无需适配的自解释格式。需要标准nm/s的外部程序应在单独副本中做显式单位转换；不得修改本归档或反复去响应。

## 7. v3：方向、响应与校准补充依据

### 7.1 SAC与SEED方向

API事实：rotate2zne的dip以水平为0、向下为正；SAC cmpinc以竖直为参考。按这些定义进行转换，`dip=cmpinc-90`。azimuth/cmpaz为从北顺时针。输出Z-up/N/E对应的SAC角度分别为(0,0)、(0,90)、(90,90)，括号顺序为(cmpaz,cmpinc)。竖直轴的方位角0只是表示选择。

项目规则：方向必须有可信元数据，不靠1/2或Z/N/E字符推断；缺失和-12345拒绝；完成各原轴响应校正后旋转，在参与轴共同可用区间内形成输出，更新方向头并保留原方向来源。

来源：
https://docs.obspy.org/packages/autogen/obspy.signal.rotate.rotate2zne.html
https://docs.obspy.org/packages/autogen/obspy.io.sac.header.html

### 7.2 calib与scale

API事实：ObsPy read的apply_calib默认False，True时会对数组应用calib；Trace合并要求calib等属性一致；SAC读取将scale映射到calib，保留旧SAC头的写出路径不保证以Stats覆写旧scale。

项目规则：明确以apply_calib=False读取，先保留并检查原字段。只有完整单位变换实际完成（或历史m/s状态被确认）后才设置派生calib=1.0、输出scale=1.0。这不是一次数据归一化或振幅变换。不先去灵敏度再完整去响应，不因合并失败就在原始数据上抹掉校准信息。

来源：
https://docs.obspy.org/_modules/obspy/core/stream.html
https://docs.obspy.org/_modules/obspy/core/trace.html
https://docs.obspy.org/_modules/obspy/io/sac/util.html

### 7.3 响应唯一性与覆盖

API事实：Trace的响应查找使用id和starttime，多个候选可能警告后选首项。这个机制不能独自证明长记录中途没有响应变化。

项目规则：每段显式检查完整通道、各元数据epoch、首末样本及原始采样信息；消歧后只传入所需inventory。原始响应与派生数据分开保存，避免重复校正。用户需有完整可解释的响应；多项冲突或未知物理单位阻止相关段，不编造元数据。

来源：
https://docs.obspy.org/_modules/obspy/core/trace.html
https://docs.obspy.org/packages/autogen/obspy.core.inventory.inventory.Inventory.get_response.html

## 8. v3：短段、非有限值与真实覆盖

### 8.1 低频窗与边缘

0.01/0.02 Hz低频角是用户要求。它们对应100/50 s时间尺度，但本包不由此推导一个普适最短数据长度，也不称最后的1 Hz带通可以修复任何反卷积错误。

项目规则：先合并真连续段，再跳过无法留下可用内部区间的短段；不靠缺口补零增加观测时长。首批按代表性响应和边界诊断检查，保留60 s缓冲和20 s警戒这两个既有初始值，不开展自动参数扫描。

API事实：water_level=None时相应路径直接反演非零频点响应，仍有噪声放大和数值问题的可能；ObsPy提供去响应诊断图。项目规则是在每个关键运算后检查有限值，数值失败不以nan_to_num、裁剪或填零伪装。

来源：
https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.remove_response.html
https://docs.obspy.org/_modules/obspy/core/trace.html

### 8.2 上采样的额外数组点

API事实：resample_poly以带边界处理的多相FIR进行采样率转换，输出长度根据输入长度和有理数比例确定。40 Hz的40点升至100 Hz时，会返回100点；输入最后样本是0.975 s，而输出名义末样本为0.990 s。

项目规则：以原始首末样本的时间支持为保守界限，目标网格只能在其中取值。本例100 Hz网格只保留0.000–0.970 s的98点（尚未应用边界警戒）；另外两点不计作新观测。此项规则限制有效覆盖，不保证内部插值完全不受边界滤波影响。

来源：
https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html
https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.interpolate.html

### 8.3 SAC有限精度

API事实：SAC采样间隔为float32，ObsPy的SAC工具包含采样间隔舍入处理。项目规则是保留可核实的精确名义网格，不因已证实的格式舍入重复重采样；没有依据的原始采样差异不可擅自消除。

来源：
https://docs.obspy.org/_modules/obspy/io/sac/util.html

## 9. v3：已校正速度的下游读取

2026-09-10检查EQNet main的seismic_trace.py时，read_mseed中存在按通道家族末位N执行积分和1 Hz高通的路径。相同文件中未找到直接SAC读取分支。它们是所检查版本/路径的事实，不能替代对用户本地安装和其他入口的核对。

来源：
https://raw.githubusercontent.com/AI4EPS/EQNet/main/eqnet/data/seismic_trace.py

项目规则：派生数组以ground_velocity和m/s字段确定物理量，不再按HN等来源名字积分；不为绕过代码改假通道名。SAC必要时经单独读取适配，保留时间、符号、组件映射及有效区间；模型归一化在副本上进行。只有实际测试读入路径后，才报告模型输入已经验证。

本包新增downstream_contract.json模板及DOWNSTREAM_HANDOFF.md，明确归档检查和模型接入是两种不同状态；交接文件本身不会自动修改第三方读取器。详见同目录的下游说明和实现检查表。

## 10. 来源与实施范围

本包正文规定的是用户要求与本项目的初始操作策略；本文件中的API事实由官方文档或源码支持，不能将两者混称“官方推荐参数”。网络main分支与在线文档会改变，运行前应记录本地实际版本，对受影响接口核实，不能以当前网页为由自动升级用户环境。

新增内容是规范和配置层面的补全。本次交付的实际检查范围见包根目录VALIDATION.md；没有提供或声称一套已在真实台站数据验证完成的处理器。

## 11. v4：结果QC与可视化

本次按用户要求增加QC交付，不重新调整信号处理参数。全批次统计与少量代表波形/PSD分开；指标定义、图件列表、抽样预算、失败和未检查状态见`QC_OUTPUTS.md`。

新增API依据：SciPy Welch的density单位为输入量平方/Hz，窗函数、段长、重叠与detrend在调用中显式指定；ObsPy的记录扫描反映记录跨度，不能直接由补齐SAC的文件头恢复真实缺口；去响应诊断使用原始计数和真实响应。

2026-09-10核对的官方文档：
https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html
https://docs.obspy.org/packages/autogen/obspy.imaging.scripts.scan.html
https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.remove_response.html

分母、交集和零/未知的区别属于本项目统计定义；6个基线样本、3个异常样本、600/120 s窗口、图形分页及状态字段是轻量交付约定，不是文献证明的最优QC设置。单个代表窗的PSD不等于长期台站噪声评价，图件不证明仪器校准或模型输入精度。
