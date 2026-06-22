# Multi-City Roadmap: Xuzhou To Nanjing

This planning document describes how to expand `jiangsu-site-rank` from a 徐州-only cafe site-scoring MVP into a reusable multi-city site selection BI tool, with 南京 as the next validation city.

The intent is not to rewrite the project. 南京 should validate whether the current 徐州 pipeline, schemas, scoring assumptions, and dashboard patterns can generalize to a second city.

## Current Project State

### What Already Works For 徐州

- Manual candidate site hypotheses exist in `data/manual/candidate_sites.csv`.
- Candidate addresses can be geocoded with 高德 Web 服务 API.
- Nearby POIs can be collected around known candidate coordinates using manually curated keyword buckets.
- Raw POI snapshots are cleaned and deduplicated.
- Site-level metrics are aggregated by radius and bucket.
- Cafe site scores are generated with v2 scoring.
- Streamlit displays a business-readable dashboard for ranked candidate review.

### Current Data Flow

1. `data/manual/candidate_sites.csv`
2. `src/geocode_candidates.py`
3. `data/processed/candidate_sites_geocoded.csv`
4. `data/manual/poi_keywords.csv`
5. `src/collect_poi_snapshots.py`
6. `data/raw/poi_snapshot_*.csv`
7. `src/clean_pois.py`
8. `data/processed/pois_cleaned.csv`
9. `data/processed/poi_observations_cleaned.csv`
10. `src/aggregate_site_metrics.py`
11. `data/processed/site_metrics.csv`
12. `src/score_sites.py`
13. `data/processed/site_scores.csv`
14. `app/streamlit_app.py`

### Current Scoring And Display Workflow

- `site_metrics.csv` provides candidate-level feature counts.
- `site_scores.csv` preserves the metric columns and appends scoring columns.
- v2 scoring uses positive components:
  - demand strength
  - transit accessibility
  - commercial maturity
  - competition fit
- Competition fit scores highest around moderate direct competition and lower when direct competition is too sparse or too saturated.
- The Streamlit dashboard shows ranking, selected-site interpretation, score components, and methodology notes.

### Current Known Limitations

- The project has only been validated on 徐州.
- Current manual data filenames are not yet city-partitioned.
- Raw and processed output paths are single-city oriented.
- Candidate selection is manual and not yet documented as a repeatable city research process.
- Competition fit target is calibrated from the current 徐州 candidate set, not from multiple cities.
- Dashboard assumes one active city dataset at a time.
- Rent, storefront visibility, lease constraints, and pedestrian flow are not included.

## Roadmap Principles

- Keep 徐州 stable.
- Make 南京 a second-city validation, not a total rewrite.
- Prioritize schema compatibility before adding features.
- Avoid city-wide crawling; keep using manually selected candidate sites.
- Keep 高德 / GCJ-02 coordinates throughout.
- Keep Chinese CSV outputs Excel-compatible with UTF-8 BOM.
- Do not add AI memos, deployment, or broad automation before the second city works.

## Recommended Ticket Roadmap

### T0012 - Scoring Algorithm Review

**Goal:** Review whether v2 scoring is suitable before applying it to 南京.

**Scope:**
- Review current v2 component weights.
- Review competition fit target and tolerance.
- Decide whether the scoring formula should remain fixed for 南京 first run.
- Document open calibration questions.

**Files likely touched:**
- `docs/methodology.md`
- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`

**Manual verification:**
- Confirm v2 scores remain reproducible for 徐州.
- Confirm no scoring code changes are required unless explicitly approved.
- Confirm ranking interpretation is clear.

**Risks / assumptions:**
- Current competition fit target may be too 徐州-specific.
- Changing weights before 南京 may hide whether the model generalizes.

**Expected output:**
- A short documented scoring review and decision on whether to freeze v2 for 南京 first run.

**Decision recorded:** Done. Freeze the current v2 scoring formula for the first 南京 run.

**Review notes:**
- Keep weights unchanged for 南京 first run: demand `0.40`, accessibility `0.25`, commercial maturity `0.20`, competition fit `0.15`.
- Keep the positive `competition_fit_score` approach. It is easier to explain than the previous subtractive competitor-pressure score.
- Keep the current competition fit target for the first 南京 pass. Do not tune it before seeing second-city results.
- Preserve `v1_site_score`, `v1_site_rank`, and `rank_change_vs_v1` only as comparison/debug context; business-facing interpretation should use v2.
- Treat 南京 as a validation test of whether the scoring assumptions travel to a denser, larger city.

**Open calibration questions for after 南京 first run:**
- Does the current moderate-competition target underrate dense 南京 commercial centers?
- Should competition fit target be global, per-city, or per business type?
- Should min-max normalization stay per city for local ranking, or should a later portfolio view support cross-city normalization?
- Do keyword buckets need city-specific additions, or can the first 南京 run use the same coffee keyword vocabulary?

### T0013 - City Config Planning

**Goal:** Design the smallest city-aware structure needed for 徐州 and 南京.

**Scope:**
- Decide whether city should be represented by folder partitioning, a config file, or both.
- Define expected city identifiers such as `xuzhou` and `nanjing`.
- Specify input and output path conventions.
- Keep backward compatibility with current 徐州 files.

**Files likely touched:**
- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`
- `docs/methodology.md`

**Manual verification:**
- Confirm the proposed structure can support current 徐州 files.
- Confirm 南京 can be added without renaming every existing artifact immediately.

**Risks / assumptions:**
- Over-partitioning too early could slow the MVP.
- Under-partitioning could make city switching brittle.

**Expected output:**
- A documented city config and path plan.

**Decision recorded:** Done. Use both light folder partitioning and a small city config plan, but implement the code changes later.

**City identifiers:**
- `xuzhou`: existing completed MVP city.
- `nanjing`: next planned validation city.

**Recommended future path convention:**

```text
data/
  manual/
    shared/
      poi_keywords.csv
    xuzhou/
      candidate_sites.csv
    nanjing/
      candidate_sites.csv
  raw/
    xuzhou/
      poi_snapshot_*.csv
    nanjing/
      poi_snapshot_*.csv
  processed/
    xuzhou/
      candidate_sites_geocoded.csv
      pois_cleaned.csv
      poi_observations_cleaned.csv
      site_metrics.csv
      site_scores.csv
    nanjing/
      candidate_sites_geocoded.csv
      pois_cleaned.csv
      poi_observations_cleaned.csv
      site_metrics.csv
      site_scores.csv
```

**Recommended future config shape:**

Use a small CSV or JSON-style config later, not a large framework. A future `data/manual/city_config.csv` would be enough:

```text
city_id,city_name,province,amap_city,manual_candidates_path,processed_dir,raw_dir,active
xuzhou,徐州,江苏省,徐州市,data/manual/xuzhou/candidate_sites.csv,data/processed/xuzhou,data/raw/xuzhou,true
nanjing,南京,江苏省,南京市,data/manual/nanjing/candidate_sites.csv,data/processed/nanjing,data/raw/nanjing,false
```

**Backward compatibility plan:**
- Do not move existing 徐州 files immediately.
- Treat current root-level files as the active `xuzhou` legacy layout until city switching work begins.
- When code changes are approved, first add city-aware path arguments while keeping current defaults.
- Only after both 徐州 and 南京 run successfully should files be migrated or copied into city folders.

**Implementation order implied by this plan:**
1. T0014 documents and prepares 南京 schema.
2. T0015 creates `data/manual/nanjing/candidate_sites.csv`.
3. T0016 adds minimal path arguments or config support required to run 南京.
4. T0020 adds dashboard city switching after both city score outputs exist.

**Manual verification for the plan:**
- Existing 徐州 dashboard and files remain untouched.
- Future 南京 paths mirror current 徐州 output names.
- Shared `poi_keywords.csv` remains reusable for first 南京 pass.

### T0014 - Nanjing Data Schema Preparation

**Goal:** Prepare 南京 manual data schemas without importing data yet.

**Scope:**
- Define 南京 candidate site CSV schema.
- Confirm it matches 徐州 candidate schema.
- Define whether 南京 uses the same `poi_keywords.csv`.
- Document Excel UTF-8 BOM requirement.

**Files likely touched:**
- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`
- `docs/Manual_Verification_Guide.md`

**Manual verification:**
- Compare 南京 planned schema to 徐州 schema.
- Confirm required columns are unchanged.

**Risks / assumptions:**
- 南京 may need additional candidate-area notes, but schema should stay stable for the first run.

**Expected output:**
- A schema checklist for 南京 candidate import.

**Decision recorded:** Done. 南京 first import must use the same candidate schema as 徐州.

**Approved 南京 candidate path for T0015:**

```text
data/manual/nanjing/candidate_sites.csv
```

**Approved candidate schema:**

```text
site_id,city,district,area_name,address,business_type,reason_for_selection
```

**Column rules:**
- `site_id`: stable unique id, recommended format `NJ_COFFEE_001`, `NJ_COFFEE_002`, etc.
- `city`: must be `南京`.
- `district`: Chinese district name, for example `玄武区`, `秦淮区`, `建邺区`, `鼓楼区`, `雨花台区`, `江宁区`, etc.
- `area_name`: clear business-area name, not a vague description.
- `address`: Chinese address or landmark string that 高德 geocoding can likely understand.
- `business_type`: keep `coffee_shop` for the first 南京 run.
- `reason_for_selection`: short Chinese business hypothesis explaining why the area is worth evaluating.

**Columns explicitly not allowed in manual input:**
- `lng`
- `lat`
- `geocode_*`
- POI counts
- score columns

Coordinates must be generated later by 高德 geocoding so all location fields remain in 高德 / GCJ-02.

**Keyword decision:**
- Use the current shared `poi_keywords.csv` for the first 南京 pass.
- Do not create 南京-specific keywords before the first run.
- Review keyword fit only after 南京 sanity-check review.

**Encoding decision:**
- Save Chinese CSV files as UTF-8 with BOM for Microsoft Excel compatibility.

**T0015 suggested import size:**
- Start with 7-10 南京 candidate areas.
- Candidate areas should span a few different urban contexts, such as core commercial, office-heavy, transport hub, university, and residential-commercial mixed areas.
- Do not attempt city-wide coverage.

### T0015 - Nanjing First Data Import

**Goal:** Add the first manually selected 南京 cafe candidate sites.

**Scope:**
- Create 南京 candidate site data using the approved schema.
- Keep candidates manually selected as business hypotheses.
- Do not call 高德 yet in this ticket.

**Files likely touched:**
- Future 南京 candidate CSV path, to be decided in T0013.
- `README.md`
- `docs/Manual_Verification_Guide.md`

**Manual verification:**
- Open the CSV in Excel and confirm Chinese text displays correctly.
- Confirm no `lng` or `lat` columns are manually added.
- Confirm candidate count is small enough for manual review.

**Risks / assumptions:**
- Poor candidate selection will weaken the second-city validation.

**Expected output:**
- A 南京 candidate CSV ready for geocoding.

### T0016 - Nanjing First Scoring Run

**Goal:** Run the existing pipeline for 南京 after candidate data is ready.

**Scope:**
- Geocode 南京 candidates.
- Collect nearby POI snapshots around candidates.
- Clean and deduplicate POIs.
- Aggregate metrics.
- Score sites with the frozen v2 model.

**Files likely touched:**
- Future 南京 raw and processed outputs.
- Potential path/config wiring files if approved in T0013.

**Manual verification:**
- Confirm geocoding success rate.
- Confirm raw POI snapshots have plausible row counts.
- Confirm cleaned and aggregated outputs have one row per candidate.
- Confirm scores are bounded 0-100.

**Risks / assumptions:**
- 高德 quota or API key limits may affect collection.
- 南京 POI density may expose scaling or pagination assumptions.

**Expected output:**
- First 南京 `site_scores` equivalent.

**Result recorded:** Done.

**Run summary:**
- Geocoded 8 南京 candidates successfully.
- Collected `data/raw/nanjing/poi_snapshot_20260622_174413.csv` with 9,713 raw POI rows.
- Cleaned 4,578 unique POIs into `data/processed/nanjing/pois_cleaned.csv`.
- Produced `data/processed/nanjing/site_metrics.csv` and `data/processed/nanjing/site_scores.csv`.
- Current 南京 top three by `site_score`: 新街口商圈, 湖南路商圈, 珠江路商圈.

### T0017 - Nanjing Streamlit Display

**Goal:** Display 南京 scoring results in Streamlit without breaking 徐州.

**Scope:**
- Add a simple way to view 南京 output.
- Keep dashboard layout consistent.
- Avoid full multi-city selector unless T0019 is ready.

**Files likely touched:**
- `app/streamlit_app.py`
- Possibly city config/path docs.

**Manual verification:**
- Confirm 徐州 dashboard still loads.
- Confirm 南京 dashboard view loads.
- Confirm labels and methodology remain city-neutral enough.

**Risks / assumptions:**
- Hardcoding a second city could create cleanup work for T0019.

**Expected output:**
- A dashboard view for 南京 first run.

**Result recorded:** Done. The dashboard now has a 南京 result view without breaking the 徐州 default.

### T0018 - Nanjing Sanity-Check Review

**Goal:** Review whether 南京 outputs are plausible before recalibrating.

**Scope:**
- Compare top-ranked 南京 candidates against known commercial logic.
- Inspect competitor counts and demand anchor counts.
- Identify obvious keyword or candidate issues.
- Decide whether reruns are needed.

**Files likely touched:**
- `docs/Manual_Verification_Guide.md`
- `docs/planning/Multi_City_Roadmap_Xuzhou_To_Nanjing.md`

**Manual verification:**
- Spot-check selected coordinates in 高德地图.
- Spot-check several POIs for top and bottom sites.
- Review whether ranking passes basic business judgment.

**Risks / assumptions:**
- Bad candidate hypotheses may look like scoring problems.
- 南京 density may differ enough that raw scores need calibration review.

**Expected output:**
- A documented sanity-check note and decision on calibration.

**Decision recorded:** Done. 南京 data makes sense for the first validation pass.

**Review notes:**
- Top-ranked 南京 candidates are plausible: 新街口商圈, 湖南路商圈, 珠江路商圈.
- Dense core business districts score high through demand, accessibility, and commercial maturity.
- Competition fit correctly flags saturation pressure in the densest markets rather than hiding it.
- 仙林大学城 is a watchpoint because the selected geocoded campus point has sparse POI signal; revisit candidate-point selection or keyword coverage later if the project continues.

### T0019 - Nanjing Scoring Calibration

**Goal:** Adjust scoring only if 南京 validation shows a clear need.

**Scope:**
- Review whether competition fit target should be city-specific or global.
- Review whether min-max normalization should be per-city.
- Keep changes small and documented.

**Files likely touched:**
- `src/score_sites.py`
- `docs/methodology.md`
- `docs/Repo_Current_State.md`

**Manual verification:**
- Re-run 徐州 and 南京 scoring.
- Compare rank changes before and after calibration.
- Confirm scores remain 0-100.

**Risks / assumptions:**
- Overfitting to 南京 would reduce portability.
- Per-city calibration may make cross-city comparison less direct.

**Expected output:**
- A documented calibration decision and updated scores if needed.

**Decision recorded:** Done. No calibration change for this pass.

**Review notes:**
- Keep frozen v2 weights unchanged.
- Keep positive `competition_fit_score` unchanged.
- Keep per-city normalization unchanged for local ranking.
- Do not regenerate scores because no scoring formula or input data changed.

### T0020 - Multi-City Selector / City Switching

**Goal:** Add a simple dashboard control to switch between 徐州 and 南京.

**Scope:**
- Add city selector to Streamlit.
- Load city-specific score files.
- Keep shared display components.
- Avoid database setup.

**Files likely touched:**
- `app/streamlit_app.py`
- City config file if created.
- `README.md`

**Manual verification:**
- Confirm 徐州 and 南京 both load from the selector.
- Confirm switching cities does not mix metrics.
- Confirm missing city files fail clearly.

**Risks / assumptions:**
- Current single-city file paths need careful migration.

**Expected output:**
- One Streamlit app that can switch between 徐州 and 南京.

**Result recorded:** Done. The Streamlit app now has a sidebar `城市` selector for 徐州 and 南京, with city-specific score and metrics paths.

### T0021 - Final Portfolio Polish

**Goal:** Package the project as a clear analytics portfolio case study.

**Scope:**
- Improve README narrative.
- Add screenshots if available.
- Add final project summary.
- Keep implementation modest.

**Files likely touched:**
- `README.md`
- `docs/Repo_Current_State.md`
- `docs/Manual_Verification_Guide.md`
- Optional screenshots under `docs/` or `assets/`.

**Manual verification:**
- Confirm a reader can understand the business problem, data flow, and outputs.
- Confirm no secrets or `.env` content are exposed.
- Confirm instructions run from a clean environment.

**Risks / assumptions:**
- Polish should not hide known limitations.

**Expected output:**
- A portfolio-ready repo narrative after 南京 validation.

**Result recorded:** Done. The README is now portfolio-facing, and `docs/Portfolio_Summary.md` provides a concise reviewer handoff.

## Recommended Next Ticket

No next implementation ticket is currently planned.

Reason: T0021 completed the two-city validation narrative and portfolio polish. The next step is manual portfolio/demo review, then a new ticket should be written only if the review identifies follow-up work.
