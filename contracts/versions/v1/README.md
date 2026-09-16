# Pipeline Contracts（契约链草案 v1.0）

七个环节的机器可读交接契约的 JSON Schema。契约是整条流水线"拆开设计、最终合拢"的接口保证：**skill 文本可以随环节迭代，契约 schema 单独版本化**；契约字段变更须升 `contract_version` 并通知所有下游。

## 文件

| 文件 | 环节 | 对应软件 |
|---|---|---|
| `common.schema.json` | 公共信封 | — |
| `preprocess.contract.schema.json` | 预处理归档 | ObsPy 流程 |
| `picking.contract.schema.json` | 拾取 | PhaseNet+ |
| `association.contract.schema.json` | 关联 | GaMMA |
| `location.contract.schema.json` | 绝对定位 | HYPOINVERSE |
| `relocation.contract.schema.json` | 重定位 | ph2dt + HypoDD |
| `detection.contract.schema.json` | 模板匹配检测 | MESS |
| `mechanism.contract.schema.json` | 机制解 | SKHASH |

各环节 schema 通过 `allOf: [{"$ref": "common.schema.json"}]` 继承公共信封（`contract_version`、`stage`、`software`、`run_id`、`created_at`、`upstream`、`status`、`qc_path`、`warnings`），另加环节自有字段。

## 公共纪律

1. **`upstream[].input_verification`**：`NOT_TESTED` 时必须暂停或明确降级声明，不许静默当作 `PASS`。
2. **下游只消费、不覆盖**：任何环节不得修改上游产品；处理不兼容时生成派生副本（见 detection 的 `derived_copy_path`）。
3. **事件 ID 血缘链**：事件 ID 由关联环节签发（`event_id_scheme`），定位、重定位（`event_mapping`）、MESS（`template_event`）、SKHASH 全程携带；换 ID 必须记录映射。
4. **速度模型一致性**：`same_as_association` / `same_as_location` 显式声明；`false` 必须在 `warnings` 中说明理由。
5. **不可用原因是数据**：`reject_reasons`、`skip_reasons`、`unavailable_reasons` 必须结构化计数留档，不是备注文本。
6. **`status` 为 `READY` 的前提**：`qc_path` 指向的 QC 产物实际存在。

## 当前状态

草案。字段和约束会随各环节 skill 的实现细化而修订；修订时更新 `contract_version` 与本 README。
