-- Cafe Site V2 keyword and deterministic category-rule seed.
-- Run after sql/schema.sql.

SET NAMES utf8mb4;

INSERT INTO poi_keywords (
    keyword_id,
    source_bucket,
    keyword,
    poi_type_hint,
    description
) VALUES
    ('KW_DIRECT_001', 'direct_competitor', '咖啡', '咖啡厅', '泛咖啡门店关键词'),
    ('KW_DIRECT_002', 'direct_competitor', '星巴克', '咖啡厅', '头部连锁咖啡品牌'),
    ('KW_DIRECT_003', 'direct_competitor', '瑞幸咖啡', '咖啡厅', '连锁咖啡品牌'),
    ('KW_DIRECT_004', 'direct_competitor', '库迪咖啡', '咖啡厅', '连锁咖啡品牌'),
    ('KW_INDIRECT_001', 'indirect_competitor', '奶茶', '饮品店', '茶饮替代消费'),
    ('KW_INDIRECT_002', 'indirect_competitor', '茶饮', '饮品店', '新式茶饮消费'),
    ('KW_INDIRECT_003', 'indirect_competitor', '面包甜点', '糕饼店', '烘焙和甜品消费'),
    ('KW_INDIRECT_004', 'indirect_competitor', '甜品', '甜品店', '甜品休闲消费'),
    ('KW_INDIRECT_005', 'indirect_competitor', '便利店', '零售服务', '便利型轻消费'),
    ('KW_DEMAND_001', 'demand_anchor', '写字楼', '商务住宅', '办公需求锚点'),
    ('KW_DEMAND_002', 'demand_anchor', '购物中心', '购物服务', '商业需求锚点'),
    ('KW_DEMAND_003', 'demand_anchor', '大学', '科教文化服务', '教育需求锚点'),
    ('KW_DEMAND_004', 'demand_anchor', '住宅小区', '商务住宅', '居住需求锚点'),
    ('KW_DEMAND_005', 'demand_anchor', '酒店', '住宿服务', '住宿需求锚点'),
    ('KW_TRANSIT_001', 'transit', '地铁站', '交通设施服务', '轨道交通锚点'),
    ('KW_TRANSIT_002', 'transit', '公交站', '交通设施服务', '公交交通锚点'),
    ('KW_TRANSIT_003', 'transit', '停车场', '交通设施服务', '停车可达性锚点'),
    ('KW_TRANSIT_004', 'transit', '高铁站', '交通设施服务', '交通枢纽锚点'),
    ('KW_OTHER_001', 'other', '商业服务', '商业服务', '通用商业活动诊断项');

INSERT INTO poi_category_rules (
    rule_code,
    keyword_id,
    core_category,
    sub_category,
    priority,
    business_meaning
) VALUES
    ('RULE_DIRECT_COFFEE_GENERIC', 'KW_DIRECT_001', 'direct_coffee', 'coffee_shop', 10, '直接咖啡需求验证与竞争压力'),
    ('RULE_DIRECT_COFFEE_STARBUCKS', 'KW_DIRECT_002', 'direct_coffee', 'coffee_shop', 10, '直接咖啡需求验证与竞争压力'),
    ('RULE_DIRECT_COFFEE_LUCKIN', 'KW_DIRECT_003', 'direct_coffee', 'coffee_shop', 10, '直接咖啡需求验证与竞争压力'),
    ('RULE_DIRECT_COFFEE_COTTI', 'KW_DIRECT_004', 'direct_coffee', 'coffee_shop', 10, '直接咖啡需求验证与竞争压力'),
    ('RULE_INDIRECT_MILK_TEA', 'KW_INDIRECT_001', 'indirect_competitor', 'tea_drink', 20, '替代性现制茶饮消费'),
    ('RULE_INDIRECT_TEA_DRINK', 'KW_INDIRECT_002', 'indirect_competitor', 'tea_drink', 20, '替代性现制茶饮消费'),
    ('RULE_INDIRECT_BAKERY', 'KW_INDIRECT_003', 'indirect_competitor', 'bakery', 20, '烘焙和甜点消费支持'),
    ('RULE_INDIRECT_DESSERT', 'KW_INDIRECT_004', 'indirect_competitor', 'bakery', 20, '甜品和休闲消费支持'),
    ('RULE_INDIRECT_CONVENIENCE', 'KW_INDIRECT_005', 'indirect_competitor', 'convenience_store', 20, '便利型轻消费支持'),
    ('RULE_DEMAND_OFFICE', 'KW_DEMAND_001', 'demand_anchor', 'office', 30, '工作日办公需求'),
    ('RULE_DEMAND_COMMERCIAL', 'KW_DEMAND_002', 'demand_anchor', 'commercial', 30, '购物和休闲商业需求'),
    ('RULE_DEMAND_EDUCATION', 'KW_DEMAND_003', 'demand_anchor', 'education', 30, '学生和教职工需求'),
    ('RULE_DEMAND_RESIDENTIAL', 'KW_DEMAND_004', 'demand_anchor', 'residential', 30, '社区日常需求'),
    ('RULE_DEMAND_HOTEL', 'KW_DEMAND_005', 'demand_anchor', 'hotel', 30, '差旅和游客需求'),
    ('RULE_TRANSIT_METRO', 'KW_TRANSIT_001', 'transit', 'metro_station', 40, '轨道交通可达性'),
    ('RULE_TRANSIT_BUS', 'KW_TRANSIT_002', 'transit', 'bus_stop', 40, '公交可达性'),
    ('RULE_TRANSIT_PARKING', 'KW_TRANSIT_003', 'transit', 'parking', 40, '自驾可达性'),
    ('RULE_TRANSIT_RAIL', 'KW_TRANSIT_004', 'transit', 'rail_station', 40, '交通枢纽可达性'),
    ('RULE_OTHER_COMMERCIAL', 'KW_OTHER_001', 'other', 'commercial', 50, '通用商业背景，仅用于低优先级诊断');
