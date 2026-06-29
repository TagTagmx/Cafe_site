-- Drop Cafe Site V2 views and tables in dependency order.
-- Run only against the dedicated local V2 database.

SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS v_site_feature_diagnostics;
DROP VIEW IF EXISTS v_site_feature_counts;
DROP VIEW IF EXISTS v_site_poi_base;

DROP TABLE IF EXISTS site_poi_relationships;
DROP TABLE IF EXISTS poi_observations;
DROP TABLE IF EXISTS poi_category_rules;
DROP TABLE IF EXISTS poi_keywords;
DROP TABLE IF EXISTS pois;
DROP TABLE IF EXISTS candidate_sites;
DROP TABLE IF EXISTS cities;

SET FOREIGN_KEY_CHECKS = 1;
