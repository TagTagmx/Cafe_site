# Repo Current State

Last updated: 2026-06-22

## Project

`jiangsu-site-rank` is a portfolio project for China-local retail site-selection analytics. The MVP is intentionally narrow:

- First completed city: 徐州.
- Second scored validation city: 南京.
- First scenario: coffee shop site selection.
- Data source: 高德 Web 服务 API only.
- Candidate strategy: manually selected business hypotheses first, then API-based evaluation.
- Coordinate system: keep all coordinates in 高德 / GCJ-02.
- Chinese CSV compatibility: save Chinese CSV files as UTF-8 with BOM for Microsoft Excel on Windows.

## Workflow

Work is organized as small tickets in `docs/Tickets.md`.

Each ticket should be:

- Small enough to implement and manually verify.
- Scoped to the current 徐州 MVP unless explicitly expanded later.
- Clear about files touched, manual verification, and out-of-scope items.
- Implemented without jumping ahead to later pipeline steps.

Current pipeline order:

1. Define candidate sites manually.
2. Geocode candidate addresses with 高德.
3. Define POI keyword buckets.
4. Collect nearby POI snapshots around known candidate coordinates.
5. Clean and deduplicate POIs.
6. Aggregate site metrics.
7. Score sites with a simple explainable model.
8. Review results in a Streamlit dashboard.

## Completed Tickets

### T0001 - Project Setup

Status: Done

Created the minimal Python project structure, README, dependency list, `.env.example`, `.gitignore`, folders, and first methodology document.

### T0002 - Manual Candidate Sites

Status: Done

Created `data/manual/candidate_sites.csv` with 7 manually selected 徐州 coffee shop candidate areas. The file is saved as UTF-8 with BOM for Excel compatibility and intentionally does not include coordinates.

### T0003 - Amap Geocoding Client

Status: Done

Added a small 高德 geocoding client and candidate geocoding script. The script loads `AMAP_API_KEY`, reads manual candidate sites, and writes `data/processed/candidate_sites_geocoded.csv` with GCJ-02 `lng` / `lat` and geocode metadata when run with a valid key.

Execution result: geocoding was run successfully on 2026-06-22 and produced 7 successful candidate geocodes in `data/processed/candidate_sites_geocoded.csv`.

### T0004 - POI Keyword Buckets

Status: Done

Created `data/manual/poi_keywords.csv` with direct competitor, indirect competitor, demand anchor, and transit keyword buckets. The file is saved as UTF-8 with BOM for Excel compatibility. Methodology notes were updated to explain bucket usage.

### T0005 - Amap POI Snapshot Collector

Status: Done

Extended the 高德 client with nearby POI search and added `src/collect_poi_snapshots.py`. The collector reads geocoded candidate sites and POI keyword buckets, queries 300m, 800m, and 1500m radii, and writes timestamped raw snapshot CSV files under `data/raw`.

Execution result: POI collection was run successfully on 2026-06-22 and produced `data/raw/poi_snapshot_20260622_113619.csv` with 7,781 rows, 7 sites, radii `300,800,1500`, all four keyword buckets, and 0 error rows.

### T0006 - POI Deduplication and Cleaning

Status: Done

Added `src/clean_pois.py` to clean raw POI snapshots and deduplicate POIs by 高德 POI id, with a name/location fallback for rows without POI id. The cleaner preserves source candidate, radius, keyword, and bucket context in summary columns.

Execution result: cleaning was run successfully on 2026-06-22 and produced `data/processed/pois_cleaned.csv` with 2,288 cleaned POIs from 7,781 raw rows. It removed 5,493 duplicate source rows, deduplicated 2,288 POIs by POI id, and preserved 1,552 POIs with multiple source contexts.

### T0007 - Site Metrics Aggregation

Status: Done

Added `src/aggregate_site_metrics.py` to aggregate cleaned POI observations into one row per candidate site. The aggregation uses `data/processed/poi_observations_cleaned.csv` so site, radius, and bucket relationships remain exact.

Execution result: aggregation was run successfully on 2026-06-22 and produced `data/processed/site_metrics.csv` with 7 candidate rows. Metrics include total POI counts, direct competitor counts, indirect competitor counts, demand anchor counts, transit counts by radius, and nearest direct competitor distance.

### T0008 - Coffee Site Scoring v1

Status: Done

Added `src/score_sites.py` to calculate the first explainable coffee site score from `data/processed/site_metrics.csv`. The v1 score combines normalized demand, accessibility, commercial maturity, and subtractive competitor pressure components.

Execution result: scoring was run successfully on 2026-06-22 and produced `data/processed/site_scores.csv` with 7 ranked candidate sites. The top three ranked sites are 彭城广场商圈, 徐州苏宁广场, and 金鹰国际购物中心.

### T0009 - Streamlit Dashboard v1

Status: Done

Added `app/streamlit_app.py` to review the scored 徐州 coffee shop candidate sites. The dashboard shows ranked candidates, score components, key site metrics, selected-site detail, and concise methodology notes.

Run command:

```powershell
python -m streamlit run app/streamlit_app.py
```

### T0010 - Dashboard UX and Business Interpretation

Status: Done

Polished `app/streamlit_app.py` so the dashboard reads more like a business analytics portfolio page. Added a top-level 初步结论, horizontal score comparison chart, selected-site business interpretation, clearer component cards, and more readable methodology notes.

### T0011 - Scoring Logic v2 / Competition Calibration

Status: Done

Updated `src/score_sites.py` to replace subtractive competitor pressure with positive `competition_fit_score`. Competition fit scores highest when direct competitors are moderate, lower when competitors are too few or too many. The v2 `site_score` is clipped to 0-100 and the output keeps `v1_site_score`, `v1_site_rank`, and `rank_change_vs_v1`.

Execution result: scoring was rerun successfully on 2026-06-22 and produced bounded v2 scores in `data/processed/site_scores.csv`. The top three changed from 彭城广场商圈, 徐州苏宁广场, 金鹰国际购物中心 under v1 to 徐州苏宁广场, 金鹰国际购物中心, 彭城广场商圈 under v2.

### T0012 - Scoring Algorithm Review

Status: Done

Reviewed the v2 scoring model before adding 南京. Decision: freeze the current v2 formula for the first 南京 run, keep component weights unchanged, keep `competition_fit_score` as the positive competition component, and postpone calibration until 南京 has a first scoring output.

### T0013 - City Config Planning

Status: Done

Documented the minimal city-aware plan. Future city ids are `xuzhou` and `nanjing`. The recommended future layout uses city-specific candidate, raw, and processed folders, while keeping `poi_keywords.csv` shared for the first 南京 pass. Current 徐州 root-level files remain valid until city-aware code changes are explicitly implemented.

### T0014 - Nanjing Data Schema Preparation

Status: Done

Prepared the 南京 manual candidate schema. The approved path for the first 南京 candidate import is `data/manual/nanjing/candidate_sites.csv`. The schema remains compatible with 徐州: `site_id, city, district, area_name, address, business_type, reason_for_selection`. Manual input must not include coordinates, geocode metadata, POI metrics, or scores. The first 南京 run should reuse the shared `poi_keywords.csv`.

### T0015 - Nanjing First Data Import

Status: Done

Created `data/manual/nanjing/candidate_sites.csv` with 8 manually selected 南京 coffee shop candidate areas. The file uses the approved schema and does not include coordinates. It is ready for manual review before geocoding.

### T0016 - Nanjing First Scoring Run

Status: Done

Ran the existing pipeline for 南京 using the frozen v2 scoring model. The run geocoded all 8 南京 candidates, collected nearby POIs, cleaned and deduplicated observations, aggregated site metrics, and wrote first 南京 site scores.

Execution result: the 南京 pipeline was run successfully on 2026-06-22. It produced `data/raw/nanjing/poi_snapshot_20260622_174413.csv` with 9,713 raw POI rows across 8 sites, radii `300,800,1500`, and all four keyword buckets. Cleaning produced 4,578 cleaned POIs in `data/processed/nanjing/pois_cleaned.csv`. Aggregation produced 8 rows in `data/processed/nanjing/site_metrics.csv`, and scoring produced 8 ranked rows in `data/processed/nanjing/site_scores.csv`.

Current 南京 top three by `site_score` are 新街口商圈, 湖南路商圈, and 珠江路商圈.

### T0017 - Nanjing Streamlit Display

Status: Done

Updated `app/streamlit_app.py` so the dashboard can display both the existing 徐州 MVP results and the 南京 first scoring run. The default dashboard view remains 徐州. The sidebar city control exposes 南京 by loading `data/processed/nanjing/site_scores.csv` and `data/processed/nanjing/site_metrics.csv`.

### T0018 - Nanjing Sanity-Check Review

Status: Done

Manual gate decision: 南京 data makes sense for the first validation pass. The top ranked candidates, 新街口商圈, 湖南路商圈, and 珠江路商圈, are plausible dense commercial/office areas. The model also surfaces useful caution: 新街口 and 珠江路 have very strong demand/access/maturity signals but low competition-fit scores because direct competitor density is high.

Important correction: low `competition_fit_score` is not low competition. 新街口 has very high actual competitor pressure; the low fit score means the model is flagging over-saturation risk.

Watchpoint: 仙林大学城 scores unusually low because the selected geocoded campus point has sparse nearby POI signal. Treat this as a candidate-point or keyword-coverage issue to revisit later, not as a current scoring-formula blocker.

### T0019 - Nanjing Scoring Calibration

Status: Done

Calibration decision: no scoring change for this pass. The frozen v2 weights, positive `competition_fit_score`, and per-city normalization remain unchanged. The dashboard and docs now show actual `competitor_pressure_score` separately from `competition_fit_score`. 徐州 and 南京 score files were not regenerated because no formula or input data changed.

### T0020 - Multi-City Selector / City Switching

Status: Done

Promoted the dashboard control to a formal `城市` selector. The selector loads 徐州 from legacy root processed files and 南京 from `data/processed/nanjing`. Shared charts, ranking table, selected-site details, and methodology notes remain in one Streamlit app.

### T0021 - Final Portfolio Polish

Status: Done

Rewrote `README.md` as a portfolio-facing case study and added `docs/Portfolio_Summary.md`. The final narrative now explains the business problem, two-city workflow, current ranked outputs, dashboard usage, scoring interpretation, known limitations, and review checks.

Screenshots were not added because Playwright is not installed in the local Python environment. This is non-blocking; the Streamlit app is still available for manual review at `http://localhost:8501` when running locally.

Non-blocking data note: an extra ignored 南京 raw snapshot exists at `data/raw/nanjing/poi_snapshot_20260622_175042.csv`. The documented T0016 scoring run uses `data/raw/nanjing/poi_snapshot_20260622_174413.csv`.

### T0022 - Final Portfolio Polish / Reviewer Handoff

Status: Done

Polished reviewer-facing documentation only. `README.md` now opens with the project value in the first paragraph, adds a 10-second summary, includes exact example result/component values for 徐州 and 南京, clarifies shared versus city-specific two-city setup, preserves the 新街口 over-saturation interpretation, and keeps limitations visible. `docs/Portfolio_Summary.md` now mirrors the reviewer handoff with concise score examples.

No scoring logic, pipeline logic, Streamlit behavior, raw data, or processed data was changed. Screenshots were not added because Playwright is not installed and no new tooling was installed.

### DOC-ONLY - Bilingual Portfolio Documentation

Status: Done

Updated `README.md` and `docs/Portfolio_Summary.md` to be English-first bilingual documentation. The docs now include concise Chinese explanations under the major English sections while preserving commands, paths, variable names, scoring interpretation, and limitations. No app, scoring, pipeline, raw data, or processed data changes were made.

## Current Files Of Interest

- `data/manual/candidate_sites.csv`
- `data/manual/nanjing/candidate_sites.csv`
- `data/manual/poi_keywords.csv`
- `data/processed/candidate_sites_geocoded.csv`
- `data/processed/nanjing/candidate_sites_geocoded.csv`
- `data/processed/nanjing/pois_cleaned.csv`
- `data/processed/nanjing/poi_observations_cleaned.csv`
- `data/processed/nanjing/site_metrics.csv`
- `data/processed/nanjing/site_scores.csv`
- `data/processed/pois_cleaned.csv`
- `data/processed/poi_observations_cleaned.csv`
- `data/processed/site_metrics.csv`
- `data/processed/site_scores.csv`
- `data/raw/nanjing/poi_snapshot_20260622_174413.csv`
- `data/raw/poi_snapshot_20260622_113619.csv`
- `app/streamlit_app.py`
- `src/amap_client.py`
- `src/geocode_candidates.py`
- `src/collect_poi_snapshots.py`
- `src/clean_pois.py`
- `src/aggregate_site_metrics.py`
- `src/score_sites.py`
- `docs/Tickets.md`
- `docs/methodology.md`
- `docs/Portfolio_Summary.md`
- `README.md`

## Next Suggested Ticket

### Final Portfolio / Demo Review

T0001 through T0022 plus the bilingual documentation pass are complete for the 徐州 MVP, 南京 validation run, dashboard city switching, and portfolio narrative. The next step is manual portfolio/demo review.

Review should confirm:

- README explains the business problem, workflow, outputs, and limitations.
- README and `docs/Portfolio_Summary.md` are readable to both English and Chinese reviewers.
- Streamlit dashboard loads both 徐州 and 南京.
- The competition interpretation is clear: `competitor_pressure_score` is actual intensity, while `competition_fit_score` is a positive fit score.
- No secrets are exposed.
- The portfolio is ready to show or needs another polish pass.

Still out of scope unless explicitly added as new tickets:

- Add other cities.
- Generate AI reports.
- Add authentication, deployment, or database setup.
- Add portfolio polish pages.

## Multi-City Roadmap

The staged roadmap for expanding from 徐州 to 南京 is documented in `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`.

The roadmap keeps 南京 as a second-city validation rather than a rewrite. The planned sequence is:

1. T0012 - Scoring Algorithm Review - Done
2. T0013 - City Config Planning - Done
3. T0014 - Nanjing Data Schema Preparation - Done
4. T0015 - Nanjing First Data Import - Done
5. T0016 - Nanjing First Scoring Run - Done
6. T0017 - Nanjing Streamlit Display - Done
7. T0018 - Nanjing Sanity-Check Review - Done
8. T0019 - Nanjing Scoring Calibration - Done
9. T0020 - Multi-City Selector / City Switching - Done
10. T0021 - Final Portfolio Polish - Done
11. T0022 - Final Portfolio Polish / Reviewer Handoff - Done
12. DOC-ONLY - Bilingual Portfolio Documentation - Done

Manual verification guidance is documented in `docs/Manual_Verification_Guide.md`.
