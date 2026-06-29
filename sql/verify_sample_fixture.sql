-- Read-only Ticket 2 verification queries.
-- Run after sql/sample_fixture.sql. Each check should return PASS.

SELECT
    'fixture_row_counts' AS check_name,
    CASE
        WHEN (SELECT COUNT(*) FROM cities) = 1
         AND (SELECT COUNT(*) FROM candidate_sites) = 9
         AND (SELECT COUNT(*) FROM pois) = 17
         AND (SELECT COUNT(*) FROM poi_keywords) = 19
         AND (SELECT COUNT(*) FROM poi_category_rules) = 19
         AND (SELECT COUNT(*) FROM poi_observations) = 38
         AND (SELECT COUNT(*) FROM site_poi_relationships) = 33
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'relationships_equal_unique_observation_pairs' AS check_name,
    CASE
        WHEN (SELECT COUNT(*) FROM site_poi_relationships) = (
            SELECT COUNT(*)
            FROM (
                SELECT site_id, poi_clean_id
                FROM poi_observations
                GROUP BY site_id, poi_clean_id
            ) AS unique_pairs
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'no_duplicate_site_poi_relationships' AS check_name,
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM site_poi_relationships
            GROUP BY site_id, poi_clean_id
            HAVING COUNT(*) > 1
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'duplicate_observations_collapse' AS check_name,
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM poi_observations
            WHERE site_id = 108
              AND poi_clean_id = 'POI_COFFEE_02'
        ) = 3
         AND (
            SELECT COUNT(*)
            FROM site_poi_relationships
            WHERE site_id = 108
              AND poi_clean_id = 'POI_COFFEE_02'
        ) = 1
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'category_conflict_resolves_to_direct_coffee' AS check_name,
    CASE
        WHEN (
            SELECT resolved_core_category
            FROM site_poi_relationships
            WHERE site_id = 107
              AND poi_clean_id = 'POI_COFFEE_01'
        ) = 'direct_coffee'
         AND (
            SELECT resolved_sub_category
            FROM site_poi_relationships
            WHERE site_id = 107
              AND poi_clean_id = 'POI_COFFEE_01'
        ) = 'coffee_shop'
         AND (
            SELECT COUNT(DISTINCT rules.core_category)
            FROM poi_observations AS observations
            INNER JOIN poi_category_rules AS rules
                ON rules.keyword_id = observations.keyword_id
            WHERE observations.site_id = 107
              AND observations.poi_clean_id = 'POI_COFFEE_01'
        ) = 3
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'shared_poi_can_relate_to_multiple_sites' AS check_name,
    CASE
        WHEN (
            SELECT COUNT(DISTINCT site_id)
            FROM site_poi_relationships
            WHERE poi_clean_id = 'POI_COFFEE_01'
        ) = 4
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'zero_nearby_poi_site_is_preserved' AS check_name,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM candidate_sites
            WHERE site_id = 109
        )
         AND NOT EXISTS (
            SELECT 1
            FROM site_poi_relationships
            WHERE site_id = 109
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

SELECT
    'resolved_categories_are_complete' AS check_name,
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM site_poi_relationships
            WHERE resolved_core_category IS NULL
               OR resolved_sub_category IS NULL
               OR resolution_rule_id IS NULL
        )
        THEN 'PASS'
        ELSE 'FAIL'
    END AS result;

-- Manual-check output: cumulative raw counts from resolved relationship fields.
SELECT
    sites.site_code,
    COUNT(relationships.relationship_id) AS all_relationships,
    COALESCE(SUM(
        relationships.resolved_core_category = 'direct_coffee'
        AND relationships.distance_m <= 300
    ), 0) AS direct_coffee_within_300m,
    COALESCE(SUM(
        relationships.resolved_core_category = 'direct_coffee'
        AND relationships.distance_m <= 800
    ), 0) AS direct_coffee_within_800m,
    COALESCE(SUM(
        relationships.resolved_core_category = 'indirect_competitor'
        AND relationships.distance_m <= 800
    ), 0) AS indirect_competitor_within_800m,
    COALESCE(SUM(
        relationships.resolved_sub_category = 'office'
        AND relationships.distance_m <= 300
    ), 0) AS office_within_300m,
    COALESCE(SUM(
        relationships.resolved_sub_category = 'office'
        AND relationships.distance_m <= 800
    ), 0) AS office_within_800m,
    COALESCE(SUM(
        relationships.resolved_core_category = 'transit'
        AND relationships.distance_m <= 800
    ), 0) AS transit_within_800m
FROM candidate_sites AS sites
LEFT JOIN site_poi_relationships AS relationships
    ON relationships.site_id = sites.site_id
GROUP BY sites.site_id, sites.site_code
ORDER BY sites.site_id;
