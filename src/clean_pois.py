from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "pois_cleaned.csv"
DEFAULT_OBSERVATIONS_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "poi_observations_cleaned.csv"

REQUIRED_COLUMNS = [
    "collected_at",
    "site_id",
    "city",
    "district",
    "area_name",
    "candidate_address",
    "candidate_lng",
    "candidate_lat",
    "radius_m",
    "keyword_id",
    "bucket",
    "keyword",
    "poi_id",
    "poi_name",
    "poi_type",
    "poi_typecode",
    "poi_address",
    "poi_lng",
    "poi_lat",
    "poi_distance_m",
    "poi_province",
    "poi_city",
    "poi_district",
]

OUTPUT_COLUMNS = [
    "poi_clean_id",
    "dedupe_method",
    "poi_id",
    "poi_name",
    "poi_name_normalized",
    "poi_type",
    "poi_typecode",
    "poi_address",
    "poi_lng",
    "poi_lat",
    "poi_province",
    "poi_city",
    "poi_district",
    "source_row_count",
    "site_ids",
    "area_names",
    "buckets",
    "keywords",
    "keyword_ids",
    "radii_m",
    "min_distance_m",
    "max_distance_m",
    "collected_at_min",
    "collected_at_max",
]

OBSERVATION_OUTPUT_COLUMNS = [
    "poi_clean_id",
    "site_id",
    "area_name",
    "radius_m",
    "bucket",
    "keywords",
    "keyword_ids",
    "min_distance_m",
    "source_row_count",
]


def clean_pois(
    raw_paths: list[Path],
    output_path: Path,
    observations_output_path: Path | None = None,
) -> pd.DataFrame:
    raw = _read_raw_snapshots(raw_paths)
    _validate_columns(raw)

    pois = raw[raw["poi_name"].astype(str).str.strip() != ""].copy()
    pois = _normalize_fields(pois)
    pois["dedupe_key"] = pois.apply(_dedupe_key, axis=1)
    pois["dedupe_method"] = pois["poi_id"].apply(
        lambda value: "poi_id" if str(value).strip() else "name_location"
    )
    pois["poi_clean_id"] = pois.apply(_clean_id, axis=1)

    cleaned = (
        pois.groupby("dedupe_key", dropna=False)
        .apply(_collapse_group, include_groups=False)
        .reset_index(drop=True)
    )
    cleaned = cleaned.sort_values(["poi_clean_id"]).loc[:, OUTPUT_COLUMNS]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False, encoding="utf-8-sig")

    if observations_output_path:
        observations = _build_observations(pois)
        observations_output_path.parent.mkdir(parents=True, exist_ok=True)
        observations.to_csv(observations_output_path, index=False, encoding="utf-8-sig")

    return cleaned


def _build_observations(pois: pd.DataFrame) -> pd.DataFrame:
    observations = (
        pois.groupby(["poi_clean_id", "site_id", "area_name", "radius_m", "bucket"], dropna=False)
        .apply(_collapse_observation_group, include_groups=False)
        .reset_index()
    )
    observations = observations.sort_values(["site_id", "radius_m", "bucket", "poi_clean_id"])
    return observations.loc[:, OBSERVATION_OUTPUT_COLUMNS]


def _collapse_observation_group(group: pd.DataFrame) -> pd.Series:
    distance_values = group["poi_distance_m_numeric"].dropna()
    min_distance = "" if distance_values.empty else int(distance_values.min())

    return pd.Series(
        {
            "keywords": _join_unique(group["keyword"]),
            "keyword_ids": _join_unique(group["keyword_id"]),
            "min_distance_m": min_distance,
            "source_row_count": len(group),
        }
    )


def _read_raw_snapshots(raw_paths: list[Path]) -> pd.DataFrame:
    paths = _expand_paths(raw_paths)
    if not paths:
        raise FileNotFoundError("No raw POI snapshot files found.")

    frames = [pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("") for path in paths]
    return pd.concat(frames, ignore_index=True)


def _expand_paths(raw_paths: list[Path]) -> list[Path]:
    if raw_paths:
        return sorted(path for path in raw_paths if path.exists())
    return sorted(DEFAULT_RAW_DIR.glob("poi_snapshot_*.csv"))


def _validate_columns(raw: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in raw.columns]
    if missing:
        raise ValueError(f"Raw POI snapshot is missing required columns: {', '.join(missing)}")


def _normalize_fields(pois: pd.DataFrame) -> pd.DataFrame:
    pois["poi_id"] = pois["poi_id"].astype(str).str.strip()
    pois["poi_name"] = pois["poi_name"].astype(str).str.strip()
    pois["poi_name_normalized"] = pois["poi_name"].map(_normalize_text)
    pois["poi_lng"] = pois["poi_lng"].astype(str).str.strip()
    pois["poi_lat"] = pois["poi_lat"].astype(str).str.strip()
    pois["poi_location_key"] = pois.apply(
        lambda row: _location_key(row["poi_lng"], row["poi_lat"]),
        axis=1,
    )
    pois["poi_distance_m_numeric"] = pd.to_numeric(pois["poi_distance_m"], errors="coerce")
    return pois


def _dedupe_key(row: pd.Series) -> str:
    poi_id = str(row["poi_id"]).strip()
    if poi_id:
        return f"id:{poi_id}"
    return f"name_location:{row['poi_name_normalized']}|{row['poi_location_key']}"


def _collapse_group(group: pd.DataFrame) -> pd.Series:
    first = group.iloc[0]
    distance_values = group["poi_distance_m_numeric"].dropna()
    min_distance = "" if distance_values.empty else int(distance_values.min())
    max_distance = "" if distance_values.empty else int(distance_values.max())

    return pd.Series(
        {
            "poi_clean_id": _clean_id(first),
            "dedupe_method": first["dedupe_method"],
            "poi_id": first["poi_id"],
            "poi_name": first["poi_name"],
            "poi_name_normalized": first["poi_name_normalized"],
            "poi_type": _first_non_empty(group, "poi_type"),
            "poi_typecode": _first_non_empty(group, "poi_typecode"),
            "poi_address": _first_non_empty(group, "poi_address"),
            "poi_lng": first["poi_lng"],
            "poi_lat": first["poi_lat"],
            "poi_province": _first_non_empty(group, "poi_province"),
            "poi_city": _first_non_empty(group, "poi_city"),
            "poi_district": _first_non_empty(group, "poi_district"),
            "source_row_count": len(group),
            "site_ids": _join_unique(group["site_id"]),
            "area_names": _join_unique(group["area_name"]),
            "buckets": _join_unique(group["bucket"]),
            "keywords": _join_unique(group["keyword"]),
            "keyword_ids": _join_unique(group["keyword_id"]),
            "radii_m": _join_unique(group["radius_m"], numeric=True),
            "min_distance_m": min_distance,
            "max_distance_m": max_distance,
            "collected_at_min": group["collected_at"].min(),
            "collected_at_max": group["collected_at"].max(),
        }
    )


def _clean_id(row: pd.Series) -> str:
    poi_id = str(row["poi_id"]).strip()
    if poi_id:
        return f"poi_{poi_id}"
    return f"poi_{row['poi_name_normalized']}_{row['poi_location_key']}"


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "")


def _location_key(lng: str, lat: str) -> str:
    try:
        return f"{float(lng):.6f},{float(lat):.6f}"
    except ValueError:
        return f"{lng},{lat}"


def _first_non_empty(group: pd.DataFrame, column: str) -> str:
    values = [str(value).strip() for value in group[column].tolist() if str(value).strip()]
    return values[0] if values else ""


def _join_unique(values: pd.Series, numeric: bool = False) -> str:
    items = sorted({str(value).strip() for value in values.tolist() if str(value).strip()})
    if numeric:
        items = sorted(items, key=lambda item: int(item))
    return "|".join(items)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and deduplicate raw 高德 POI snapshots.")
    parser.add_argument("--raw", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--observations-output", type=Path, default=DEFAULT_OBSERVATIONS_OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cleaned = clean_pois(
        raw_paths=args.raw,
        output_path=args.output,
        observations_output_path=args.observations_output,
    )
    print(f"Wrote {len(cleaned)} cleaned POIs to {args.output}")
    print(f"Wrote cleaned POI observations to {args.observations_output}")


if __name__ == "__main__":
    main()
