from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "site_metrics.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "site_scores.csv"

ID_COLUMNS = [
    "site_id",
    "city",
    "district",
    "area_name",
    "address",
    "business_type",
    "lng",
    "lat",
]

REQUIRED_METRIC_COLUMNS = [
    "demand_anchor_count_800m",
    "demand_anchor_count_1500m",
    "transit_count_800m",
    "transit_count_1500m",
    "total_poi_count_800m",
    "total_poi_count_1500m",
    "indirect_competitor_count_800m",
    "indirect_competitor_count_1500m",
    "direct_competitor_count_800m",
    "direct_competitor_count_1500m",
    "nearest_direct_competitor_distance_m",
]

OUTPUT_METRIC_COLUMNS = [
    "total_poi_count_300m",
    "direct_competitor_count_300m",
    "indirect_competitor_count_300m",
    "demand_anchor_count_300m",
    "transit_count_300m",
    "total_poi_count_800m",
    "direct_competitor_count_800m",
    "indirect_competitor_count_800m",
    "demand_anchor_count_800m",
    "transit_count_800m",
    "total_poi_count_1500m",
    "direct_competitor_count_1500m",
    "indirect_competitor_count_1500m",
    "demand_anchor_count_1500m",
    "transit_count_1500m",
    "nearest_direct_competitor_distance_m",
]

WEIGHTS = {
    "demand_score": 0.40,
    "accessibility_score": 0.25,
    "commercial_maturity_score": 0.20,
    "competition_fit_score": 0.15,
}

COMPETITION_FIT_TARGET = 30.0
COMPETITION_UNDER_SUPPLY_TOLERANCE = 30.0
COMPETITION_OVER_SUPPLY_TOLERANCE = 90.0


def score_sites(input_path: Path, output_path: Path) -> pd.DataFrame:
    metrics = pd.read_csv(input_path, encoding="utf-8-sig", dtype=str).fillna("")
    _validate_columns(metrics)
    original_columns = metrics.columns.tolist()
    metrics = _coerce_metric_columns(metrics)

    scored = metrics.copy()
    scored["demand_raw"] = (
        scored["demand_anchor_count_800m"] * 0.60
        + scored["demand_anchor_count_1500m"] * 0.40
    )
    scored["accessibility_raw"] = (
        scored["transit_count_800m"] * 0.65
        + scored["transit_count_1500m"] * 0.35
    )
    scored["commercial_maturity_raw"] = (
        scored["total_poi_count_800m"] * 0.45
        + scored["total_poi_count_1500m"] * 0.25
        + scored["indirect_competitor_count_800m"] * 0.20
        + scored["indirect_competitor_count_1500m"] * 0.10
    )
    scored["competitor_density_raw"] = (
        scored["direct_competitor_count_800m"] * 0.65
        + scored["direct_competitor_count_1500m"] * 0.35
    )
    scored["nearest_competitor_pressure_raw"] = _inverse_minmax(
        scored["nearest_direct_competitor_distance_m"]
    )

    scored["demand_score"] = _minmax(scored["demand_raw"]) * 100
    scored["accessibility_score"] = _minmax(scored["accessibility_raw"]) * 100
    scored["commercial_maturity_score"] = _minmax(scored["commercial_maturity_raw"]) * 100
    scored["competitor_pressure_score"] = (
        _minmax(scored["competitor_density_raw"]) * 0.75
        + scored["nearest_competitor_pressure_raw"] * 0.25
    ) * 100
    scored["competition_fit_score"] = _competition_fit(scored["competitor_density_raw"]) * 100

    scored["v1_site_score"] = (
        scored["demand_score"] * 0.40
        + scored["accessibility_score"] * 0.25
        + scored["commercial_maturity_score"] * 0.20
        - scored["competitor_pressure_score"] * 0.15
    ).round(2)

    scored["site_score"] = (
        scored["demand_score"] * WEIGHTS["demand_score"]
        + scored["accessibility_score"] * WEIGHTS["accessibility_score"]
        + scored["commercial_maturity_score"] * WEIGHTS["commercial_maturity_score"]
        + scored["competition_fit_score"] * WEIGHTS["competition_fit_score"]
    ).clip(lower=0, upper=100).round(2)

    component_columns = [
        "demand_score",
        "accessibility_score",
        "commercial_maturity_score",
        "competition_fit_score",
    ]
    for column in [*component_columns, "competitor_pressure_score"]:
        scored[column] = scored[column].round(2)

    scored["v1_site_rank"] = scored["v1_site_score"].rank(method="first", ascending=False).astype(int)
    scored["site_rank"] = scored["site_score"].rank(method="first", ascending=False).astype(int)
    scored["rank_change_vs_v1"] = scored["v1_site_rank"] - scored["site_rank"]
    scored = scored.sort_values(["site_rank", "site_id"])

    output_columns = [
        "site_rank",
        "site_score",
        "v1_site_rank",
        "v1_site_score",
        "rank_change_vs_v1",
        *component_columns,
        "competitor_pressure_score",
        "demand_raw",
        "accessibility_raw",
        "commercial_maturity_raw",
        "competitor_density_raw",
        "nearest_competitor_pressure_raw",
        *original_columns,
    ]
    output = scored.loc[:, output_columns]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output


def _validate_columns(metrics: pd.DataFrame) -> None:
    required = [*ID_COLUMNS, *OUTPUT_METRIC_COLUMNS]
    missing = [column for column in required if column not in metrics.columns]
    if missing:
        raise ValueError(f"site_metrics.csv is missing required columns: {', '.join(missing)}")


def _coerce_metric_columns(metrics: pd.DataFrame) -> pd.DataFrame:
    output = metrics.copy()
    for column in OUTPUT_METRIC_COLUMNS:
        output[column] = pd.to_numeric(output[column], errors="coerce").fillna(0)
    return output


def _minmax(series: pd.Series) -> pd.Series:
    minimum = series.min()
    maximum = series.max()
    if maximum == minimum:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - minimum) / (maximum - minimum)


def _inverse_minmax(series: pd.Series) -> pd.Series:
    return 1 - _minmax(series)


def _competition_fit(series: pd.Series) -> pd.Series:
    def score(value: float) -> float:
        if value <= COMPETITION_FIT_TARGET:
            return max(0.0, 1 - ((COMPETITION_FIT_TARGET - value) / COMPETITION_UNDER_SUPPLY_TOLERANCE))
        return max(0.0, 1 - ((value - COMPETITION_FIT_TARGET) / COMPETITION_OVER_SUPPLY_TOLERANCE))

    return series.map(score)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score 徐州 coffee shop candidate sites.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scores = score_sites(input_path=args.input, output_path=args.output)
    print(f"Wrote {len(scores)} scored candidate sites to {args.output}")


if __name__ == "__main__":
    main()
