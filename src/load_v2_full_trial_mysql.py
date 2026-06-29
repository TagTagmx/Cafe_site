"""Load the deterministic Xuzhou/Nanjing V2 full trial into MySQL 8."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Sequence

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.import_v2_sample import RELATIONSHIP_INSERT_SQL
from src.prepare_v2_full_trial import (
    DEFAULT_CITY_SOURCES,
    DEFAULT_RULES_PATH,
    CitySource,
    _split_ids,
)


KEYWORDS_PATH = PROJECT_ROOT / "data" / "sample" / "v2" / "poi_keywords.csv"
RESET_SQL_PATH = PROJECT_ROOT / "sql" / "reset_v2.sql"
SCHEMA_SQL_PATH = PROJECT_ROOT / "sql" / "schema.sql"
VIEWS_SQL_PATH = PROJECT_ROOT / "sql" / "views.sql"
EXPECTED_COUNTS = {
    "cities": 2,
    "candidate_sites": 15,
    "pois": 6866,
    "poi_keywords": 19,
    "poi_category_rules": 19,
    "poi_observations": 17341,
    "site_poi_relationships": 8661,
}


def _optional(value: object) -> object | None:
    return None if pd.isna(value) or str(value).strip() == "" else value


def _execute_sql_file(connection: Any, path: Path) -> None:
    text = path.read_text(encoding="utf-8-sig")
    statements = []
    current = []
    for line in text.splitlines():
        if line.lstrip().startswith("--"):
            continue
        current.append(line)
        if line.rstrip().endswith(";"):
            statements.append("\n".join(current).strip().rstrip(";"))
            current = []
    if any(part.strip() for part in current):
        statements.append("\n".join(current).strip())
    cursor = connection.cursor()
    try:
        for statement in statements:
            if statement:
                cursor.execute(statement)
    finally:
        cursor.close()


def _executemany(
    cursor: Any,
    sql: str,
    rows: Iterable[Sequence[object]],
    batch_size: int = 1000,
) -> None:
    batch: list[Sequence[object]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            cursor.executemany(sql, batch)
            batch.clear()
    if batch:
        cursor.executemany(sql, batch)


def build_load_rows(
    city_sources: tuple[CitySource, ...] = DEFAULT_CITY_SOURCES,
    keywords_path: Path = KEYWORDS_PATH,
    rules_path: Path = DEFAULT_RULES_PATH,
) -> dict[str, list[tuple[object, ...]]]:
    """Build deterministic relational rows without connecting to MySQL."""
    keywords = pd.read_csv(keywords_path, encoding="utf-8-sig")
    rules = pd.read_csv(rules_path, encoding="utf-8-sig")
    result: dict[str, list[tuple[object, ...]]] = {
        "cities": [],
        "candidate_sites": [],
        "pois": [],
        "poi_keywords": [],
        "poi_category_rules": [],
        "poi_observations": [],
    }

    result["poi_keywords"] = [
        (
            row["keyword_id"],
            row.get("bucket", row.get("source_bucket")),
            row["keyword"],
            _optional(row.get("poi_type_hint")),
            _optional(row.get("description")),
        )
        for row in keywords.to_dict("records")
    ]
    result["poi_category_rules"] = [
        (
            row["rule_code"],
            row["keyword_id"],
            row["core_category"],
            row["sub_category"],
            int(row["priority"]),
            row["business_meaning"],
        )
        for row in rules.to_dict("records")
    ]
    valid_keywords = {row[0] for row in result["poi_keywords"]}

    seen_pois: set[str] = set()
    for source in city_sources:
        result["cities"].append((source.city_code, source.city_name))
        sites = pd.read_csv(
            source.processed_dir / "candidate_sites_geocoded.csv",
            encoding="utf-8-sig",
        )
        pois = pd.read_csv(
            source.processed_dir / "pois_cleaned.csv",
            encoding="utf-8-sig",
        )
        observations = pd.read_csv(
            source.processed_dir / "poi_observations_cleaned.csv",
            encoding="utf-8-sig",
        )

        site_codes = set(sites["site_id"].astype(str))
        result["candidate_sites"].extend(
            (
                source.city_code,
                str(row["site_id"]),
                row["area_name"],
                float(row["lat"]),
                float(row["lng"]),
                _optional(row.get("address")),
                _optional(row.get("district")),
                _optional(row.get("business_type")),
            )
            for row in sites.to_dict("records")
        )

        for row in pois.to_dict("records"):
            poi_clean_id = str(row["poi_clean_id"])
            if poi_clean_id in seen_pois:
                raise ValueError(f"POI ID occurs in multiple city inputs: {poi_clean_id}")
            seen_pois.add(poi_clean_id)
            amap_poi_id = _optional(row.get("poi_id"))
            result["pois"].append(
                (
                    poi_clean_id,
                    source.city_code,
                    amap_poi_id,
                    f"{source.city_code}:{poi_clean_id}",
                    "amap_id" if amap_poi_id is not None else "fallback",
                    row["poi_name"],
                    row["poi_name_normalized"],
                    float(row["poi_lat"]),
                    float(row["poi_lng"]),
                    _optional(row.get("poi_type")),
                    _optional(row.get("poi_address")),
                )
            )

        city_pois = set(pois["poi_clean_id"].astype(str))
        for row_number, row in enumerate(observations.to_dict("records"), start=1):
            site_code = str(row["site_id"])
            poi_clean_id = str(row["poi_clean_id"])
            if site_code not in site_codes or poi_clean_id not in city_pois:
                raise ValueError(
                    f"Broken source reference: {source.city_code}/{site_code}/{poi_clean_id}"
                )
            keyword_ids = _split_ids(row["keyword_ids"])
            unknown = set(keyword_ids) - valid_keywords
            if unknown:
                raise ValueError(f"Unknown keyword IDs: {sorted(unknown)}")
            radius = int(row["radius_m"])
            distance = int(row["min_distance_m"])
            if radius not in (300, 800, 1500) or distance > radius:
                raise ValueError(
                    f"Invalid radius/distance: {source.city_code}/{site_code}/{poi_clean_id}"
                )
            for keyword_id in keyword_ids:
                result["poi_observations"].append(
                    (
                        f"full:{source.city_code}:{row_number}:{keyword_id}",
                        source.city_code,
                        site_code,
                        poi_clean_id,
                        keyword_id,
                        radius,
                        distance,
                        json.dumps(
                            {
                                "source": "poi_observations_cleaned.csv",
                                "source_row_count": int(row["source_row_count"]),
                            },
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    )
                )
    return result


def _require_empty_database(cursor: Any) -> None:
    for table in (
        "site_poi_relationships",
        "poi_observations",
        "poi_category_rules",
        "poi_keywords",
        "pois",
        "candidate_sites",
        "cities",
    ):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        if cursor.fetchone()[0] != 0:
            raise RuntimeError(
                f"{table} is not empty; rerun with --reset or use a clean database"
            )


def load_rows(connection: Any, rows: dict[str, list[tuple[object, ...]]]) -> None:
    cursor = connection.cursor()
    try:
        _require_empty_database(cursor)
        _executemany(
            cursor,
            "INSERT INTO cities (city_code, city_name) VALUES (%s, %s)",
            rows["cities"],
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
                (site_code, site_name, lat, lng, address, district, note, city_code)
                for city_code, site_code, site_name, lat, lng, address, district, note
                in rows["candidate_sites"]
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
                    poi_id, amap_id, dedup_key, method, name, normalized, lat, lng,
                    amap_type, address, city_code,
                )
                for (
                    poi_id, city_code, amap_id, dedup_key, method, name, normalized,
                    lat, lng, amap_type, address,
                ) in rows["pois"]
            ),
        )
        _executemany(
            cursor,
            """
            INSERT INTO poi_keywords (
                keyword_id, source_bucket, keyword, poi_type_hint, description
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            rows["poi_keywords"],
        )
        _executemany(
            cursor,
            """
            INSERT INTO poi_category_rules (
                rule_code, keyword_id, core_category, sub_category,
                priority, business_meaning
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            rows["poi_category_rules"],
        )
        _executemany(
            cursor,
            """
            INSERT INTO poi_observations (
                source_observation_key, site_id, poi_clean_id, keyword_id,
                search_radius_m, observed_distance_m, source_context
            )
            SELECT %s, site_id, %s, %s, %s, %s, %s
            FROM candidate_sites
            WHERE site_code = %s
              AND city_id = (SELECT city_id FROM cities WHERE city_code = %s)
            """,
            (
                (key, poi_id, keyword_id, radius, distance, context, site_code, city)
                for key, city, site_code, poi_id, keyword_id, radius, distance, context
                in rows["poi_observations"]
            ),
        )
        cursor.execute(RELATIONSHIP_INSERT_SQL)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def _mysql_settings() -> dict[str, object]:
    load_dotenv(PROJECT_ROOT / ".env")
    required = ("MYSQL_DATABASE", "MYSQL_USER")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing database settings: {', '.join(missing)}")
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.environ["MYSQL_USER"],
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "charset": "utf8mb4",
        "use_unicode": True,
    }


def connect_mysql(include_database: bool = True) -> Any:
    try:
        import mysql.connector  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "mysql-connector-python is required; install requirements.txt"
        ) from exc
    settings = _mysql_settings()
    if include_database:
        settings["database"] = os.environ["MYSQL_DATABASE"]
    return mysql.connector.connect(**settings)


def create_database() -> None:
    database = os.environ["MYSQL_DATABASE"]
    if not re.fullmatch(r"[A-Za-z0-9_]+", database):
        raise ValueError("MYSQL_DATABASE may contain only letters, digits, and underscore")
    connection = connect_mysql(include_database=False)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
        finally:
            cursor.close()
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load deterministic full-trial V2 rows into MySQL 8."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop/recreate V2 views and tables before loading.",
    )
    parser.add_argument(
        "--create-database",
        action="store_true",
        help="Create MYSQL_DATABASE when absent; requires database-create privilege.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Build and validate all load rows without connecting to MySQL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_load_rows()
    actual = {table: len(values) for table, values in rows.items()}
    for table, expected in EXPECTED_COUNTS.items():
        if table != "site_poi_relationships" and actual[table] != expected:
            raise SystemExit(
                f"{table} has {actual[table]} prepared rows; expected {expected}"
            )
    if args.validate_only:
        print(
            "PASS: prepared deterministic full-trial rows: "
            + ", ".join(f"{name}={count}" for name, count in actual.items())
        )
        return

    if args.create_database:
        load_dotenv(PROJECT_ROOT / ".env")
        create_database()
    connection = connect_mysql()
    try:
        if args.reset:
            _execute_sql_file(connection, RESET_SQL_PATH)
            _execute_sql_file(connection, SCHEMA_SQL_PATH)
            connection.commit()
        load_rows(connection, rows)
        _execute_sql_file(connection, VIEWS_SQL_PATH)
        connection.commit()
    finally:
        connection.close()
    print("PASS: full-trial rows and feature views loaded; run the V2-T5 verifier.")


if __name__ == "__main__":
    main()
