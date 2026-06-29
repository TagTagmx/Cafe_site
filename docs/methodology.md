# Methodology

This project ranks candidate coffee shop sites in 徐州 and 南京 using explainable POI evidence. Transparency remains more important than hidden model complexity so each score can be traced back to visible local-market signals.

## V1 And V2 Method Boundary

- **V1:** pandas reads cleaned CSV observations, aggregates site metrics, applies the frozen transparent score, and supplies the two-city Streamlit dashboard.
- **V2:** MySQL stores normalized entities and evidence, derives one deterministic relationship per unique site/POI pair, and exposes raw cumulative feature counts through SQL views. Python remains responsible for normalization, interactions, final scoring, and bilingual explanation labels.

V2 verification compares every MySQL feature-view value with the pandas reference output. This is feature parity, not a claim that V1 and V2 use identical business features or produce identical rankings. Neither path uses machine learning or predicts revenue.

V1 使用 pandas/CSV 完成聚合与评分；V2 使用 MySQL 保存关系型证据并由 SQL 生成可审计特征，再由 Python 完成评分和解释。两条路径都属于决策支持，不替代实地踏勘和租赁判断。

## Candidate Unit

Each row represents one manually defined candidate site. A site should include a name, address, district or area label, and optional notes about why it was selected.

## Feature Groups

Initial scoring will use four feature groups:

1. Competitor pressure
   - Nearby coffee shops and tea shops.
   - Higher direct competitor density should reduce the score unless the area also shows strong demand.

2. Demand signals
   - Office buildings, shopping centers, schools, residential communities, hotels, and other foot-traffic generators.
   - Higher demand density should increase the score.

3. Accessibility
   - Transit stations, major roads, parking-related POIs, and commercial entrances.
   - Better access should increase the score.

4. Commercial maturity
   - Food and beverage POI density, retail density, and entertainment or lifestyle POIs.
   - A mature commercial area can indicate stronger customer flow, but may also overlap with competitor pressure.

## POI Keyword Buckets

The first POI search vocabulary lives in `data/manual/poi_keywords.csv`. It is intentionally small and focused on evaluating the 7 manually selected 徐州 candidate sites rather than discovering every possible commercial area.

The first version uses four buckets:

- `direct_competitor`: coffee shops and major coffee chains that directly compete for coffee demand.
- `indirect_competitor`: tea drinks, bakery, dessert, and other substitute leisure-consumption formats.
- `demand_anchor`: offices, shopping centers, universities, residential communities, and hotels that may generate coffee demand.
- `transit`: metro, bus, parking, and high-speed rail access signals that may improve candidate reachability.

Keyword results should retain their source keyword and bucket metadata during collection and cleaning. A POI may appear under multiple keywords or radii, so later cleaning must deduplicate without losing the reason it was collected.

## POI Cleaning

T0006 creates `data/processed/pois_cleaned.csv` from raw snapshot files. The cleaner removes repeated POI rows caused by overlapping radii, repeated candidate areas, and multiple keyword matches.

Deduplication rules:

- Use 高德 `poi_id` as the primary deduplication key when present.
- Fall back to normalized POI name plus GCJ-02 location when `poi_id` is missing.
- Preserve source context by retaining all matched `site_ids`, `area_names`, `buckets`, `keywords`, `keyword_ids`, and `radii_m`.
- Keep `source_row_count`, `min_distance_m`, and `max_distance_m` so later aggregation can reason about repeated observations.

The cleaner also writes `data/processed/poi_observations_cleaned.csv`, which keeps exact `poi_clean_id`, `site_id`, `radius_m`, and `bucket` combinations. Site-level aggregation should use this observation table instead of expanding pipe-separated summary fields from `pois_cleaned.csv`.

## Site Metrics Aggregation

T0007 creates `data/processed/site_metrics.csv` with one row per candidate site.

Current metrics:

- Total unique POI counts at 300m, 800m, and 1500m.
- Direct competitor counts at 300m, 800m, and 1500m.
- Indirect competitor counts at 300m, 800m, and 1500m.
- Demand anchor counts at 300m, 800m, and 1500m.
- Transit counts at 300m, 800m, and 1500m.
- Nearest direct competitor distance.

Counts are based on deduplicated POI observations for each candidate, radius, and bucket. The metrics are descriptive inputs for scoring and should not yet be interpreted as final site recommendations.

## Coffee Site Score v2

T0011 updates `data/processed/site_scores.csv` with the v2 scoring model. It remains simple, explainable, and based only on the currently available POI metrics.

Component inputs:

- `demand_score`: weighted mix of 800m and 1500m demand anchor counts.
- `accessibility_score`: weighted mix of 800m and 1500m transit counts.
- `commercial_maturity_score`: weighted mix of total POI density and indirect competitor density.
- `competitor_pressure_score`: actual competition intensity indicator. Higher values mean stronger direct-competitor crowding and/or closer nearby competitors.
- `competition_fit_score`: positive competition calibration score used in the v2 site score. It is highest when direct competitors are moderate, lower when competitors are too few or too many.

The v2 site score uses this weighted additive model:

```text
site_score =
  demand_score * 0.40
  + accessibility_score * 0.25
  + commercial_maturity_score * 0.20
  + competition_fit_score * 0.15
```

Each component is normalized to a comparable 0-100 scale before weighting. The final v2 `site_score` is clipped to the 0-100 range.

Competition fit uses the weighted direct-competitor density from 800m and 1500m counts. The current target is a moderate density around 30 weighted direct competitors. Scores decline more quickly when competition is below the target, because very few competitors may indicate weak category validation. Scores decline more gradually above the target, because dense coffee competition may still coexist with strong demand in core commercial areas.

Important interpretation: `competition_fit_score` is not "competition level". A saturated market such as 南京新街口 can have very high `competitor_pressure_score` and direct competitor counts, while receiving a low `competition_fit_score` because the positive scoring component treats over-saturation as a risk.

The output keeps `v1_site_score`, `v1_site_rank`, and `rank_change_vs_v1` to make the calibration effect visible.

## T0012 Scoring Review Decision

Before adding 南京, the current v2 score should be frozen for the first second-city validation run.

Decision:

- Keep v2 component weights unchanged for 南京 first run.
- Keep `competition_fit_score` as a positive component.
- Do not tune the competition fit target until 南京 has produced a first full scoring output.
- Use 南京 results to judge whether the target is too strict for denser commercial areas.
- Keep per-city ranking as the near-term goal; do not attempt cross-city absolute comparison yet.

This keeps 南京 as a validation exercise rather than a moving-target scoring rewrite.

## T0013 City Config Planning

The project should move toward city-aware paths gradually. The smallest useful model is:

- `city_id`: stable lowercase English id, such as `xuzhou` or `nanjing`.
- `city_name`: Chinese display name, such as `徐州` or `南京`.
- `amap_city`: 高德 API city hint, such as `徐州市` or `南京市`.
- city-specific manual candidate files.
- city-specific raw and processed outputs.
- shared POI keyword buckets for the first 南京 pass.

Recommended future layout:

```text
data/manual/shared/poi_keywords.csv
data/manual/xuzhou/candidate_sites.csv
data/manual/nanjing/candidate_sites.csv
data/raw/xuzhou/
data/raw/nanjing/
data/processed/xuzhou/
data/processed/nanjing/
```

For backward compatibility, current root-level 徐州 files should remain valid until city-aware code changes are explicitly implemented.

## Notes

- The first version should avoid hidden model complexity.
- The score is a decision-support signal, not a final site decision.
- Manual review remains important for rent, frontage, visibility, lease terms, and operational constraints that may not appear in POI data.
- A future V2/MySQL advisory agent should consume verified evidence read-only, preserve feature provenance, and cite limitations. The existing V1 rules-based site analyst is separate; V2 agent integration is outside this release.
