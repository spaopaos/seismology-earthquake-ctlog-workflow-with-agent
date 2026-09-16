---
name: seismic-picking
description: 对规范的100 Hz、m/s三分量UTC逐日归档执行钉版PhaseNet+，生成带极性与有效区间标记的标准拾取CSV。
---

# Picking

发布版本 0.2.0。先读包根目录 `AGENTS.md`。使用 `pipeline.json` 的地区与运行设置、`runtime.local.json` 的解释器映射；禁止依赖开发机路径、聊天历史或某个环境名称。

统一入口（`python` 是明确选择的现有或已部署解释器）：

```bash
python <package>/seisflow.py --runtime <mapping.json> run --config <run>/pipeline.json --stage picking
```

固定格式转换与程序调用使用本技能维护的 `scripts/`，由统一入口调用。正常新数据运行不改写转换器。所有下游读取当前 `contract.v2.json`，原生输入校验失败时停止受影响步骤。新配置使用新运行目录；不覆盖已完成结果或伪造验证报告。参数依据和用户选择写入运行配置及记录，不只留在对话中。

科学程序完成、接口验证通过、科学质量已审阅是不同状态。报告实际计数、排除原因、QC路径与尚未验证项。


## 随包 Wiki 的使用

本环节先读取 `knowledge/bindings/picking.md`，或运行包入口 `seisflow.py knowledge stage --stage picking` 获取明确阅读路线。需要解释参数/方法时，通过 `knowledge search --stage picking --query <问题>` 查询，再用 `knowledge read --id <条目ID>` 和 `knowledge source --id <来源ID> --page <PDF页码>` 回到原文。

带上 `--run-dir <运行目录> --stage picking` 可记录实际返回的条目/来源；对关键配置选择使用 `knowledge cite` 保存条目、配置值和理由。自动生成的阶段知识上下文只表示资料已提供，不代表agent实际读过，也不代表科学事实已独立验证。具体命令见 `docs/WIKI_INTEGRATION.md`。

Wiki论文与历史手册用于其声明的证据范围；本阶段的具体格式、默认值与决策权限以对应的钉版代码/手册和维护规则核对。不要将论文案例值自动填为地区默认值。正式运行固定知识快照，新增经验先保存在运行目录。


## 输入与执行

先完成预处理统一归档验证。读取 shim 保持 E/N/Z 输入顺序，移除原读取器的 HN 积分、去响应、滤波和重采样路径。HH与HN已知数组回读检查必须通过，然后使用 `toolchain.json` 中的本地权重执行实际推理；不依赖自动下载或隐式缓存。

默认 `min_prob=0.3`、整日输入、batch_size=1。CPU/GPU与并行预算来自配置；GPU必须明确卡号。当前发布入口不自动执行分块降级；若整日输入资源不足，报告并停止，按维护流程验证新的分块实现后再使用。不得悄悄裁短日期或跳过组日。

输出文件名必须包含组和日期；每个已处理组日保留一个CSV，包括没有拾取的空文件。运行器核对输出数等于输入数，并保存逐文件哈希。原归档保持物理单位，模型内部归一化只作用于模型输入副本。

## 输出

`picking/picks.csv` 是后续唯一标准拾取入口，保留 `station_id, phase_time, phase_type, phase_score, phase_amplitude, polarity_score, instrument_family, usable_3c` 等字段；振幅为线性 m/s。原始模型CSV目录仅作留档。

规范化脚本以原始台站身份映射和每日有效区间计算 `usable_3c/outside_usable`，保留区间外拾取并标记；后续关联明确排除。极性分数来自 `phase_polarity`，取值[-1,1]，只有P极性用于后续极性分析。QC包含P/S分布、计数和波形叠加；日容量监控参考28800次/震相，不能当作事件数物理上限。跨后端结果应实测比较，不采用某个案例差异百分比作为通用合格阈值。

读取器事实和排查依据见 `references/EQNET_FACTS.md`、`references/TROUBLESHOOTING.md`。
