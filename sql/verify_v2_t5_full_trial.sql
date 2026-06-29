-- Read-only V2-T5 full-trial database checks.
-- Exact counts correspond to the 2026-06-29 Xuzhou/Nanjing processed artifacts.
-- Python verification additionally compares every feature value with pandas.

SELECT 'cities_count' AS check_name,
       IF((SELECT COUNT(*) FROM cities) = 2, 'PASS', 'FAIL') AS result;
SELECT 'candidate_sites_count' AS check_name,
       IF((SELECT COUNT(*) FROM candidate_sites) = 15, 'PASS', 'FAIL') AS result;
SELECT 'pois_count' AS check_name,
       IF((SELECT COUNT(*) FROM pois) = 6866, 'PASS', 'FAIL') AS result;
SELECT 'keywords_count' AS check_name,
       IF((SELECT COUNT(*) FROM poi_keywords) = 19, 'PASS', 'FAIL') AS result;
SELECT 'rules_count' AS check_name,
       IF((SELECT COUNT(*) FROM poi_category_rules) = 19, 'PASS', 'FAIL') AS result;
SELECT 'observations_count' AS check_name,
       IF((SELECT COUNT(*) FROM poi_observations) = 17341, 'PASS', 'FAIL') AS result;
SELECT 'relationships_count' AS check_name,
       IF((SELECT COUNT(*) FROM site_poi_relationships) = 8661, 'PASS', 'FAIL') AS result;

SELECT 'relationships_equal_unique_site_poi_pairs' AS check_name,
       IF(
           (SELECT COUNT(*) FROM site_poi_relationships) =
           (SELECT COUNT(*) FROM (
               SELECT site_id, poi_clean_id
               FROM poi_observations
               GROUP BY site_id, poi_clean_id
           ) AS unique_pairs),
           'PASS', 'FAIL'
       ) AS result;

SELECT 'foreign_keys_have_no_orphans' AS check_name,
       IF(
           NOT EXISTS (
               SELECT 1 FROM candidate_sites s
               LEFT JOIN cities c ON c.city_id = s.city_id
               WHERE c.city_id IS NULL
           )
           AND NOT EXISTS (
               SELECT 1 FROM pois p
               LEFT JOIN cities c ON c.city_id = p.city_id
               WHERE c.city_id IS NULL
           )
           AND NOT EXISTS (
               SELECT 1 FROM poi_observations o
               LEFT JOIN candidate_sites s ON s.site_id = o.site_id
               LEFT JOIN pois p ON p.poi_clean_id = o.poi_clean_id
               LEFT JOIN poi_keywords k ON k.keyword_id = o.keyword_id
               WHERE s.site_id IS NULL OR p.poi_clean_id IS NULL OR k.keyword_id IS NULL
           )
           AND NOT EXISTS (
               SELECT 1 FROM site_poi_relationships r
               LEFT JOIN candidate_sites s ON s.site_id = r.site_id
               LEFT JOIN pois p ON p.poi_clean_id = r.poi_clean_id
               LEFT JOIN poi_category_rules cr ON cr.rule_id = r.resolution_rule_id
               WHERE s.site_id IS NULL OR p.poi_clean_id IS NULL OR cr.rule_id IS NULL
           ),
           'PASS', 'FAIL'
       ) AS result;

SELECT 'site_and_poi_city_are_consistent' AS check_name,
       IF(NOT EXISTS (
           SELECT 1
           FROM site_poi_relationships r
           INNER JOIN candidate_sites s ON s.site_id = r.site_id
           INNER JOIN pois p ON p.poi_clean_id = r.poi_clean_id
           WHERE s.city_id <> p.city_id
       ), 'PASS', 'FAIL') AS result;

SELECT 'radius_and_distance_are_consistent' AS check_name,
       IF(NOT EXISTS (
           SELECT 1 FROM poi_observations
           WHERE search_radius_m NOT IN (300, 800, 1500)
              OR observed_distance_m > search_radius_m
       ), 'PASS', 'FAIL') AS result;

SELECT 'relationship_distance_bands_are_consistent' AS check_name,
       IF(NOT EXISTS (
           SELECT 1 FROM site_poi_relationships
           WHERE distance_band <> CASE
               WHEN distance_m <= 300 THEN 'within_300m'
               WHEN distance_m <= 800 THEN 'within_800m'
               ELSE 'within_1500m'
           END
       ), 'PASS', 'FAIL') AS result;

SELECT 'resolved_categories_match_rules' AS check_name,
       IF(NOT EXISTS (
           SELECT 1
           FROM site_poi_relationships r
           INNER JOIN poi_category_rules cr ON cr.rule_id = r.resolution_rule_id
           WHERE r.resolved_core_category <> cr.core_category
              OR r.resolved_sub_category <> cr.sub_category
       ), 'PASS', 'FAIL') AS result;

SELECT 'feature_view_has_one_row_per_site' AS check_name,
       IF(
           (SELECT COUNT(*) FROM v_site_feature_counts) =
           (SELECT COUNT(*) FROM candidate_sites),
           'PASS', 'FAIL'
       ) AS result;

SELECT 'all_cumulative_feature_counts_are_monotonic' AS check_name,
       IF(NOT EXISTS (
           SELECT 1 FROM v_site_feature_counts
           WHERE direct_coffee_within_300m > direct_coffee_within_800m
              OR direct_coffee_within_800m > direct_coffee_within_1500m
              OR indirect_support_within_300m > indirect_support_within_800m
              OR indirect_support_within_800m > indirect_support_within_1500m
              OR office_within_300m > office_within_800m
              OR office_within_800m > office_within_1500m
              OR commercial_within_300m > commercial_within_800m
              OR commercial_within_800m > commercial_within_1500m
              OR residential_within_300m > residential_within_800m
              OR residential_within_800m > residential_within_1500m
              OR education_within_300m > education_within_800m
              OR education_within_800m > education_within_1500m
              OR hotel_within_300m > hotel_within_800m
              OR hotel_within_800m > hotel_within_1500m
              OR transit_within_300m > transit_within_800m
              OR transit_within_800m > transit_within_1500m
              OR total_poi_activity_within_300m > total_poi_activity_within_800m
              OR total_poi_activity_within_800m > total_poi_activity_within_1500m
       ), 'PASS', 'FAIL') AS result;
