---
name: seismic-post-detection-relocation
description: MESS 检测后的联合重定位：ph2dt 的 dt.ct + MESS 原生 dt.cc，IDAT=3 联合 hypoDD，含 DAMP 阻尼探测。
---

# 联合 CC+CT 重定位（dt.ct + dt.cc IDAT=3）

## 概述

将目录走时差分（dt.ct，来自 ph2dt）与互相关差分走时（dt.cc，来自 MESS 模板匹配）联合求解 hypoDD 重定位，对所有事件（含 MESS 新检出）产出统一基准的精定位目录。

## 前置条件

| 输入 | 来源 |
|---|---|
| dt.ct | relocation 阶段 ph2dt 产出（复用，不重跑） |
| dt.cc | detection 阶段 MESS 产出 |
| event.dat | detection 阶段 MESS 关联产出 |
| hypoDD 二进制 | 钉版 v2.1beta（MAXEVE=6500） |
| 台站别名文件 | relocation 阶段 station_aliases.json |

## 步骤

### 1. 确定联合事件集合

事件集合 = 全部 hypoDD strict 目录事件（作为模板）+ MESS 新检出事件。

受 MAXEVE=6500 限制：
- 全部模板 + MESS 新检出按 best_cc 从高到低截取至 ≤6500
- 建议将新检出裁至 CC≥0.4（与三档交付下限一致）

### 2. 构建输入文件

**event.dat**（联合）：
- MESS 行沿用（模板事件 + 新检出），格式统一为 **10 字段**、时间 **8 位 HHMMSScc**
- 补入 strict 目录中未自检的模板行（strict 格式，同 10 字段）
- 深度不加偏置（`hypodd_depth_offset_km=0` 已在 config 中设置）

**dt.ct**（改写 ID）：
- 将旧 event_index 映射为 strict CSV 行号
- 保留双端都在联合集合内的对（其余弃）

**dt.cc**（改写台站名）：
- 将裸台站名（如 `LE001`）改为 S%04d 别名（从 station_aliases.json）
- 双位置码台站按 HH 族优先
- 仅保留双端在联合集合内的对

**hypoDD.inp**：
```
IDAT=3（ct+cc 联合）
IPHA=3, DIST=100
OBSCC=4, OBSCT=6
ISTART=2, ISOLV=2（LSQR）, IAQ=1, NSET=4
NITER  WTCCP WTCCS WRCC WDCC  WTCTP WTCTS WRCT WDCT  DAMP
   4    1.0   0.5  -9   -9    1.0   0.5   6    5   <DAMP>
   8    1.0   0.5  -9   -9    1.0   0.4   4    4   <DAMP>
  12    1.0   0.5   4    4    1.0   0.4   4    4   <DAMP>
  16    1.0   0.5   3    2    1.0   0.3   3    2   <DAMP>
```

> ⚠ dt.cc 文件引用行后**不能有空行**（会报 "line 10" 错）。

### 3. DAMP 阻尼探测（五档并行）

用 Python 生成五档配置（**不要用 sed**——CRLF 文件上 sed 会静默失配）：

```python
DAMPS = [50, 100, 200, 400, 800]
base = open("hypoDD.inp").read().replace("\r\n", "\n")
for d in DAMPS:
    txt = base.replace("<DAMP>", f" {d}.0")
    open(f"hypoDD_d{d}.inp", "w", newline="\n").write(txt)
```

五档**并行**运行（hypoDD 是单进程，机器多核时可同时跑五个）。

#### 选定判据

| 指标 | 稳定标准 |
|---|---|
| 相邻阻尼解差异 | 水平中位 <200 m |
| 事件保留数 | 低阻尼不应大幅下降 |
| 紧致度（最近邻） | 不随阻尼单调恶化 |
| 深度分布 | 不出现系统性拉深/拉浅 |

选稳定平台中部（通常 200–400）的值作为终版 DAMP。

### 4. 终版求解

用选定 DAMP 重跑一次，产出 `hypoDD.reloc`。

### 5. 解析终版目录

从 `hypoDD.reloc` 解析（注意**首列=cusp ID**，非末列）：
- cusp < 模板总数 → 模板事件（对应 strict CSV 行号）
- cusp ≥ 1000000 → MESS 新检出

合并 MESS catalog.csv 的 best_cc、strict 目录的 ML，产出联合目录 CSV。

### 6. 被剔事件补回

hypoDD 会因走时不一致剔除部分事件（固有行为）。对被剔的大事件（用户判断是否补回），按 strict 坐标补入目录。

## 交付

| 产物 | 说明 |
|---|---|
| `joint_relocated_catalog.csv` | 终版联合目录（含 event_id, source, 坐标, 深度, ML, best_cc） |
| `hypoDD.reloc` + 各迭代 | 原生 hypoDD 输出 |
| DAMP 扫描对比表 | 五档指标矩阵 |

## 关键坑

1. **hypoDD.inp dt.cc 行后空行** → "line 10" 错
2. **event.dat 11 字段** → 统一为 10 字段
3. **event.dat 时间 9~10 位** → 归一为 8 位 HHMMSScc
4. **reloc 输出首列是 cusp ID**（不是末列）
5. **sed 在 CRLF 文件上静默失配** → 用 Python 生成配置
6. **dt.ct 的 ID 是 gamma event_index**（6171 事件空间），不是 strict 行号
7. **PALM hypodd_depth_offset_km=5.0 会给 event.dat 全部深度 +5 km** → config 中设 0
