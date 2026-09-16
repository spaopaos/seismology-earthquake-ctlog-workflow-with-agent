# MESS 后的联合 HypoDD 重定位

标准顺序：预处理 → PhaseNet+ → GaMMA → HYPOINVERSE → HypoDD（CT，提供模板）→ MESS → HypoDD（CC+CT）。最后一个阶段名为 `post_detection_relocation`，`all` 包含该阶段。

## 三套结果

CC≥0.4、0.6、0.8 分别进入独立求解，各自选择 DAMP，共三套正式目录。每套使用同一套初始配对/联合迭代设置，DAMP 试算保存在各自 qc/。不再交叉展开成九套目录。

CT 到时必须来自原始独立 PhaseNet+ 拾取，保留 CSV 行号、概率和完整仪器组。MESS 到时只定位匹配窗口，默认 P±0.6 s、S±1.0 s，概率至少 0.3；这些是显式可调整的初始设置。窗口内多个拾取或同一拾取被多个事件索取均排除。缺测保留缺测，不用模板/MESS 到时补值。共用一次匹配决定，再按三 CC 集合筛选，保持共同事件的 CT 归属一致。

CC 为 MESS 实测差分时，统一发震时间和可逆台站别名。事件原生时间的百分秒取整、模板原发震时间和检测发震时间的差别必须反映到 CC 修正与 CT 走时。移除 MESS 导出时声明的深度偏移，以原海平面基准 P 模型求解；新阶段不以平移震源替代模型基准处理。

ph2dt 生成 CT 配对，其原始输出留在 ct_pairing/。联合 event.dat 保留两类连接需要的事件和模板参考，允许单个事件只有 CC 连接。正式求解要求两类数据均有有效观测，并在原生输出中确认两类均有使用。

## 参数与判定

`configs/pipeline.example.json` 给出完整联合设置。配对从原中档 MINLNK/MINOBS=4、MAXDIST=100 km、MAXSEP=10 km、MAXNGH=10 开始。IDAT=3、IPHA=3、OBSCC=0、OBSCT=4；按手册联合聚类的有效链接门槛是两者之和。CC 实际权重在迭代表中为正。

四组 NITER 分别为 4/8/12/16。初段 CT 权重较高，后段增强 CC，同时保留 CT；最终 WDCC=2 km、WDCT=3 km。WR 值大于等于 1 是标准差倍数，小于 1 为秒，−9 关闭剔除。以上只是起始参数，不构成区域最优结论。

每个 CC 档从 DAMP=20/50/100/200 试算，按共享 `spatial-evidence-1.7` 规则比较相邻候选的共同事件结构和逐簇质心漂移，采用支持的最小值。需要更大邻居时扩展候选并使用新试验目录。CND 40–80 只作经验参考；缺证据不自动通过。第一轮选择的 DAMP 不能直接用于第二轮。

Vp/Vs 使用同地区上游有依据的比值。默认空间比较尺度取上游定位 ERH 正有限值的中位数，明确不是 MESS 新事件的误差估计。不能从 MESS 同源互相关到时重算一个“独立 Wadati”依据。

## 启动和迁移

复用已有 runtime.local.json。为新修订初始化新目录，填入实际 archive、stations、velocity_model，保留上游契约链；可用已有 `picking/association/location/relocation` 的只读路径或链接，新配置的 `post_detection_relocation.detection_catalogs` 可指向原 MESS 三档目录。

```bash
./runtime/phasenet_plus/bin/python seisflow.py --runtime runtime.local.json init --workdir /path/to/new-run
./runtime/phasenet_plus/bin/python seisflow.py --runtime runtime.local.json run \
  --config /path/to/new-run/pipeline.json --stage post_detection_relocation
```

填写配置后执行；示例路径不是自动推断的地区输入。旧配置没有联合设置时明确拒绝，不能在旧 run_state 或 knowledge.lock 上补改以伪装同一次运行。原始 Wiki/PDF 不随工作流更新而重写。

## 交付与限制

`post_detection_relocation/{cc_0p4,cc_0p6,cc_0p8}/catalog.csv` 保存检测事件的正式重定位结果。`reference_events.csv` 单独保存求解所需参考事件，`event_lineage.csv` 说明保留、排除及 CC/CT 来源。另有原生结果、独立拾取匹配/排除、差分时修正、试算选择、日志和 QC，顶层 `catalogs.json` 与 `contract.v2.json` 汇总三档。

READY 表示支持的正式联合运行；EMPTY 表示经过检查的无事件结果；UNAVAILABLE 表示缺观测、缺阻尼证据或求解失败。不可用档不发布伪造的零事件目录，整体状态为 PARTIAL。`status=known/new` 保留检测时的身份判据，不能用时间窗匹配自动合并事件。

最终坐标标记 `location_method=hypodd_cc_ct`，原始模板坐标另列。分别记录原生最终 CC/CT 残差及观测数量；数量可能是事件—观测关联次数，不应当作唯一差分时数。参数稳定与求解完成不证明地质位置或绝对深度准确，震级未绝对标定。
