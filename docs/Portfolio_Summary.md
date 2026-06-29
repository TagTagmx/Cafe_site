# Cafe Site V2 Portfolio Summary / 项目摘要

## Project / 项目

Cafe Site V2 is an explainable retail site-selection analytics project built with MySQL 8.4, SQL feature engineering, Python/pandas scoring, and Streamlit review. It converts manually selected candidate sites and 高德 POI observations into a normalized, auditable site–POI evidence model.

Cafe Site V2 是一个可解释的零售选址分析项目。项目使用 MySQL 8.4 管理候选点、POI、采集证据和候选点–POI 关系，通过 SQL 生成基础特征，由 Python/pandas 完成评分与解释，并在 Streamlit 中进行人工复核。

## Business Question / 业务问题

Given a small set of plausible candidate sites in 徐州 and 南京, which locations deserve deeper fieldwork, rent validation, and operating review?

在一组人工筛选的徐州、南京候选点中，哪些点位更值得优先进行实地踏勘、租金核验和经营可行性复核？

The system prioritizes known candidate sites. It does not crawl an entire city, predict revenue, or make leasing decisions automatically.

## Portfolio Architecture / 作品集架构

```text
高德 POI evidence
-> deterministic migration
-> MySQL relational model
-> unique site–POI relationships
-> SQL feature views
-> pandas parity verification
-> Python scoring and explanations
-> Streamlit review
```

The central engineering decision is to separate auditable evidence from business transformations:

- MySQL stores normalized entities, foreign keys, observation provenance, resolved categories, and unique site–POI relationships.
- SQL aggregates cumulative raw features without embedding final scoring rules.
- Python owns interaction features, saturation logic, scenario scores, ranks, and bilingual explanations.
- Streamlit is the review layer rather than the system of record.

## Verified Result / 已验证结果

The completed full trial was loaded and verified on MySQL Community Server 8.4.10.

| Measure | Result |
| --- | ---: |
| Cities | 2 |
| Candidate sites | 15 |
| Canonical POIs | 6,866 |
| Expanded observations | 17,341 |
| Unique site–POI relationships | 8,661 |
| Named SQL checks | 15 PASS |
| SQL/pandas feature parity | Exact match |

Verification covered foreign keys, orphan references, city consistency, radius and distance constraints, distance bands, category resolution, relationship uniqueness, and every feature cell for all 15 sites.

完整试运行已在 MySQL 8.4.10 上通过验证：外键与语义完整性检查通过，15 项 SQL 检查全部为 `PASS`，MySQL 特征视图与 pandas 参考结果逐值一致。

## Feature And Scoring Story / 特征与评分

The relational feature layer exposes direct coffee, indirect support, office, commercial, residential, education, hotel, transit, total activity, and nearest-coffee evidence across cumulative distance bands.

The Python layer distinguishes signals that simple POI counts often conflate:

- Coffee validation can plateau while competition pressure continues rising.
- Indirect consumption support is gated by direct coffee validation.
- Transit only contributes through synergy with nearby demand.
- Low validation is uncertainty, not an automatic low-saturation bonus.
- Saturation risk is conditional on validated coffee demand and surrounding market activity.

Outputs remain inspectable through `site_feature_summary.csv`, `site_scores.csv`, and `site_explanations.csv`.

## What A Reviewer Should Notice / 评审应关注

- The many-to-many site–POI relationship is modeled explicitly.
- Repeated keyword and radius hits cannot inflate core feature counts.
- Category conflicts resolve deterministically before aggregation.
- SQL and Python responsibilities are deliberately separated.
- Cross-engine parity is tested rather than assumed.
- Scores and explanations are reproducible and challengeable.
- Limitations remain visible: no rent, frontage, lease, cost, or real performance data.

## Review Layer / 复核层

The V2 Streamlit app displays raw evidence, normalized components, interactions, scenario scores, bilingual explanations, and migration comparison fields. It helps a reviewer interrogate the model; it does not replace the database evidence or final business judgment.

```powershell
python -m streamlit run app/v2_review_app.py
```

## Background And Next Step / 背景与下一步

V2 is the portfolio version; an earlier pandas/CSV prototype remains only for historical and migration traceability.

A future read-only AI advisory layer could cite verified feature provenance and draft bilingual comparison notes. It is not part of the completed V2 scope.
