-- Cafe Site V2 minimal relational schema.
-- Target: MySQL 8.0+ with utf8mb4.
-- Select the destination database before running this file.

SET NAMES utf8mb4;

CREATE TABLE cities (
    city_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    city_code VARCHAR(50) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (city_id),
    UNIQUE KEY uq_cities_code (city_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE candidate_sites (
    site_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    city_id INT UNSIGNED NOT NULL,
    site_code VARCHAR(100) NOT NULL,
    site_name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    address VARCHAR(500) NULL,
    district VARCHAR(100) NULL,
    site_type_note VARCHAR(255) NULL,
    PRIMARY KEY (site_id),
    UNIQUE KEY uq_candidate_sites_city_code (city_id, site_code),
    KEY ix_candidate_sites_city (city_id),
    CONSTRAINT fk_candidate_sites_city
        FOREIGN KEY (city_id) REFERENCES cities (city_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE pois (
    poi_clean_id VARCHAR(255) NOT NULL,
    city_id INT UNSIGNED NOT NULL,
    amap_poi_id VARCHAR(100) NULL,
    dedup_key VARCHAR(600) NOT NULL,
    dedup_method VARCHAR(20) NOT NULL,
    poi_name VARCHAR(255) NOT NULL,
    normalized_poi_name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    amap_type VARCHAR(255) NULL,
    address VARCHAR(500) NULL,
    PRIMARY KEY (poi_clean_id),
    UNIQUE KEY uq_pois_dedup_key (dedup_key),
    UNIQUE KEY uq_pois_city_amap_id (city_id, amap_poi_id),
    KEY ix_pois_city_location (city_id, latitude, longitude),
    CONSTRAINT fk_pois_city
        FOREIGN KEY (city_id) REFERENCES cities (city_id),
    CONSTRAINT ck_pois_dedup_method
        CHECK (dedup_method IN ('amap_id', 'fallback'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE poi_keywords (
    keyword_id VARCHAR(50) NOT NULL,
    source_bucket VARCHAR(100) NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    poi_type_hint VARCHAR(255) NULL,
    description VARCHAR(500) NULL,
    PRIMARY KEY (keyword_id),
    UNIQUE KEY uq_poi_keywords_bucket_keyword (source_bucket, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE poi_category_rules (
    rule_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    rule_code VARCHAR(100) NOT NULL,
    keyword_id VARCHAR(50) NOT NULL,
    core_category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    priority SMALLINT UNSIGNED NOT NULL,
    business_meaning VARCHAR(500) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (rule_id),
    UNIQUE KEY uq_category_rules_code (rule_code),
    UNIQUE KEY uq_category_rules_assignment (
        keyword_id,
        core_category,
        sub_category
    ),
    KEY ix_category_rules_resolution (
        keyword_id,
        is_active,
        priority,
        rule_id
    ),
    CONSTRAINT fk_category_rules_keyword
        FOREIGN KEY (keyword_id) REFERENCES poi_keywords (keyword_id),
    CONSTRAINT ck_category_rules_core_category
        CHECK (
            core_category IN (
                'direct_coffee',
                'indirect_competitor',
                'demand_anchor',
                'transit',
                'other'
            )
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE poi_observations (
    observation_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_observation_key VARCHAR(255) NOT NULL,
    site_id INT UNSIGNED NOT NULL,
    poi_clean_id VARCHAR(255) NOT NULL,
    keyword_id VARCHAR(50) NOT NULL,
    search_radius_m INT UNSIGNED NOT NULL,
    observed_distance_m INT UNSIGNED NOT NULL,
    collected_at DATETIME NULL,
    source_context JSON NULL,
    PRIMARY KEY (observation_id),
    UNIQUE KEY uq_poi_observations_source_key (source_observation_key),
    KEY ix_poi_observations_site_poi (site_id, poi_clean_id),
    KEY ix_poi_observations_keyword (keyword_id),
    CONSTRAINT fk_poi_observations_site
        FOREIGN KEY (site_id) REFERENCES candidate_sites (site_id),
    CONSTRAINT fk_poi_observations_poi
        FOREIGN KEY (poi_clean_id) REFERENCES pois (poi_clean_id),
    CONSTRAINT fk_poi_observations_keyword
        FOREIGN KEY (keyword_id) REFERENCES poi_keywords (keyword_id),
    CONSTRAINT ck_poi_observations_radius
        CHECK (search_radius_m IN (300, 800, 1500)),
    CONSTRAINT ck_poi_observations_distance
        CHECK (observed_distance_m <= search_radius_m)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE site_poi_relationships (
    relationship_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    site_id INT UNSIGNED NOT NULL,
    poi_clean_id VARCHAR(255) NOT NULL,
    distance_m INT UNSIGNED NOT NULL,
    distance_band VARCHAR(20) NOT NULL,
    resolved_core_category VARCHAR(50) NOT NULL,
    resolved_sub_category VARCHAR(100) NOT NULL,
    resolution_rule_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (relationship_id),
    UNIQUE KEY uq_site_poi_relationship (site_id, poi_clean_id),
    KEY ix_relationships_site_distance (site_id, distance_m),
    KEY ix_relationships_site_core_distance (
        site_id,
        resolved_core_category,
        distance_m
    ),
    KEY ix_relationships_site_sub_distance (
        site_id,
        resolved_sub_category,
        distance_m
    ),
    CONSTRAINT fk_relationships_site
        FOREIGN KEY (site_id) REFERENCES candidate_sites (site_id),
    CONSTRAINT fk_relationships_poi
        FOREIGN KEY (poi_clean_id) REFERENCES pois (poi_clean_id),
    CONSTRAINT fk_relationships_resolution_rule
        FOREIGN KEY (resolution_rule_id) REFERENCES poi_category_rules (rule_id),
    CONSTRAINT ck_relationships_distance_band
        CHECK (
            distance_band IN (
                'within_300m',
                'within_800m',
                'within_1500m'
            )
        ),
    CONSTRAINT ck_relationships_core_category
        CHECK (
            resolved_core_category IN (
                'direct_coffee',
                'indirect_competitor',
                'demand_anchor',
                'transit',
                'other'
            )
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
