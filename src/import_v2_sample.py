"""Import the Cafe Site V2 synthetic CSV fixture into a clean MySQL 8 database."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any, Iterable, Sequence

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_DIR = ROOT / "data" / "sample" / "v2"

FILE_COLUMNS = {
    "candidate_sites.csv": (
        "city_code", "city_name", "site_code", "site_name", "latitude",
        "longitude", "address", "district", "site_type_note",
    ),
    "pois.csv": (
        "poi_clean_id", "city_code", "amap_poi_id", "dedup_key",
        "dedup_method", "poi_name", "normalized_poi_name", "latitude",
        "longitude", "amap_type", "address",
    ),
    "poi_keywords.csv": (
        "keyword_id", "source_bucket", "keyword", "poi_type_hint", "description",
    ),
    "poi_category_rules.csv": (
        "rule_code", "keyword_id", "core_category", "sub_category", "priority",
        "business_meaning",
    ),
    "poi_observations.csv": (
        "source_observation_key", "site_code", "poi_clean_id", "keyword_id",
        "search_radius_m", "observed_distance_m", "collected_at",
    ),
}

EXPECTED_SAMPLE_COUNTS = {
    "candidate_sites.csv": 9,
    "pois.csv": 17,
    "poi_keywords.csv": 19,
    "poi_category_rules.csv": 19,
    "poi_observations.csv": 38,
}

RELATIONSHIP_INSERT_SQL = """
INSERT INTO site_poi_relationships (
    site_id, poi_clean_id, distance_m, distance_band,
    resolved_core_category, resolved_sub_category, resolution_rule_id
)
SELECT
    ranked.site_id,
    ranked.poi_clean_id,
    ranked.minimum_distance_m,
    CASE
        WHEN ranked.minimum_distance_m <= 300 THEN 'within_300m'
        WHEN ranked.minimum_distance_m <= 800 THEN 'within_800m'
        ELSE 'within_1500m'
    END,
    ranked.core_category,
    ranked.sub_category,
    ranked.rule_id
FROM (
    SELECT
        observations.site_id,
        observations.poi_clean_id,
        MIN(observations.observed_distance_m) OVER (
            PARTITION BY observations.site_id, observations.poi_clean_id
        ) AS minimum_distance_m,
        rules.rule_id,
        rules.core_category,
        rules.sub_category,
        ROW_NUMBER() OVER (
            PARTITION BY observations.site_id, observations.poi_clean_id
            ORDER BY rules.priority ASC, rules.rule_id ASC
        ) AS resolution_rank
    FROM poi_observations AS observations
    INNER JOIN poi_category_rules AS rules
        ON rules.keyword_id = observations.keyword_id
       AND rules.is_active = TRUE
) AS ranked
WHERE ranked.resolution_rank = 1
"""


def read_fixture(fixture_dir: Path) -> dict[str, list[dict[str, str]]]:
    """Read and validate the committed CSV fixture without connecting to MySQL."""
    fixture: dict[str, list[dict[str, str]]] = {}
    for filename, required_columns in FILE_COLUMNS.items():
        path = fixture_dir / filename
        if not path.is_file():
            raise ValueError(f"Missing fixture file: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = set(required_columns) - set(reader.fieldnames or ())
            if missing:
                raise ValueError(
                    f"{filename} is missing columns: {', '.join(sorted(missing))}"
                )
            rows = list(reader)
        if len(rows) != EXPECTED_SAMPLE_COUNTS[filename]:
            raise ValueError(
                f"{filename} has {len(rows)} rows; "
                f"expected {EXPECTED_SAMPLE_COUNTS[filename]}"
            )
        fixture[filename] = rows

    _validate_references(fixture)
    return fixture


def _validate_references(fixture: dict[str, list[dict[str, str]]]) -> None:
    _require_unique(fixture["candidate_sites.csv"], "site_code")
    _require_unique(fixture["pois.csv"], "poi_clean_id")
    _require_unique(fixture["pois.csv"], "dedup_key")
    _require_unique(fixture["poi_keywords.csv"], "keyword_id")
    _require_unique(fixture["poi_category_rules.csv"], "rule_code")
    _require_unique(fixture["poi_category_rules.csv"], "keyword_id")
    _require_unique(fixture["poi_observations.csv"], "source_observation_key")

    city_names: dict[str, str] = {}
    for row in fixture["candidate_sites.csv"]:
        existing_name = city_names.setdefault(row["city_code"], row["city_name"])
        if existing_name != row["city_name"]:
            raise ValueError(f"Inconsistent city_name for {row['city_code']}")

    site_codes = {row["site_code"] for row in fixture["candidate_sites.csv"]}
    poi_ids = {row["poi_clean_id"] for row in fixture["pois.csv"]}
    keyword_ids = {row["keyword_id"] for row in fixture["poi_keywords.csv"]}
    rule_keywords = {
        row["keyword_id"] for row in fixture["poi_category_rules.csv"]
    }
    if rule_keywords != keyword_ids:
        raise ValueError("Each sample keyword must have one category-rule mapping")

    unique_pairs: set[tuple[str, str]] = set()
    for row in fixture["poi_observations.csv"]:
        if row["site_code"] not in site_codes:
            raise ValueError(f"Unknown site_code: {row['site_code']}")
        if row["poi_clean_id"] not in poi_ids:
            raise ValueError(f"Unknown poi_clean_id: {row['poi_clean_id']}")
        if row["keyword_id"] not in keyword_ids:
            raise ValueError(f"Unknown keyword_id: {row['keyword_id']}")
        radius = int(row["search_radius_m"])
        distance = int(row["observed_distance_m"])
        if radius not in (300, 800, 1500) or distance > radius:
            raise ValueError(
                f"Invalid radius/distance for {row['source_observation_key']}"
            )
        unique_pairs.add((row["site_code"], row["poi_clean_id"]))

    if len(unique_pairs) != 33:
        raise ValueError(
            f"Fixture derives {len(unique_pairs)} site/POI pairs; expected 33"
        )


def _require_unique(rows: list[dict[str, str]], column: str) -> None:
    values = [row[column] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"Fixture column must be unique: {column}")


def _optional(value: str) -> str | None:
    value = value.strip()
    return value or None


def _executemany(cursor: Any, sql: str, rows: Iterable[Sequence[Any]]) -> None:
    cursor.executemany(sql, list(rows))


def import_fixture(connection: Any, fixture: dict[str, list[dict[str, str]]]) -> None:
    """Insert validated fixture rows and derive one relationship per site/POI."""
    cursor = connection.cursor()
    try:
        cities = {
            (row["city_code"], row["city_name"])
            for row in fixture["candidate_sites.csv"]
        }
        for city_code, city_name in sorted(cities):
            cursor.execute(
                """
                INSERT INTO cities (city_code, city_name)
                VALUES (%s, %s)
                """,
                (city_code, city_name),
            )

        _executemany(
            cursor,
            """
            INSERT INTO candidate_sites (
                city_id, site_code, site_name, latitude, longitude,
                address, district, site_type_note
            )
            SELECT city_id, %s, %s, %s, %s, %s, %s, %s
            FROM cities WHERE city_code = %s
            """,
            (
                (
                    row["site_code"], row["site_name"], row["latitude"],
                    row["longitude"], _optional(row["address"]),
                    _optional(row["district"]), _optional(row["site_type_note"]),
                    row["city_code"],
                )
                for row in fixture["candidate_sites.csv"]
            ),
        )
        _executemany(
            cursor,
            """
            INSERT INTO pois (
                poi_clean_id, city_id, amap_poi_id, dedup_key, dedup_method,
                poi_name, normalized_poi_name, latitude, longitude, amap_type, address
            )
            SELECT %s, city_id, %s, %s, %s, %s, %s, %s, %s, %s, %s
            FROM cities WHERE city_code = %s
            """,
            (
                (
                    row["poi_clean_id"], _optional(row["amap_poi_id"]),
                    row["dedup_key"], row["dedup_method"], row["poi_name"],
                    row["normalized_poi_name"], row["latitude"], row["longitude"],
                    _optional(row["amap_type"]), _optional(row["address"]),
                    row["city_code"],
                )
                for row in fixture["pois.csv"]
            ),
        )
        _executemany(
            cursor,
            """
            INSERT INTO poi_keywords (
                keyword_id, source_bucket, keyword, poi_type_hint, description
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (
                (
                    row["keyword_id"], row["source_bucket"], row["keyword"],
                    _optional(row["poi_type_hint"]), _optional(row["description"]),
                )
                for row in fixture["poi_keywords.csv"]
            ),
        )
        _executemany(
            cursor,
            """
            INSERT INTO poi_category_rules (
                rule_code, keyword_id, core_category, sub_category,
                priority, business_meaning
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                (
                    row["rule_code"], row["keyword_id"], row["core_category"],
                    row["sub_category"], int(row["priority"]),
                    row["business_meaning"],
                )
                for row in fixture["poi_category_rules.csv"]
            ),
        )
        _executemany(
            cursor,
            """
            INSERT INTO poi_observations (
                source_observation_key, site_id, poi_clean_id, keyword_id,
                search_radius_m, observed_distance_m, collected_at
            )
            SELECT %s, site_id, %s, %s, %s, %s, %s
            FROM candidate_sites WHERE site_code = %s
            """,
            (
                (
                    row["source_observation_key"], row["poi_clean_id"],
                    row["keyword_id"], int(row["search_radius_m"]),
                    int(row["observed_distance_m"]), _optional(row["collected_at"]),
                    row["site_code"],
                )
                for row in fixture["poi_observations.csv"]
            ),
        )
        cursor.execute(RELATIONSHIP_INSERT_SQL)
        _validate_database_counts(cursor)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def _validate_database_counts(cursor: Any) -> None:
    expected = {
        "cities": 1,
        "candidate_sites": 9,
        "pois": 17,
        "poi_keywords": 19,
        "poi_category_rules": 19,
        "poi_observations": 38,
        "site_poi_relationships": 33,
    }
    for table, expected_count in expected.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        actual_count = cursor.fetchone()[0]
        if actual_count != expected_count:
            raise RuntimeError(
                f"{table} has {actual_count} rows; expected {expected_count}"
            )

    cursor.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT site_id, poi_clean_id
            FROM poi_observations
            GROUP BY site_id, poi_clean_id
        ) AS unique_pairs
        """
    )
    if cursor.fetchone()[0] != expected["site_poi_relationships"]:
        raise RuntimeError(
            "Relationship count does not match unique site/POI observation pairs"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import the committed V2 fixture into an empty database that already "
            "contains sql/schema.sql."
        )
    )
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate fixture files and references without connecting to MySQL.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    fixture = read_fixture(args.fixture_dir)
    if args.validate_only:
        print("PASS: V2 sample fixture is structurally valid.")
        return

    load_dotenv(ROOT / ".env")
    try:
        import mysql.connector  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "mysql-connector-python is required. Run: "
            "python -m pip install -r requirements.txt"
        ) from exc

    required = ("MYSQL_DATABASE", "MYSQL_USER")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Missing database settings: {', '.join(missing)}")

    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.environ["MYSQL_DATABASE"],
        charset="utf8mb4",
        use_unicode=True,
    )
    try:
        import_fixture(connection, fixture)
    finally:
        connection.close()
    print("PASS: imported 38 observations and derived 33 relationships.")


if __name__ == "__main__":
    main()
