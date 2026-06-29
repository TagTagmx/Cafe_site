# Cafe Site V2 SQL

These files implement the MySQL 8 relational model, synthetic fixtures, deterministic relationship derivation, raw feature views, and V2-T5 full-trial verification. Scoring remains in Python.

## Ticket 5: Full-Trial Load And Feature Parity

The deterministic loader prepares the current 徐州/南京 processed data, resets
the V2 tables when requested, loads the relational evidence, derives unique
site/POI relationships, and creates the feature views:

```bash
python src/load_v2_full_trial_mysql.py --validate-only
python src/load_v2_full_trial_mysql.py --create-database --reset
python src/verify_v2_full_trial_mysql.py
```

Use `--reset` without `--create-database` when `MYSQL_DATABASE` already exists.
The Python verifier checks exact table counts, referential and semantic
integrity, and cell-level parity between MySQL `v_site_feature_counts` and the
pandas full-trial output.

The optional read-only SQL checks are:

```bash
mysql -u <user> -p <database> < sql/verify_v2_t5_full_trial.sql
```

All named checks must return `PASS`. See
`docs/V2_T5_MySQL_Verification_Guide.md` for the complete runbook and expected
counts.

## Ticket 4: Python Scoring And Exports

After Ticket 3 verification passes, run the scorer against MySQL:

```bash
python src/score_v2_sites.py
```

For offline verification with the committed feature-view fixture:

```bash
python src/score_v2_sites.py \
  --input-csv data/sample/v2/site_feature_counts.csv \
  --output-dir data/exports/v2
```

Run the eight read-only evidence queries in `sql/v2_t4_manual_review.sql`. Final scores remain in the CSV exports because the documented SQL/Python boundary assigns business transformations to Python.

## Ticket 3: CSV Import And Feature Views

Create an empty local database, copy the `MYSQL_*` values from `.env.example` into `.env`, and run:

```bash
mysql -u <user> -p <database> < sql/schema.sql
python src/import_v2_sample.py
mysql -u <user> -p <database> < sql/views.sql
mysql -u <user> -p <database> < sql/verify_v2_t3.sql
```

The importer intentionally requires empty V2 tables. It loads the committed files in `data/sample/v2/`, derives `site_poi_relationships` in the same transaction, and rolls back if expected counts fail. Validate CSV structure without MySQL using:

```bash
python src/import_v2_sample.py --validate-only
```

`sql/verify_v2_t3.sql` is read-only. All six named checks should return `PASS`; its final query displays the raw feature rows for manual inspection.

Do not run `seed_category_rules.sql` or `sample_fixture.sql` before the CSV importer because those Ticket 2 files contain the same logical fixture.

## Ticket 2: SQL-Only Fixture

The original SQL-only verification path remains available:

```bash
mysql -u <user> -p <database> < sql/schema.sql
mysql -u <user> -p <database> < sql/seed_category_rules.sql
mysql -u <user> -p <database> < sql/sample_fixture.sql
mysql -u <user> -p <database> < sql/verify_sample_fixture.sql
```

The Ticket 2 verification file is read-only. Its named checks should return `PASS`.

## Expected Fixture Counts

| Table | Rows |
| --- | ---: |
| `cities` | 1 |
| `candidate_sites` | 9 |
| `pois` | 17 |
| `poi_keywords` | 19 |
| `poi_category_rules` | 19 |
| `poi_observations` | 38 |
| `site_poi_relationships` | 33 |

The fixture covers moderate direct coffee, weak demand foundation, high indirect support with low direct coffee, mature high-activity competition, possible saturation, transit without supporting demand, category conflict, repeated observations, shared POIs, fallback deduplication, and a zero-nearby-POI site.

`site_poi_relationships` is derived from unique `(site_id, poi_clean_id)` observation pairs. Its resolved category fields use the documented priority order; original observation evidence remains available for diagnostics.

`v_site_feature_counts` exposes cumulative raw counts at 300m, 800m, and 1500m. It counts stored relationships, not observation rows. Normalization, saturation logic, scoring, and explanation labels remain Python responsibilities for Ticket 4.
