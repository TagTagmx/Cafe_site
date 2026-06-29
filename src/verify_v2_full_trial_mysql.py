"""Verify V2-T5 MySQL integrity and exact feature parity with pandas."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_CHECKS_PATH = PROJECT_ROOT / "sql" / "verify_v2_t5_full_trial.sql"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.load_v2_full_trial_mysql import EXPECTED_COUNTS, connect_mysql
from src.prepare_v2_full_trial import build_full_trial
from src.score_v2_sites import COUNT_COLUMNS


KEY_COLUMNS = ["city_code", "site_code"]
PARITY_COLUMNS = [
    "city_name",
    "site_name",
    "district",
    *COUNT_COLUMNS,
    "nearest_direct_coffee_distance_m",
]


def compare_feature_frames(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
) -> list[str]:
    """Return human-readable parity differences; an empty list means exact parity."""
    expected_indexed = expected.set_index(KEY_COLUMNS).sort_index()
    actual_indexed = actual.set_index(KEY_COLUMNS).sort_index()
    differences: list[str] = []
    missing = expected_indexed.index.difference(actual_indexed.index)
    extra = actual_indexed.index.difference(expected_indexed.index)
    if len(missing):
        differences.append(f"missing SQL sites: {list(missing)}")
    if len(extra):
        differences.append(f"unexpected SQL sites: {list(extra)}")
    common = expected_indexed.index.intersection(actual_indexed.index)
    for key in common:
        for column in PARITY_COLUMNS:
            expected_value = expected_indexed.loc[key, column]
            actual_value = actual_indexed.loc[key, column]
            if pd.isna(expected_value) and pd.isna(actual_value):
                continue
            if str(expected_value) != str(actual_value):
                if column in COUNT_COLUMNS or column == "nearest_direct_coffee_distance_m":
                    expected_number = pd.to_numeric(expected_value, errors="coerce")
                    actual_number = pd.to_numeric(actual_value, errors="coerce")
                    if (
                        pd.notna(expected_number)
                        and pd.notna(actual_number)
                        and float(expected_number) == float(actual_number)
                    ):
                        continue
                differences.append(
                    f"{key} {column}: pandas={expected_value!r}, mysql={actual_value!r}"
                )
    return differences


def _scalar(cursor: object, query: str) -> int:
    cursor.execute(query)
    return int(cursor.fetchone()[0])


def run_named_sql_checks(connection: object, path: Path = SQL_CHECKS_PATH) -> int:
    """Execute the committed read-only SQL checks and require every result to pass."""
    text = path.read_text(encoding="utf-8-sig")
    statements: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("--"):
            continue
        current.append(line)
        if line.rstrip().endswith(";"):
            statements.append("\n".join(current).strip().rstrip(";"))
            current = []
    if any(part.strip() for part in current):
        statements.append("\n".join(current).strip())

    results: list[tuple[str, str]] = []
    cursor = connection.cursor()
    try:
        for statement in statements:
            if not statement:
                continue
            cursor.execute(statement)
            row = cursor.fetchone()
            if row is None or len(row) != 2:
                raise RuntimeError("Each V2-T5 SQL check must return check_name/result")
            results.append((str(row[0]), str(row[1])))
    finally:
        cursor.close()
    failures = [name for name, result in results if result != "PASS"]
    if failures:
        raise RuntimeError(f"Named SQL checks failed: {', '.join(failures)}")
    return len(results)


def verify_mysql(connection: object) -> tuple[dict[str, int], int]:
    checks = {
        "cities": "SELECT COUNT(*) FROM cities",
        "candidate_sites": "SELECT COUNT(*) FROM candidate_sites",
        "pois": "SELECT COUNT(*) FROM pois",
        "poi_keywords": "SELECT COUNT(*) FROM poi_keywords",
        "poi_category_rules": "SELECT COUNT(*) FROM poi_category_rules",
        "poi_observations": "SELECT COUNT(*) FROM poi_observations",
        "site_poi_relationships": "SELECT COUNT(*) FROM site_poi_relationships",
    }
    cursor = connection.cursor(dictionary=True)
    plain_cursor = connection.cursor()
    try:
        counts = {name: _scalar(plain_cursor, query) for name, query in checks.items()}
        for name, expected in EXPECTED_COUNTS.items():
            if counts[name] != expected:
                raise RuntimeError(f"{name}: expected {expected}, got {counts[name]}")

        integrity_queries = {
            "unique_relationship_pairs": """
                SELECT COUNT(*) FROM (
                    SELECT site_id, poi_clean_id FROM poi_observations
                    GROUP BY site_id, poi_clean_id
                ) pairs
            """,
            "orphan_observations": """
                SELECT COUNT(*) FROM poi_observations o
                LEFT JOIN candidate_sites s ON s.site_id = o.site_id
                LEFT JOIN pois p ON p.poi_clean_id = o.poi_clean_id
                LEFT JOIN poi_keywords k ON k.keyword_id = o.keyword_id
                WHERE s.site_id IS NULL OR p.poi_clean_id IS NULL OR k.keyword_id IS NULL
            """,
            "cross_city_relationships": """
                SELECT COUNT(*) FROM site_poi_relationships r
                JOIN candidate_sites s ON s.site_id = r.site_id
                JOIN pois p ON p.poi_clean_id = r.poi_clean_id
                WHERE s.city_id <> p.city_id
            """,
            "invalid_radius_distance": """
                SELECT COUNT(*) FROM poi_observations
                WHERE search_radius_m NOT IN (300, 800, 1500)
                   OR observed_distance_m > search_radius_m
            """,
            "invalid_distance_band": """
                SELECT COUNT(*) FROM site_poi_relationships
                WHERE distance_band <> CASE
                    WHEN distance_m <= 300 THEN 'within_300m'
                    WHEN distance_m <= 800 THEN 'within_800m'
                    ELSE 'within_1500m' END
            """,
            "category_rule_mismatches": """
                SELECT COUNT(*) FROM site_poi_relationships r
                JOIN poi_category_rules cr ON cr.rule_id = r.resolution_rule_id
                WHERE r.resolved_core_category <> cr.core_category
                   OR r.resolved_sub_category <> cr.sub_category
            """,
        }
        integrity = {
            name: _scalar(plain_cursor, query)
            for name, query in integrity_queries.items()
        }
        if integrity["unique_relationship_pairs"] != EXPECTED_COUNTS[
            "site_poi_relationships"
        ]:
            raise RuntimeError("Unique observation pairs do not match relationships")
        for name, count in integrity.items():
            if name != "unique_relationship_pairs" and count != 0:
                raise RuntimeError(f"{name}: expected 0, got {count}")

        cursor.execute("SELECT * FROM v_site_feature_counts ORDER BY city_code, site_code")
        actual_features = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
        expected_features, _ = build_full_trial()
        differences = compare_feature_frames(expected_features, actual_features)
        if differences:
            preview = "\n".join(differences[:20])
            raise RuntimeError(f"Feature parity failed:\n{preview}")
        sql_check_count = run_named_sql_checks(connection)
        return counts, sql_check_count
    finally:
        cursor.close()
        plain_cursor.close()


def main() -> None:
    connection = connect_mysql()
    try:
        counts, sql_check_count = verify_mysql(connection)
    finally:
        connection.close()
    print(
        "PASS: MySQL integrity and pandas feature parity verified: "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
        + f", named_sql_checks={sql_check_count}"
    )


if __name__ == "__main__":
    main()
