"""Prepare a full-data Cafe Site V2 migration trial from legacy CSV artifacts.

The output mirrors ``v_site_feature_counts`` and is suitable for the V2 scorer.
It is intentionally database-independent so relationship counts can be audited
before the same source rows are loaded into MySQL.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_PATH = PROJECT_ROOT / "data" / "sample" / "v2" / "poi_category_rules.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "exports" / "v2" / "full_trial"
RADII = (300, 800, 1500)


@dataclass(frozen=True)
class CitySource:
    city_code: str
    city_name: str
    processed_dir: Path


DEFAULT_CITY_SOURCES = (
    CitySource("xuzhou", "徐州", PROJECT_ROOT / "data" / "processed"),
    CitySource("nanjing", "南京", PROJECT_ROOT / "data" / "processed" / "nanjing"),
)


def _split_ids(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def load_rules(path: Path = DEFAULT_RULES_PATH) -> pd.DataFrame:
    rules = pd.read_csv(path, encoding="utf-8-sig")
    required = {
        "rule_code",
        "keyword_id",
        "core_category",
        "sub_category",
        "priority",
    }
    missing = required - set(rules.columns)
    if missing:
        raise ValueError(f"Category rules are missing: {', '.join(sorted(missing))}")
    rules["priority"] = pd.to_numeric(rules["priority"], errors="raise")
    # MySQL resolves equal-priority rules by auto-incremented rule_id, which
    # follows the seed CSV insertion order.
    rules["rule_order"] = range(1, len(rules) + 1)
    if rules["keyword_id"].duplicated().any():
        raise ValueError("Migration trial requires one category rule per keyword_id")
    return rules


def build_city_trial(
    source: CitySource,
    rules: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return V2 feature counts and relationship diagnostics for one city."""
    sites_path = source.processed_dir / "candidate_sites_geocoded.csv"
    observations_path = source.processed_dir / "poi_observations_cleaned.csv"
    if not sites_path.is_file() or not observations_path.is_file():
        raise FileNotFoundError(
            f"Missing processed migration inputs under {source.processed_dir}"
        )

    sites = pd.read_csv(sites_path, encoding="utf-8-sig")
    observations = pd.read_csv(observations_path, encoding="utf-8-sig")
    required_sites = {"site_id", "area_name", "district"}
    required_observations = {"site_id", "poi_clean_id", "keyword_ids", "min_distance_m"}
    if missing := required_sites - set(sites.columns):
        raise ValueError(f"Candidate sites are missing: {', '.join(sorted(missing))}")
    if missing := required_observations - set(observations.columns):
        raise ValueError(f"Observations are missing: {', '.join(sorted(missing))}")
    if sites["site_id"].duplicated().any():
        raise ValueError(f"{source.city_code} candidate site IDs are not unique")

    rule_lookup = rules.set_index("keyword_id").to_dict("index")
    expanded_rows: list[dict[str, object]] = []
    for row in observations.to_dict("records"):
        keyword_ids = _split_ids(row["keyword_ids"])
        if not keyword_ids:
            raise ValueError(
                f"No keyword IDs for {row['site_id']} / {row['poi_clean_id']}"
            )
        unknown = [keyword_id for keyword_id in keyword_ids if keyword_id not in rule_lookup]
        if unknown:
            raise ValueError(f"Unknown keyword IDs: {', '.join(sorted(set(unknown)))}")
        for keyword_id in keyword_ids:
            rule = rule_lookup[keyword_id]
            expanded_rows.append(
                {
                    "site_code": str(row["site_id"]),
                    "poi_clean_id": str(row["poi_clean_id"]),
                    "distance_m": int(row["min_distance_m"]),
                    "rule_code": rule["rule_code"],
                    "priority": int(rule["priority"]),
                    "rule_order": int(rule["rule_order"]),
                    "core_category": rule["core_category"],
                    "sub_category": rule["sub_category"],
                }
            )

    expanded = pd.DataFrame(expanded_rows)
    relationships = (
        expanded.sort_values(
            ["site_code", "poi_clean_id", "priority", "rule_order"],
            kind="stable",
        )
        .groupby(["site_code", "poi_clean_id"], as_index=False)
        .first()
    )
    minimum_distances = (
        expanded.groupby(["site_code", "poi_clean_id"], as_index=False)["distance_m"]
        .min()
        .rename(columns={"distance_m": "minimum_distance_m"})
    )
    relationships = relationships.drop(columns="distance_m").merge(
        minimum_distances,
        on=["site_code", "poi_clean_id"],
        validate="one_to_one",
    )

    feature_rows: list[dict[str, object]] = []
    diagnostic_rows: list[dict[str, object]] = []
    for site_index, site in enumerate(sites.to_dict("records"), start=1):
        site_code = str(site["site_id"])
        related = relationships[relationships["site_code"] == site_code]
        row: dict[str, object] = {
            "city_code": source.city_code,
            "city_name": source.city_name,
            "site_id": f"{source.city_code}:{site_code}",
            "site_code": site_code,
            "site_name": site["area_name"],
            "district": site.get("district", ""),
        }
        category_filters = {
            "direct_coffee": related["core_category"].eq("direct_coffee"),
            "indirect_support": related["core_category"].eq("indirect_competitor"),
            "office": related["sub_category"].eq("office"),
            "commercial": related["sub_category"].eq("commercial"),
            "residential": related["sub_category"].eq("residential"),
            "education": related["sub_category"].eq("education"),
            "hotel": related["sub_category"].eq("hotel"),
            "transit": related["core_category"].eq("transit"),
            "total_poi_activity": pd.Series(True, index=related.index),
        }
        for category, category_filter in category_filters.items():
            for radius in RADII:
                row[f"{category}_within_{radius}m"] = int(
                    (category_filter & related["minimum_distance_m"].le(radius)).sum()
                )
        direct = related[related["core_category"].eq("direct_coffee")]
        row["nearest_direct_coffee_distance_m"] = (
            direct["minimum_distance_m"].min() if not direct.empty else pd.NA
        )
        feature_rows.append(row)

        source_site_rows = observations[observations["site_id"].astype(str) == site_code]
        diagnostic_rows.append(
            {
                "city_code": source.city_code,
                "site_code": site_code,
                "site_name": site["area_name"],
                "source_cleaned_observation_rows": len(source_site_rows),
                "unique_site_poi_relationships": len(related),
                "collapsed_repeated_rows": len(source_site_rows) - len(related),
            }
        )

    unknown_sites = set(observations["site_id"].astype(str)) - set(sites["site_id"].astype(str))
    if unknown_sites:
        raise ValueError(f"Observations reference unknown sites: {sorted(unknown_sites)}")
    return pd.DataFrame(feature_rows), pd.DataFrame(diagnostic_rows)


def build_full_trial(
    city_sources: tuple[CitySource, ...] = DEFAULT_CITY_SOURCES,
    rules_path: Path = DEFAULT_RULES_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rules = load_rules(rules_path)
    results = [build_city_trial(source, rules) for source in city_sources]
    return (
        pd.concat([result[0] for result in results], ignore_index=True),
        pd.concat([result[1] for result in results], ignore_index=True),
    )


def write_trial_outputs(
    features: pd.DataFrame,
    diagnostics: pd.DataFrame,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_path = output_dir / "site_feature_counts.csv"
    diagnostic_path = output_dir / "relationship_diagnostics.csv"
    features.to_csv(feature_path, index=False, encoding="utf-8-sig")
    diagnostics.to_csv(diagnostic_path, index=False, encoding="utf-8-sig")
    return feature_path, diagnostic_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build auditable V2 feature counts from current full CSV data."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    features, diagnostics = build_full_trial()
    paths = write_trial_outputs(features, diagnostics, args.output_dir)
    print(
        f"Wrote {len(features)} sites and "
        f"{int(diagnostics['unique_site_poi_relationships'].sum())} unique relationships: "
        + ", ".join(str(path) for path in paths)
    )


if __name__ == "__main__":
    main()
