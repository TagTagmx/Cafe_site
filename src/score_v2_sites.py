"""Cafe Site V2 analytical scoring built on ``v_site_feature_counts``."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "exports" / "v2"

IDENTIFIER_COLUMNS = [
    "city_code",
    "city_name",
    "site_id",
    "site_code",
    "site_name",
    "district",
]

CATEGORIES = [
    "direct_coffee",
    "indirect_support",
    "office",
    "commercial",
    "residential",
    "education",
    "hotel",
    "transit",
    "total_poi_activity",
]

COUNT_COLUMNS = [
    f"{category}_within_{radius}m"
    for category in CATEGORIES
    for radius in (300, 800, 1500)
]

REQUIRED_FEATURE_COLUMNS = [
    *IDENTIFIER_COLUMNS,
    *COUNT_COLUMNS,
    "nearest_direct_coffee_distance_m",
]

LABELS_ZH = {
    "Validated coffee demand": "咖啡需求已验证",
    "Strong demand, high competition": "需求强但竞争高",
    "Unvalidated coffee demand": "咖啡需求未验证",
    "Infrastructure-rich but coffee-weak": "消费配套强但咖啡偏弱",
    "Low demand foundation": "需求基础不足",
    "Transit-supported demand": "交通放大型需求",
    "Oversaturated coffee cluster": "咖啡竞争过密",
}


@dataclass(frozen=True)
class V2ScoringConfig:
    """Provisional business assumptions; these are not calibrated predictions."""

    direct_300m_weight: float = 0.75
    direct_800m_weight: float = 0.25
    office_300m_weight: float = 0.75
    office_800m_weight: float = 0.25
    general_300m_weight: float = 0.60
    general_800m_weight: float = 0.40

    office_cap: float = 4.0
    commercial_cap: float = 4.0
    residential_cap: float = 4.0
    education_cap: float = 3.0
    hotel_cap: float = 3.0
    indirect_support_cap: float = 4.0
    transit_cap: float = 3.0
    poi_density_cap: float = 10.0
    competition_pressure_cap: float = 6.0

    validation_low_confidence_threshold: float = 40.0
    infrastructure_rich_threshold: float = 60.0
    strong_market_activity_threshold: float = 50.0
    oversaturation_threshold: float = 65.0
    transit_supported_threshold: float = 45.0


DEFAULT_CONFIG = V2ScoringConfig()

RAW_COLUMNS = [
    "direct_coffee_core_raw",
    "office_demand_raw",
    "commercial_demand_raw",
    "residential_demand_raw",
    "education_demand_raw",
    "hotel_demand_raw",
    "indirect_support_raw",
    "transit_accessibility_raw",
    "poi_density_raw",
]

SCORE_COLUMNS = [
    "office_demand_score",
    "commercial_demand_score",
    "residential_demand_score",
    "education_demand_score",
    "hotel_demand_score",
    "demand_anchor_score",
    "coffee_validation_score",
    "competition_pressure_score",
    "saturation_risk_score",
    "indirect_support_score",
    "effective_indirect_support_score",
    "transit_accessibility_score",
    "transit_demand_synergy_score",
    "market_activity_score",
    "poi_density_capped_score",
    "unvalidated_coffee_demand_risk_score",
]


def load_features_from_mysql() -> pd.DataFrame:
    """Read raw V2 feature counts from MySQL without writing database state."""
    load_dotenv(PROJECT_ROOT / ".env")
    try:
        import mysql.connector  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "mysql-connector-python is required for MySQL input. "
            "Install requirements.txt or use --input-csv."
        ) from exc

    required = ("MYSQL_DATABASE", "MYSQL_USER")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing database settings: {', '.join(missing)}")

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
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM v_site_feature_counts ORDER BY site_id")
            return pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
        finally:
            cursor.close()
    finally:
        connection.close()


def read_feature_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def score_v2_features(
    features: pd.DataFrame,
    config: V2ScoringConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    """Transform raw SQL features into bounded, auditable V2 scores."""
    base = _validate_and_coerce_features(features)
    scored = base.copy()

    scored["direct_coffee_core_raw"] = (
        config.direct_300m_weight * scored["direct_coffee_within_300m"]
        + config.direct_800m_weight * scored["direct_coffee_within_800m"]
    )
    scored["office_demand_raw"] = (
        config.office_300m_weight * scored["office_within_300m"]
        + config.office_800m_weight * scored["office_within_800m"]
    )

    for category in (
        "commercial",
        "residential",
        "education",
        "hotel",
        "indirect_support",
        "transit",
        "total_poi_activity",
    ):
        output_name = {
            "commercial": "commercial_demand_raw",
            "residential": "residential_demand_raw",
            "education": "education_demand_raw",
            "hotel": "hotel_demand_raw",
            "indirect_support": "indirect_support_raw",
            "transit": "transit_accessibility_raw",
            "total_poi_activity": "poi_density_raw",
        }[category]
        scored[output_name] = (
            config.general_300m_weight * scored[f"{category}_within_300m"]
            + config.general_800m_weight * scored[f"{category}_within_800m"]
        )

    scored["office_demand_score"] = _capped_score(
        scored["office_demand_raw"], config.office_cap
    )
    scored["commercial_demand_score"] = _capped_score(
        scored["commercial_demand_raw"], config.commercial_cap
    )
    scored["residential_demand_score"] = _capped_score(
        scored["residential_demand_raw"], config.residential_cap
    )
    scored["education_demand_score"] = _capped_score(
        scored["education_demand_raw"], config.education_cap
    )
    scored["hotel_demand_score"] = _capped_score(
        scored["hotel_demand_raw"], config.hotel_cap
    )
    scored["indirect_support_score"] = _capped_score(
        scored["indirect_support_raw"], config.indirect_support_cap
    )
    scored["transit_accessibility_score"] = _capped_score(
        scored["transit_accessibility_raw"], config.transit_cap
    )
    scored["poi_density_capped_score"] = _capped_score(
        scored["poi_density_raw"], config.poi_density_cap
    )

    scored["demand_anchor_score"] = (
        0.35 * scored["office_demand_score"]
        + 0.25 * scored["commercial_demand_score"]
        + 0.20 * scored["residential_demand_score"]
        + 0.10 * scored["education_demand_score"]
        + 0.10 * scored["hotel_demand_score"]
    )
    scored["coffee_validation_score"] = scored["direct_coffee_core_raw"].map(
        _coffee_validation_score
    )
    scored["competition_pressure_score"] = _capped_score(
        scored["direct_coffee_core_raw"],
        config.competition_pressure_cap,
    )
    scored["effective_indirect_support_score"] = (
        scored["indirect_support_score"]
        * scored["coffee_validation_score"]
        / 100.0
    )
    scored["market_activity_score"] = (
        0.60 * scored["poi_density_capped_score"]
        + 0.40 * scored["demand_anchor_score"]
    )

    demand_strength = (
        0.40 * scored["office_demand_score"]
        + 0.25 * scored["commercial_demand_score"]
        + 0.15 * scored["residential_demand_score"]
        + 0.20 * scored["coffee_validation_score"]
    )
    scored["transit_demand_synergy_score"] = (
        scored["transit_accessibility_score"] * demand_strength / 100.0
    )
    scored["unvalidated_coffee_demand_risk_score"] = (
        scored["market_activity_score"]
        * (100.0 - scored["coffee_validation_score"])
        / 100.0
    )

    validated = (
        scored["coffee_validation_score"]
        >= config.validation_low_confidence_threshold
    )
    scored["saturation_risk_score"] = pd.NA
    scored.loc[validated, "saturation_risk_score"] = (
        scored.loc[validated, "competition_pressure_score"]
        * (
            1.0
            - 0.40
            * scored.loc[validated, "market_activity_score"]
            / 100.0
        )
    ).clip(0, 100)
    scored["saturation_risk_score"] = pd.to_numeric(
        scored["saturation_risk_score"], errors="coerce"
    )
    scored["saturation_risk_status"] = "low_confidence"
    scored.loc[validated, "saturation_risk_status"] = "applicable"

    saturation_penalty = scored["saturation_risk_score"].fillna(0.0)
    scored["community_daily_score"] = (
        0.35 * scored["residential_demand_score"]
        + 0.20 * scored["coffee_validation_score"]
        + 0.10 * scored["effective_indirect_support_score"]
        + 0.10 * scored["transit_demand_synergy_score"]
        - 0.25 * saturation_penalty
    ).clip(0, 100)
    scored["site_score"] = (
        0.30 * scored["demand_anchor_score"]
        + 0.25 * scored["coffee_validation_score"]
        + 0.10 * scored["effective_indirect_support_score"]
        + 0.10 * scored["transit_demand_synergy_score"]
        + 0.10 * scored["market_activity_score"]
        - 0.15 * saturation_penalty
    ).clip(0, 100)
    scored["scenario_name"] = "balanced_v2"

    labels = scored.apply(
        lambda row: _explanation_label(row, config),
        axis=1,
    )
    scored["primary_label_en"] = labels
    scored["primary_label_zh"] = labels.map(LABELS_ZH)
    scored["explanation_en"] = scored.apply(_explanation_en, axis=1)
    scored["explanation_zh"] = scored.apply(_explanation_zh, axis=1)
    scored["is_infrastructure_rich_coffee_weak"] = (
        (scored["coffee_validation_score"] < config.validation_low_confidence_threshold)
        & (scored["indirect_support_score"] >= config.infrastructure_rich_threshold)
    )
    scored["is_unvalidated_high_activity"] = (
        (scored["coffee_validation_score"] < config.validation_low_confidence_threshold)
        & (scored["market_activity_score"] >= config.strong_market_activity_threshold)
    )

    scored = _rank_sites(scored)
    for column in [*RAW_COLUMNS, *SCORE_COLUMNS, "community_daily_score", "site_score"]:
        scored[column] = scored[column].round(2)
    return scored


def write_v2_exports(
    base_features: pd.DataFrame,
    scored: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    """Write base, score, and explanation CSVs with Excel-safe UTF-8 BOM."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "base_features": output_dir / "site_feature_summary.csv",
        "scores": output_dir / "site_scores.csv",
        "explanations": output_dir / "site_explanations.csv",
    }

    validated_base = _validate_and_coerce_features(base_features)
    validated_base.to_csv(paths["base_features"], index=False, encoding="utf-8-sig")

    score_output_columns = [
        "site_rank",
        "site_score",
        "scenario_name",
        *IDENTIFIER_COLUMNS,
        *RAW_COLUMNS,
        *SCORE_COLUMNS,
        "saturation_risk_status",
        "community_daily_score",
    ]
    scored.loc[:, score_output_columns].to_csv(
        paths["scores"], index=False, encoding="utf-8-sig"
    )

    explanation_columns = [
        "site_rank",
        "site_score",
        *IDENTIFIER_COLUMNS,
        "primary_label_en",
        "primary_label_zh",
        "explanation_en",
        "explanation_zh",
        "saturation_risk_status",
        "is_infrastructure_rich_coffee_weak",
        "is_unvalidated_high_activity",
    ]
    scored.loc[:, explanation_columns].to_csv(
        paths["explanations"], index=False, encoding="utf-8-sig"
    )
    return paths


def minmax_normalize(series: pd.Series) -> pd.Series:
    """Normalize to 0..100; a zero-variance input safely returns all zeros."""
    numeric = pd.to_numeric(series, errors="coerce").fillna(0.0)
    minimum = numeric.min()
    maximum = numeric.max()
    if maximum == minimum:
        return pd.Series(0.0, index=series.index)
    return ((numeric - minimum) / (maximum - minimum) * 100.0).clip(0, 100)


def _capped_score(series: pd.Series, cap: float) -> pd.Series:
    if cap <= 0:
        raise ValueError("Score cap must be positive")
    return (pd.to_numeric(series, errors="coerce").fillna(0.0) / cap * 100.0).clip(
        0, 100
    )


def _coffee_validation_score(raw_value: float) -> float:
    """Plateau after moderate direct-coffee presence."""
    value = max(0.0, float(raw_value))
    if value <= 1.0:
        return value * 45.0
    if value < 3.0:
        return 45.0 + (value - 1.0) / 2.0 * 55.0
    return 100.0


def _validate_and_coerce_features(features: pd.DataFrame) -> pd.DataFrame:
    missing = [
        column for column in REQUIRED_FEATURE_COLUMNS if column not in features.columns
    ]
    if missing:
        raise ValueError(f"V2 feature input is missing: {', '.join(missing)}")
    if features.empty:
        raise ValueError("V2 feature input has no candidate sites")
    if features["site_id"].duplicated().any():
        raise ValueError("V2 feature input must contain one row per site_id")

    output = features.copy()
    for column in COUNT_COLUMNS:
        output[column] = pd.to_numeric(output[column], errors="raise")
        if (output[column] < 0).any():
            raise ValueError(f"V2 feature counts cannot be negative: {column}")
    output["nearest_direct_coffee_distance_m"] = pd.to_numeric(
        output["nearest_direct_coffee_distance_m"], errors="coerce"
    )
    _validate_cumulative_counts(output)
    return output


def _validate_cumulative_counts(features: pd.DataFrame) -> None:
    for category in CATEGORIES:
        within_300m = features[f"{category}_within_300m"]
        within_800m = features[f"{category}_within_800m"]
        within_1500m = features[f"{category}_within_1500m"]
        if ((within_300m > within_800m) | (within_800m > within_1500m)).any():
            raise ValueError(f"Non-cumulative distance counts for {category}")


def _rank_sites(scored: pd.DataFrame) -> pd.DataFrame:
    ranked = scored.sort_values(
        ["city_code", "site_score", "site_id"],
        ascending=[True, False, True],
        kind="stable",
    ).copy()
    ranked["site_rank"] = ranked.groupby("city_code", sort=False).cumcount() + 1
    return ranked


def _explanation_label(row: pd.Series, config: V2ScoringConfig) -> str:
    validation = float(row["coffee_validation_score"])
    activity = float(row["market_activity_score"])
    indirect = float(row["indirect_support_score"])
    saturation = row["saturation_risk_score"]

    if validation < config.validation_low_confidence_threshold:
        if indirect >= config.infrastructure_rich_threshold:
            return "Infrastructure-rich but coffee-weak"
        if activity < 15.0:
            return "Low demand foundation"
        return "Unvalidated coffee demand"
    if pd.notna(saturation) and float(saturation) >= config.oversaturation_threshold:
        return "Oversaturated coffee cluster"
    if (
        activity >= config.strong_market_activity_threshold
        and float(row["competition_pressure_score"]) >= 50.0
    ):
        return "Strong demand, high competition"
    if float(row["transit_demand_synergy_score"]) >= config.transit_supported_threshold:
        return "Transit-supported demand"
    return "Validated coffee demand"


def _explanation_en(row: pd.Series) -> str:
    saturation = (
        "not scored because coffee demand is not sufficiently validated"
        if row["saturation_risk_status"] == "low_confidence"
        else f"{row['saturation_risk_score']:.1f}/100"
    )
    return (
        f"{row['primary_label_en']}. Coffee validation is "
        f"{row['coffee_validation_score']:.1f}/100 and direct competition pressure "
        f"is {row['competition_pressure_score']:.1f}/100. Effective indirect "
        f"support is {row['effective_indirect_support_score']:.1f}/100 after "
        f"validation gating. Saturation risk is {saturation}."
    )


def _explanation_zh(row: pd.Series) -> str:
    saturation = (
        "因咖啡需求验证不足而不评分"
        if row["saturation_risk_status"] == "low_confidence"
        else f"{row['saturation_risk_score']:.1f}/100"
    )
    return (
        f"{row['primary_label_zh']}。咖啡需求验证分为 "
        f"{row['coffee_validation_score']:.1f}/100，直接竞争压力分为 "
        f"{row['competition_pressure_score']:.1f}/100。间接消费支持经过验证门控后为 "
        f"{row['effective_indirect_support_score']:.1f}/100。饱和风险为{saturation}。"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score Cafe Site V2 raw features and write analytical CSV exports."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        help="Optional CSV equivalent of v_site_feature_counts; otherwise use MySQL.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    features = (
        read_feature_csv(args.input_csv)
        if args.input_csv
        else load_features_from_mysql()
    )
    scored = score_v2_features(features)
    paths = write_v2_exports(features, scored, args.output_dir)
    print(
        f"Wrote {len(scored)} V2 sites: "
        + ", ".join(str(path) for path in paths.values())
    )


if __name__ == "__main__":
    main()
