from __future__ import annotations

import unittest
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.import_v2_sample import DEFAULT_FIXTURE_DIR, read_fixture


FEATURE_COUNTS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample"
    / "v2"
    / "site_feature_counts.csv"
)


class V2SampleFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = read_fixture(DEFAULT_FIXTURE_DIR)
        rules = {
            row["keyword_id"]: row
            for row in cls.fixture["poi_category_rules.csv"]
        }
        observations_by_pair = defaultdict(list)
        for observation in cls.fixture["poi_observations.csv"]:
            pair = (observation["site_code"], observation["poi_clean_id"])
            observations_by_pair[pair].append(observation)

        cls.relationships = []
        for (site_code, poi_clean_id), observations in observations_by_pair.items():
            resolved = min(
                (rules[row["keyword_id"]] for row in observations),
                key=lambda row: (int(row["priority"]), row["rule_code"]),
            )
            cls.relationships.append(
                {
                    "site_code": site_code,
                    "poi_clean_id": poi_clean_id,
                    "distance_m": min(
                        int(row["observed_distance_m"]) for row in observations
                    ),
                    "core_category": resolved["core_category"],
                    "sub_category": resolved["sub_category"],
                }
            )

    def test_relationship_count_matches_unique_pairs(self) -> None:
        self.assertEqual(len(self.relationships), 33)

    def test_moderate_site_cumulative_counts(self) -> None:
        rows = [
            row
            for row in self.relationships
            if row["site_code"] == "moderate_coffee"
        ]
        direct_300m = sum(
            row["core_category"] == "direct_coffee" and row["distance_m"] <= 300
            for row in rows
        )
        self.assertEqual(len(rows), 4)
        self.assertEqual(direct_300m, 2)

    def test_mature_site_cumulative_counts(self) -> None:
        rows = [
            row for row in self.relationships if row["site_code"] == "mature_market"
        ]
        direct_300m = sum(
            row["core_category"] == "direct_coffee" and row["distance_m"] <= 300
            for row in rows
        )
        direct_800m = sum(
            row["core_category"] == "direct_coffee" and row["distance_m"] <= 800
            for row in rows
        )
        self.assertEqual(len(rows), 10)
        self.assertEqual((direct_300m, direct_800m), (3, 5))

    def test_conflict_and_duplicates_resolve_once(self) -> None:
        conflict = [
            row
            for row in self.relationships
            if row["site_code"] == "category_conflict"
        ]
        duplicate = [
            row
            for row in self.relationships
            if row["site_code"] == "duplicate_observation"
        ]
        self.assertEqual(len(conflict), 1)
        self.assertEqual(conflict[0]["core_category"], "direct_coffee")
        self.assertEqual(len(duplicate), 1)

    def test_offline_feature_view_matches_derived_relationships(self) -> None:
        features = pd.read_csv(FEATURE_COUNTS_PATH, encoding="utf-8-sig").set_index(
            "site_code"
        )
        category_rules = {
            "direct_coffee": ("core_category", "direct_coffee"),
            "indirect_support": ("core_category", "indirect_competitor"),
            "office": ("sub_category", "office"),
            "commercial": ("sub_category", "commercial"),
            "residential": ("sub_category", "residential"),
            "education": ("sub_category", "education"),
            "hotel": ("sub_category", "hotel"),
            "transit": ("core_category", "transit"),
        }

        for site_code in features.index:
            relationships = [
                row for row in self.relationships if row["site_code"] == site_code
            ]
            for radius in (300, 800, 1500):
                self.assertEqual(
                    features.loc[
                        site_code,
                        f"total_poi_activity_within_{radius}m",
                    ],
                    sum(row["distance_m"] <= radius for row in relationships),
                )
                for category, (field, value) in category_rules.items():
                    self.assertEqual(
                        features.loc[
                            site_code,
                            f"{category}_within_{radius}m",
                        ],
                        sum(
                            row[field] == value and row["distance_m"] <= radius
                            for row in relationships
                        ),
                        f"{site_code} {category} {radius}m",
                    )


if __name__ == "__main__":
    unittest.main()
