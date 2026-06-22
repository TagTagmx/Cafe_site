from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_sites_geocoded.csv"
DEFAULT_OBSERVATIONS_PATH = PROJECT_ROOT / "data" / "processed" / "poi_observations_cleaned.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "site_metrics.csv"

RADII = [300, 800, 1500]
BUCKETS = ["direct_competitor", "indirect_competitor", "demand_anchor", "transit"]

REQUIRED_CANDIDATE_COLUMNS = [
    "site_id",
    "city",
    "district",
    "area_name",
    "address",
    "business_type",
    "lng",
    "lat",
]

REQUIRED_OBSERVATION_COLUMNS = [
    "poi_clean_id",
    "site_id",
    "radius_m",
    "bucket",
    "min_distance_m",
]


def aggregate_site_metrics(
    candidates_path: Path,
    observations_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    candidates = pd.read_csv(candidates_path, encoding="utf-8-sig", dtype=str).fillna("")
    observations = pd.read_csv(observations_path, encoding="utf-8-sig", dtype=str).fillna("")
    _validate_columns(candidates, REQUIRED_CANDIDATE_COLUMNS, candidates_path)
    _validate_columns(observations, REQUIRED_OBSERVATION_COLUMNS, observations_path)

    observations["radius_m"] = pd.to_numeric(observations["radius_m"], errors="coerce").astype("Int64")
    observations["min_distance_m_numeric"] = pd.to_numeric(
        observations["min_distance_m"],
        errors="coerce",
    )

    rows: list[dict[str, object]] = []
    for _, candidate in candidates.iterrows():
        site_id = candidate["site_id"]
        site_observations = observations[observations["site_id"] == site_id]

        row: dict[str, object] = {
            "site_id": site_id,
            "city": candidate["city"],
            "district": candidate["district"],
            "area_name": candidate["area_name"],
            "address": candidate["address"],
            "business_type": candidate["business_type"],
            "lng": candidate["lng"],
            "lat": candidate["lat"],
        }

        for radius in RADII:
            radius_observations = site_observations[site_observations["radius_m"] == radius]
            row[f"total_poi_count_{radius}m"] = _count_unique(radius_observations)

            for bucket in BUCKETS:
                bucket_observations = radius_observations[radius_observations["bucket"] == bucket]
                row[f"{bucket}_count_{radius}m"] = _count_unique(bucket_observations)

        direct_observations = site_observations[site_observations["bucket"] == "direct_competitor"]
        row["nearest_direct_competitor_distance_m"] = _min_distance(direct_observations)

        rows.append(row)

    metrics = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_path, index=False, encoding="utf-8-sig")
    return metrics


def _validate_columns(frame: pd.DataFrame, required_columns: list[str], path: Path) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def _count_unique(frame: pd.DataFrame) -> int:
    return int(frame["poi_clean_id"].nunique())


def _min_distance(frame: pd.DataFrame) -> int | str:
    values = frame["min_distance_m_numeric"].dropna()
    if values.empty:
        return ""
    return int(values.min())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate cleaned POI observations into site-level metrics.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = aggregate_site_metrics(
        candidates_path=args.candidates,
        observations_path=args.observations,
        output_path=args.output,
    )
    print(f"Wrote {len(metrics)} site metric rows to {args.output}")


if __name__ == "__main__":
    main()
