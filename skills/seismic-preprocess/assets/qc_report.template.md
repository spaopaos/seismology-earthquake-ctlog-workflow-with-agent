# 预处理QC摘要：{{run_id}}

> 本文件是填写模板，不是结果。用实际表替换占位；没有计算的字段写“未计算”及原因，不能编造数字或直接将NOT_RUN改为通过。

## 本次状态

预处理：{{preprocessing_status}}；归档回读：{{archive_validation_status}}；QC生成：{{qc_generation_status}}；图件审阅：{{visual_review_status}}。PhaseNet+读入验证：{{model_input_verification_status}}。

输出：{{output_root}}。UTC请求：{{start_utc}}至{{end_utc_exclusive}}（终点不含）。日期范围来源：{{date_range_source}}。

## 数据规模与完成情况

| 统计项 | 实际值 | 口径或缺项说明 |
|---|---|---|
| 去重台站数 / 仪器组数 | {{station_count}} / {{sensor_group_count}} | NET.STA与NET.STA.LOC.FAMILY分别计数 |
| 请求组日数 / 已发布组日数 | {{expected_group_day_count}} / {{published_group_days}} | 请求范围与已知部署范围明确 |
| 全日 / 部分日 / 未交付 | {{complete_partial_missing}} | 不能按SAC文件跨度判定全日 |
| 缺分量 / 缺响应 / 失败 | {{input_or_processing_issue_counts}} | 不把不同原因混为缺测 |
| 3C实际交付可用时长 | {{delivered_usable_3c_seconds}} s | 取三轴可用区间交集，不求平均 |

原始采样率分布：{{sampling_rate_summary}}。实际已执行频带：{{effective_band_summary}}。受限频带组及原因：{{band_limited_groups}}。整日与请求内覆盖率分别见`availability.csv`。

## 图表入口

按`qc_artifacts.json`列出真正存在的总览、波形、PSD和响应诊断图；未生成项给状态和原因，不建立无效链接。

{{actual_artifact_links_and_omissions}}

## 抽样检查

已选择{{selected_baseline_count}}个基线例和{{selected_anomaly_count}}个实际异常例；选择规则、时窗和配置见`sample_selection.csv`。未覆盖的采样率/响应/方向类型：{{uncovered_categories}}。

真实查看者与查看范围：{{reviewer_and_reviewed_files}}。有证据支持的观察：{{observed_findings}}。尚未实际查看或检查的内容：{{unreviewed_or_untested_items}}。

原始counts与速度m/s分别显示，PSD只来自有效连续片段。抽样诊断不能解释为全台网精度或长期噪声评价。

## 交付限制与下游注意

{{blocking_issues_and_required_follow_up}}

读取100 Hz带限m/s数据时，保留实际频带、方向与缺口信息，防止重复去响应/积分。QC完成不等于PhaseNet+读入路径验证完成；模型测试未运行时保持NOT_TESTED。统计来源与实际绘图脚本：{{source_tables_and_script}}。
