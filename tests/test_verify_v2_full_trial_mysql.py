from __future__ import annotations

import unittest

import pandas as pd

from src.score_v2_sites import COUNT_COLUMNS
from src.verify_v2_full_trial_mysql import compare_feature_frames


def feature_frame(value: int = 0) -> pd.DataFrame:
    row = {
        "city_code": "test",
        "city_name": "Test City",
        "site_code": "SITE_1",
        "site_name": "Test Site",
        "district": "Test District",
        "nearest_direct_coffee_distance_m": None,
    }
    row.update({column: value for column in COUNT_COLUMNS})
    return pd.DataFrame([row])


class MysqlFeatureParityTests(unittest.TestCase):
    def test_equal_features_have_no_differences(self) -> None:
        self.assertEqual(compare_feature_frames(feature_frame(), feature_frame()), [])

    def test_numeric_representation_does_not_create_false_difference(self) -> None:
        expected = feature_frame(1)
        actual = feature_frame(1)
        actual[COUNT_COLUMNS] = actual[COUNT_COLUMNS].astype(float)
        self.assertEqual(compare_feature_frames(expected, actual), [])

    def test_feature_mismatch_is_reported(self) -> None:
        expected = feature_frame()
        actual = feature_frame()
        actual.loc[0, "direct_coffee_within_300m"] = 1
        differences = compare_feature_frames(expected, actual)
        self.assertEqual(len(differences), 1)
        self.assertIn("direct_coffee_within_300m", differences[0])


if __name__ == "__main__":
    unittest.main()
