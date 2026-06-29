# V2-T5 MySQL Full-Trial Verification

This runbook loads the deterministic 徐州/南京 full trial into MySQL 8 and
compares MySQL feature views with the existing pandas output. It does not change
V1 behavior or V2 scoring weights.

Status: verified on MySQL Community Server 8.4.10. The completed run passed all
15 named SQL checks and exact pandas/MySQL feature parity for all 15 sites.

## Prerequisites

- MySQL 8.0 or newer.
- `mysql-connector-python` from `requirements.txt`.
- Current local processed artifacts under `data/processed/`.
- `.env` values:

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=cafe_site_v2
MYSQL_USER=your_local_user
MYSQL_PASSWORD=your_local_password
```

The database must be dedicated to this local V2 trial. `--reset` drops all V2
views and tables named in `sql/reset_v2.sql`.

## 1. Validate Prepared Rows Without MySQL

```powershell
python src/load_v2_full_trial_mysql.py --validate-only
```

Expected result:

```text
cities=2
candidate_sites=15
pois=6866
poi_keywords=19
poi_category_rules=19
poi_observations=17341
```

The 17,341 observation records are deterministic expansions of 16,127 cleaned
observation rows by keyword ID. They derive 8,661 unique site/POI relationships.

## 2. Create, Reset, And Load

If the configured user may create databases:

```powershell
python src/load_v2_full_trial_mysql.py --create-database --reset
```

If the database already exists:

```powershell
python src/load_v2_full_trial_mysql.py --reset
```

The command executes `sql/reset_v2.sql`, `sql/schema.sql`, loads all rows in one
data transaction, derives `site_poi_relationships`, and executes `sql/views.sql`.
Without `--reset`, the loader requires every V2 table to be empty.

## 3. Run Automated Integrity And Feature-Parity Verification

```powershell
python src/verify_v2_full_trial_mysql.py
```

This command fails with a nonzero exit code unless all of the following hold:

- Exact table counts match the prepared source.
- Relationships equal unique `(site_id, poi_clean_id)` observation pairs.
- No observation foreign-key references are missing.
- Sites and related POIs belong to the same city.
- Observation radii and distances are valid.
- Relationship distance bands match distance values.
- Resolved categories match their selected category rules.
- Every identifier, cumulative feature count, and nearest-coffee distance from
  `v_site_feature_counts` exactly matches `build_full_trial()` in pandas.

Expected successful summary:

```text
cities=2
candidate_sites=15
pois=6866
poi_keywords=19
poi_category_rules=19
poi_observations=17341
site_poi_relationships=8661
```

## 4. Run Read-Only SQL Checks

When the MySQL command-line client is available:

```powershell
mysql -u <user> -p <database> < sql/verify_v2_t5_full_trial.sql
```

Every named result must be `PASS`. These SQL checks cover exact counts, orphan
references, city consistency, radius/distance constraints, relationship bands,
resolved categories, view row counts, and cumulative radius monotonicity.
Cross-engine cell-level parity remains the responsibility of
`src/verify_v2_full_trial_mysql.py`.

## 5. Score And Review

After verification passes:

```powershell
python src/score_v2_sites.py --output-dir data/exports/v2/full_trial/mysql_scored
python -m streamlit run app/v2_review_app.py
```

V2-T5 was marked Done only after an actual MySQL 8.4 run of steps 2 through 4
passed. Offline validation alone is not sufficient when repeating this workflow.
