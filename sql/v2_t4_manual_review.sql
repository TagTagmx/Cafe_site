-- Cafe Site V2 Ticket 4: eight read-only SQL review queries.
-- These inspect the raw evidence consumed by Python scoring.

-- 1. Proves the feature view has exactly one row per candidate site.
SELECT
    COUNT(*) AS feature_rows,
    COUNT(DISTINCT site_id) AS unique_sites
FROM v_site_feature_counts;

-- 2. Proves cumulative distance counts never decrease at wider radii.
SELECT site_code
FROM v_site_feature_counts
WHERE direct_coffee_within_300m > direct_coffee_within_800m
   OR direct_coffee_within_800m > direct_coffee_within_1500m
   OR total_poi_activity_within_300m > total_poi_activity_within_800m
   OR total_poi_activity_within_800m > total_poi_activity_within_1500m;

-- 3. Shows the exact 300m-heavy raw signals passed to Python transformations.
SELECT
    site_code,
    0.75 * direct_coffee_within_300m
        + 0.25 * direct_coffee_within_800m AS direct_coffee_core_raw,
    0.75 * office_within_300m
        + 0.25 * office_within_800m AS office_demand_raw
FROM v_site_feature_counts
ORDER BY site_code;

-- 4. Shows direct-coffee evidence used differently for validation and pressure.
SELECT
    site_code,
    direct_coffee_within_300m,
    direct_coffee_within_800m,
    direct_coffee_within_1500m,
    nearest_direct_coffee_distance_m
FROM v_site_feature_counts
ORDER BY direct_coffee_within_800m DESC, site_code;

-- 5. Finds the indirect-support trap: many substitutes but little direct coffee.
SELECT
    site_code,
    direct_coffee_within_800m,
    indirect_support_within_800m,
    total_poi_activity_within_800m
FROM v_site_feature_counts
WHERE indirect_support_within_800m >= 3
  AND direct_coffee_within_800m = 0
ORDER BY indirect_support_within_800m DESC;

-- 6. Finds transit-heavy sites whose surrounding demand foundation is weak.
SELECT
    site_code,
    transit_within_800m,
    office_within_800m,
    commercial_within_800m,
    residential_within_800m,
    direct_coffee_within_800m
FROM v_site_feature_counts
WHERE transit_within_800m >= 2
ORDER BY transit_within_800m DESC;

-- 7. Compares high direct-coffee clusters with their wider market activity.
SELECT
    site_code,
    direct_coffee_within_300m,
    direct_coffee_within_800m,
    total_poi_activity_within_300m,
    total_poi_activity_within_800m
FROM v_site_feature_counts
WHERE direct_coffee_within_800m >= 3
ORDER BY direct_coffee_within_800m DESC, total_poi_activity_within_800m DESC;

-- 8. Proves 1500m coffee is retained as context but separated from core pressure.
SELECT
    site_code,
    direct_coffee_within_800m AS core_pressure_context,
    direct_coffee_within_1500m AS district_background,
    direct_coffee_within_1500m - direct_coffee_within_800m
        AS coffee_between_800m_and_1500m
FROM v_site_feature_counts
ORDER BY coffee_between_800m_and_1500m DESC, site_code;
