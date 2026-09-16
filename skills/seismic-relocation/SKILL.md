---
name: seismic-relocation
description: 使用ph2dt和HypoDD生成三套独立参数目录，按实际阻尼试算的空间稳定性选择DAMP，保留空档和证据不足状态。
---

# Relocation

发布版本 0.2.0。先读包根目录 `AGENTS.md`。使用 `pipeline.json` 的地区与运行设置、`runtime.local.json` 的解释器映射；禁止依赖开发机路径、聊天历史或某个环境名称。

统一入口（`python` 是明确选择的现有或已部署解释器）：

```bash
python <package>/seisflow.py --runtime <mapping.json> run --config <run>/pipeline.json --stage relocation
```

固定格式转换与程序调用使用本技能维护的 `scripts/`，由统一入口调用。正常新数据运行不改写转换器。所有下游读取当前 `contract.v2.json`，原生输入校验失败时停止受影响步骤。新配置使用新运行目录；不覆盖已完成结果或伪造验证报告。参数依据和用户选择写入运行配置及记录，不只留在对话中。

科学程序完成、接口验证通过、科学质量已审阅是不同状态。报告实际计数、排除原因、QC路径与尚未验证项。


## 随包 Wiki 的使用

本环节先读取 `knowledge/bindings/relocation.md`，或运行包入口 `seisflow.py knowledge stage --stage relocation` 获取明确阅读路线。需要解释参数/方法时，通过 `knowledge search --stage relocation --query <问题>` 查询，再用 `knowledge read --id <条目ID>` 和 `knowledge source --id <来源ID> --page <PDF页码>` 回到原文。

带上 `--run-dir <运行目录> --stage relocation` 可记录实际返回的条目/来源；对关键配置选择使用 `knowledge cite` 保存条目、配置值和理由。自动生成的阶段知识上下文只表示资料已提供，不代表agent实际读过，也不代表科学事实已独立验证。具体命令见 `docs/WIKI_INTEGRATION.md`。

Wiki论文与历史手册用于其声明的证据范围；本阶段的具体格式、默认值与决策权限以对应的钉版代码/手册和维护规则核对。不要将论文案例值自动填为地区默认值。正式运行固定知识快照，新增经验先保存在运行目录。


## 输入与三档

消费当前定位和关联契约，使用同一地区P波模型。`vp_vs_ratio` 必须有当前数据的Wadati等明确依据，不能把旧地区1.73当作通用事实；常数比值的适用性需检查。

固定转换器保留可逆台站身份，按台站位置和震相选最高概率观测。配对和求解使用钉版二进制。三档各自执行配对、阻尼试算和正式重定位，默认MINLNK/MINOBS/OBSCT为3/4/6，末组WDCT为4/3/2km；各档完整目录保留，不进行事后质量切片。

初始配对MAXDIST=100km、MAXSEP=10km、MAXNGH=10。它们是可检查的项目初始设置；变更在配置中显式记录并用新的运行目录实验。迭代表见 `scripts/run_hypodd.py`：S波权重0.5/0.5/0.4/0.3，不是WRCT秒数。WRCT大于等于1为标准差倍数，0到1之间为秒，-9为不剔除；不得混淆。

## DAMP权限

运行20/50/100/200等明确候选的小量试算。按照 `references/damping.md` 的当前规则，检查相邻试算共同事件的结构稳定性、簇质心漂移、覆盖率和实际初始ERH尺度，采用有证据支持的最小DAMP。CND40–80仅是经验参考，不参与自动通过/拒绝判定。证据不足才交用户判断或准备明确的新试验；不伪造选择文件。

正式运行必须消费与当前输入、模型、参数和试算产物匹配的选择证据。各档分别发布READY、EMPTY或UNAVAILABLE；无证据/求解失败不能记为0事件。MESS只消费中档READY目录；中档不可用时明确停止检测。

本阶段是 MESS 前的第一轮重定位，使用目录差分时间 IDAT=2。MESS 完成后必须继续 post_detection_relocation，使用独立 PhaseNet+ CT 与 MESS CC 联合 IDAT=3；该阶段仅交付三套 CC 档目录，重新执行同一套 DAMP 空间证据规则。维护的 run_hypodd.py 同时支持经过独立输入校验的联合模式。
