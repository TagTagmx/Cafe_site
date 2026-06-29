# Cafe Site V2 Implementation Spec

## Purpose

This document records the approved V2 implementation plan for evolving the current CSV-based two-city Cafe Site portfolio project into an explainable MySQL-backed site-selection system.

V2 must preserve the current working CSV pipeline and Streamlit dashboard until each MySQL-backed component is independently verified.

V2 outputs are rule-based decision-support signals. They are not revenue predictions, leasing recommendations, or machine-learning forecasts.

## Current Baseline

The current project already supports:

- Manual candidate site inputs for Xuzhou and Nanjing.
- AMap geocoding and nearby POI collection in Python.
- POI cleaning and deduplication.
- CSV-based site metrics and scoring.
- A Streamlit dashboard with city switching.

The current pipeline remains the compatibility fallback during V2 work.

## Core V2 Business Rules

- Office demand should be strongly weighted toward the 300m range because white-collar coffee purchases are convenience-driven.
- Direct coffee stores have two roles: coffee-demand validation and competition pressure.
- Low direct coffee competition must not automatically be treated as opportunity.
- Tea, bakery, dessert, convenience-store, and restaurant activity does not independently prove coffee demand.
- Indirect consumption support must be gated by direct coffee validation.
- High market activity with low direct coffee validation should be identified as unvalidated coffee demand.
- Direct coffee presence at 1500m is district background, not core store-level pressure.
- Total POI density should be capped or lightly weighted so irrelevant density does not dominate results.
- Scores are rule-based decision-support signals, not revenue predictions.

## Provisional Scoring Contract

The V2 direct-coffee core signal is 300m-heavy:

```text
direct_coffee_core_raw =
    0.75 * direct_coffee_within_300m
  + 0.25 * direct_coffee_within_800m
```

This same raw direct-coffee signal may feed both coffee validation and competition pressure, but the score transformations must differ:

- `coffee_validation_score` rises from zero to moderate direct-coffee presence, then plateaus.
- `competition_pressure_score` continues increasing as direct-coffee density rises.

Office demand is also 300m-heavy:

```text
office_demand_raw =
    0.75 * office_within_300m
  + 0.25 * office_within_800m
```

Indirect support is gated by coffee validation:

```text
effective_indirect_support =
    indirect_support_score
  * coffee_validation_score
  / 100
```

The provisional `community_daily_score` weighting is:

```text
residential demand +35
coffee validation +20
effective indirect support +10
transit synergy +10
saturation risk -25
```

All thresholds, caps, and score transformations are provisional until tested against sample data and manual review.

Saturation risk is conditional on coffee-demand validation:

```text
if coffee_validation_score is low:
    saturation_risk = not_applicable or low_confidence
    primary_label = "Unvalidated coffee demand"
else:
    saturation_risk = competition_pressure adjusted by market_activity
```

Low competition plus low activity must not be rewarded as low saturation risk. High indirect support plus low direct-coffee validation must be interpreted conservatively as `Infrastructure-rich but coffee-weak`, not as an automatic opportunity.

Transit amplifies existing nearby demand and does not independently create coffee demand:

```text
transit_accessibility =
    normalized transit_within_800m

demand_strength =
    weighted office demand
  + weighted commercial/demand anchors
  + weighted coffee validation

transit_synergy =
    transit_accessibility * demand_strength
```

V2 does not require walking-network analysis, routing, or time-based accessibility.

## Distance-Band Semantics

All standard distance-band features are cumulative unless explicitly named otherwise:

- `within_300m` includes all POIs with `distance_m <= 300`.
- `within_800m` includes all POIs with `distance_m <= 800`.
- `within_1500m` includes all POIs with `distance_m <= 1500`.

Feature names should use forms such as `direct_coffee_within_300m`, `direct_coffee_within_800m`, `office_within_300m`, `office_within_800m`, and `transit_within_800m`. If an exclusive band is introduced later, its bounds must be explicit, for example `office_300m_to_800m`.

## Data Model Principles

`poi_observations` and `site_poi_relationships` must not be treated as two independent imported sources of truth.

V2 imports detailed POI observations first. Then it derives `site_poi_relationships` deterministically by grouping each unique `(site_id, poi_clean_id)` pair from observations.

SQL feature views must count unique site-POI relationships, not keyword matches or raw observation rows.

POI deduplication should remain simple and deterministic:

- Use the AMap POI ID as the primary deduplication key when available.
- Otherwise use normalized POI name, rounded latitude/longitude, and city as the fallback key.
- Fuzzy matching, coordinate clustering, and advanced duplicate resolution are future improvements, not V2 requirements.

A POI may retain multiple descriptive meanings, but it must not double-count inside the same core scoring feature. Core scoring category assignment must be deterministic and auditable, with more specific business meanings taking priority:

1. `direct_coffee`
2. `indirect_competitor`
3. `demand_anchor`
4. `transit`
5. `other` / `generic_commercial`

`core_category` controls this broad conflict priority. `sub_category` supplies the specific business meaning used for feature columns, including `office`, `commercial`, `residential`, `education`, `hotel`, `tea_drink`, `bakery`, and `convenience_store`.

The deterministic result is stored on each derived site-POI relationship as `resolved_core_category` and `resolved_sub_category`. SQL feature views aggregate these resolved fields and do not repeat category conflict resolution.

For example, Starbucks resolves to `direct_coffee` for coffee validation and must not also inflate that same core feature through generic commercial activity. A POI must not double-count inside one core feature, while its original rule matches and other descriptive context may remain available for diagnostics and explanation.

## SQL And Python Responsibility Boundary

MySQL and SQL own:

- Raw imported POI observations.
- Deduplicated POIs.
- Deterministic site-POI relationships.
- Deterministic core category assignments.
- Cumulative distance bands.
- Raw, auditable feature counts.
- Diagnostic views or equivalent manual-check outputs.

Python owns:

- Score normalization.
- Coffee-validation curves.
- Competition-pressure transformations.
- Saturation-risk logic.
- Indirect-support gating.
- Transit-synergy calculation.
- Final score calculation.
- Explanation labels.
- Export-ready scoring tables.

SQL feature views aggregate `site_poi_relationships.resolved_core_category` and `resolved_sub_category` into raw counts. They must not re-run category conflict resolution or embed validation plateaus, saturation-risk formulas, final score normalization, explanation labels, or other final business scoring transformations.

## Explanation Label Vocabulary

V2 scoring outputs use the following standard explanation labels:

| English | Chinese |
| --- | --- |
| Validated coffee demand | 咖啡需求已验证 |
| Strong demand, high competition | 需求强但竞争高 |
| Unvalidated coffee demand | 咖啡需求未验证 |
| Infrastructure-rich but coffee-weak | 消费配套强但咖啡偏弱 |
| Low demand foundation | 需求基础不足 |
| Transit-supported demand | 交通放大型需求 |
| Oversaturated coffee cluster | 咖啡竞争过密 |

These labels are explanation aids derived from rule-based scoring outputs. They are not separate machine-learning predictions.

## Preflight Clarification

Before implementation begins, the team must treat all documented thresholds, caps, weights, and category rules as provisional business assumptions rather than statistically validated claims.

V2 is an explainable decision-support model. It is not a revenue prediction model and must not be presented as one.

Real calibration would require evidence such as rent, store sales, measured foot traffic, store survival, or operator-level performance data. Collecting and modeling those data are outside the current project scope.

The current roadmap also excludes machine learning, revenue prediction, city-specific threshold calibration, PostGIS, Airflow, Docker, cloud deployment, real-time data pipelines, complex fuzzy matching, walking-route analysis, user login, and agent integration. These are future considerations only if later evidence establishes a clear need.

## Six-Ticket Roadmap

### 1. Documentation And Scoring Contract

**Objective:** Align the repo around V2 as a future MySQL-backed scoring system while preserving the current CSV pipeline and Streamlit dashboard.

**Main Deliverables:**

- V2 implementation spec covering architecture, feature definitions, provisional formulas, distance-band semantics, scoring boundaries, and explanation labels.
- Documentation cleanup for stale or conflicting notes around Nanjing, database scope, and current versus future behavior.
- Explicit rule that all scores are rule-based decision-support signals, not revenue predictions or ML forecasts.
- Clear scoring distinction between coffee validation and competition pressure.
- Saturation-risk contract that returns an unvalidated-demand interpretation when direct coffee demand is not validated.
- Explicit SQL/Python responsibility boundary.
- Simple transit-synergy definition and standard bilingual explanation-label vocabulary.

**Out Of Scope:**

- Code changes.
- SQL execution.
- Data migration.
- Streamlit changes.
- Final threshold validation.

**Automated Checks:**

- Markdown/path sanity where practical.
- Confirm no app, source, SQL, or data files changed.

**Manual Verification:**

- Confirm docs distinguish current CSV behavior from future V2 behavior.
- Confirm Chinese text displays correctly.
- Confirm provisional formulas and thresholds are marked provisional.
- Confirm the saturation, transit, responsibility-boundary, and explanation-label contracts are internally consistent.

**Acceptance Criteria:**

- A new implementer can understand the V2 contract without touching the working CSV pipeline.
- Current project state, V2 direction, and unresolved scoring decisions are not contradictory.
- Thresholds are clearly provisional, and the documentation states which missing real-world data would be required for calibration.
- Low coffee validation cannot be interpreted as low saturation risk or automatic opportunity.
- SQL/Python ownership, transit synergy, and the explanation-label vocabulary are explicit.

### 2. MySQL Schema, Category Rules, And Small Sample Fixture

**Objective:** Add a minimal relational model and tiny sample dataset before any full POI migration.

**Implementation Status:** Implemented as MySQL 8 SQL artifacts in `sql/`. Runtime loading remains to be verified in an environment with a MySQL client.

**Main Deliverables:**

- MySQL schema for cities, candidate sites, POIs, POI keywords, category rules, POI observations, and derived site-POI relationships.
- Primary keys, foreign keys, uniqueness constraints, and indexes for candidate/site/POI lookup and feature aggregation.
- Imported `poi_observations` as detailed search-result evidence.
- Deterministically derived `site_poi_relationships` grouped from unique `(site_id, poi_clean_id)` pairs, with `resolved_core_category` and `resolved_sub_category` stored on each relationship.
- Category rule seed mapping current keyword buckets into V2 categories such as direct coffee, indirect support, office, commercial, residential, education, hotel, and transit.
- Deterministic core category priority: direct coffee, indirect competitor, demand anchor, transit, then other/generic commercial.
- Explicit category semantics: `core_category` controls broad conflict priority, while `sub_category` drives specific raw feature columns.
- Simple deduplication using AMap POI ID when available and normalized name plus rounded coordinates plus city otherwise.
- Tiny GitHub-safe sample fixture covering at least two sites, shared POIs, cumulative distance bands, and the required edge cases.
- Cumulative feature naming such as `direct_coffee_within_300m`, with explicit names for any exclusive diagnostic bands.

**Out Of Scope:**

- Full raw/processed data import.
- New AMap API calls.
- Streamlit integration.
- Final business threshold tuning.

**Automated Checks:**

- Load schema and sample fixture into a local MySQL database.
- Verify primary key, foreign key, and uniqueness rules.
- Query row counts for all sample tables.
- Verify derived `site_poi_relationships` count equals unique site-POI pairs from observations.
- Verify duplicate raw observations do not inflate derived relationships or core features.

**Manual Verification:**

- Confirm one POI can relate to multiple candidate sites.
- Confirm repeated keyword/radius observations collapse to one site-POI relationship.
- Confirm sample rows cover:
  - Moderate direct coffee, which should validate coffee demand.
  - Zero or very low direct coffee plus low activity, which should indicate unvalidated demand or a weak foundation.
  - High indirect competition plus low direct coffee, which should indicate infrastructure-rich but coffee-weak rather than an automatic opportunity.
  - High direct coffee plus high activity, which should represent a mature market with competition pressure.
  - High direct coffee plus low activity, which should expose possible saturation risk.
  - Transit-heavy plus weak demand, where transit must not independently create a strong opportunity.
  - A POI matching conflicting categories.
  - A repeated raw POI observation that must not inflate final features.
  - A zero-nearby-POI site that must be handled safely and explainably.
- Confirm the conflicting POI resolves to one deterministic core scoring category while retaining descriptive context.
- Confirm sample data contains no credentials or large raw API dumps.

**Acceptance Criteria:**

- The sample database can be rebuilt from committed schema and small fixtures.
- The relational model preserves traceability from candidate site to observation evidence to one deterministic site-POI relationship per site and POI.
- Category conflicts are resolved consistently before feature counting.
- Each derived relationship stores its resolved core and sub-category, while source matches remain traceable for diagnostics.
- Required edge cases, duplicate handling, and cumulative distance-band naming are represented in the fixture.

### 3. Reproducible Python Import And SQL Feature Views

**Objective:** Create a reproducible import path from sample CSVs into MySQL and SQL views that output base features from unique site-POI relationships.

**Implementation Status:** Implemented at repository-artifact level. The committed CSV fixture passes static structure/reference/count checks. Runtime import and view verification remain pending in an environment with MySQL 8.

**Main Deliverables:**

- Python import script for sample candidates, POIs, keywords, and observations.
- Deterministic relationship-build step that groups observations into `site_poi_relationships`.
- SQL views:
  - `v_site_poi_base`
  - `v_site_feature_counts`
  - diagnostic view or equivalent manual-check output, which may include explicitly named exclusive distance bands.
- Raw base feature columns for cumulative 300m, 800m, and 1500m counts, including direct coffee, indirect support, office, commercial, residential, education, hotel, transit, total POI activity, and nearest direct coffee distance.
- SQL counting logic based on `resolved_core_category` and `resolved_sub_category` from unique site-POI relationships.

**Out Of Scope:**

- Scoring logic.
- Normalization.
- Validation plateaus, saturation formulas, final-score transformations, and explanation labels.
- Streamlit integration.
- Full data migration.

**Automated Checks:**

- Python compile/import smoke check.
- Import script row-count validation.
- Derived relationship row count matches unique `(site_id, poi_clean_id)` pairs.
- SQL view queries return one row per sample candidate.
- Required feature columns are present.
- Repeated keyword matches do not inflate core feature counts.

**Manual Verification:**

- Hand-check sample count outputs for at least two sites.
- Confirm cumulative-radius semantics are correct.
- Confirm category-priority handling prevents double-counting within a core feature.
- Confirm SQL views consume stored resolved category fields rather than re-running conflict resolution.
- Confirm 1500m direct coffee is available as background context but not treated as core pressure in SQL.

**Acceptance Criteria:**

- A clean local sample DB can be populated and queried reproducibly.
- SQL produces traceable base features from deduplicated site-POI relationships.
- SQL views output raw auditable counts and diagnostic evidence only.
- SQL does not re-run category conflict resolution or embed validation plateaus, saturation-risk formulas, final score normalization, explanation labels, or other final business scoring transformations.

### 4. Python Interaction Features, Scoring, Explanations, Tests, And Exports

**Objective:** Build the V2 Python scoring layer on top of SQL base features.

**Implementation Status:** Implemented at repository-artifact level in `src/score_v2_sites.py`, with an offline feature-view fixture, deterministic tests, CSV exports, and a beginner verification guide. MySQL-backed execution remains pending until Tickets 2 and 3 are runtime-verified.

**Implemented Provisional Assumptions:**

- Fixed caps are used instead of candidate-set-relative normalization so adding a candidate does not change every existing score.
- Direct coffee and office raw signals use the documented 75% 300m / 25% 800m weighting. Direct coffee at 1500m remains context only.
- Coffee validation rises to 45 at a raw direct signal of 1, reaches 100 at 3, and then plateaus.
- Competition pressure rises linearly to its cap at a raw direct signal of 6.
- Indirect support is capped at a raw signal of 4 and multiplied by coffee validation.
- Saturation is low-confidence below a coffee-validation score of 40. Otherwise, market activity can reduce, but not remove, direct-competition risk.
- POI density is capped at a weighted raw count of 10 and has only a limited contribution through market activity.
- `community_daily_score` implements the documented residential +35%, validation +20%, effective indirect +10%, transit synergy +10%, and saturation risk -25% formula.
- The balanced `site_score` uses demand anchors +30%, coffee validation +25%, effective indirect support +10%, transit synergy +10%, market activity +10%, and saturation risk -15%.
- Low saturation is never added as a positive bonus; this prevents low competition from becoming an automatic opportunity.

**Main Deliverables:**

- Python scorer that reads SQL base-feature output and writes V2 analytical exports.
- Separate score transformations for validation and pressure:
  - `coffee_validation_score` increases from zero to moderate direct-coffee presence, then plateaus.
  - `competition_pressure_score` increases with direct-coffee density and does not plateau at moderate presence.
- Interaction features:
  - `office_demand_score`
  - `coffee_validation_score`
  - `competition_pressure_score`
  - `saturation_risk_score`
  - `indirect_support_score`
  - `effective_indirect_support_score`
  - `transit_demand_synergy_score`
  - `market_activity_score`
  - `poi_density_capped_score`
  - `unvalidated_coffee_demand_risk_score`
- Scenario scores, including `community_daily_score`.
- Standard English and Chinese explanation labels defined by the V2 vocabulary.
- CSV exports for base features, scores, and explanations.

**Out Of Scope:**

- Replacing current `src/score_sites.py`.
- Changing current CSV score outputs.
- Revenue prediction or ML modeling.
- Finalizing unvalidated thresholds as economic truth.

**Automated Checks:**

- Unit or fixture checks for:
  - 300m-heavy office demand.
  - shared 300m-heavy raw direct-coffee signal.
  - validation plateau behavior.
  - pressure continuing to rise with density.
  - indirect support gating.
  - low validation producing unvalidated demand with saturation not applicable or low confidence.
  - high indirect support plus low direct coffee producing infrastructure-rich but coffee-weak.
  - transit-heavy plus weak demand not producing a strong opportunity.
  - zero-variance normalization.
  - zero nearby POIs.
  - score bounds.
  - high activity plus low validation labeling.
- Python compile check.
- Export header and row-count checks.

**Manual Verification:**

- Confirm indirect support cannot create coffee opportunity without coffee validation.
- Confirm low direct coffee presence is labeled unvalidated demand, not opportunity.
- Confirm low direct coffee validation is not labeled as low saturation risk.
- Confirm high indirect support with low direct coffee is labeled infrastructure-rich but coffee-weak.
- Confirm dense direct coffee can show both strong validation and high pressure.
- Confirm total POI density is capped or lightly weighted.
- Review sample explanations for business readability.

**Acceptance Criteria:**

- V2 scoring is reproducible on the sample DB.
- Coffee validation and competition pressure are behaviorally distinct even when derived from the same core direct-coffee raw signal.
- Python owns all normalization, interaction transformations, saturation logic, final scoring, and explanation labels.
- Low coffee validation produces an unvalidated-demand interpretation; infrastructure-rich but coffee-weak remains a distinct conservative label or flag.
- Raw, normalized, interaction, scenario, and explanation outputs are auditable.
- Current CSV scoring remains untouched.

### 5. Streamlit V2 Review Mode And Full-Data Migration Trial

**Objective:** Add a V2 review surface and test full current data migration only after sample scoring is verified.

**Main Deliverables:**

- Streamlit V2 review mode or separate V2 app entrypoint that does not break the existing CSV dashboard.
- V2 display for base evidence, normalized components, interaction features, scenario scores, explanation labels, and comparison notes.
- Full-data migration trial using existing generated Xuzhou/Nanjing processed artifacts into MySQL.
- Traceability/comparison notes between current CSV v2 scores and new MySQL-backed V2 outputs; exact score parity is not required.
- Migration validation that feature counts are based on unique site-POI relationships, not keyword-match volume.

**Out Of Scope:**

- Removing or replacing the existing dashboard.
- New AMap collection.
- Adding new cities.
- Authentication or deployment.
- Committing full raw data or full database dumps.

**Automated Checks:**

- Python compile check.
- Streamlit import/smoke check where practical.
- Migration row counts match source CSV counts.
- Derived relationship counts match unique site-POI pairs.
- No foreign key violations.
- V2 exports remain bounded and have required columns.

**Manual Verification:**

- Confirm current Xuzhou/Nanjing CSV dashboard still loads.
- Confirm V2 mode is clearly labeled as V2/sample or V2/migrated review.
- Spot-check Xuzhou top sites, Nanjing Xinjiekou over-saturation, and Nanjing Xianlin sparse-POI watchpoint.
- Confirm city switching does not mix current CSV and V2 outputs.
- Confirm repeated keyword hits do not visibly inflate feature evidence.
- Review and explain ranking changes using documented V2 relationship counting and scoring logic.

**Acceptance Criteria:**

- V2 can be reviewed in Streamlit without disrupting the current portfolio dashboard.
- Full current data can be migrated locally and compared against the CSV baseline.
- Raw POI relationship counts and feature-count differences are auditable and explainable.
- Score and ranking differences caused by documented V2 logic are acceptable; the goal is traceable difference, not identical scores.
- Ranking changes are reviewed and explained rather than automatically treated as defects.

### 6. Backup Workflow And Portfolio Documentation

**Objective:** Package the verified V2 workflow safely for portfolio review.

**Main Deliverables:**

- Backup/export documentation for schema export, optional tiny sample dump, analytical CSV exports, and local-only full DB dumps.
- GitHub-safe handling rules for `.env`, credentials, raw API data, processed data, and database backups.
- Updated README, repo state, methodology, portfolio summary, and manual verification guide.
- Final V2 limitations and unresolved decisions list.
- Documentation that `poi_observations` are imported evidence and `site_poi_relationships` are derived deterministic relationships.
- Documentation preserving provisional thresholds, conditional saturation semantics, cumulative distance bands, category conflict resolution, SQL/Python ownership, transit synergy, explanation labels, and traceable-difference expectations.

**Out Of Scope:**

- Claiming revenue prediction.
- Claiming machine-learning forecasting.
- Publishing credentials, full raw API data, or full database dumps.
- Hiding known limitations such as rent, lease, frontage, visibility, and operator cost gaps.

**Automated Checks:**

- Confirm ignored paths cover `.env`, raw data, processed data, and local DB dump outputs.
- Markdown/path sanity where practical.
- Python compile check if any code changed in prior tickets.

**Manual Verification:**

- Confirm portfolio docs accurately describe current CSV baseline and V2 MySQL workflow.
- Confirm Chinese and English reviewer-facing text is readable.
- Confirm no secrets or large generated artifacts appear in `git status`.
- Confirm V2 formulas and thresholds are labeled provisional where not validated.
- Confirm docs explain relationship-derived feature counting and category-priority conflict handling.
- Confirm docs preserve the saturation, distance-band, responsibility-boundary, transit, label, deduplication, and migration-parity limitations.

**Acceptance Criteria:**

- The repo is safe to share.
- Reviewers can understand the current working CSV project, the verified V2 architecture, and the remaining unresolved business/model decisions.
- Assumptions and limitations remain visible, including the absence of real calibration data and the non-predictive meaning of explanation labels.
- The current CSV pipeline remains available as the compatibility fallback.

## First Implementation Step

Tickets 1 through 4 are complete at the repository-artifact level. Ticket 5 is in progress with a separate Streamlit review surface and a full-data CSV dry-migration trial. MySQL fixture/view verification, MySQL full-data parity, and final manual review remain required before Ticket 5 can be marked done.

No MySQL schema, import scripts, scoring code, Streamlit V2 mode, or migration work should begin until the V2 contract is documented and reviewed.
