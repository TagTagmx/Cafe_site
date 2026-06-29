# Cafe Site V2 — MySQL POI Site Analytics

An explainable coffee-site decision-support project built around MySQL 8.4 relational modeling, deterministic POI migration, SQL feature views, Python scoring, and Streamlit review.

这是一个面向咖啡门店选址的可解释分析项目：使用 MySQL 8.4 建模候选点、POI、采集证据和候选点–POI 关系，通过 SQL 生成可审计特征，再由 Python 完成评分与双语解释，最后在 Streamlit 中复核。

## 10-Second Read / 10 秒了解项目

- **Business question:** Which candidate sites in 徐州 and 南京 deserve deeper field and lease review?
- **Core architecture:** MySQL relational evidence → SQL feature engineering → Python scoring → Streamlit review.
- **Data model:** 15 candidate sites, 6,866 canonical POIs, and 8,661 unique site–POI relationships.
- **Reliability:** deterministic migration, foreign-key checks, semantic-integrity checks, and exact SQL/pandas feature parity.
- **Output:** auditable feature, score, and explanation exports plus a V2 review dashboard.
- **Positioning:** decision support, not revenue prediction or an automatic leasing decision.

项目重点不是“做一个仪表盘”，而是建立一条可复现、可检查、可解释的选址分析链路。Streamlit 是结果复核层；MySQL 关系模型、迁移规则和特征验证才是 V2 的核心。

## Architecture / 技术架构

```text
Manual candidate sites + 高德 POI observations
                    |
                    v
       Deterministic Python preparation
                    |
                    v
 MySQL 8.4 relational evidence and constraints
                    |
                    v
 SQL base views over unique site–POI relationships
                    |
          +---------+---------+
          |                   |
          v                   v
 pandas parity check    Python scoring
                              |
                              v
                 CSV exports + Streamlit review
```

Responsibilities stay explicit:

- **MySQL / SQL:** normalized entities, observation evidence, deterministic relationships, category resolution, cumulative feature counts, and diagnostics.
- **Python / pandas:** migration orchestration, fixed-cap transformations, interaction features, final scores, ranks, explanations, and cross-engine parity verification.
- **Streamlit:** human review of evidence, interactions, scenarios, explanations, and comparison fields.

## Relational Data Model / 关系型数据模型

| Table | Purpose |
| --- | --- |
| `cities` | Stable city identifiers and display metadata |
| `candidate_sites` | Manually selected site hypotheses |
| `pois` | Canonical deduplicated POIs |
| `poi_keywords` | Search vocabulary and source buckets |
| `poi_category_rules` | Deterministic business classification rules |
| `poi_observations` | Auditable keyword/radius collection evidence |
| `site_poi_relationships` | One derived relationship per unique `(site_id, poi_clean_id)` pair |

The relationship layer prevents repeated keyword and radius hits from inflating features. Each relationship stores its resolved core and sub-category, while the original observation evidence remains traceable.

候选点和 POI 是多对多关系。V2 先保留原始采集证据，再按唯一 `(site_id, poi_clean_id)` 确定性生成关系层，避免同一 POI 因关键词或半径重复命中而被重复计分。

## Deterministic Migration / 确定性迁移

The full-trial loader:

1. Reads the existing 徐州 and 南京 processed evidence.
2. Builds canonical cities, sites, POIs, keywords, category rules, and expanded observations.
3. Loads all evidence into a dedicated MySQL database.
4. Derives unique site–POI relationships from observations.
5. Resolves category conflicts using documented priority rules.
6. Creates the SQL feature and diagnostic views.

Category priority is:

```text
direct_coffee
> indirect_competitor
> demand_anchor
> transit
> other / generic_commercial
```

This makes migration repeatable and prevents one POI from double-counting inside the same core feature.

## Verified MySQL 8.4 Result / MySQL 8.4 验证结果

The full 徐州/南京 trial was loaded and verified on MySQL Community Server 8.4.10.

| Entity | Verified rows |
| --- | ---: |
| Cities | 2 |
| Candidate sites | 15 |
| Canonical POIs | 6,866 |
| POI keywords | 19 |
| Category rules | 19 |
| Expanded observations | 17,341 |
| Unique site–POI relationships | 8,661 |

Verification passed:

- Foreign-key and orphan-reference checks.
- City/site consistency.
- Radius, distance, and distance-band constraints.
- Category-resolution and relationship-uniqueness checks.
- All 15 named SQL acceptance checks.
- Exact cell-level parity between MySQL `v_site_feature_counts` and the pandas reference output for all 15 sites.
- MySQL-backed scoring and all three analytical exports.

## Run The Verified Workflow / 运行已验证流程

Prerequisites:

- Python dependencies from `requirements.txt`.
- MySQL 8.0 or newer; the verified environment used MySQL Community Server 8.4.10.
- Local processed artifacts under `data/processed/`.
- A local `.env` based on `.env.example`:

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=cafe_site_v2
MYSQL_USER=your_local_user
MYSQL_PASSWORD=your_local_password
```

Validate prepared rows without changing MySQL:

```powershell
python src/load_v2_full_trial_mysql.py --validate-only
```

Create or reset the dedicated database and load the full trial:

```powershell
python src/load_v2_full_trial_mysql.py --create-database --reset
```

If the configured database already exists:

```powershell
python src/load_v2_full_trial_mysql.py --reset
```

Verify integrity and exact SQL/pandas feature parity:

```powershell
python src/verify_v2_full_trial_mysql.py
```

Run MySQL-backed scoring:

```powershell
python src/score_v2_sites.py --output-dir data/exports/v2/full_trial/mysql_scored
```

Open the V2 review layer:

```powershell
python -m streamlit run app/v2_review_app.py
```

The reset command targets the dedicated V2 schema. Read `docs/V2_T5_MySQL_Verification_Guide.md` before running it.

## Feature Engineering And Scoring / 特征工程与评分

SQL views aggregate unique relationships into cumulative 300m, 800m, and 1500m features for direct coffee, indirect support, office, commercial, residential, education, hotel, transit, total POI activity, and nearest direct-coffee distance.

Python then calculates:

- Demand-anchor components, with nearby evidence weighted more heavily.
- Coffee-demand validation that rises with moderate direct-coffee presence and then plateaus.
- Competition pressure that continues rising after validation plateaus.
- Indirect support gated by coffee validation.
- Transit-demand synergy, so transit alone cannot create an opportunity.
- Market activity, unvalidated-demand risk, and conditional saturation risk.
- Balanced and community-oriented scenario scores.
- Conservative bilingual explanation labels.

The balanced V2 score is:

```text
site_score =
    demand_anchor_score * 0.30
  + coffee_validation_score * 0.25
  + effective_indirect_support_score * 0.10
  + transit_demand_synergy_score * 0.10
  + market_activity_score * 0.10
  - saturation_risk_score * 0.15
```

Low competition is never added as an automatic bonus. Low validation is treated as uncertainty, not as evidence of low saturation.

## V2 Review Layer / V2 复核层

`app/v2_review_app.py` presents:

- Raw relational evidence and cumulative distance features.
- Normalized components and interaction features.
- Balanced and scenario scores.
- Bilingual explanation labels and site narratives.
- Legacy comparison fields for migration traceability.

The dashboard supports review; it does not hide or replace the underlying SQL and CSV evidence.

## Verification Commands / 验证命令

```powershell
python -m compileall app src
python -m unittest discover -s tests -v
python src/load_v2_full_trial_mysql.py --validate-only
python src/verify_v2_full_trial_mysql.py
```

Optional read-only SQL acceptance checks:

```powershell
mysql -u <user> -p <database> < sql/verify_v2_t5_full_trial.sql
```

Every named SQL result must be `PASS`.

## Project Structure

```text
app/v2_review_app.py                 V2 Streamlit review layer
data/sample/v2/                      Small committed verification fixtures
docs/                                Methodology, implementation, and runbooks
sql/schema.sql                       MySQL relational schema
sql/views.sql                        Base feature and diagnostic views
sql/verify_v2_t5_full_trial.sql      Read-only acceptance checks
src/load_v2_full_trial_mysql.py      Deterministic full-trial loader
src/prepare_v2_full_trial.py         Source preparation and relationship logic
src/verify_v2_full_trial_mysql.py    Integrity and SQL/pandas parity verifier
src/score_v2_sites.py                V2 interactions, scoring, and exports
tests/                               Deterministic fixture and scoring tests
```

## Limitations / 项目边界

- Candidate sites are manually selected hypotheses, not exhaustive city coverage.
- POI quality depends on 高德 coverage, keywords, geocoding, and representative candidate points.
- The model does not include rent, lease terms, frontage, visibility, store size, operating cost, or real store performance.
- Scores support within-city prioritization; they are not absolute cross-city investment rankings.
- Thresholds and scenario weights are explainable business assumptions, not statistically trained predictions.
- 南京仙林大学城 remains a sparse-evidence watchpoint requiring candidate-point or keyword review.

本项目不做全城自动找铺，不预测营收，也不替代实地踏勘、租金核验和最终租赁决策。

## Project Background

V2 supersedes an earlier pandas/CSV prototype, which remains in the repository for history and migration traceability.

## Optional Roadmap / 可选后续方向

A future read-only AI advisory layer could retrieve verified relational evidence, cite feature provenance, compare scenarios, and draft bilingual review notes. It should not change scores, mutate the database, or make autonomous leasing decisions without a separate design and verification ticket.
