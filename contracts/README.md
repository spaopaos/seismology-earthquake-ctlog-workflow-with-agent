# Pipeline contracts v2.0

正式交接文件为每个运行目录的 `contract.v2.json`；当前前五环节为2.0，MESS每个CC目录为2.1。v2使用JSON Schema draft 2020-12。完整验证由当前解释器或runtime.local.json的validator_python执行；不依赖环境名称。versions/v1仅作旧格式参考。

## 公共结构

所有阶段包含 版本化 `contract_version`（按阶段Schema规定）、`stage`、`software`、`run_id`、`created_at`、`upstream`、`status`、`artifacts`。

- `upstream` 只放阶段契约；检查报告放入 `verification`。状态值仅为 `PASS/FAIL/NOT_TESTED`，说明放在独立 note/basis 字段。
- 所有操作路径相对**当前契约所在目录**解析，或使用显式绝对路径。路径中不夹计数、括号说明、通配符或“其余两档同理”。
- `artifacts` 为操作路径登记表：每个角色给出纯路径、file/directory、required，以及文件的 SHA256。目录只检查存在性，不声称对整个波形库做了哈希核验。
- `READY` 必须提供实际 QC；没有QC不能升级为READY。文件缺失、哈希改变、计数矛盾、事件引用断裂或重复ID等问题在 `validation.issues` 留下结构化记录，操作读取器拒绝消费。
- `validation.schema_status`、`artifact_status`、`scientific_status` 分开。迁移过程不重新执行科学验证，`scientific_status` 保持 `NOT_TESTED`。旧检查结论保留为 `source_record`，不扩大原验证范围。
- `provenance` 记录旧契约路径、SHA256、原时间、修订时间和修订说明。原记录没有run_id时，以源文件哈希形成记录标识，不伪造旧运行时间。

## 各阶段的操作字段

| 阶段 | 主要字段 |
|---|---|
| preprocess | 保留嵌套 `data_contract` 与 `reader_requirements`；`manifest_path`、`archive_root` |
| picking | `outputs.picks_path`、实际表头、模型及读取验证 |
| association | `outputs.events_path/assignments_path`、`stats.unassociated_picks_path`；eps单位字段为 `dbscan_eps_s` |
| location | `model_file.p_path/s_path`、`station_file.path`、`phase_file.path`；`outputs.catalog_path/arc_path/rejected_path`；`stats.events_in/located/rejected` |
| relocation | `outputs.catalogs` 与 `reloc_paths` 按 loose/medium/strict 分别列出；`event_mapping_path` |
| detection | 单HypoDD中档模板库；每份CC目录有独立2.1契约，selection.cc_min为0.4/0.6/0.8；根catalogs.json只做导航 |
| mechanism | 共享v2信封；目前无真实产物，未进行该环节的端到端验证 |

不因源文件同名就声称速度模型表示等价。没有独立证据时，定位的 `comparison_with_association` 为 `NOT_TESTED`。

## 读取与发布

受维护的技能脚本通过同目录 `contract_io.py` 引用共享实现 `pipeline_contracts.py`。

```python
from contract_io import load_contract, product_path, publish_payload
doc, path = load_contract(run_directory, "location")
catalog = product_path(run_directory, "location", "outputs.catalog_path")
```

传目录时优先读取 `contract.v2.json`；传旧契约路径时，只有相邻v2的源SHA256与旧文件一致才接受迁移副本。没有迁移副本时明确报错，不临时猜测字段。操作读取会校验自身及上游链；`check_artifacts=False` 只供审阅元数据，生产读取不得使用。

已有模板和早期生成器的JSON先作为**源元数据**完成，再经统一发布器生成v2。未完成的 `template_only=true` 模板禁止发布。

```bash
<validator_python> -B contracts/pipeline_contracts.py publish run/source_payload.json --stage location --out run/contract.v2.json
<validator_python> -B contracts/pipeline_contracts.py validate run/contract.v2.json
```

拾取和关联生成器已调用同一发布接口。预处理、定位、重定位与检测的交接报告须在声明完成前运行发布器；它读取实际文件、规范路径、核算关键数量并验证Schema。已有v2原生元数据也可经该入口发布。输出或源快照已存在时拒绝覆盖，需给出新的修订文件名。

科学环境缺少现代jsonschema时，仅把Schema验证交给 `runtime.local.json`中的validator_python 指定的已有解释器；科学程序本身仍运行在原环境。配置的解释器不可用时报告依赖问题，不自动创建或升级环境。

## 迁移与执行范围

发布包不含开发地区的历史结果。显式迁移使用 `migrate_contracts.py --source <file> --stage <stage> --out <new-file>`，格式迁移不声称科学程序重新执行。

操作读取递归核对完整上游链。新的预处理发布器逐文件登记波形和元数据的SHA256。定位和重定位保留 `station_aliases.json`，使原生短台站码可逆地对应完整身份。当前机制解Schema仅为格式预留，不表示已交付机制解程序。

## 重定位的部分交付

现行重定位Schema支持 `tiers.statuses` 的 READY/EMPTY/UNAVAILABLE。EMPTY目录有表头且事件数为0；未执行求解时不声明原生reloc文件。UNAVAILABLE不发布该档目录，未知的去留与孤儿数量不填成0。存在空档或不可用档时总体状态为PARTIAL。MESS只读取READY且非空的中档，并核验完整上游运行链。
