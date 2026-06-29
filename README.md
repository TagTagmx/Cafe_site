# jiangsu-site-rank

Decision-support case study for coffee shop site selection / 咖啡店选址决策支持案例. The project combines a local data pipeline, 高德 Web 服务 API geocoding and POI collection, feature engineering / 特征工程, explainable scoring / 可解释评分, and a Streamlit dashboard that turns manually selected candidate sites / 候选点 in 徐州 and 南京 into ranked business evidence with interpretation.

本项目面向中国本地零售选址分析：从人工挑选的咖啡店候选点出发，通过高德地理编码和周边 POI 采集，生成可解释的选址评分和仪表盘解读。它不是自动租铺决策工具，而是用于支持实地踏勘、租金核验和商业判断的 decision support / 决策支持案例。

## 10-Second Read

- **Problem:** Which candidate sites deserve deeper review for coffee shop expansion?
- **Cities:** 徐州 MVP plus 南京 second-city validation.
- **Data:** Manual candidate sites enriched with 高德 geocoding and nearby POIs.
- **Method:** Deduplicate POIs, engineer demand/access/competition features, score with transparent weights.
- **Output:** Streamlit dashboard with city switching, ranked sites, component breakdowns, and business interpretation.
- **Positioning:** Decision support, not an automatic leasing decision.

本项目考虑“哪些咖啡店候选点值得优先深入评估”。当前覆盖徐州和南京，使用人工候选点、高德 POI、特征工程、可解释评分和 Streamlit 仪表盘，输出用于业务复核的排序结果。

## V1 And V2 Architecture / V1 与 V2 架构

The repository keeps two explicit, working paths:

- **V1 — pandas/CSV dashboard:** the original two-city POI pipeline aggregates and scores CSV files with pandas, then serves `app/streamlit_app.py`.
- **V2 — MySQL relational workflow:** MySQL stores cities, candidate sites, canonical POIs, observation evidence, category rules, and deterministic site–POI relationships. SQL exposes auditable raw feature counts; Python performs the documented scoring and explanation logic; `app/v2_review_app.py` provides a separate review dashboard.

仓库保留两条清晰路径：V1 是基于 pandas/CSV 的双城市评分仪表盘；V2 是经过 MySQL 8.4 验证的关系型数据流程。V2 没有改写 V1，也没有改变已冻结的评分权重。

All V2 tickets are complete. The full 徐州/南京 trial was loaded and verified on MySQL Community Server 8.4.10. Foreign keys and semantic integrity passed, all 15 named SQL checks passed, and every MySQL feature value matched the pandas reference output.

## What V2 Adds / V2 新增内容

- Relational tables for cities, sites, POIs, observations, keywords, and category rules / 关系型核心表。
- A deterministic many-to-many site–POI relationship layer / 确定性的候选点–POI 关系层。
- Foreign-key and semantic-integrity checks / 外键与语义完整性检查。
- Exact SQL/pandas feature parity verification / SQL 与 pandas 特征逐值一致性验证。
- A stronger, auditable data foundation for a future AI advisory agent / 为未来 AI 选址顾问提供更可靠、可追溯的数据基础。

V2 remains explainable decision support. It does not include a MySQL-connected AI advisory agent, machine learning, revenue prediction, or automatic leasing decisions. The existing V1 dashboard has a local rules-based site analyst, but it does not query or mutate the V2 database.

## Verified MySQL 8.4 Workflow / 已验证工作流

Configure the local `MYSQL_*` values shown in `.env.example`, then run:

```powershell
# Deterministic load / 确定性加载
python src/load_v2_full_trial_mysql.py --create-database --reset

# FK, integrity, and SQL/pandas parity verification / 外键、完整性与特征一致性验证
python src/verify_v2_full_trial_mysql.py

# MySQL-backed scoring export / 基于 MySQL 的评分导出
python src/score_v2_sites.py --output-dir data/exports/v2/full_trial/mysql_scored

# V2 review dashboard / V2 复核仪表盘
python -m streamlit run app/v2_review_app.py
```

Use `python src/load_v2_full_trial_mysql.py --reset` when the configured database already exists. The reset targets the dedicated local V2 schema; see `docs/V2_T5_MySQL_Verification_Guide.md` before running it.

## What This Demonstrates

- A small but complete site selection / 选址 analytics workflow from manual candidate sites to dashboard review.
- 高德 Web 服务 API geocoding and POI snapshots for China-local retail context.
- Feature engineering / 特征工程 for demand anchors / 需求锚点, accessibility / 可达性, commercial maturity / 商业成熟度, and competition pressure / 竞争压力.
- Explainable scoring / 可解释评分 with visible component values.
- Business interpretation in a Streamlit dashboard rather than a black-box recommendation.

项目展示了一个从人工候选点、数据采集、清洗聚合、特征工程、评分到仪表盘解读的小型完整选址分析流程，重点是可解释、可复核，而不是黑箱自动推荐。

## Current Results

These example values come from local generated score outputs under `data/processed`. The generated CSV files are ignored by git and are not meant to be committed.

下表展示本地已生成评分结果中的示例值。`data/processed` 属于生成产物，不应提交到repo。

| City | Rank | Candidate | Score | Demand / 需求 | Access / 可达性 | Maturity / 商业成熟度 | Competition pressure / 竞争压力 | Competition fit / 竞争适配度 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 徐州 | 1 | 徐州苏宁广场 | 86.89 | 97.96 | 100.00 | 98.89 | 94.63 | 19.50 |
| 徐州 | 2 | 金鹰国际购物中心 | 86.57 | 98.90 | 95.84 | 95.94 | 89.59 | 25.78 |
| 徐州 | 3 | 彭城广场商圈 | 86.56 | 100.00 | 96.89 | 100.00 | 95.03 | 15.56 |
| 南京 | 1 | 新街口商圈 | 84.86 | 99.66 | 100.00 | 100.00 | 97.17 | 0.00 |
| 南京 | 2 | 湖南路商圈 | 84.08 | 97.69 | 93.77 | 67.18 | 62.82 | 54.17 |
| 南京 | 3 | 珠江路商圈 | 78.27 | 100.00 | 83.20 | 81.53 | 92.27 | 7.78 |

Important interpretation: `competition_fit_score` is not raw competition level. Actual competition intensity is shown by `competitor_pressure_score` and direct competitor counts. 南京新街口 can rank high overall because demand anchors / 需求锚点, accessibility / 可达性, and commercial maturity / 商业成熟度 are very strong, while its low `competition_fit_score` flags over-saturation risk.

重要解读：`competition_fit_score` 不是“竞争少”。真实竞争强度应看 `competitor_pressure_score` 和直接竞品数量。南京新街口整体排名高，是因为需求、交通和商业成熟度很强；但它的竞争适配度为 0，表示模型识别到过度饱和风险。

## Dashboard

Run the dashboard:

```powershell
python -m streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`, then use the sidebar `城市` selector to switch between 徐州 and 南京.

打开 `http://localhost:8501` 后，可以在侧边栏通过 `城市` 选择器切换徐州和南京。

The dashboard shows / 仪表盘包含：

- Ranked candidate sites / 候选点排名.
- Overall score and component breakdown / 总分与分项拆解.
- Direct competitor counts by radius / 不同半径内直接竞品数量.
- Demand anchors and transit counts / 需求锚点与交通点数量.
- Competition pressure versus competition fit / 竞争压力与竞争适配度对比.
- Selected-site business interpretation / 单点业务解读.
- Methodology notes and model limitations / 方法说明与模型边界.

## Two-City Setup

Shared project pieces / 共享部分：

- `data/manual/poi_keywords.csv`: shared POI keyword buckets for direct competitors, indirect competitors, demand anchors, and transit.
- `src/`: shared geocoding, POI collection, cleaning, aggregation, and scoring scripts.
- `app/streamlit_app.py`: one Streamlit dashboard with a `城市` selector.

City-specific pieces / 城市特定部分：

| City | Manual candidates | Processed score path | Dashboard loading |
| --- | --- | --- | --- |
| 徐州 | `data/manual/candidate_sites.csv` | `data/processed/site_scores.csv` | legacy root processed files |
| 南京 | `data/manual/nanjing/candidate_sites.csv` | `data/processed/nanjing/site_scores.csv` | `data/processed/nanjing` |

The current scripts default to the original 徐州 paths. 南京 has already been run into city-specific folders for validation. This README does not invent extra commands that the code does not support.

当前脚本默认使用徐州的原始路径；南京结果已按城市文件夹生成，用于第二城市验证。README 保持命令可执行，不虚构额外 CLI 参数。

## Pipeline

1. Define manually selected candidate sites / 定义人工候选点.
2. Geocode candidate addresses with 高德 Web 服务 API / 高德地理编码.
3. Collect nearby POIs around candidate coordinates at 300m, 800m, and 1500m / 按半径采集周边 POI.
4. Store raw snapshots under `data/raw` / 保存原始快照.
5. Clean and deduplicate POIs into `data/processed` / 清洗去重.
6. Aggregate one metrics row per candidate site / 汇总候选点指标.
7. Score each candidate with an explainable weighted model / 可解释加权评分.
8. Review results in Streamlit / 在仪表盘中复核.

## Running The Default Pipeline

Create a local `.env` file from `.env.example` and set:

```powershell
AMAP_API_KEY=your_key_here
```

Then run the pipeline scripts in order for the default 徐州 path:

```powershell
python src/geocode_candidates.py
python src/collect_poi_snapshots.py
python src/clean_pois.py
python src/aggregate_site_metrics.py
python src/score_sites.py
```

Generated raw and processed outputs are ignored by git. 生成的 `data/raw/` 和 `data/processed/` 文件不提交。

## Scoring Model

The v2 score is intentionally simple and inspectable / v2 评分模型保持简单、可解释：

```text
site_score =
  demand_score * 0.40
  + accessibility_score * 0.25
  + commercial_maturity_score * 0.20
  + competition_fit_score * 0.15
```

Component meaning / 指标含义：

- `demand_score`: demand anchors / 需求锚点, such as offices, shopping centers, schools, residential communities, and hotels.
- `accessibility_score`: accessibility / 可达性, based on transit and parking-related access signals.
- `commercial_maturity_score`: commercial maturity / 商业成熟度, based on surrounding POI density and adjacent commercial formats.
- `competitor_pressure_score`: competition pressure / 竞争压力. Higher means more direct competitor crowding and/or closer competitors.
- `competition_fit_score`: competition fit / 竞争适配度. Higher means competition is closer to a moderate target.

## Known Limitations

- No rent, lease term, frontage, visibility, store size, or operator cost data.
- Candidate sites are manually selected and do not represent exhaustive city coverage.
- POI quality depends on 高德 API coverage and keyword choices.
- Per-city normalization supports within-city ranking, not absolute cross-city investment ranking.
- 南京仙林大学城 is a sparse-POI watchpoint: the current geocoded campus point may need a better representative point or keyword review.
- High traffic and high competition can coexist; saturated locations require manual judgment beyond POI counts.

中文限制说明：当前模型未纳入租金、租约、门头、可见性、铺位面积和运营成本；候选点不是全城穷举；POI 结果受高德覆盖和关键词影响；城市内归一化适合本城排序，不适合直接做跨城市绝对投资比较；南京仙林大学城目前 POI 信号偏稀疏，需要后续复核。

## Screenshots

No screenshot is committed in this pass. The local environment does not currently have Playwright installed, and this documentation ticket avoids adding new tooling. Run the Streamlit command above to review the dashboard directly.

本次未提交截图，因为本地环境没有 Playwright，且本票据不安装新工具。可直接运行 Streamlit 查看仪表盘。

## Project Structure

```text
app/              Streamlit dashboard
data/manual/      Manually curated candidate inputs and POI keywords
data/raw/         Raw API snapshots, ignored by git
data/processed/   Generated cleaned data, metrics, and scores, ignored by git
docs/             Methodology, tickets, planning, and verification notes
notebooks/        Exploratory analysis placeholder
sql/              Cafe Site V2 schema, raw feature views, fixtures, and verification SQL
src/              Pipeline scripts and reusable API/client logic
```

## Verification

Useful checks before review:

```powershell
python -m compileall app src
python src/verify_v2_full_trial_mysql.py
python -m streamlit run app/streamlit_app.py
python -m streamlit run app/v2_review_app.py
```

Manual review should confirm / 人工复核要点：

- The dashboard loads for both 徐州 and 南京.
- City switching does not mix metrics.
- `.env`, `data/raw/`, and `data/processed/` remain ignored.
- 新街口 is interpreted as high actual competition pressure with over-saturation risk.
- Model limitations remain visible in the README and dashboard.

## Optional Future Roadmap / 可选后续方向

A V2/MySQL advisory layer is a future extension, not part of this release. A sensible next step would connect a read-only agent to verified site evidence so it can cite feature provenance, compare scenarios, and draft bilingual review notes. It should not change scores, write to the database, or make autonomous leasing decisions without a separate design and verification ticket.

AI 顾问层属于可选后续工作。建议先做只读、可引用证据、可解释的分析助手，并继续保留人工复核与最终决策边界。
