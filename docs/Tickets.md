# jiangsu-site-rank Tickets

This roadmap keeps the MVP small and centered on 徐州 coffee shop site selection. Manually selected candidate sites come first; 高德 Web 服务 API data is used to evaluate those sites, not to crawl entire cities.

Project principles:

- Start small.
- Use manually selected candidate sites first.
- Use 高德 API to evaluate selected sites only.
- Keep all coordinates in 高德 / GCJ-02.
- Save Chinese CSV files as UTF-8 with BOM for Microsoft Excel compatibility.
- Keep each ticket small enough to implement and verify manually.
- Do not add 南京 yet.
- Do not overbuild AI reports, automation, or multi-city comparison before the 徐州 pipeline and dashboard work.

Current expansion planning:

- 徐州 MVP is complete through T0011.
- 南京 is the next city, but it should be treated as a second-city validation of the existing BI workflow.
- Detailed staged roadmap: `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`.
- Manual checks: `docs/Manual_Verification_Guide.md`.

## T0001 - Project Setup

Status: Done

### Goal

Create a clean minimal Python project structure for the site-selection MVP.

### Scope

- Create the base repository structure.
- Add project README.
- Add Python dependency list.
- Add environment variable example file.
- Add ignored local/generated paths.
- Add first methodology document.

### Files Likely Touched

- `README.md`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `docs/methodology.md`
- `data/manual/`
- `data/raw/`
- `data/processed/`
- `src/`
- `app/`
- `docs/`
- `notebooks/`
- `sql/`

### Manual Verification

- Confirm all expected folders exist.
- Confirm README explains the project goal, MVP scope, and planned pipeline.
- Confirm `.env.example` includes `AMAP_API_KEY`.
- Confirm generated data folders are ignored.

### Out Of Scope

- 高德 API calls.
- Candidate site data.
- POI collection.
- Dashboard code.

## T0002 - Manual Candidate Sites

Status: Done

### Goal

Create the first manually selected 徐州 coffee shop candidate site dataset.

### Scope

- Create `data/manual/candidate_sites.csv`.
- Include 7 candidate areas in 徐州.
- Use address-only records without longitude or latitude.
- Save Chinese CSV content as UTF-8 with BOM for Excel compatibility.
- Treat each candidate as a business hypothesis to evaluate later.

### Files Likely Touched

- `data/manual/candidate_sites.csv`
- `README.md`

### Manual Verification

- Open the CSV in Microsoft Excel on Windows and confirm Chinese text displays correctly.
- Confirm the schema is exactly:
  `site_id, city, district, area_name, address, business_type, reason_for_selection`.
- Confirm there are 7 徐州 candidate records.
- Confirm no `lng` or `lat` columns exist.

### Out Of Scope

- 高德 geocoding.
- POI collection.
- Scoring.
- 南京 or other city data.

## T0003 - Amap Geocoding Client

Status: Done

### Goal

Geocode manually selected candidate addresses using 高德 Web 服务 API.

### Scope

- Load `AMAP_API_KEY` from `.env`.
- Read `data/manual/candidate_sites.csv`.
- Geocode each candidate address.
- Preserve all coordinates in 高德 / GCJ-02.
- Save `data/processed/candidate_sites_geocoded.csv`.
- Include `lng`, `lat`, and useful geocode metadata such as formatted address, geocode level, API status, and raw match count.

### Files Likely Touched

- `src/amap_client.py`
- `src/geocode_candidates.py`
- `data/processed/candidate_sites_geocoded.csv`
- `README.md`

### Manual Verification

- Confirm the script fails clearly if `AMAP_API_KEY` is missing.
- Run the geocoding script with a valid key.
- Confirm output has one row per input candidate.
- Confirm `lng` and `lat` are populated for successful geocodes.
- Spot-check several coordinates in 高德地图.
- Confirm the output CSV opens correctly in Excel if it contains Chinese text.

### Out Of Scope

- POI collection.
- Coordinate conversion to WGS-84 or BD-09.
- Automatic city-wide search.
- Scoring or dashboard work.

## T0004 - POI Keyword Buckets

Status: Done

### Goal

Define the first set of POI keyword buckets used to evaluate coffee shop candidate areas.

### Scope

- Create `data/manual/poi_keywords.csv`.
- Include buckets for direct competitors, indirect competitors, demand anchors, and transit keywords.
- Keep keywords specific enough for 高德 nearby POI search.
- Save Chinese CSV content as UTF-8 with BOM for Excel compatibility.

### Files Likely Touched

- `data/manual/poi_keywords.csv`
- `docs/methodology.md`

### Manual Verification

- Confirm the CSV opens correctly in Microsoft Excel on Windows.
- Confirm each keyword has a bucket and description.
- Confirm buckets cover direct competition, indirect competition, demand anchors, and transit.
- Confirm the file avoids large city-crawling categories that are too broad for the MVP.

### Out Of Scope

- Calling 高德 API.
- Tuning weights.
- POI deduplication.
- Multi-city keyword strategy.

## T0005 - Amap POI Snapshot Collector

Status: Done

### Goal

Collect nearby POI snapshots around each geocoded candidate site using selected keyword buckets.

### Scope

- Read geocoded candidate sites.
- Read POI keyword buckets.
- Query 高德 nearby POI search around each candidate.
- Use 300m, 800m, and 1500m radii.
- Save timestamped raw snapshot CSV files in `data/raw`.
- Preserve source candidate, radius, keyword, and bucket metadata.

### Files Likely Touched

- `src/amap_client.py`
- `src/collect_poi_snapshots.py`
- `data/raw/poi_snapshot_*.csv`
- `README.md`

### Manual Verification

- Run the collector for the 7 徐州 candidates.
- Confirm raw output includes candidate id, radius, keyword, bucket, POI id, name, type, address, location, and distance where available.
- Confirm output is timestamped.
- Confirm row counts are plausible for the selected radii and keywords.
- Spot-check several POIs in 高德地图.

### Out Of Scope

- Deduplicated POI tables.
- Scoring.
- Dashboard visualization.
- Crawling all 徐州 POIs.

## T0006 - POI Deduplication and Cleaning

Status: Done

### Goal

Clean and deduplicate raw POI snapshot results while preserving source search context.

### Scope

- Read timestamped raw POI snapshots.
- Normalize key fields such as name, POI id, location, type, radius, keyword, and bucket.
- Deduplicate by POI id where available.
- Fall back to name and location matching where POI id is missing.
- Preserve source keyword, bucket, candidate, and radius metadata.
- Save cleaned POI data in `data/processed`.

### Files Likely Touched

- `src/clean_pois.py`
- `data/processed/pois_cleaned.csv`
- `docs/methodology.md`

### Manual Verification

- Confirm duplicate POIs from overlapping keywords or radii are handled.
- Confirm cleaned output retains enough metadata to explain why each POI was collected.
- Compare raw and cleaned row counts.
- Spot-check duplicate examples manually.

### Out Of Scope

- Site-level aggregation.
- Scoring.
- Dashboard work.
- Advanced fuzzy matching beyond the MVP need.

## T0007 - Site Metrics Aggregation

Status: Done

### Goal

Aggregate cleaned POI data into one metrics row per candidate site.

### Scope

- Read geocoded candidate sites.
- Read cleaned POI data.
- Create one row per candidate site.
- Aggregate direct competitor counts by radius.
- Aggregate indirect competitor counts by radius.
- Aggregate demand anchor counts by radius.
- Aggregate transit counts by radius.
- Calculate nearest competitor distance where possible.
- Save aggregated metrics in `data/processed`.

### Files Likely Touched

- `src/aggregate_site_metrics.py`
- `data/processed/site_metrics.csv`
- `docs/methodology.md`

### Manual Verification

- Confirm there is one metrics row per candidate site.
- Confirm count columns are non-negative and use clear names.
- Confirm direct competitor, demand anchor, and transit counts can be traced back to cleaned POIs.
- Manually inspect the nearest competitor for at least two candidates.

### Out Of Scope

- Weighted scoring.
- Machine learning.
- Dashboard work.
- Rent, lease, or store-front data.

## T0008 - Coffee Site Scoring v1

Status: Done

### Goal

Create a simple explainable scoring model for 徐州 coffee shop site selection.

### Scope

- Read `data/processed/site_metrics.csv`.
- Normalize selected metrics across candidate sites.
- Create demand, accessibility, commercial maturity, and competitor pressure components.
- Calculate a weighted `site_score`.
- Save scored candidates in `data/processed`.
- Document the scoring assumptions.

### Files Likely Touched

- `src/score_sites.py`
- `data/processed/site_scores.csv`
- `docs/methodology.md`

### Manual Verification

- Confirm every candidate receives a score.
- Confirm score components are visible and explainable.
- Confirm competitor pressure reduces the score rather than increasing it.
- Confirm the ranked output is plausible after manual review.

### Out Of Scope

- Machine learning.
- AI-generated investment memos.
- Multi-city comparison.
- Automatic score optimization.

## T0009 - Streamlit Dashboard v1

Status: Done

### Goal

Build the first lightweight dashboard for reviewing ranked 徐州 coffee shop candidate sites.

### Scope

- Load scored candidate data.
- Show ranked candidate sites.
- Show score breakdown by component.
- Show competitor counts, demand anchor counts, transit counts, and nearest competitor distance.
- Include concise methodology notes.
- Keep the dashboard focused on manual review of the MVP outputs.

### Files Likely Touched

- `app/streamlit_app.py`
- `data/processed/site_scores.csv`
- `docs/methodology.md`
- `README.md`

### Manual Verification

- Run the Streamlit app locally.
- Confirm all 7 candidates appear.
- Confirm ranking matches `site_scores.csv`.
- Confirm score components and key metrics are visible.
- Confirm methodology notes explain that the score is decision support, not a final site decision.

### Out Of Scope

- 南京 or other cities.
- AI report generation.
- Portfolio polish pages.
- Authentication, deployment, or database setup.

## T0010 - Dashboard UX and Business Interpretation

Status: Done

### Goal

Polish the 徐州 MVP dashboard so it reads more like a business analytics portfolio page.

### Scope

- Improve dashboard layout.
- Add top-level 初步结论.
- Add selected-site interpretation text.
- Make Chinese candidate names readable in charts.
- Improve methodology note readability.

### Files Likely Touched

- `app/streamlit_app.py`

### Manual Verification

- Run the Streamlit app locally.
- Confirm the dashboard opens.
- Confirm selected-site business interpretation appears.

### Out Of Scope

- Scoring logic changes.
- 高德 API calls.
- 南京 or other cities.

## T0011 - Scoring Logic v2 / Competition Calibration

Status: Done

### Goal

Replace subtractive competitor pressure with a positive competition fit score.

### Scope

- Score competition highest when direct competitors are moderate.
- Score lower when direct competitors are too few or too many.
- Keep final score in a clear 0-100 range.
- Preserve v1 score and rank comparison columns.
- Update dashboard and methodology labels.

### Files Likely Touched

- `src/score_sites.py`
- `data/processed/site_scores.csv`
- `app/streamlit_app.py`
- `docs/methodology.md`
- `README.md`

### Manual Verification

- Run the scoring script.
- Run `python -m compileall app src`.
- Run Streamlit and confirm the dashboard loads.
- Confirm all score components are positive and easy to interpret.

### Out Of Scope

- 高德 API calls.
- POI recollection.
- 南京 or other cities.
- Machine learning.

## T0012 - Scoring Algorithm Review

Status: Done

### Goal

Review v2 scoring assumptions before applying the model to 南京.

### Scope

- Review current component weights.
- Review competition fit target and tolerance.
- Decide whether to freeze v2 for 南京 first run.
- Document calibration questions.

### Files Likely Touched

- `docs/methodology.md`
- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`

### Manual Verification

- Confirm 徐州 v2 scores remain reproducible.
- Confirm the scoring decision is documented before 南京 import.

### Risks / Assumptions

- Current competition fit target may be too 徐州-specific.
- Changing weights before 南京 may make second-city validation less meaningful.

### Expected Output

- A short scoring review and freeze/calibration decision.

### Decision

- Freeze current v2 scoring for the first 南京 run.
- Keep component weights unchanged.
- Keep `competition_fit_score` positive and documented.
- Revisit calibration only after 南京 first scoring output exists.

## T0013 - City Config Planning

Status: Done

### Goal

Define the smallest city-aware structure needed to support 徐州 and 南京.

### Scope

- Decide city ids and path conventions.
- Plan whether to use folder partitioning, config, or both.
- Preserve current 徐州 outputs.

### Files Likely Touched

- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`
- `docs/methodology.md`

### Manual Verification

- Confirm current 徐州 files still map cleanly to the proposed structure.
- Confirm 南京 can be added without a rewrite.

### Risks / Assumptions

- Too much abstraction would slow the MVP.
- Too little structure could make city switching brittle.

### Expected Output

- Documented city config and path strategy.

### Decision

- Use city ids `xuzhou` and `nanjing`.
- Plan light folder partitioning under `data/manual`, `data/raw`, and `data/processed`.
- Keep `poi_keywords.csv` shared for the first 南京 pass.
- Preserve current 徐州 root-level files until code changes are explicitly approved.

## T0014 - Nanjing Data Schema Preparation

Status: Done

### Goal

Prepare 南京 input schemas before adding data.

### Scope

- Define 南京 candidate CSV schema.
- Confirm schema compatibility with 徐州.
- Decide whether 南京 uses the existing POI keyword file.

### Files Likely Touched

- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`
- `docs/Manual_Verification_Guide.md`

### Manual Verification

- Compare 南京 planned schema with 徐州 candidate schema.
- Confirm Chinese CSV UTF-8 BOM requirement is documented.

### Risks / Assumptions

- 南京 may need richer notes later, but first schema should stay compatible.

### Expected Output

- A schema checklist for 南京 candidate import.

### Decision

- 南京 candidate path for T0015: `data/manual/nanjing/candidate_sites.csv`.
- Schema must remain:
  `site_id, city, district, area_name, address, business_type, reason_for_selection`.
- Manual input must not include `lng`, `lat`, geocode fields, POI metrics, or score fields.
- Reuse shared `poi_keywords.csv` for the first 南京 pass.
- Save Chinese CSV as UTF-8 with BOM.

## T0015 - Nanjing First Data Import

Status: Done

### Goal

Add first manually selected 南京 cafe candidate sites.

### Scope

- Create 南京 candidate data using the approved schema.
- Keep sites as manual business hypotheses.
- Do not call 高德 in this ticket.

### Files Likely Touched

- Future 南京 candidate CSV path from T0013.
- `README.md`
- `docs/Manual_Verification_Guide.md`

### Manual Verification

- Open the CSV in Excel and confirm Chinese text displays correctly.
- Confirm no `lng` or `lat` columns are manually added.

### Risks / Assumptions

- Poor candidate hypotheses weaken second-city validation.

### Expected Output

- 南京 candidate CSV ready for geocoding.

### Result

- Created `data/manual/nanjing/candidate_sites.csv`.
- Added 8 manually selected 南京 coffee shop candidate areas.
- Kept the approved T0014 schema.
- Did not add coordinates or call 高德.

## T0016 - Nanjing First Scoring Run

Status: Done

### Goal

Run the existing pipeline for 南京 after candidate data is ready.

### Scope

- Geocode 南京 candidates.
- Collect nearby POI snapshots around candidate coordinates.
- Clean and deduplicate POIs.
- Aggregate metrics.
- Score with the frozen v2 model.

### Files Likely Touched

- Future 南京 raw and processed outputs.
- Path/config wiring files if approved in T0013.

### Manual Verification

- Confirm geocoding success rate.
- Confirm raw, cleaned, aggregated, and scored outputs are created.
- Confirm scores are bounded 0-100.

### Risks / Assumptions

- 高德 quota or 南京 density may expose pagination assumptions.

### Expected Output

- First 南京 scored candidate output.

### Result

- Geocoded 8 南京 candidates successfully.
- Collected `data/raw/nanjing/poi_snapshot_20260622_174413.csv` with 9,713 raw POI rows across 8 sites, radii `300,800,1500`, and all four keyword buckets.
- Cleaned the raw snapshot into `data/processed/nanjing/pois_cleaned.csv` with 4,578 cleaned POIs and `data/processed/nanjing/poi_observations_cleaned.csv`.
- Aggregated `data/processed/nanjing/site_metrics.csv` with 8 candidate rows.
- Scored `data/processed/nanjing/site_scores.csv` with the frozen v2 model. Scores are bounded 0-100.
- Current 南京 top three: 新街口商圈, 湖南路商圈, 珠江路商圈.

## T0017 - Nanjing Streamlit Display

Status: Done

### Goal

Display 南京 scoring results without breaking 徐州.

### Scope

- Add a simple 南京 view.
- Keep dashboard layout consistent.
- Avoid final city selector until T0020.

### Files Likely Touched

- `app/streamlit_app.py`
- City config/path docs.

### Manual Verification

- Confirm 徐州 still loads.
- Confirm 南京 view loads.

### Risks / Assumptions

- Hardcoding a second view could create cleanup work later.

### Expected Output

- Dashboard view for 南京 first run.

### Result

- Added a simple temporary dashboard result view control in `app/streamlit_app.py`.
- Preserved the existing 徐州 MVP score and metrics paths as the default view.
- Added a 南京 first-run view that loads `data/processed/nanjing/site_scores.csv` and `data/processed/nanjing/site_metrics.csv`.
- Kept full multi-city switching out of scope until T0020.

## T0018 - Nanjing Sanity-Check Review

Status: Done

### Goal

Review 南京 outputs before recalibration.

### Scope

- Compare top-ranked 南京 sites against business judgment.
- Inspect demand, transit, and competitor metrics.
- Decide whether reruns or calibration are needed.

### Files Likely Touched

- `docs/Manual_Verification_Guide.md`
- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`

### Manual Verification

- Spot-check coordinates and POIs in 高德地图.
- Review top and bottom ranked candidates.

### Risks / Assumptions

- Bad candidate hypotheses may look like scoring issues.

### Expected Output

- Sanity-check note and calibration decision.

### Result

- Manual gate decision: 南京 data makes sense for the first validation pass.
- Top-ranked sites are plausible for business review: 新街口商圈, 湖南路商圈, 珠江路商圈.
- The ranking reflects dense CBD demand/access/maturity signals while still showing saturation pressure through lower competition-fit scores.
- Manual correction: 新街口 must not be interpreted as low competition. It has very high actual competitor pressure; its `competition_fit_score` is low only because the model treats over-saturation as a risk.
- Watchpoint: 仙林大学城 scores unusually low because the selected geocoded campus point has sparse nearby POI signal; treat this as a candidate-point/keyword coverage issue to revisit later, not a reason to recalibrate now.
- Decision: proceed without rerunning the 南京 pipeline and without changing v2 scoring before T0019.

## T0019 - Nanjing Scoring Calibration

Status: Done

### Goal

Adjust scoring only if 南京 validation shows a clear need.

### Scope

- Review whether competition fit should be global or city-specific.
- Review per-city normalization assumptions.
- Keep changes small and documented.

### Files Likely Touched

- `src/score_sites.py`
- `docs/methodology.md`
- `docs/Repo_Current_State.md`

### Manual Verification

- Re-run 徐州 and 南京 scores.
- Compare rank changes.
- Confirm scores remain 0-100.

### Risks / Assumptions

- Overfitting to 南京 could reduce portability.

### Expected Output

- Documented calibration decision and updated scores if needed.

### Result

- Calibration decision: no scoring change for this pass.
- Kept the frozen v2 weights and positive `competition_fit_score` unchanged.
- Clarified dashboard and docs so actual `competitor_pressure_score` is visible separately from `competition_fit_score`.
- Kept per-city normalization unchanged for local ranking.
- Did not regenerate 徐州 or 南京 score files because no formula or input data changed.
- Deferred any future calibration to a later ticket if more cities, stronger ground truth, rent data, or field review evidence show a clear need.

## T0020 - Multi-City Selector / City Switching

Status: Done

### Goal

Add a simple dashboard control to switch between 徐州 and 南京.

### Scope

- Add city selector.
- Load city-specific score files.
- Avoid database setup.

### Files Likely Touched

- `app/streamlit_app.py`
- City config file if created.
- `README.md`

### Manual Verification

- Confirm both cities load.
- Confirm switching does not mix metrics.

### Risks / Assumptions

- Current single-city paths need careful migration.

### Expected Output

- One dashboard that can switch between 徐州 and 南京.

### Result

- Promoted the temporary dashboard result view into a formal `城市` selector.
- The selector loads 徐州 from the legacy root processed files and 南京 from `data/processed/nanjing`.
- Kept the shared dashboard layout, charts, ranking table, single-site detail, and methodology notes.
- Avoided database setup and broader path migration.

## T0021 - Final Portfolio Polish

Status: Done

### Goal

Package the project as a clear analytics portfolio case study.

### Scope

- Improve README narrative.
- Add screenshots if available.
- Add final project summary.
- Keep known limitations visible.

### Files Likely Touched

- `README.md`
- `docs/Repo_Current_State.md`
- `docs/Manual_Verification_Guide.md`

### Manual Verification

- Confirm a reader can understand the business problem, data flow, and outputs.
- Confirm no `.env` content or secrets are exposed.

### Risks / Assumptions

- Polish should not hide model limitations.

### Expected Output

- Portfolio-ready repo narrative after 南京 validation.

### Result

- Rewrote `README.md` as a portfolio-facing case study with business framing, current outputs, dashboard usage, pipeline steps, scoring interpretation, and limitations.
- Added `docs/Portfolio_Summary.md` as a concise final project summary for reviewers.
- Kept the over-saturation interpretation explicit: low `competition_fit_score` does not mean low competition.
- Confirmed `.env`, `data/raw`, and `data/processed` are ignored by git.
- Screenshot note: screenshots were not added because Playwright is not installed in the local Python environment.
- Non-blocking issue logged: an extra ignored 南京 raw snapshot exists at `data/raw/nanjing/poi_snapshot_20260622_175042.csv`; the documented T0016 scoring run uses `data/raw/nanjing/poi_snapshot_20260622_174413.csv`.

## T0022 - Final Portfolio Polish / Reviewer Handoff

Status: Done

### Goal

Make the project more immediately impressive and understandable for a GitHub or recruiter reviewer in the first 10 seconds.

### Scope

- Documentation and portfolio polish only.
- Do not change scoring logic.
- Do not change data pipeline logic.
- Do not change Streamlit app behavior unless a tiny text-only copy fix is clearly necessary.
- Do not commit generated raw or processed CSV files.
- Keep `.env`, `data/raw/`, and `data/processed/` ignored.

### Files Touched

- `README.md`
- `docs/Portfolio_Summary.md`
- `docs/Tickets.md`
- `docs/Repo_Current_State.md`
- `docs/Manual_Verification_Guide.md`

### Result

- Strengthened the README opening around data pipeline, 高德 API collection, feature engineering, explainable scoring, Streamlit dashboard, and business interpretation.
- Added a 10-second reviewer summary.
- Added a compact example result table with exact top-three score/component values for 徐州 and 南京 from local processed outputs.
- Clarified the two-city setup: shared keyword/scripts/dashboard pieces versus city-specific candidate and processed-output paths.
- Preserved the 新街口 interpretation: high actual competition pressure can coexist with a low `competition_fit_score` due to over-saturation risk.
- Kept limitations visible, including missing rent/lease/frontage/visibility/store-size/cost data and the 南京仙林大学城 sparse-POI watchpoint.
- Did not add screenshots because Playwright is not installed and this ticket avoids installing new tooling.

### Verification

- `python -m compileall app src`
- Streamlit localhost check.
- `.gitignore` check for `.env`, `data/raw/`, and `data/processed/`.

## DOC-ONLY - Bilingual Portfolio Documentation

Status: Done

### Goal

Make the GitHub-facing documentation bilingual so both English and Chinese reviewers can quickly understand the project.

### Scope

- Documentation only.
- Do not change app code, scoring code, data pipeline code, generated datasets, or Streamlit behavior.
- Do not commit `.env`, `data/raw/`, or `data/processed/`.
- Do not rewrite technical meaning or scoring interpretation.

### Files Touched

- `README.md`
- `docs/Portfolio_Summary.md`
- `docs/Tickets.md`
- `docs/Repo_Current_State.md`
- `docs/Manual_Verification_Guide.md`

### Result

- Reworked `README.md` as English-first bilingual documentation with concise Chinese explanations under major sections.
- Reworked `docs/Portfolio_Summary.md` as a bilingual reviewer handoff.
- Preserved decision-support positioning, two-city setup, 高德 API pipeline description, scoring interpretation, 新街口 over-saturation explanation, and known limitations.
- Kept commands, paths, code blocks, and column names unchanged.
- Did not add screenshots or install new tooling.

### Verification

- `python -m compileall app src`
- Streamlit run/localhost check.
- `.gitignore` check for `.env`, `data/raw/`, and `data/processed/`.
