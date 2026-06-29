-- Cafe Site V2 Ticket 3 raw feature and diagnostic views.
-- Run after importing the sample CSV fixture.

CREATE OR REPLACE VIEW v_site_poi_base AS
SELECT
    cities.city_code,
    cities.city_name,
    sites.site_id,
    sites.site_code,
    sites.site_name,
    sites.district,
    relationships.relationship_id,
    relationships.poi_clean_id,
    pois.poi_name,
    relationships.distance_m,
    relationships.distance_band,
    relationships.resolved_core_category,
    relationships.resolved_sub_category,
    relationships.resolution_rule_id
FROM candidate_sites AS sites
INNER JOIN cities ON cities.city_id = sites.city_id
INNER JOIN site_poi_relationships AS relationships
    ON relationships.site_id = sites.site_id
INNER JOIN pois ON pois.poi_clean_id = relationships.poi_clean_id;

CREATE OR REPLACE VIEW v_site_feature_counts AS
SELECT
    cities.city_code,
    cities.city_name,
    sites.site_id,
    sites.site_code,
    sites.site_name,
    sites.district,
    COALESCE(SUM(relationships.resolved_core_category = 'direct_coffee' AND relationships.distance_m <= 300), 0) AS direct_coffee_within_300m,
    COALESCE(SUM(relationships.resolved_core_category = 'direct_coffee' AND relationships.distance_m <= 800), 0) AS direct_coffee_within_800m,
    COALESCE(SUM(relationships.resolved_core_category = 'direct_coffee' AND relationships.distance_m <= 1500), 0) AS direct_coffee_within_1500m,
    COALESCE(SUM(relationships.resolved_core_category = 'indirect_competitor' AND relationships.distance_m <= 300), 0) AS indirect_support_within_300m,
    COALESCE(SUM(relationships.resolved_core_category = 'indirect_competitor' AND relationships.distance_m <= 800), 0) AS indirect_support_within_800m,
    COALESCE(SUM(relationships.resolved_core_category = 'indirect_competitor' AND relationships.distance_m <= 1500), 0) AS indirect_support_within_1500m,
    COALESCE(SUM(relationships.resolved_sub_category = 'office' AND relationships.distance_m <= 300), 0) AS office_within_300m,
    COALESCE(SUM(relationships.resolved_sub_category = 'office' AND relationships.distance_m <= 800), 0) AS office_within_800m,
    COALESCE(SUM(relationships.resolved_sub_category = 'office' AND relationships.distance_m <= 1500), 0) AS office_within_1500m,
    COALESCE(SUM(relationships.resolved_sub_category = 'commercial' AND relationships.distance_m <= 300), 0) AS commercial_within_300m,
    COALESCE(SUM(relationships.resolved_sub_category = 'commercial' AND relationships.distance_m <= 800), 0) AS commercial_within_800m,
    COALESCE(SUM(relationships.resolved_sub_category = 'commercial' AND relationships.distance_m <= 1500), 0) AS commercial_within_1500m,
    COALESCE(SUM(relationships.resolved_sub_category = 'residential' AND relationships.distance_m <= 300), 0) AS residential_within_300m,
    COALESCE(SUM(relationships.resolved_sub_category = 'residential' AND relationships.distance_m <= 800), 0) AS residential_within_800m,
    COALESCE(SUM(relationships.resolved_sub_category = 'residential' AND relationships.distance_m <= 1500), 0) AS residential_within_1500m,
    COALESCE(SUM(relationships.resolved_sub_category = 'education' AND relationships.distance_m <= 300), 0) AS education_within_300m,
    COALESCE(SUM(relationships.resolved_sub_category = 'education' AND relationships.distance_m <= 800), 0) AS education_within_800m,
    COALESCE(SUM(relationships.resolved_sub_category = 'education' AND relationships.distance_m <= 1500), 0) AS education_within_1500m,
    COALESCE(SUM(relationships.resolved_sub_category = 'hotel' AND relationships.distance_m <= 300), 0) AS hotel_within_300m,
    COALESCE(SUM(relationships.resolved_sub_category = 'hotel' AND relationships.distance_m <= 800), 0) AS hotel_within_800m,
    COALESCE(SUM(relationships.resolved_sub_category = 'hotel' AND relationships.distance_m <= 1500), 0) AS hotel_within_1500m,
    COALESCE(SUM(relationships.resolved_core_category = 'transit' AND relationships.distance_m <= 300), 0) AS transit_within_300m,
    COALESCE(SUM(relationships.resolved_core_category = 'transit' AND relationships.distance_m <= 800), 0) AS transit_within_800m,
    COALESCE(SUM(relationships.resolved_core_category = 'transit' AND relationships.distance_m <= 1500), 0) AS transit_within_1500m,
    COALESCE(SUM(relationships.distance_m <= 300), 0) AS total_poi_activity_within_300m,
    COALESCE(SUM(relationships.distance_m <= 800), 0) AS total_poi_activity_within_800m,
    COALESCE(SUM(relationships.distance_m <= 1500), 0) AS total_poi_activity_within_1500m,
    MIN(CASE
        WHEN relationships.resolved_core_category = 'direct_coffee'
        THEN relationships.distance_m
    END) AS nearest_direct_coffee_distance_m
FROM candidate_sites AS sites
INNER JOIN cities ON cities.city_id = sites.city_id
LEFT JOIN site_poi_relationships AS relationships
    ON relationships.site_id = sites.site_id
GROUP BY
    cities.city_code,
    cities.city_name,
    sites.site_id,
    sites.site_code,
    sites.site_name,
    sites.district;

CREATE OR REPLACE VIEW v_site_feature_diagnostics AS
SELECT
    sites.site_id,
    sites.site_code,
    COUNT(DISTINCT relationships.relationship_id) AS unique_site_poi_relationships,
    COUNT(observations.observation_id) AS joined_observation_rows,
    COUNT(observations.observation_id)
        - COUNT(DISTINCT relationships.relationship_id) AS repeated_observation_rows,
    COUNT(DISTINCT CASE
        WHEN relationships.distance_m <= 300 THEN relationships.relationship_id
    END) AS poi_within_300m,
    COUNT(DISTINCT CASE
        WHEN relationships.distance_m > 300 AND relationships.distance_m <= 800
        THEN relationships.relationship_id
    END) AS poi_300m_to_800m,
    COUNT(DISTINCT CASE
        WHEN relationships.distance_m > 800 AND relationships.distance_m <= 1500
        THEN relationships.relationship_id
    END) AS poi_800m_to_1500m,
    COUNT(DISTINCT CASE
        WHEN relationships.resolved_core_category = 'direct_coffee'
        THEN relationships.relationship_id
    END) AS resolved_direct_coffee_relationships
FROM candidate_sites AS sites
LEFT JOIN site_poi_relationships AS relationships
    ON relationships.site_id = sites.site_id
LEFT JOIN poi_observations AS observations
    ON observations.site_id = relationships.site_id
   AND observations.poi_clean_id = relationships.poi_clean_id
GROUP BY sites.site_id, sites.site_code;
