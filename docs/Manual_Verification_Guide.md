# Manual Verification Guide

This guide lists manual checks for the current 徐州 MVP and the planned 南京 expansion. It is intentionally practical and should stay aligned with `docs/Tickets.md`.

## Current 徐州 MVP Checks

### Data Inputs

- Open `data/manual/candidate_sites.csv` in Microsoft Excel and confirm Chinese text displays correctly.
- Confirm candidate rows use the expected schema:
  `site_id, city, district, area_name, address, business_type, reason_for_selection`.
- Confirm no manual longitude or latitude fields are present in the original candidate file.
- Open `data/manual/poi_keywords.csv` and confirm bucket names cover direct competitors, indirect competitors, demand anchors, and transit.

### Geocoding

- Run `python src/geocode_candidates.py` only when `.env` contains a valid `AMAP_API_KEY`.
- Confirm `data/processed/candidate_sites_geocoded.csv` has one row per candidate.
- Confirm all successful rows have 高德 / GCJ-02 `lng` and `lat`.
- Spot-check several coordinates in 高德地图.

### POI Snapshot Collection

- Run `python src/collect_poi_snapshots.py` only after geocoding succeeds.
- Confirm a timestamped `data/raw/poi_snapshot_*.csv` is created.
- Confirm rows include candidate id, radius, keyword, bucket, POI id, name, address, location, and distance where available.
- Confirm no unexpected city-wide crawl was performed.

### Cleaning And Metrics

- Run `python src/clean_pois.py`.
- Confirm `data/processed/pois_cleaned.csv` and `data/processed/poi_observations_cleaned.csv` exist.
- Confirm duplicate raw rows are reduced in the cleaned POI file.
- Run `python src/aggregate_site_metrics.py`.
- Confirm `data/processed/site_metrics.csv` has one row per candidate site.

### Scoring And Dashboard

- Run `python src/score_sites.py`.
- Confirm `data/processed/site_scores.csv` has one row per candidate.
- Confirm v2 `site_score` is in the 0-100 range.
- Confirm `competition_fit_score` is present and positive.
- Run `python -m streamlit run app/streamlit_app.py`.
- Confirm the dashboard loads at `http://localhost:8501`.
- Confirm the dashboard shows ranking, score components, selected-site interpretation, and methodology notes.

## 南京 Expansion Checks

### Before Data Import

- Confirm T0012 scoring assumptions are documented.
- Confirm T0013 city path/config plan is documented.
- Confirm 南京 candidate schema matches 徐州 candidate schema.
- Confirm planned 南京 candidate path is `data/manual/nanjing/candidate_sites.csv`.
- Confirm planned schema is exactly:
  `site_id, city, district, area_name, address, business_type, reason_for_selection`.
- Confirm `lng`, `lat`, `geocode_*`, POI count, and score columns are not part of the manual input schema.
- Confirm the first 南京 run will reuse the shared `poi_keywords.csv`.

### 南京 First Data Import

- Open the 南京 candidate CSV in Excel and confirm Chinese text displays correctly.
- Confirm coordinates are not manually added.
- Confirm candidate sites are manually selected business hypotheses, not city-wide crawls.
- Confirm `site_id` values use a stable prefix such as `NJ_COFFEE_001`.
- Confirm `business_type` is `coffee_shop`.
- Confirm candidate count stays small enough for manual review, recommended 7-10 rows.
- Current T0015 file to review: `data/manual/nanjing/candidate_sites.csv`.

### 南京 Pipeline Run

- Confirm geocoding success rate is acceptable.
- Confirm raw POI snapshots are timestamped and scoped to candidate coordinates.
- Confirm cleaned POI outputs preserve source keyword, bucket, radius, and candidate context.
- Confirm site metrics have one row per 南京 candidate.
- Confirm v2 scores are bounded 0-100.
- Current T0016 geocoded file: `data/processed/nanjing/candidate_sites_geocoded.csv`.
- Current T0016 raw snapshot: `data/raw/nanjing/poi_snapshot_20260622_174413.csv`.
- Current T0016 cleaned files: `data/processed/nanjing/pois_cleaned.csv` and `data/processed/nanjing/poi_observations_cleaned.csv`.
- Current T0016 scoring files: `data/processed/nanjing/site_metrics.csv` and `data/processed/nanjing/site_scores.csv`.
- Current T0016 top three by `site_score`: 新街口商圈, 湖南路商圈, 珠江路商圈.

### 南京 Dashboard Review

- Run `python -m streamlit run app/streamlit_app.py`.
- Confirm the default city selector value is `徐州`.
- Switch the sidebar city selector to `南京`.
- Confirm 南京 results can be viewed without breaking 徐州.
- Confirm top-ranked 南京 candidates pass basic business judgment.
- Spot-check selected POIs and coordinates in 高德地图.
- Confirm the no-calibration decision remains acceptable after reviewing the city selector output.

### 南京 Sanity And Calibration Decision

- Current manual decision: 南京 data makes sense for the first validation pass.
- Current calibration decision: keep frozen v2 scoring unchanged.
- Interpretation correction: 新街口 has high actual competition pressure. A low `competition_fit_score` means over-saturation risk, not low competition.
- Watchpoint for later: 仙林大学城 may need a better representative candidate point or keyword review because the current geocoded campus point has sparse POI signal.

## Common Failure Modes

- Chinese CSV opens as mojibake: ensure UTF-8 with BOM.
- Candidate rows missing after geocoding: inspect API status and formatted address.
- POI counts look too high: check duplicate raw snapshots and radius/keyword combinations.
- Scores look counterintuitive: review demand, transit, commercial maturity, and competition fit separately before changing weights.
- Dashboard errors on missing columns: verify `site_scores.csv` preserves `site_metrics.csv` columns.

## Final Portfolio Review

- Read `README.md` and confirm the project is understandable without reading the full ticket log.
- Confirm the opening paragraph communicates the pipeline, 高德 API collection, feature engineering, explainable scoring, Streamlit dashboard, and business interpretation.
- Confirm the 10-second summary is clear for a GitHub/recruiter reviewer.
- Confirm the README example result table includes both 徐州 and 南京 with score/component values.
- Confirm the README explains shared versus city-specific setup without inventing unsupported commands.
- Read `docs/Portfolio_Summary.md` and confirm it is accurate enough for a quick reviewer handoff.
- Run `python -m streamlit run app/streamlit_app.py`.
- Confirm the dashboard opens at `http://localhost:8501`.
- Confirm the `城市` selector loads both 徐州 and 南京.
- Confirm 新街口 is interpreted as high actual competition pressure with over-saturation risk, not low competition.
- Confirm known limitations remain visible, especially missing rent, lease, frontage, visibility, and operating-cost data.
- Confirm the 南京仙林大学城 sparse-POI watchpoint remains visible.
- Confirm `.env` is not shared or committed.
- Optional: add screenshots manually if needed for a portfolio page or external presentation.
