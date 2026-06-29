# Cafe Site V2 Ticket 4 Verification Guide

Ticket 4 keeps final scoring in Python. SQL verifies the raw evidence entering the model; pandas verifies the exported scores and explanations.

## Run The Offline Sample

```powershell
python src\score_v2_sites.py `
  --input-csv data\sample\v2\site_feature_counts.csv `
  --output-dir data\exports\v2
```

After MySQL Ticket 3 verification succeeds, omit `--input-csv` to read `v_site_feature_counts` using the `MYSQL_*` settings in `.env`.

The scorer writes:

- `site_feature_summary.csv`: unchanged raw SQL feature evidence.
- `site_scores.csv`: raw transformations, normalized components, interactions, scenario score, balanced site score, and rank.
- `site_explanations.csv`: bilingual labels, narrative explanations, and conservative-risk flags.

## A. Eight Manual SQL Checks

The same executable queries are collected in `sql/v2_t4_manual_review.sql`.

### 1. Confirm One Feature Row Per Site

```sql
SELECT
    COUNT(*) AS feature_rows,
    COUNT(DISTINCT site_id) AS unique_sites
FROM v_site_feature_counts;
```

What it proves: both numbers must match. Otherwise one site is duplicated and could be scored more than once.

### 2. Find Broken Cumulative Counts

```sql
SELECT site_code
FROM v_site_feature_counts
WHERE direct_coffee_within_300m > direct_coffee_within_800m
   OR direct_coffee_within_800m > direct_coffee_within_1500m
   OR total_poi_activity_within_300m > total_poi_activity_within_800m
   OR total_poi_activity_within_800m > total_poi_activity_within_1500m;
```

What it proves: this should return zero rows. A cumulative 800m count cannot be smaller than its 300m count.

### 3. Inspect The 300m-Heavy Raw Signals

```sql
SELECT
    site_code,
    0.75 * direct_coffee_within_300m
        + 0.25 * direct_coffee_within_800m AS direct_coffee_core_raw,
    0.75 * office_within_300m
        + 0.25 * office_within_800m AS office_demand_raw
FROM v_site_feature_counts
ORDER BY site_code;
```

What it proves: nearby offices and coffee stores contribute three times the marginal weight of evidence found only between 300m and 800m.

### 4. Compare Validation And Pressure Evidence

```sql
SELECT
    site_code,
    direct_coffee_within_300m,
    direct_coffee_within_800m,
    direct_coffee_within_1500m,
    nearest_direct_coffee_distance_m
FROM v_site_feature_counts
ORDER BY direct_coffee_within_800m DESC, site_code;
```

What it proves: sites can share strong coffee-demand validation while having different competitive pressure. Python plateaus validation but continues increasing pressure.

### 5. Find The Indirect-Support Trap

```sql
SELECT
    site_code,
    direct_coffee_within_800m,
    indirect_support_within_800m,
    total_poi_activity_within_800m
FROM v_site_feature_counts
WHERE indirect_support_within_800m >= 3
  AND direct_coffee_within_800m = 0
ORDER BY indirect_support_within_800m DESC;
```

What it proves: these sites have beverage/retail infrastructure without direct evidence of coffee preference. Their indirect support must be gated toward zero.

### 6. Find Transit Without Demand

```sql
SELECT
    site_code,
    transit_within_800m,
    office_within_800m,
    commercial_within_800m,
    residential_within_800m,
    direct_coffee_within_800m
FROM v_site_feature_counts
WHERE transit_within_800m >= 2
ORDER BY transit_within_800m DESC;
```

What it proves: transit accessibility alone is not a coffee opportunity. Check whether offices, commerce, residences, or validated coffee demand support it.

### 7. Compare Mature And Possibly Saturated Clusters

```sql
SELECT
    site_code,
    direct_coffee_within_300m,
    direct_coffee_within_800m,
    total_poi_activity_within_300m,
    total_poi_activity_within_800m
FROM v_site_feature_counts
WHERE direct_coffee_within_800m >= 3
ORDER BY direct_coffee_within_800m DESC, total_poi_activity_within_800m DESC;
```

What it proves: similar coffee density can mean maturity in an active market or saturation in a weak market. Competition count cannot be interpreted alone.

### 8. Separate District Background From Store-Level Pressure

```sql
SELECT
    site_code,
    direct_coffee_within_800m AS core_pressure_context,
    direct_coffee_within_1500m AS district_background,
    direct_coffee_within_1500m - direct_coffee_within_800m
        AS coffee_between_800m_and_1500m
FROM v_site_feature_counts
ORDER BY coffee_between_800m_and_1500m DESC, site_code;
```

What it proves: 1500m coffee remains visible for context but is not included in `direct_coffee_core_raw`.

## B. Four Pandas Checks

Run these from the repository root after creating `data/exports/v2`.

### 1. Check Rows, Ranks, And Score Bounds

```python
import pandas as pd

scores = pd.read_csv("data/exports/v2/site_scores.csv", encoding="utf-8-sig")
assert scores["site_id"].is_unique
assert sorted(scores["site_rank"]) == list(range(1, len(scores) + 1))
assert scores["site_score"].between(0, 100).all()
```

What it proves: every site appears once, ranks are complete, and final scores stay within the documented range.

### 2. Confirm Validation Plateaus While Pressure Rises

```python
dense = scores.sort_values("direct_coffee_core_raw")
plateau = dense[dense["coffee_validation_score"] == 100]
assert plateau["competition_pressure_score"].is_monotonic_increasing
```

What it proves: after demand validation reaches its plateau, additional direct competitors still increase pressure.

### 3. Confirm Indirect Support Is Gated

```python
expected = (
    scores["indirect_support_score"]
    * scores["coffee_validation_score"]
    / 100
)
assert (scores["effective_indirect_support_score"] - expected).abs().max() < 0.02
assert (
    scores.loc[scores["coffee_validation_score"] == 0,
               "effective_indirect_support_score"] == 0
).all()
```

What it proves: tea, bakery, convenience, and similar activity cannot independently create coffee demand.

### 4. Confirm Low Validation Does Not Become “Low Saturation”

```python
explanations = pd.read_csv(
    "data/exports/v2/site_explanations.csv",
    encoding="utf-8-sig",
)
low_confidence = explanations["saturation_risk_status"] == "low_confidence"
assert low_confidence.any()
assert explanations.loc[low_confidence, "primary_label_en"].isin({
    "Unvalidated coffee demand",
    "Infrastructure-rich but coffee-weak",
    "Low demand foundation",
}).all()
```

What it proves: low direct-coffee evidence produces a conservative demand interpretation instead of an automatic low-competition opportunity.

## C. Five Business Questions

1. Do the top-ranked sites have real nearby demand anchors, or are they ranking mainly because coffee competitors already exist?
2. For every `Infrastructure-rich but coffee-weak` site, is there local evidence that tea or convenience consumption can transfer to coffee?
3. Where high validation and high pressure coexist, does surrounding activity support a mature market, or does the cluster look oversaturated?
4. Are transit-supported sites useful during the intended trading hours, or is transit activity disconnected from likely cafe customers?
5. Would rent, frontage, measured pedestrian flow, customer spending power, or store-size constraints reverse the model’s shortlist?

These questions require fieldwork and operating data. The V2 score is decision support, not a lease or revenue prediction.
