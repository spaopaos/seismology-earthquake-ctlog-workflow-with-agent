# 带限速度归档的下游读取约定

本文件是预处理与PhaseNet/PhaseNet+/MESS之间的交接规范，不启动这些程序，不替用户安装或修改全局环境。实际模型输入能力以锁定的读取器与权重为准。

## 1. 归档到底是什么

每个成功站日包含三条100 Hz、m/s、Z/N/E带限速度数据，三个SAC文件及每日metadata。名义目标带通1–40 Hz；低采样率的实际高端更低，以每日metadata为准。原始台网/台站/位置码/仪器家族保留用于追踪，因此HN等名字不再能独自描述派生数组当前的物理量。

SAC使用kuser0=VEL_M_S、idep=IUNKN、scale=1.0。read(...,apply_calib=False)读回，calib应为1.0。SAC的IVEL规范含义与本包m/s不同，不仅凭idep判断是否应再去响应。

## 2. 必须消除的重复变换

对本归档不要再乘原灵敏度或calib，不再remove_sensitivity/remove_response，不再执行加速度到速度积分；无新任务依据时不重复滤波。即使数值头仍是HN/BN/EN，也不能由名字覆盖metadata声明的ground_velocity。

2026-09-10查阅EQNet main的`eqnet/data/seismic_trace.py`时，`SeismicTraceIterableDataset.read_mseed()`中有按站点键（去掉分量后的通道家族）最后字符为N执行`integrate().filter("highpass", freq=1.0)`的路径。这是**一个版本和读取路径的观察，不是所有PhaseNet版本的通用规则**。必须检查用户本地版本；仅把归档转成MiniSEED、不给响应参数，不足以排除这条积分路径。

若现有读取器不能尊重“已是速度”的输入状态，应使用经过检查的读取适配器或受支持的中间数组/文件入口；没有这种路径时标记BLOCKED，不偷偷把HN改为HH，不擅自修改全局EQNet源码。原始通道映射必须保留。

## 3. 文件格式、三分量和时间

SAC归档不等于模型入口已支持SAC。检查本地预测入口和实际数据集实现，再决定直接读、转换为其支持的文件格式，或用读取适配器构建输入。不要编造不存在的`--format SAC`等命令。

转换保留浮点m/s数值与名义时间网格；若目标格式不能携带全部单位/缺口信息，就以明确的旁置文件和适配器传递，不能认为这些信息自动进入模型。

按该权重的实际分量顺序装配。2026-09-10查看的EQNet读取示例使用E/N/Z到数组的映射，这不是允许对全部模型硬编码同一顺序。先核查，再记录。

采样间隔的已知SAC浮点舍入不应触发再次插值；真实采样率/时钟问题不能由格式容差掩盖。

## 4. 有效区间必须被消费

每日metadata记录各分量data_intervals、usable_intervals及三分量共同可用区间，均以UTC日100 Hz网格的整数半开下标表示。0值既可能是填充值也可能是真实信号，不能用波形等于0反推。

窗口跨过缺口时按实际读取器与任务协议切分、拒绝或标为无效；不能跨缺口插值填信号。拾取时刻、极性窗口、振幅窗及模板必须检查所需的有效支持。局部缺口不自动否定整个站日，模型能接受规则数组也不等于缺口中的预测是有效观测。

## 5. 归档完成与模型接入验证独立

`downstream_contract.json`由实际预处理运行生成，包含物理量、单位、实际频带的元数据位置、100 Hz网格、禁止的重复变换和有效区间来源。模板内`template_only=true`、路径空值及NOT_RUN状态不能当作真实交付。

根目录`archive_validation_status`可为NOT_RUN、PASSED、PARTIAL或FAILED；每个站日仍采用Skill的READY/PARTIAL_DAY等状态。模型接入`model_input_verification.status`初始NOT_TESTED，不因为归档检查通过就变成PASSED。

以后接入时至少完成一次**模型归一化前**的数组检查：已知速度数组通过实际读取路径后，在必要的分量重排及明确格式精度转换之外，数值、符号、物理单位和时间应匹配。包括强震来源通道标识，检查额外积分/缩放路径。模型临时归一化单独记录，不能拿归一化后的相等去证明之前未发生额外单位变换。

只做了静态源码核对时记录STATIC_REVIEW_ONLY，不声称实际读取已经通过；完成实际读入检查后才记录PASSED或FAILED及真实版本、权重身份、输入形式和证据路径。

## 6. 来源

以下为2026-09-10核查的官方资料，main分支可变，运行必须检查本地版本：

- EQNet读取器：https://raw.githubusercontent.com/AI4EPS/EQNet/main/eqnet/data/seismic_trace.py
- EQNet预测入口：https://raw.githubusercontent.com/AI4EPS/EQNet/main/predict.py
- PhaseNet原仓库：https://github.com/AI4EPS/PhaseNet
- SAC字段：https://docs.obspy.org/packages/autogen/obspy.io.sac.header.html
- SAC↔ObsPy字段映射：https://docs.obspy.org/_modules/obspy/io/sac/util.html

上面的实际读取风险来自代码核查；要求使用显式物理量、消除重复变换和保留有效区间，是本项目的交接设计，不是声称原仓库已自动实现这些保护。

## v4新增QC交接

后续Skill还应读取`qc/qc_summary.json`、`qc/availability.csv`和`qc/archive_integrity.csv`以了解处理范围、已执行频带、缺项和检查状态。它们不替代各日metadata中的实际有效区间。只看到QC的COMPLETE不能当成全台网数据完整，也不能把AGENT_REVIEWED当成波形科学质量的保证。`model_input_verification.status`仍须由真实读入测试单独建立。QC链接在实际生成后写入downstream_contract，空模板保持NOT_RUN/NOT_TESTED。
