---
name: seismic-location
description: 使用钉版HYPOINVERSE1.40和固定转换器完成绝对定位，验证原生文件、台站别名及事件引用。
---

# Location

发布版本 0.2.0。先读包根目录 `AGENTS.md`。使用 `pipeline.json` 的地区与运行设置、`runtime.local.json` 的解释器映射；禁止依赖开发机路径、聊天历史或某个环境名称。

统一入口（`python` 是明确选择的现有或已部署解释器）：

```bash
python <package>/seisflow.py --runtime <mapping.json> run --config <run>/pipeline.json --stage location
```

固定格式转换与程序调用使用本技能维护的 `scripts/`，由统一入口调用。正常新数据运行不改写转换器。所有下游读取当前 `contract.v2.json`，原生输入校验失败时停止受影响步骤。新配置使用新运行目录；不覆盖已完成结果或伪造验证报告。参数依据和用户选择写入运行配置及记录，不只留在对话中。

科学程序完成、接口验证通过、科学质量已审阅是不同状态。报告实际计数、排除原因、QC路径与尚未验证项。


## 随包 Wiki 的使用

本环节先读取 `knowledge/bindings/location.md`，或运行包入口 `seisflow.py knowledge stage --stage location` 获取明确阅读路线。需要解释参数/方法时，通过 `knowledge search --stage location --query <问题>` 查询，再用 `knowledge read --id <条目ID>` 和 `knowledge source --id <来源ID> --page <PDF页码>` 回到原文。

带上 `--run-dir <运行目录> --stage location` 可记录实际返回的条目/来源；对关键配置选择使用 `knowledge cite` 保存条目、配置值和理由。自动生成的阶段知识上下文只表示资料已提供，不代表agent实际读过，也不代表科学事实已独立验证。具体命令见 `docs/WIKI_INTEGRATION.md`。

Wiki论文与历史手册用于其声明的证据范围；本阶段的具体格式、默认值与决策权限以对应的钉版代码/手册和维护规则核对。不要将论文案例值自动填为地区默认值。正式运行固定知识快照，新增经验先保存在运行目录。


## 地区输入

`input/velocity.csv` 显式给出depth_top_km/vp_km_s/vs_km_s。当前CRH转换支持首层0km、层深和速度严格递增的分层模型；P/S层界相同。其他格式须有明确单位/基准的适配，模型超出支持范围则说明原因。以海平面为深度基准，台站高程单位m。

台站输入使用完整身份。转换器产生唯一五字符别名，映射保存在 `input/station_aliases.json`；`.arc`中的别名必须随该文件解释，不能丢弃网络码或截断长台站名。

## 定位设置与检查

使用包内已验证二进制及哈希。当前定位运行器采用固定初始设置：LET 5 2 3 2 2、RMS 4 .10 2 3、ERR .10、MIN 4、ZTR 5 F、DI1 1 50 3 6、DIS 4 15 3.5 7、WET 1 .5 .2 .1。P+S模型显式使用CRH/SAL；POS取配置值，在独立S模型存在时不替代该模型。

上述为现有定位profile，迁移时核对区域适用性。发现初始深度、距离降权等不适合当前数据时报告用户，由维护后的显式配置/工具修订进行实验，不擅自改程序内部或假称已使用GaMMA逐事件深度种子。

生成文件必须先由 `verify_phase_dat.py` 校验，再启动定位。明确打开PRT/SUM/ARC。保留原生输出及拒绝事件；QC显示RMS、GAP、ERH/ERZ和定位警告。较小残差不证明深度准确。

需准备HypoDD的Vp/Vs时，调用 `scripts/wadati_pos.py --assoc-dir <run>/association --out <run>/location/qc/wadati`，检查有效配对、拟合与离散程度，再把有依据的值写入relocation配置。
