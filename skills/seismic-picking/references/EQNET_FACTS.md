# EQNet 代码事实核查记录

核查日期：2026-09-10 · 基准：`knowledge/repos/EQNet` @ `af94a08`（只读钉版）
行号以该 commit 为准；换版本须重新核对。

## 读取路径（`eqnet/data/seismic_trace.py`）

| # | 事实 | 位置 |
|---|---|---|
| F1 | `read_mseed()` 对通道族末位为 `N` 的台站执行 `trace.integrate().filter("highpass", 1.0)`（"acceleration to velocity"）——对已是速度的 HN 数据是错误二次积分 | `read_mseed` 内 `if sta[-1] == "N"`（约 L809） |
| F2 | `read_mseed()` 支持 `response_path`/`response_xml` 触发 `remove_sensitivity`；本项目两者必须为 None | 同上 |
| F3 | `highpass_filter > 0` 时读入即零相位高通（corners=4）；`predict.py` 主分支默认 `--highpass_filter 1.0` | `predict.py` 参数定义（约 L500） |
| F4 | 采样率 ≠ `--sampling_rate` 时 `trace.interpolate(sampling_rate, method="linear")` 线性插值——本项目禁止，shim 直接拒绝 | `read_mseed` 重采样段 |
| F5 | `merge(fill_value="latest")`；随后 `trim(begin, end, pad=True, fill_value=0)` | 同上 |
| F6 | 分量映射 `comp2idx = {"3":0,"2":1,"1":2,"E":0,"N":1,"Z":2}`，数组按 E,N,Z 排布 | 同上 |
| F7 | `station_id = tr.id[:-1]`（台站+仪器组粒度），HH 与 HN 组自然分开 | 同上 |
| F8 | `begin_time` 以 `isoformat(timespec="milliseconds")` 传递（@100 Hz 为 0.1 采样点） | 同上 |
| F9 | data_list 每行一个文件，或逗号分隔多文件（E,N,Z 合并入同一 stream 再按台站分组） | `sample()` |

## 模型与归一化（`eqnet/models/unet.py`）

| # | 事实 | 位置 |
|---|---|---|
| F10 | 预测路径的归一化在模型内部：`UNet.forward()` 首行 `moving_normalize(x, filter=1024, stride=128)`（10.24 s 滑窗，reflect padding，**非原地**——caller 的 `meta["data"]` 保持原始值供振幅测量） | `forward`（约 L258）；`moving_normalize`（约 L15） |
| F11 | `seismic_trace.py` 顶部的全局 mean/std `normalize()` 只被训练读取路径使用，预测路径不经过——旧 palm-eq-catalog skill 称"按窗归一化压制小事件"的归因不准确 | `normalize`（约 L29） |
| F12 | 极性分支 `encoder_polarity` 只取 `x[:, -1:, :, :]`（最后通道=Z） | `forward` 内 `add_polarity` 段 |
| F13 | 网络下采样 4 级、stride 4，输入长度须 padding 到 1024 整数倍（`padding()` 自动处理） | `seismic_trace.padding` |

## 拾取提取（`eqnet/utils/postprocess.py`）

| # | 事实 | 位置 |
|---|---|---|
| F14 | picks CSV 列：`station_id, phase_index, phase_time, phase_score, phase_type, dt_s, phase_polarity, phase_amplitude` | `extract_picks`（约 L120–160） |
| F15 | `phase_polarity` 是拾取点 ±3 样本窗内 softmax P(up)−P(down) 的有符号分数 [-1,1]，**非概率**；P/S 拾取均带此值 | 约 L140–148 |
| F16 | `phase_amplitude`：原始波形三分量逐点最大绝对值在窗内的最大值（P 窗 10 s、S 窗 5 s，截于下一拾取）；m/s 数据上是真实物理量 | 约 L150–157 |
| F17 | `--min_prob` 为 P/S 共用单阈值（默认 0.3），无分设参数 | `predict.py` 参数 |
| F18 | `detect_peaks`：`kernel=128`（@100 Hz 为 1.28 s 最小峰距）；`K = max(round(nt/30s×10), 3)`——每 30 s 每震相最多 10 个拾取，触顶无报错 | `detect_peaks`（约 L31） |

## 推理行为（`predict.py`）

| # | 事实 | 位置 |
|---|---|---|
| F19 | 不切 patch 时整条记录直接进网络（`sample()` 的 `not cut_patch` 分支），`batch_size=1` 因各文件长度不一 | `sample()`；`predict.py` |
| F20 | 输出文件命名：`parent_dir` 取路径末 `subdir_level+1` 段；默认 0。多输入同名时静默覆盖（palm 流水线实测 133 万窗口塌缩为 1.6 万输出，98.8% 丢失） | `pred_phasenet_plus` 写文件段 |
| F21 | 无拾取的文件也会 touch 空 CSV——计数断言时分母应含空文件 | 同上 |
| F22 | 权重自动下载 `PhaseNet-Plus-v1/model_99.pth`，`check_hash=True` | `main()` |
| F23 | `torch.backends.*.allow_tf32 = True` 硬编码；跨后端拾取差异 ~7% 属正常（palm 流水线实测 ROCm vs CUDA） | `main()` |

## 论文事实（Zhu & Beroza 2019, GJI 216:261–273；`knowledge/papers/phasenet_zhu_beroza_2019.*`）

| # | 事实 |
|---|---|
| F24 | 训练用未滤波 100 Hz 数据、30 s 随机位置窗口、按窗 mean/std 归一化；论文明确 PhaseNet 不需要滤波预处理 |
| F25 | 频带说明：本流水线归档为 1–40 Hz 带限，与训练数据有差异。用户裁定：滤波是地震学通用做法，已知并接受，不作跟踪 |
