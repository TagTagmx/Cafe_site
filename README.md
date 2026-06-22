# jiangsu-site-rank

Decision-support case study for coffee shop site selection in Jiangsu. The project combines a local data pipeline, 高德 Web 服务 API geocoding/POI collection, feature engineering, explainable scoring, and a Streamlit dashboard that turns manually selected candidate areas into ranked business evidence with interpretation.

It is deliberately not an automatic leasing decision tool. The score helps prioritize field visits and rent/lease review; it does not replace judgment about frontage, visibility, unit economics, or contract terms.

## 10-Second Read

- **Problem:** Which candidate areas deserve deeper review for coffee shop expansion?
- **Cities:** 徐州 MVP plus 南京 second-city validation.
- **Data:** Manual candidate sites enriched with 高德 geocoding and nearby POIs.
- **Method:** Deduplicate POIs, aggregate demand/access/competition metrics, score with transparent weights.
- **Output:** Streamlit dashboard with city switching, ranked sites, component breakdowns, and business interpretation.
- **Status:** Two-city workflow is complete; known limitations are documented.

## Example Results

These example values come from the local generated score outputs under `data/processed`. The CSV outputs are generated artifacts and are not meant to be committed.

| City | Rank | Candidate | Score | Demand | Access | Maturity | Competition pressure | Competition fit |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 徐州 | 1 | 徐州苏宁广场 | 86.89 | 97.96 | 100.00 | 98.89 | 94.63 | 19.50 |
| 徐州 | 2 | 金鹰国际购物中心 | 86.57 | 98.90 | 95.84 | 95.94 | 89.59 | 25.78 |
| 徐州 | 3 | 彭城广场商圈 | 86.56 | 100.00 | 96.89 | 100.00 | 95.03 | 15.56 |
| 南京 | 1 | 新街口商圈 | 84.86 | 99.66 | 100.00 | 100.00 | 97.17 | 0.00 |
| 南京 | 2 | 湖南路商圈 | 84.08 | 97.69 | 93.77 | 67.18 | 62.82 | 54.17 |
| 南京 | 3 | 珠江路商圈 | 78.27 | 100.00 | 83.20 | 81.53 | 92.27 | 7.78 |

`competition_fit_score` is not raw competition level. Raw crowding is represented by `competitor_pressure_score` and direct competitor counts. 南京新街口 ranks high overall because demand, access, and commercial maturity are very strong, while its `competition_fit_score` is low because the model flags over-saturation risk.

## Dashboard

Run the dashboard:

```powershell
python -m streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`, then use the sidebar `城市` selector to switch between 徐州 and 南京.

The dashboard shows:

- Ranked candidate sites.
- Overall score and component breakdown.
- Direct competitor counts by radius.
- Demand anchor and transit counts.
- Actual competition pressure versus competition fit.
- Selected-site business interpretation.
- Methodology notes and model limitations.

## Two-City Setup

Shared project pieces:

- `data/manual/poi_keywords.csv`: shared POI keyword buckets for direct competitors, indirect competitors, demand anchors, and transit.
- `src/`: shared geocoding, POI collection, cleaning, aggregation, and scoring scripts.
- `app/streamlit_app.py`: one dashboard with a `城市` selector.

City-specific pieces:

| City | Manual candidates | Processed score path | Dashboard loading |
| --- | --- | --- | --- |
| 徐州 | `data/manual/candidate_sites.csv` | `data/processed/site_scores.csv` | legacy root processed files |
| 南京 | `data/manual/nanjing/candidate_sites.csv` | `data/processed/nanjing/site_scores.csv` | `data/processed/nanjing` |

The current scripts default to the original 徐州 paths. 南京 has already been run into city-specific folders for validation; the README does not invent extra CLI commands for city switching.

## Pipeline

1. Define manually selected candidate sites.
2. Geocode candidate addresses with 高德 Web 服务 API.
3. Collect nearby POIs around candidate coordinates at 300m, 800m, and 1500m.
4. Store raw snapshots under `data/raw`.
5. Clean and deduplicate POIs into `data/processed`.
6. Aggregate one metrics row per candidate site.
7. Score each candidate with an explainable weighted model.
8. Review results in Streamlit.

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

Generated raw and processed outputs are ignored by git.

## Scoring Model

The v2 score is intentionally simple and inspectable:

```text
site_score =
  demand_score * 0.40
  + accessibility_score * 0.25
  + commercial_maturity_score * 0.20
  + competition_fit_score * 0.15
```

Component meaning:

- `demand_score`: demand anchors such as offices, shopping centers, schools, residential communities, and hotels.
- `accessibility_score`: transit and parking-related access signals.
- `commercial_maturity_score`: surrounding POI density and adjacent commercial formats.
- `competitor_pressure_score`: actual competition intensity, where higher means more direct competitor crowding and/or closer competitors.
- `competition_fit_score`: positive scoring component, where higher means competition is closer to a moderate target.

## Known Limitations

- No rent, lease term, frontage, visibility, store size, or operator cost data.
- Candidate sites are manually selected and do not represent exhaustive city coverage.
- POI quality depends on 高德 API coverage and keyword choices.
- Per-city normalization supports local ranking but should not be treated as absolute cross-city comparison.
- 南京仙林大学城 is a watchpoint: the current geocoded campus point has sparse nearby POI signal and may need a better representative point or keyword review.
- High traffic and high competition can coexist; saturated locations require manual judgment beyond POI counts.

## Screenshots

No screenshot is committed in this pass. The local environment does not currently have Playwright installed, and this polish ticket avoids adding new tooling. Run the Streamlit command above to review the dashboard directly.

## Project Structure

```text
app/              Streamlit dashboard
data/manual/      Manually curated candidate inputs and POI keywords
data/raw/         Raw API snapshots, ignored by git
data/processed/   Generated cleaned data, metrics, and scores, ignored by git
docs/             Methodology, tickets, planning, and verification notes
notebooks/        Exploratory analysis placeholder
sql/              Optional SQL snippets placeholder
src/              Pipeline scripts and reusable API/client logic
```

## Verification

Useful checks before review:

```powershell
python -m compileall app src
python -m streamlit run app/streamlit_app.py
```

Manual review should confirm:

- The dashboard loads for both 徐州 and 南京.
- City switching does not mix metrics.
- `.env`, `data/raw/`, and `data/processed/` remain ignored.
- 新街口 is interpreted as high actual competition pressure with over-saturation risk.
- Model limitations remain visible in the README and dashboard.
