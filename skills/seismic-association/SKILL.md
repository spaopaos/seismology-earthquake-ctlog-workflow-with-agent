---
name: seismic-association
description: 使用GaMMA将标准P/S拾取关联为事件；解释DBSCAN邻域、计算估计值并消费用户选择，保留参数依据与归属。
---

# Association

发布版本 0.2.0。先读包根目录 `AGENTS.md`。使用 `pipeline.json` 的地区与运行设置、`runtime.local.json` 的解释器映射；禁止依赖开发机路径、聊天历史或某个环境名称。

统一入口（`python` 是明确选择的现有或已部署解释器）：

```bash
python <package>/seisflow.py --runtime <mapping.json> run --config <run>/pipeline.json --stage association
```

固定格式转换与程序调用使用本技能维护的 `scripts/`，由统一入口调用。正常新数据运行不改写转换器。所有下游读取当前 `contract.v2.json`，原生输入校验失败时停止受影响步骤。新配置使用新运行目录；不覆盖已完成结果或伪造验证报告。参数依据和用户选择写入运行配置及记录，不只留在对话中。

科学程序完成、接口验证通过、科学质量已审阅是不同状态。报告实际计数、排除原因、QC路径与尚未验证项。


## 随包 Wiki 的使用

本环节先读取 `knowledge/bindings/association.md`，或运行包入口 `seisflow.py knowledge stage --stage association` 获取明确阅读路线。需要解释参数/方法时，通过 `knowledge search --stage association --query <问题>` 查询，再用 `knowledge read --id <条目ID>` 和 `knowledge source --id <来源ID> --page <PDF页码>` 回到原文。

带上 `--run-dir <运行目录> --stage association` 可记录实际返回的条目/来源；对关键配置选择使用 `knowledge cite` 保存条目、配置值和理由。自动生成的阶段知识上下文只表示资料已提供，不代表agent实际读过，也不代表科学事实已独立验证。具体命令见 `docs/WIKI_INTEGRATION.md`。

Wiki论文与历史手册用于其声明的证据范围；本阶段的具体格式、默认值与决策权限以对应的钉版代码/手册和维护规则核对。不要将论文案例值自动填为地区默认值。正式运行固定知识快照，新增经验先保存在运行目录。


## 参数准备

向用户简单说明 `dbscan_eps`：拾取预分组的邻域时间尺度，较小可能拆散同一事件，较大增加分组和计算负担。推荐默认10秒，同时由钉版GaMMA的 `estimate_eps()` 按当前台网计算参考值供选择。已有配置或对话选择直接保存消费，不重复询问。配置中该项为null时，入口会准备两种值并在关联前停止，不替用户选择。

`dbscan_vp_km_s` 用于DBSCAN空间缩放；分层P/S走时使用用户提供模型。区域投影、搜索深度上界和台站外扩距离有明确配置。单层模型底层延伸不意味着搜索深度为0。跨日期变更和台站变化需要重新准备参数。

初始最少总拾取/P/S/台站组阈值5/3/1/3，sigma阈值2.0/1.0，oversample=5。这些是项目初始profile，供当前数据检查适用性，不能称为对所有地区最优的原仓库默认。覆盖值写入 `pipeline.json`；最终报告以 `effective_config.json` 为准。

## 必须保持的语义

振幅传入钉版GaMMA时为有限、正值、线性m/s；禁止预先取对数。保留完整网络、台站、位置与仪器组身份。准备器明确计数剔除无效区间和非正振幅的记录；原始拾取行号保留至归属和未归属表。

输出 `gamma_events.csv/gamma_assignments.csv/gamma_unassociated.csv` 和当前契约。事件ID在一次运行内稳定；跨独立运行合并必须使用run_id命名空间，不能直接拼同名gm编号。零事件是有效分析结果，不制造事件以推进下游。GaMMA输出的震级不作为已标定绝对震级。

版本行为依据见 `references/GAMMA_FACTS.md` 和随包钉版源码。
