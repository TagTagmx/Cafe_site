from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.prepare_v2_full_trial import CitySource, build_city_trial, load_rules
from src.score_v2_sites import REQUIRED_FEATURE_COLUMNS, score_v2_features


class FullTrialPreparationTests(unittest.TestCase):
    def test_repeated_and_conflicting_hits_collapse_to_one_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            processed = Path(temp_dir)
            pd.DataFrame(
                [
                    {
                        "site_id": "SITE_1",
                        "area_name": "Test Site",
                        "district": "Test District",
                    }
                ]
            ).to_csv(processed / "candidate_sites_geocoded.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "site_id": "SITE_1",
                        "poi_clean_id": "POI_1",
                        "keyword_ids": "KW_OTHER_001|KW_DIRECT_001",
                        "min_distance_m": 250,
                    },
                    {
                        "site_id": "SITE_1",
                        "poi_clean_id": "POI_1",
                        "keyword_ids": "KW_DIRECT_001",
                        "min_distance_m": 240,
                    },
                ]
            ).to_csv(processed / "poi_observations_cleaned.csv", index=False)

            features, diagnostics = build_city_trial(
                CitySource("test", "Test", processed),
                load_rules(),
            )

        self.assertTrue(set(REQUIRED_FEATURE_COLUMNS).issubset(features.columns))
        self.assertEqual(features.loc[0, "direct_coffee_within_300m"], 1)
        self.assertEqual(features.loc[0, "commercial_within_300m"], 0)
        self.assertEqual(features.loc[0, "nearest_direct_coffee_distance_m"], 240)
        self.assertEqual(diagnostics.loc[0, "unique_site_poi_relationships"], 1)
        self.assertEqual(diagnostics.loc[0, "collapsed_repeated_rows"], 1)
        scored = score_v2_features(features)
        self.assertEqual(len(scored), 1)


if __name__ == "__main__":
    unittest.main()
