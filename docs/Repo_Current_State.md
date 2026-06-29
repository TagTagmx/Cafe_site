# Repo Current State

Last updated: 2026-06-29

## Final Project Status

`jiangsu-site-rank` is complete for the current portfolio scope. Cafe Site V2 is the main portfolio version:

- MySQL-backed relational storage for sites, POIs, observations, category rules, and deterministic site–POI relationships.
- SQL raw feature and diagnostic views.
- Python scoring, interactions, explanations, exports, and exact pandas parity verification.
- `app/v2_review_app.py` as the human review layer.

V2 is verified on MySQL Community Server 8.4.10 and is not a machine-learning model or an automatic leasing decision system. The earlier pandas/CSV implementation remains available for history and migration comparison.

## Completed Cafe Site V2

Cafe Site V2 is the completed database-backed architecture and the repository's primary GitHub-facing project.

| Ticket | Status |
| --- | --- |
| V2-T1 Documentation and scoring contract | Done |
| V2-T2 MySQL schema, category rules, and sample fixture | Done; MySQL 8.4 verified |
| V2-T3 Reproducible import and SQL feature views | Done; MySQL 8.4 verified |
| V2-T4 Python interaction scoring and explanations | Done; MySQL-backed run verified |
| V2-T5 Streamlit V2 review mode and full-data migration trial | Done |
| V2-T6 Final V2 wrap-up and portfolio documentation | Done |

V2 is explainable decision support, not machine learning or revenue prediction.

## What V2 Adds

- Normalized relational tables and auditable observation evidence.
- One deterministic relationship per unique site/POI pair.
- Foreign-key, city-consistency, distance-band, and category-resolution checks.
- Exact cell-level parity between the MySQL feature view and pandas reference features.
- A stronger evidence and provenance layer for a future read-only AI advisory agent.

## Files Of Interest

V2 implementation:

- `README.md`
- `app/v2_review_app.py`
- `src/prepare_v2_full_trial.py`
- `src/load_v2_full_trial_mysql.py`
- `src/verify_v2_full_trial_mysql.py`
- `src/score_v2_sites.py`
- `sql/schema.sql`
- `sql/views.sql`
- `sql/verify_v2_t5_full_trial.sql`
- `data/sample/v2/`
- `docs/methodology.md`
- `docs/Cafe_Site_V2_Implementation_Spec.md`
- `docs/Cafe_Site_V2_Database_Scoring_Plan.md`
- `sql/seed_category_rules.sql`
- `sql/sample_fixture.sql`
- `sql/verify_sample_fixture.sql`
- `src/import_v2_sample.py`
- `sql/verify_v2_t3.sql`
- `data/sample/v2/site_feature_counts.csv`
- `docs/V2_T4_Verification_Guide.md`
- `docs/V2_T5_MySQL_Verification_Guide.md`
- `sql/v2_t4_manual_review.sql`
- `sql/README.md`

Historical compatibility path:

- `app/streamlit_app.py`
- Legacy collection, cleaning, aggregation, and score scripts under `src/`
- Existing ignored/generated CSV artifacts under `data/raw/` and `data/processed/`

## MySQL Runtime Verification

Tickets 2 through 5 define and verify the MySQL 8 foundation, deterministic relationships, raw feature views, Python interactions and scoring, bilingual explanations, analytical CSV exports, and V2 review dashboard.

MySQL Community Server 8.4.10 is running locally at `127.0.0.1:3307`. The committed Ticket 3 CSV fixture loaded successfully in a separate fixture database: 38 observations derived 33 relationships, and all six `sql/verify_v2_t3.sql` checks passed.

The deterministic V2-T5 full trial was reset and loaded into `cafe_site_v2`. Verified counts are 2 cities, 15 sites, 6,866 POIs, 19 keywords, 19 category rules, 17,341 expanded observations, and 8,661 unique site/POI relationships. Foreign-key and semantic-integrity checks passed, all 15 named V2-T5 SQL checks passed, and every MySQL feature value matched the pandas output exactly. MySQL-backed scoring also wrote all 15 site outputs successfully. No scoring weights changed.

Verified commands:

```powershell
python src/load_v2_full_trial_mysql.py --create-database --reset
python src/verify_v2_full_trial_mysql.py
python src/score_v2_sites.py --output-dir data/exports/v2/full_trial/mysql_scored
python -m streamlit run app/v2_review_app.py
```

## Optional Next Phase

The V2/MySQL AI advisory layer is intentionally deferred. A future ticket may connect a read-only agent to verified features and provenance for scenario comparison and bilingual advisory notes. The existing V1 local rules-based site analyst is separate. Any future V2 agent must not silently change scoring, mutate the database, or make autonomous leasing decisions.

## Safety Notes

- Never commit `.env`, API keys, or database credentials.
- Keep `data/raw/` and `data/processed/` as ignored local/generated data.
- Do not commit full database dumps or production-sized exports.
- Only tiny synthetic fixtures and schema/verification SQL belong in the repository.
