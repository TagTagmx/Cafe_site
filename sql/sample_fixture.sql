-- Cafe Site V2 GitHub-safe synthetic fixture.
-- Run after sql/schema.sql and sql/seed_category_rules.sql in a clean database.
-- The data is fictional and exists only to exercise Ticket 2 edge cases.

SET NAMES utf8mb4;
START TRANSACTION;

INSERT INTO cities (city_id, city_code, city_name)
VALUES (1, 'fixture_city', '示例城市');

INSERT INTO candidate_sites (
    site_id,
    city_id,
    site_code,
    site_name,
    latitude,
    longitude,
    district,
    site_type_note
) VALUES
    (101, 1, 'moderate_coffee', '适度咖啡验证点', 32.0600000, 118.7900000, '示例区', 'moderate_direct_coffee'),
    (102, 1, 'weak_foundation', '低活跃弱基础点', 32.0610000, 118.7910000, '示例区', 'low_coffee_low_activity'),
    (103, 1, 'infra_coffee_weak', '配套强咖啡弱点', 32.0620000, 118.7920000, '示例区', 'high_indirect_low_direct'),
    (104, 1, 'mature_market', '成熟高活跃市场点', 32.0630000, 118.7930000, '示例区', 'high_direct_high_activity'),
    (105, 1, 'possible_saturation', '可能饱和点', 32.0640000, 118.7940000, '示例区', 'high_direct_low_activity'),
    (106, 1, 'transit_weak_demand', '交通强需求弱点', 32.0650000, 118.7950000, '示例区', 'transit_heavy_weak_demand'),
    (107, 1, 'category_conflict', '分类冲突检查点', 32.0660000, 118.7960000, '示例区', 'conflicting_poi_category'),
    (108, 1, 'duplicate_observation', '重复观察检查点', 32.0670000, 118.7970000, '示例区', 'duplicate_raw_observation'),
    (109, 1, 'zero_nearby', '零周边POI检查点', 32.0680000, 118.7980000, '示例区', 'zero_nearby_poi');

INSERT INTO pois (
    poi_clean_id,
    city_id,
    amap_poi_id,
    dedup_key,
    dedup_method,
    poi_name,
    normalized_poi_name,
    latitude,
    longitude,
    amap_type,
    address
) VALUES
    ('POI_COFFEE_01', 1, 'AMAP_COFFEE_01', 'amap:AMAP_COFFEE_01', 'amap_id', '星巴克示例店', '星巴克示例店', 32.0601000, 118.7901000, '咖啡厅', '示例地址1'),
    ('POI_COFFEE_02', 1, 'AMAP_COFFEE_02', 'amap:AMAP_COFFEE_02', 'amap_id', '瑞幸咖啡示例店', '瑞幸咖啡示例店', 32.0602000, 118.7902000, '咖啡厅', '示例地址2'),
    ('POI_COFFEE_03', 1, 'AMAP_COFFEE_03', 'amap:AMAP_COFFEE_03', 'amap_id', '库迪咖啡示例店', '库迪咖啡示例店', 32.0603000, 118.7903000, '咖啡厅', '示例地址3'),
    ('POI_COFFEE_04', 1, 'AMAP_COFFEE_04', 'amap:AMAP_COFFEE_04', 'amap_id', '本地咖啡A店', '本地咖啡a店', 32.0604000, 118.7904000, '咖啡厅', '示例地址4'),
    ('POI_COFFEE_05', 1, 'AMAP_COFFEE_05', 'amap:AMAP_COFFEE_05', 'amap_id', '本地咖啡B店', '本地咖啡b店', 32.0605000, 118.7905000, '咖啡厅', '示例地址5'),
    ('POI_TEA_01', 1, 'AMAP_TEA_01', 'amap:AMAP_TEA_01', 'amap_id', '示例茶饮一店', '示例茶饮一店', 32.0611000, 118.7911000, '饮品店', '示例地址6'),
    ('POI_TEA_02', 1, 'AMAP_TEA_02', 'amap:AMAP_TEA_02', 'amap_id', '示例茶饮二店', '示例茶饮二店', 32.0612000, 118.7912000, '饮品店', '示例地址7'),
    ('POI_BAKERY_01', 1, 'AMAP_BAKERY_01', 'amap:AMAP_BAKERY_01', 'amap_id', '示例面包店', '示例面包店', 32.0613000, 118.7913000, '糕饼店', '示例地址8'),
    ('POI_CONVENIENCE_01', 1, 'AMAP_CONVENIENCE_01', 'amap:AMAP_CONVENIENCE_01', 'amap_id', '示例便利店', '示例便利店', 32.0614000, 118.7914000, '零售服务', '示例地址9'),
    ('POI_OFFICE_01', 1, 'AMAP_OFFICE_01', 'amap:AMAP_OFFICE_01', 'amap_id', '示例写字楼一座', '示例写字楼一座', 32.0621000, 118.7921000, '商务住宅', '示例地址10'),
    ('POI_OFFICE_02', 1, 'AMAP_OFFICE_02', 'amap:AMAP_OFFICE_02', 'amap_id', '示例写字楼二座', '示例写字楼二座', 32.0622000, 118.7922000, '商务住宅', '示例地址11'),
    ('POI_MALL_01', 1, 'AMAP_MALL_01', 'amap:AMAP_MALL_01', 'amap_id', '示例购物中心', '示例购物中心', 32.0623000, 118.7923000, '购物服务', '示例地址12'),
    ('POI_RESIDENTIAL_01', 1, 'AMAP_RESIDENTIAL_01', 'amap:AMAP_RESIDENTIAL_01', 'amap_id', '示例住宅小区', '示例住宅小区', 32.0624000, 118.7924000, '商务住宅', '示例地址13'),
    ('POI_METRO_01', 1, 'AMAP_METRO_01', 'amap:AMAP_METRO_01', 'amap_id', '示例地铁站', '示例地铁站', 32.0631000, 118.7931000, '交通设施服务', '示例地址14'),
    ('POI_BUS_01', 1, 'AMAP_BUS_01', 'amap:AMAP_BUS_01', 'amap_id', '示例公交站', '示例公交站', 32.0632000, 118.7932000, '交通设施服务', '示例地址15'),
    ('POI_PARKING_01', 1, 'AMAP_PARKING_01', 'amap:AMAP_PARKING_01', 'amap_id', '示例停车场', '示例停车场', 32.0633000, 118.7933000, '交通设施服务', '示例地址16'),
    (
        'POI_OTHER_FALLBACK_01',
        1,
        NULL,
        'fallback:示例商业服务点|32.0634|118.7934|fixture_city',
        'fallback',
        '示例商业服务点',
        '示例商业服务点',
        32.0634000,
        118.7934000,
        '商业服务',
        '示例地址17'
    );

INSERT INTO poi_observations (
    source_observation_key,
    site_id,
    poi_clean_id,
    keyword_id,
    search_radius_m,
    observed_distance_m,
    collected_at,
    source_context
) VALUES
    -- Moderate direct coffee: two coffee POIs plus nearby demand anchors.
    ('OBS_MOD_001', 101, 'POI_COFFEE_01', 'KW_DIRECT_002', 300, 120, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'moderate_direct_coffee')),
    ('OBS_MOD_002', 101, 'POI_COFFEE_01', 'KW_DIRECT_002', 800, 120, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'repeated_radius_observation')),
    ('OBS_MOD_003', 101, 'POI_COFFEE_02', 'KW_DIRECT_003', 300, 260, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'moderate_direct_coffee')),
    ('OBS_MOD_004', 101, 'POI_OFFICE_01', 'KW_DEMAND_001', 300, 180, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'nearby_office')),
    ('OBS_MOD_005', 101, 'POI_MALL_01', 'KW_DEMAND_002', 800, 650, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'commercial_anchor')),

    -- Low coffee and low activity.
    ('OBS_WEAK_001', 102, 'POI_OTHER_FALLBACK_01', 'KW_OTHER_001', 800, 700, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'low_coffee_low_activity')),

    -- High indirect support with no direct coffee.
    ('OBS_INFRA_001', 103, 'POI_TEA_01', 'KW_INDIRECT_001', 300, 100, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_indirect_low_direct')),
    ('OBS_INFRA_002', 103, 'POI_TEA_02', 'KW_INDIRECT_002', 300, 250, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_indirect_low_direct')),
    ('OBS_INFRA_003', 103, 'POI_BAKERY_01', 'KW_INDIRECT_003', 300, 180, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_indirect_low_direct')),
    ('OBS_INFRA_004', 103, 'POI_CONVENIENCE_01', 'KW_INDIRECT_005', 300, 300, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_indirect_low_direct')),
    ('OBS_INFRA_005', 103, 'POI_OFFICE_01', 'KW_DEMAND_001', 800, 450, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'supporting_office')),
    ('OBS_INFRA_006', 103, 'POI_MALL_01', 'KW_DEMAND_002', 800, 700, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'supporting_commercial')),

    -- High direct coffee with high activity.
    ('OBS_MATURE_001', 104, 'POI_COFFEE_01', 'KW_DIRECT_002', 300, 100, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_high_activity')),
    ('OBS_MATURE_002', 104, 'POI_COFFEE_02', 'KW_DIRECT_003', 300, 180, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_high_activity')),
    ('OBS_MATURE_003', 104, 'POI_COFFEE_03', 'KW_DIRECT_004', 300, 250, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_high_activity')),
    ('OBS_MATURE_004', 104, 'POI_COFFEE_04', 'KW_DIRECT_001', 800, 500, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_high_activity')),
    ('OBS_MATURE_005', 104, 'POI_COFFEE_05', 'KW_DIRECT_001', 800, 750, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_high_activity')),
    ('OBS_MATURE_006', 104, 'POI_OFFICE_01', 'KW_DEMAND_001', 300, 100, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_activity')),
    ('OBS_MATURE_007', 104, 'POI_OFFICE_02', 'KW_DEMAND_001', 300, 280, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_activity')),
    ('OBS_MATURE_008', 104, 'POI_MALL_01', 'KW_DEMAND_002', 300, 300, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_activity')),
    ('OBS_MATURE_009', 104, 'POI_RESIDENTIAL_01', 'KW_DEMAND_004', 800, 700, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_activity')),
    ('OBS_MATURE_010', 104, 'POI_METRO_01', 'KW_TRANSIT_001', 800, 600, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'transit_support')),

    -- High direct coffee with weak activity.
    ('OBS_SAT_001', 105, 'POI_COFFEE_01', 'KW_DIRECT_002', 300, 80, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_low_activity')),
    ('OBS_SAT_002', 105, 'POI_COFFEE_02', 'KW_DIRECT_003', 300, 120, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_low_activity')),
    ('OBS_SAT_003', 105, 'POI_COFFEE_03', 'KW_DIRECT_004', 300, 160, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_low_activity')),
    ('OBS_SAT_004', 105, 'POI_COFFEE_04', 'KW_DIRECT_001', 300, 220, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_low_activity')),
    ('OBS_SAT_005', 105, 'POI_COFFEE_05', 'KW_DIRECT_001', 300, 280, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'high_direct_low_activity')),
    ('OBS_SAT_006', 105, 'POI_OTHER_FALLBACK_01', 'KW_OTHER_001', 800, 700, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'weak_activity')),

    -- Transit-heavy site with weak demand.
    ('OBS_TRANSIT_001', 106, 'POI_METRO_01', 'KW_TRANSIT_001', 300, 100, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'transit_heavy_weak_demand')),
    ('OBS_TRANSIT_002', 106, 'POI_BUS_01', 'KW_TRANSIT_002', 300, 150, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'transit_heavy_weak_demand')),
    ('OBS_TRANSIT_003', 106, 'POI_PARKING_01', 'KW_TRANSIT_003', 300, 300, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'transit_heavy_weak_demand')),
    ('OBS_TRANSIT_004', 106, 'POI_OTHER_FALLBACK_01', 'KW_OTHER_001', 800, 700, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'weak_demand')),

    -- One POI with direct-coffee, demand-anchor, and generic-commercial meanings.
    ('OBS_CONFLICT_001', 107, 'POI_COFFEE_01', 'KW_DIRECT_002', 300, 120, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'conflicting_category')),
    ('OBS_CONFLICT_002', 107, 'POI_COFFEE_01', 'KW_DEMAND_002', 300, 120, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'conflicting_category')),
    ('OBS_CONFLICT_003', 107, 'POI_COFFEE_01', 'KW_OTHER_001', 300, 120, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'conflicting_category')),

    -- Repeated observations for one site-POI pair.
    ('OBS_DUP_001', 108, 'POI_COFFEE_02', 'KW_DIRECT_001', 300, 200, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'duplicate_observation')),
    ('OBS_DUP_002', 108, 'POI_COFFEE_02', 'KW_DIRECT_003', 800, 200, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'duplicate_observation')),
    ('OBS_DUP_003', 108, 'POI_COFFEE_02', 'KW_DIRECT_003', 1500, 200, '2026-01-01 10:00:00', JSON_OBJECT('scenario', 'duplicate_observation'));

INSERT INTO site_poi_relationships (
    site_id,
    poi_clean_id,
    distance_m,
    distance_band,
    resolved_core_category,
    resolved_sub_category,
    resolution_rule_id
)
SELECT
    ranked.site_id,
    ranked.poi_clean_id,
    ranked.minimum_distance_m,
    CASE
        WHEN ranked.minimum_distance_m <= 300 THEN 'within_300m'
        WHEN ranked.minimum_distance_m <= 800 THEN 'within_800m'
        ELSE 'within_1500m'
    END AS distance_band,
    ranked.core_category,
    ranked.sub_category,
    ranked.rule_id
FROM (
    SELECT
        observations.site_id,
        observations.poi_clean_id,
        MIN(observations.observed_distance_m) OVER (
            PARTITION BY observations.site_id, observations.poi_clean_id
        ) AS minimum_distance_m,
        rules.rule_id,
        rules.core_category,
        rules.sub_category,
        ROW_NUMBER() OVER (
            PARTITION BY observations.site_id, observations.poi_clean_id
            ORDER BY rules.priority ASC, rules.rule_id ASC
        ) AS resolution_rank
    FROM poi_observations AS observations
    INNER JOIN poi_category_rules AS rules
        ON rules.keyword_id = observations.keyword_id
       AND rules.is_active = TRUE
) AS ranked
WHERE ranked.resolution_rank = 1;

COMMIT;
