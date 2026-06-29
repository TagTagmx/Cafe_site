# Cafe Site V2 Methodology / 方法说明

Cafe Site V2 ranks manually selected coffee-site hypotheses in 徐州 and 南京 using relational POI evidence. The method is rule-based, explainable, and designed so every score can be traced back to stored observations and deterministic site–POI relationships.

本方法以 MySQL 关系型证据为基础，通过可审计的 SQL 特征和 Python 规则评分支持候选点复核。它不是机器学习预测，也不替代实地踏勘和租赁决策。

## Analytical Unit / 分析单元

Each analytical row is one manually defined candidate site. Candidate selection happens before POI evaluation; the project does not search an entire city for every possible storefront.

Sites retain stable identifiers, city membership, coordinates, addresses, and selection notes. Scores are ranked within each city.

## Evidence And Relational Model / 证据与关系模型

V2 separates source evidence from derived relationships:

- `poi_observations` stores imported keyword, radius, site, POI, and distance evidence.
- `site_poi_relationships` is derived by grouping each unique `(site_id, poi_clean_id)` pair.
- SQL feature views count relationships, not raw observation rows or keyword-match volume.

A single POI can be close to multiple sites, and one site can have many POIs. Modeling this many-to-many relationship explicitly preserves provenance while preventing repeated searches from inflating features.

## POI Identity And Deduplication / POI 去重

Canonical POI identity uses:

1. 高德 POI ID when available.
2. A deterministic fallback based on normalized name, rounded location, and city.

Repeated radius and keyword observations remain available as evidence but collapse to one relationship for each site and canonical POI. Advanced fuzzy matching and coordinate clustering are outside the current scope.

## Category Resolution / 分类冲突处理

Each relationship receives one resolved core category and one resolved sub-category. Core conflicts use this priority:

```text
direct_coffee
> indirect_competitor
> demand_anchor
> transit
> other / generic_commercial
```

Sub-categories preserve specific business meanings such as `office`, `commercial`, `residential`, `education`, `hotel`, `tea_drink`, `bakery`, and `convenience_store`.

For example, a Starbucks POI resolves to `direct_coffee` and cannot also inflate the same core feature as generic commercial activity. Original observation context remains available for diagnostics.

## Distance Semantics / 距离语义

Standard distance features are cumulative:

```text
within_300m  ⊆  within_800m  ⊆  within_1500m
```

Feature names state the radius explicitly, such as:

- `direct_coffee_within_300m`
- `office_within_800m`
- `transit_within_1500m`

Nearby evidence receives more weight for store-level demand. Direct coffee and office signals use a 75% 300m / 25% 800m weighting; direct coffee at 1500m remains district context rather than a core scoring input.

## SQL Feature Layer / SQL 特征层

`v_site_feature_counts` exposes one row per candidate site with cumulative counts for:

- Direct coffee.
- Indirect consumption support.
- Office, commercial, residential, education, and hotel demand.
- Transit.
- Total POI activity.
- Nearest direct-coffee distance.

SQL owns deterministic joins, resolved-category aggregation, cumulative counts, and diagnostics. It does not embed validation plateaus, saturation formulas, score normalization, final ranks, or explanation labels.

## Python Interaction Layer / Python 交互特征层

`src/score_v2_sites.py` reads the SQL feature view and applies fixed-cap transformations. Fixed caps avoid candidate-set-relative normalization, so adding another candidate does not automatically change every existing score.

### Demand Anchors

Demand combines normalized office, commercial, residential, education, and hotel signals:

```text
demand_anchor_score =
    office_demand_score * 0.35
  + commercial_demand_score * 0.25
  + residential_demand_score * 0.20
  + education_demand_score * 0.10
  + hotel_demand_score * 0.10
```

### Coffee Validation And Competition Pressure

Direct coffee has two distinct meanings:

- `coffee_validation_score` rises with moderate direct-coffee presence and then plateaus.
- `competition_pressure_score` continues increasing as direct-coffee density rises.

This allows a dense cluster to show both strong category validation and high competitive pressure.

### Indirect Support Gate

Tea, bakery, dessert, and similar formats cannot independently prove coffee demand:

```text
effective_indirect_support_score =
    indirect_support_score
  * coffee_validation_score
  / 100
```

High indirect infrastructure with weak coffee validation receives the conservative interpretation `Infrastructure-rich but coffee-weak`.

### Transit-Demand Synergy

Transit amplifies nearby demand rather than creating it:

```text
transit_demand_synergy_score =
    transit_accessibility_score
  * demand_strength
  / 100
```

A transit-heavy location with weak office, commercial, residential, and coffee evidence should not become a strong opportunity.

### Saturation And Unvalidated Demand

Saturation is conditional on coffee validation:

- Below the validation threshold, saturation is `low_confidence`, not automatically low.
- Above the threshold, competition pressure is adjusted by surrounding market activity.
- Strong market activity with weak coffee validation is flagged as unvalidated demand.
- Low competition is never added as a positive bonus.

## Final Scores / 最终评分

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

The scorer also produces `community_daily_score`, interaction features, scenario metadata, city-level ranks, and bilingual explanation labels. Scores are clipped to 0–100 and remain decision-support signals rather than revenue forecasts.

## SQL/Pandas Parity / SQL 与 pandas 一致性

The V2 verifier independently prepares the pandas reference features and compares them with MySQL `v_site_feature_counts`.

Parity requires:

- Identical site identifiers and row counts.
- Identical cumulative feature counts.
- Identical nearest direct-coffee distances.
- No extra or missing feature rows.

The verified full trial matched every feature cell for all 15 sites. This validates deterministic migration and aggregation; it is not a claim that all business thresholds are statistically optimal.

## Explanation Labels / 解释标签

Standard bilingual labels include:

- Validated coffee demand / 咖啡需求已验证
- Strong demand, high competition / 需求强但竞争高
- Unvalidated coffee demand / 咖啡需求未验证
- Infrastructure-rich but coffee-weak / 消费配套强但咖啡偏弱
- Low demand foundation / 需求基础不足
- Transit-supported demand / 交通放大型需求
- Oversaturated coffee cluster / 咖啡竞争过密

Labels summarize rule-based evidence and never replace the underlying feature values.

## Limitations / 方法边界

- Candidate sites are manually selected and do not represent exhaustive city coverage.
- POI results depend on 高德 coverage, keyword design, geocoding, and candidate-point quality.
- No rent, frontage, visibility, store size, lease term, operating cost, or actual store-performance data is included.
- Scores support within-city prioritization, not absolute cross-city investment ranking.
- Thresholds and caps are documented business assumptions rather than statistically trained parameters.
- Manual review remains mandatory.

## Historical Note

An earlier pandas/CSV methodology remains visible in the ticket history for migration context; V2 is the current portfolio method.

## Future Advisory Layer

A future V2 agent should consume verified evidence read-only, preserve feature provenance, cite limitations, and avoid autonomous database or scoring changes.
