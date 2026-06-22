# Portfolio Summary

## Project

`jiangsu-site-rank` is a China-local retail site-selection analytics case study. It evaluates coffee shop candidate areas in 徐州 and 南京 using manually selected business hypotheses, 高德 Web 服务 API geocoding, nearby POI snapshots, feature engineering, explainable scoring, and a Streamlit dashboard with business interpretation.

## Business Question

Given a small set of plausible candidate areas, which sites deserve deeper manual review for coffee shop expansion?

The project does not try to identify every possible location in a city. It ranks known candidate areas so a business user can prioritize field visits, rent checks, and operating feasibility review.

## Current Outputs

- 徐州 MVP: 7 candidate areas scored and displayed in the dashboard.
- 南京 validation run: 8 candidate areas scored using the frozen v2 model.
- Dashboard: one Streamlit app with a sidebar `城市` selector for 徐州 and 南京.

Current top candidates:

| City | Rank | Candidate | Score | Note |
| --- | ---: | --- | ---: | --- |
| 徐州 | 1 | 徐州苏宁广场 | 86.89 | Strong demand/access/maturity, high competition pressure |
| 徐州 | 2 | 金鹰国际购物中心 | 86.57 | Similar top-tier commercial profile |
| 徐州 | 3 | 彭城广场商圈 | 86.56 | Highest maturity/demand, very crowded |
| 南京 | 1 | 新街口商圈 | 84.86 | High overall score, clear over-saturation risk |
| 南京 | 2 | 湖南路商圈 | 84.08 | Strong score with more moderate competition fit |
| 南京 | 3 | 珠江路商圈 | 78.27 | Strong demand, high competition pressure |

## Model Interpretation

The v2 score combines demand, accessibility, commercial maturity, and competition fit. Competition fit is a positive scoring component, not raw competition level.

For example, 南京新街口 has very high actual competition pressure. Its low `competition_fit_score` means the area may be over-saturated, not that competition is weak.

## Reviewer First Impression

The README is designed to communicate the project in roughly 10 seconds: data pipeline, 高德 API collection, feature engineering, explainable scoring, dashboard, two-city validation, and explicit limitations.

## Review Status

南京 sanity check passed for a first validation run. No scoring recalibration was applied after the first 南京 review. Known watchpoints remain documented, especially the sparse POI signal around the current 仙林大学城 candidate point.

## What A Reviewer Should Notice

- The workflow is reproducible and inspectable.
- Generated raw and processed data are separated from manual inputs.
- The score is transparent enough to challenge.
- Limitations are visible rather than hidden.
- The dashboard supports comparison within each city, not absolute cross-city investment ranking.
