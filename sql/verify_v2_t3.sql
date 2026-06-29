-- Read-only Cafe Site V2 Ticket 3 acceptance checks.
-- Run after sql/views.sql. Every named check should return PASS.

SELECT
    'feature_view_has_one_row_per_site' AS check_name,
    CASE WHEN (SELECT COUNT(*) FROM v_site_feature_counts)
            = (SELECT COUNT(*) FROM candidate_sites)
        THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT
    'base_view_equals_unique_relationships' AS check_name,
    CASE WHEN (SELECT COUNT(*) FROM v_site_poi_base)
            = (SELECT COUNT(*) FROM site_poi_relationships)
        THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT
    'duplicate_keyword_hits_do_not_inflate_features' AS check_name,
    CASE
        WHEN (SELECT direct_coffee_within_300m FROM v_site_feature_counts
              WHERE site_code = 'duplicate_observation') = 1
         AND (SELECT joined_observation_rows FROM v_site_feature_diagnostics
              WHERE site_code = 'duplicate_observation') = 3
        THEN 'PASS' ELSE 'FAIL'
    END AS result;

SELECT
    'category_conflict_counts_once_as_direct_coffee' AS check_name,
    CASE
        WHEN (SELECT direct_coffee_within_300m FROM v_site_feature_counts
              WHERE site_code = 'category_conflict') = 1
         AND (SELECT total_poi_activity_within_300m FROM v_site_feature_counts
              WHERE site_code = 'category_conflict') = 1
        THEN 'PASS' ELSE 'FAIL'
    END AS result;

SELECT
    'cumulative_distance_counts_are_monotonic' AS check_name,
    CASE WHEN NOT EXISTS (
        SELECT 1 FROM v_site_feature_counts
        WHERE direct_coffee_within_300m > direct_coffee_within_800m
           OR direct_coffee_within_800m > direct_coffee_within_1500m
           OR total_poi_activity_within_300m > total_poi_activity_within_800m
           OR total_poi_activity_within_800m > total_poi_activity_within_1500m
    ) THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT
    'zero_nearby_site_is_zero_filled' AS check_name,
    CASE
        WHEN (SELECT total_poi_activity_within_1500m
              FROM v_site_feature_counts WHERE site_code = 'zero_nearby') = 0
         AND (SELECT nearest_direct_coffee_distance_m
              FROM v_site_feature_counts WHERE site_code = 'zero_nearby') IS NULL
        THEN 'PASS' ELSE 'FAIL'
    END AS result;

SELECT * FROM v_site_feature_counts ORDER BY site_id;
