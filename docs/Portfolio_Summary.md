# Portfolio Summary / 项目摘要

## Project / 项目

`jiangsu-site-rank` is a China-local retail site-selection analytics case study. V1 evaluates 徐州 and 南京 candidate sites through a pandas/CSV scoring dashboard. V2 adds a verified MySQL relational site–POI model, SQL feature views, deterministic migration checks, Python scoring, and a separate Streamlit review dashboard.

本项目是中国本地零售选址分析案例。V1 提供 pandas/CSV 双城市评分仪表盘；V2 增加经过 MySQL 8.4 验证的关系型候选点–POI 数据模型、SQL 特征层和独立复核仪表盘。

## Business Question / 业务问题

Given a small set of plausible candidate sites, which locations deserve deeper manual review for coffee shop expansion?

在一组人工挑选的候选点中，哪些点位更值得优先进行实地踏勘、租金核验和经营可行性复核？

The project does not try to identify every possible location in a city. It ranks known candidate sites so a reviewer can prioritize field visits and business due diligence.

本项目不做全城自动找铺，也不替代最终租赁决策；它是用于排序和复核优先级的 decision support / 决策支持工具。

## Current Outputs / 当前产出

- 徐州 MVP: 7 candidate sites scored and displayed in the dashboard.
- 南京 validation run: 8 candidate sites scored using the frozen v2 model.
- V1 dashboard: one Streamlit app with a sidebar `城市` selector for 徐州 and 南京.
- V2: 15 sites, 6,866 canonical POIs, and 8,661 unique site–POI relationships loaded and verified on MySQL 8.4.
- Verification: FK and semantic checks passed; all SQL feature values matched pandas exactly.

当前已完成徐州 MVP、南京第二城市验证，以及一个可切换城市的 Streamlit 仪表盘。

| City | Rank | Candidate | Score | Note |
| --- | ---: | --- | ---: | --- |
| 徐州 | 1 | 徐州苏宁广场 | 86.89 | Strong demand/access/maturity, high competition pressure |
| 徐州 | 2 | 金鹰国际购物中心 | 86.57 | Similar top-tier commercial profile |
| 徐州 | 3 | 彭城广场商圈 | 86.56 | Highest maturity/demand, very crowded |
| 南京 | 1 | 新街口商圈 | 84.86 | High overall score, clear over-saturation risk |
| 南京 | 2 | 湖南路商圈 | 84.08 | Strong score with more moderate competition fit |
| 南京 | 3 | 珠江路商圈 | 78.27 | Strong demand, high competition pressure |

## Model Interpretation / 模型解读

The v2 score combines demand anchors / 需求锚点, accessibility / 可达性, commercial maturity / 商业成熟度, and competition fit / 竞争适配度. Competition fit is a positive scoring component, not raw competition level.

`competition_fit_score` 不是原始竞争强度。真实竞争压力应看 `competitor_pressure_score` 和直接竞品数量。

For example, 南京新街口 has very high actual competition pressure. Its low `competition_fit_score` means the area may be over-saturated, not that competition is weak. It can still rank high overall because demand, access, and commercial maturity are strong.

例如南京新街口：整体排名高，是因为需求、交通和商业成熟度很强；但竞争适配度很低，表示过度饱和风险，而不是“竞争少”。

## Reviewer First Impression / 给评审的第一印象

The README is designed to communicate the project in roughly 10 seconds: data pipeline, 高德 API collection, feature engineering, explainable scoring, dashboard, two-city validation, and explicit limitations.

README 的目标是在约 10 秒内让 GitHub/recruiter 评审理解：这是一个有数据管线、有高德 API 采集、有特征工程、有可解释评分、有仪表盘、有业务解读、并清楚写出限制的双城市选址案例。

## Review Status / 复核状态

南京 sanity check passed for a first validation run. No scoring recalibration was applied after the first 南京 review. Known watchpoints remain documented, especially the sparse POI signal around the current 南京仙林大学城 candidate point.

南京首轮验证通过，暂未重新校准评分模型。已记录的重点风险包括：南京仙林大学城当前候选点 POI 信号偏稀疏，后续可能需要更合适的代表点或关键词复核。

## What A Reviewer Should Notice / 评审应关注

- The workflow is reproducible and inspectable / 流程可复现、可检查。
- Generated raw and processed data are separated from manual inputs / 人工输入与生成数据分离。
- The score is transparent enough to challenge / 评分足够透明，可以被质疑和复核。
- Limitations are visible rather than hidden / 限制条件没有被隐藏。
- The dashboard supports within-city comparison, not absolute cross-city investment ranking / 仪表盘支持城市内比较，不宣称跨城市绝对投资排序。
- V2 provides an auditable foundation for a future MySQL-connected AI advisory agent; the existing local V1 rules-based analyst is separate / V2 为未来连接 MySQL 的 AI 顾问层提供可审计基础，现有 V1 本地规则分析器与其分离。
