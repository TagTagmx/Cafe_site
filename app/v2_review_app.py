"""Separate Streamlit review surface for Cafe Site V2 artifacts."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.score_v2_sites import read_feature_csv, score_v2_features


SAMPLE_FEATURES = PROJECT_ROOT / "data" / "sample" / "v2" / "site_feature_counts.csv"
MIGRATED_FEATURES = (
    PROJECT_ROOT / "data" / "exports" / "v2" / "full_trial" / "site_feature_counts.csv"
)
LEGACY_SCORE_PATHS = {
    "xuzhou": PROJECT_ROOT / "data" / "processed" / "site_scores.csv",
    "nanjing": PROJECT_ROOT / "data" / "processed" / "nanjing" / "site_scores.csv",
}

EVIDENCE_COLUMNS = [
    "direct_coffee_within_300m",
    "direct_coffee_within_800m",
    "direct_coffee_within_1500m",
    "indirect_support_within_800m",
    "office_within_800m",
    "commercial_within_800m",
    "residential_within_800m",
    "education_within_800m",
    "hotel_within_800m",
    "transit_within_800m",
    "total_poi_activity_within_800m",
    "nearest_direct_coffee_distance_m",
]

COMPONENT_COLUMNS = [
    "demand_anchor_score",
    "coffee_validation_score",
    "competition_pressure_score",
    "saturation_risk_score",
    "market_activity_score",
]

INTERACTION_COLUMNS = [
    "indirect_support_score",
    "effective_indirect_support_score",
    "transit_accessibility_score",
    "transit_demand_synergy_score",
    "poi_density_capped_score",
    "unvalidated_coffee_demand_risk_score",
]


@st.cache_data
def load_review_data(path: Path) -> pd.DataFrame:
    scored = score_v2_features(read_feature_csv(path))
    comparisons = []
    for city_code, legacy_path in LEGACY_SCORE_PATHS.items():
        if not legacy_path.is_file():
            continue
        legacy = pd.read_csv(legacy_path, encoding="utf-8-sig")
        if not {"site_id", "site_rank", "site_score"}.issubset(legacy.columns):
            continue
        comparison = legacy[["site_id", "site_rank", "site_score"]].copy()
        comparison["city_code"] = city_code
        comparison["site_code"] = comparison["site_id"].astype(str)
        comparison = comparison.rename(
            columns={"site_rank": "legacy_rank", "site_score": "legacy_score"}
        ).drop(columns="site_id")
        comparisons.append(comparison)
    if comparisons:
        scored = scored.merge(
            pd.concat(comparisons, ignore_index=True),
            on=["city_code", "site_code"],
            how="left",
            validate="one_to_one",
        )
        scored["rank_change_vs_legacy"] = scored["legacy_rank"] - scored["site_rank"]
    return scored


def format_score(value: object) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    return "N/A" if pd.isna(numeric) else f"{float(numeric):.2f}"


def main() -> None:
    st.set_page_config(page_title="Cafe Site V2 Review", layout="wide")
    st.title("Cafe Site V2 Review / V2 复核")
    st.warning(
        "This is a provisional rule-based review surface, not a revenue prediction. "
        "It does not replace the current CSV dashboard."
    )

    sources = {"Synthetic sample / 合成样例": SAMPLE_FEATURES}
    if MIGRATED_FEATURES.is_file():
        sources["Local full-data trial / 本地全量试迁移"] = MIGRATED_FEATURES
    selected_source = st.sidebar.radio("Review dataset / 复核数据", list(sources))
    data = load_review_data(sources[selected_source])

    cities = data["city_name"].drop_duplicates().tolist()
    selected_city = st.sidebar.selectbox("City / 城市", cities)
    city_data = data[data["city_name"] == selected_city].sort_values("site_rank")
    selected_site = st.selectbox(
        "Candidate site / 候选点",
        city_data["site_name"].tolist(),
    )
    row = city_data[city_data["site_name"] == selected_site].iloc[0]

    metrics = st.columns(4)
    metrics[0].metric("V2 rank / 排名", int(row["site_rank"]))
    metrics[1].metric("Balanced score / 综合分", format_score(row["site_score"]))
    metrics[2].metric(
        "Community daily / 社区日常场景",
        format_score(row["community_daily_score"]),
    )
    metrics[3].metric("Label / 标签", row["primary_label_zh"])

    st.subheader("Explanation / 解释")
    st.info(row["explanation_zh"])
    st.caption(row["explanation_en"])

    left, right = st.columns(2)
    with left:
        st.subheader("Base evidence / 基础证据")
        evidence = pd.DataFrame(
            {"feature": EVIDENCE_COLUMNS, "value": [row[column] for column in EVIDENCE_COLUMNS]}
        )
        st.dataframe(evidence, hide_index=True, width="stretch")
    with right:
        st.subheader("Normalized components / 标准化组件")
        components = pd.DataFrame(
            {
                "component": COMPONENT_COLUMNS,
                "score": [row[column] for column in COMPONENT_COLUMNS],
            }
        )
        st.dataframe(components, hide_index=True, width="stretch")

    st.subheader("Interaction features / 交互特征")
    interactions = pd.DataFrame(
        {
            "interaction": INTERACTION_COLUMNS,
            "score": [row[column] for column in INTERACTION_COLUMNS],
        }
    )
    st.dataframe(interactions, hide_index=True, width="stretch")

    st.subheader("City ranking / 城市内排序")
    ranking_columns = [
        "site_rank",
        "site_name",
        "site_score",
        "community_daily_score",
        "primary_label_zh",
        "saturation_risk_status",
    ]
    if "legacy_rank" in city_data.columns and city_data["legacy_rank"].notna().any():
        ranking_columns.extend(
            ["legacy_rank", "legacy_score", "rank_change_vs_legacy"]
        )
    st.dataframe(
        city_data[ranking_columns],
        hide_index=True,
        width="stretch",
    )

    st.subheader("Comparison notes / 对比说明")
    st.markdown(
        """
- V2 counts unique site–POI relationships after deterministic category priority; repeated keyword hits do not add evidence.
- The legacy dashboard and V2 use different feature contracts and formulas, so exact score or rank parity is not expected.
- Coffee validation and competition pressure share raw direct-coffee evidence but use different transformations.
- Saturation is not scored when coffee validation is insufficient; low competition is not treated as automatic opportunity.
"""
    )


if __name__ == "__main__":
    main()
