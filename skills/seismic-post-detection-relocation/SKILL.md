---
name: seismic-post-detection-relocation
description: MESS 后轻量联合重定位：第一轮 medium 档 ph2dt dt.ct 原样复用 + MESS 原生 dt.cc，IDAT=3 联合 HypoDD；三个 CC 档各自按空间证据试算 DAMP，仅交付三套目录。
---

# Post-MESS joint relocation (lite: first-round CT reuse)

先读包根目录 AGENTS.md 与 knowledge/bindings/post_detection_relocation.md。复用 runtime.local.json 中的 science_python、钉版 HypoDD，不安装环境、不修改钉版上游源码。本阶段不重跑 PhaseNet、不重跑 ph2dt。

```bash
python seisflow.py --runtime runtime.local.json run --config <new-run>/pipeline.json --stage post_detection_relocation
```

此阶段位于 detection 之后，并包含在 all 的末尾。首次 CT relocation 仍位于 MESS 之前，为 MESS 提供中档模板库，也是本阶段复用 dt.ct 的来源。

## 数据和三套目录

只消费已完成 MESS 的 cc_0p4、cc_0p6、cc_0p8 三套检测契约，加上第一轮 relocation medium 档的 `input/dt.ct`（与其 solver 证据 `qc/damping_selection.json` 的哈希绑定，逐字节一致）。每套独立联合求解，只交付三套正式目录；DAMP 试算留在各目录 qc/ 中。不要把每套再展开成松、中、紧九套目录，不跨 CC 档合并。

CC 读取 MESS 导出的 dt.cc。维护转换器统一事件发震时间、事件顺序 DT=T1−T2 和台站别名；依据模板原发震时间修正后使用 OTC=0。裸台站名存在网络歧义时拒绝输入。反算检查事件深度偏移，恢复海平面基准，与原 P 模型一致；不得只平移事件而不核对模型基准。

CT 是第一轮 ph2dt 的原生 dt.ct 原样复用：不匹配拾取、不补窗、不改写数值。dt.ct 引用的目录事件进入联合事件表，非 MESS 事件沿用第一轮 event.dat 原始行；其台站并入 station.dat 并与既有别名核对坐标。复用来源的 tier 由 ct_reuse.relocation_tier 指定（默认 medium，与模板库同源）。

联合求解要求 CC 与复用 CT 均非空，并从实际原生结果确认两类约束都参与；缺任一类时报告 UNAVAILABLE，不静默改成单一数据类型。有效联合链接门槛为 OBSCC+OBSCT（默认 0+4=4，按手册 IDAT=3 求和语义）。

## 参数试算和证据

沿用 ../seismic-relocation/references/damping.md 及同一 damping_metrics.py 实现。每个 CC 档独立试算，检查相邻候选的去质心结构、两次解各簇质心漂移、共同事件覆盖和丢失，采用有证据支持的最小 DAMP。CND 40–80 只是经验参考。候选没有更大邻居、失败或资料不足时不选值。

初始 DAMP 候选为 20/50/100/200；需要扩展时声明新的候选与实验目录。不得直接沿用初轮选择结果。P/S 比值和 P 模型取同一地区已验证上游并检查适用性；上游 ERH 中位数仅是对比尺度，不是 MESS 新事件的实测误差。无 ERH 依据时明确补充。

联合加权分四段（CT 先约束较大尺度，随后增强近距离 CC，保留非零 CT 权重），全部配置见 configs/pipeline.example.json。WRCC/WRCT 的 >=1 表示标准差倍数，0–1 为秒，-9 关闭剔除；WDCC/WDCT 为 km。数值是项目初始工作设置，非地区最优。

## 发布、恢复与检查

产出 post_detection_relocation/{cc_0p4,cc_0p6,cc_0p8}/catalog.csv、reference_events.csv、event_lineage.csv、原生输出、复用与适配审计（ct_reuse.json、cc_adaptation.json）、两类观测数、参数、完整试算与日志，以及顶层 contract.v2.json、catalogs.json、QC。

事件 ID 与 MESS 一致；新坐标的 location_method 为 hypodd_cc_ct，method 为 joint_lite_cc_ct。参考事件另列；不能凭 known_match_method 合并事件，也不要求同一事件在三个独立求解中坐标相同。

输入、配置、脚本、模型、试算/正式原生文件均校验身份，复用 dt.ct 与第一轮 solver 证据逐字节绑定。正式运行重新计算空间选择证据；缺失/篡改不通过。参数变化用新运行目录，旧运行的契约和知识锁不得补改。

成功执行、非空目录和 DAMP 稳定都不等于地质位置准确。分别报告 CC、CT 的实际使用数量、残差范围、未保留事件和深度变化；最终日志 RMS 不冒充可比较的全目录残差降幅。检测事件的目录连接仅经由其模板的互相关链，其绝对位置不确定性未被测量。
