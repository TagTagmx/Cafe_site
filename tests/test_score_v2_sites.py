from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.score_v2_sites import (
    COUNT_COLUMNS,
    read_feature_csv,
    minmax_normalize,
    score_v2_features,
    write_v2_exports,
)


SAMPLE_FEATURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample"
    / "v2"
    / "site_feature_counts.csv"
)


def feature_row(site_id: int, site_code: str, **counts: float) -> dict:
    row = {
        "city_code": "test_city",
        "city_name": "Test City",
        "site_id": site_id,
        "site_code": site_code,
        "site_name": site_code.replace("_", " ").title(),
        "district": "Test District",
        "nearest_direct_coffee_distance_m": None,
    }
    row.update({column: 0 for column in COUNT_COLUMNS})
    row.update(counts)
    return row


class V2ScoringTests(unittest.TestCase):
    def test_rank_restarts_for_each_city(self) -> None:
        rows = [
            feature_row(1, "city_a_site"),
            feature_row(2, "city_b_site"),
        ]
        rows[1]["city_code"] = "second_city"
        rows[1]["city_name"] = "Second City"
        scored = score_v2_features(pd.DataFrame(rows))
        self.assertEqual(scored["site_rank"].tolist(), [1, 1])

    def test_office_demand_is_300m_heavy(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "near_office",
                    office_within_300m=1,
                    office_within_800m=1,
                    office_within_1500m=1,
                    total_poi_activity_within_300m=1,
                    total_poi_activity_within_800m=1,
                    total_poi_activity_within_1500m=1,
                ),
                feature_row(
                    2,
                    "far_office",
                    office_within_800m=1,
                    office_within_1500m=1,
                    total_poi_activity_within_800m=1,
                    total_poi_activity_within_1500m=1,
                ),
            ]
        )
        scored = score_v2_features(features).set_index("site_code")
        self.assertEqual(scored.loc["near_office", "office_demand_raw"], 1.0)
        self.assertEqual(scored.loc["far_office", "office_demand_raw"], 0.25)

    def test_validation_plateaus_while_pressure_keeps_rising(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "moderate",
                    direct_coffee_within_300m=3,
                    direct_coffee_within_800m=3,
                    direct_coffee_within_1500m=3,
                    total_poi_activity_within_300m=3,
                    total_poi_activity_within_800m=3,
                    total_poi_activity_within_1500m=3,
                ),
                feature_row(
                    2,
                    "dense",
                    direct_coffee_within_300m=5,
                    direct_coffee_within_800m=5,
                    direct_coffee_within_1500m=5,
                    total_poi_activity_within_300m=5,
                    total_poi_activity_within_800m=5,
                    total_poi_activity_within_1500m=5,
                ),
            ]
        )
        scored = score_v2_features(features).set_index("site_code")
        self.assertEqual(scored.loc["moderate", "coffee_validation_score"], 100)
        self.assertEqual(scored.loc["dense", "coffee_validation_score"], 100)
        self.assertGreater(
            scored.loc["dense", "competition_pressure_score"],
            scored.loc["moderate", "competition_pressure_score"],
        )

    def test_direct_coffee_core_is_300m_heavy_and_ignores_1500m(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "near_direct",
                    direct_coffee_within_300m=1,
                    direct_coffee_within_800m=1,
                    direct_coffee_within_1500m=1,
                    total_poi_activity_within_300m=1,
                    total_poi_activity_within_800m=1,
                    total_poi_activity_within_1500m=1,
                ),
                feature_row(
                    2,
                    "far_direct",
                    direct_coffee_within_800m=1,
                    direct_coffee_within_1500m=1,
                    total_poi_activity_within_800m=1,
                    total_poi_activity_within_1500m=1,
                ),
                feature_row(
                    3,
                    "district_background",
                    direct_coffee_within_800m=1,
                    direct_coffee_within_1500m=20,
                    total_poi_activity_within_800m=1,
                    total_poi_activity_within_1500m=20,
                ),
            ]
        )
        scored = score_v2_features(features).set_index("site_code")
        self.assertEqual(scored.loc["near_direct", "direct_coffee_core_raw"], 1)
        self.assertEqual(scored.loc["far_direct", "direct_coffee_core_raw"], 0.25)
        self.assertEqual(
            scored.loc["far_direct", "coffee_validation_score"],
            scored.loc["district_background", "coffee_validation_score"],
        )

    def test_low_competition_is_not_an_automatic_bonus(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "one_coffee_only",
                    direct_coffee_within_300m=1,
                    direct_coffee_within_800m=1,
                    direct_coffee_within_1500m=1,
                    total_poi_activity_within_300m=1,
                    total_poi_activity_within_800m=1,
                    total_poi_activity_within_1500m=1,
                )
            ]
        )
        row = score_v2_features(features).iloc[0]
        self.assertEqual(row["coffee_validation_score"], 45)
        self.assertLess(row["site_score"], 10)

    def test_indirect_support_is_gated_and_labeled_conservatively(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "indirect_only",
                    indirect_support_within_300m=4,
                    indirect_support_within_800m=4,
                    indirect_support_within_1500m=4,
                    total_poi_activity_within_300m=4,
                    total_poi_activity_within_800m=4,
                    total_poi_activity_within_1500m=4,
                )
            ]
        )
        row = score_v2_features(features).iloc[0]
        self.assertEqual(row["indirect_support_score"], 100)
        self.assertEqual(row["effective_indirect_support_score"], 0)
        self.assertEqual(
            row["primary_label_en"],
            "Infrastructure-rich but coffee-weak",
        )
        self.assertEqual(row["saturation_risk_status"], "low_confidence")
        self.assertTrue(pd.isna(row["saturation_risk_score"]))

    def test_transit_alone_does_not_create_opportunity(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "transit_only",
                    transit_within_300m=3,
                    transit_within_800m=3,
                    transit_within_1500m=3,
                    total_poi_activity_within_300m=3,
                    total_poi_activity_within_800m=3,
                    total_poi_activity_within_1500m=3,
                )
            ]
        )
        row = score_v2_features(features).iloc[0]
        self.assertEqual(row["transit_accessibility_score"], 100)
        self.assertEqual(row["transit_demand_synergy_score"], 0)
        self.assertLess(row["site_score"], 25)

    def test_high_activity_with_low_validation_is_unvalidated(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "busy_without_coffee",
                    office_within_300m=4,
                    office_within_800m=4,
                    office_within_1500m=4,
                    commercial_within_300m=4,
                    commercial_within_800m=4,
                    commercial_within_1500m=4,
                    total_poi_activity_within_300m=10,
                    total_poi_activity_within_800m=10,
                    total_poi_activity_within_1500m=10,
                )
            ]
        )
        row = score_v2_features(features).iloc[0]
        self.assertEqual(row["primary_label_en"], "Unvalidated coffee demand")
        self.assertGreater(row["unvalidated_coffee_demand_risk_score"], 60)
        self.assertEqual(row["saturation_risk_status"], "low_confidence")

    def test_zero_nearby_pois_and_zero_variance_are_safe(self) -> None:
        features = pd.DataFrame([feature_row(1, "empty")])
        row = score_v2_features(features).iloc[0]
        self.assertEqual(row["site_score"], 0)
        self.assertEqual(row["primary_label_en"], "Low demand foundation")
        normalized = minmax_normalize(pd.Series([5, 5, 5]))
        self.assertTrue((normalized == 0).all())

    def test_scores_are_bounded(self) -> None:
        high_counts = {
            column: 50
            for column in COUNT_COLUMNS
        }
        scored = score_v2_features(
            pd.DataFrame([feature_row(1, "extreme", **high_counts)])
        )
        for column in [
            "site_score",
            "community_daily_score",
            "coffee_validation_score",
            "competition_pressure_score",
            "indirect_support_score",
            "effective_indirect_support_score",
            "transit_demand_synergy_score",
            "market_activity_score",
            "poi_density_capped_score",
        ]:
            self.assertTrue(scored[column].between(0, 100).all(), column)

    def test_sample_exports_have_expected_headers_and_rows(self) -> None:
        features = read_feature_csv(SAMPLE_FEATURE_PATH)
        scored = score_v2_features(features)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_v2_exports(features, scored, Path(temp_dir))
            base = pd.read_csv(paths["base_features"], encoding="utf-8-sig")
            scores = pd.read_csv(paths["scores"], encoding="utf-8-sig")
            explanations = pd.read_csv(
                paths["explanations"], encoding="utf-8-sig"
            )

        self.assertEqual(len(base), 9)
        self.assertEqual(len(scores), 9)
        self.assertEqual(len(explanations), 9)
        self.assertIn("coffee_validation_score", scores.columns)
        self.assertIn("community_daily_score", scores.columns)
        self.assertIn("primary_label_en", explanations.columns)
        self.assertIn("primary_label_zh", explanations.columns)

        indexed = scored.set_index("site_code")
        self.assertGreater(
            indexed.loc["possible_saturation", "saturation_risk_score"],
            indexed.loc["mature_market", "saturation_risk_score"],
        )
        self.assertEqual(
            indexed.loc["infra_coffee_weak", "primary_label_en"],
            "Infrastructure-rich but coffee-weak",
        )

    def test_invalid_cumulative_counts_are_rejected(self) -> None:
        features = pd.DataFrame(
            [
                feature_row(
                    1,
                    "invalid",
                    direct_coffee_within_300m=2,
                    direct_coffee_within_800m=1,
                    direct_coffee_within_1500m=2,
                )
            ]
        )
        with self.assertRaisesRegex(ValueError, "Non-cumulative"):
            score_v2_features(features)


if __name__ == "__main__":
    unittest.main()
