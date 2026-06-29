# Cafe Site V2 Database and Scoring Plan

## 1. Project Direction

本项目不应该只是一个咖啡店选址评分看板。

It should become an explainable site-selection data system based on AMap POI data, MySQL relational modeling, SQL feature engineering, Python scoring logic, and Streamlit visualization.

核心目标是把城市周边 POI 数据转化成可解释的选址判断。

The project should not treat demand, transit, competition, and surrounding businesses as isolated indicators.

它应该分析这些因素之间的关系。

For example, direct coffee competitors should be interpreted as both coffee demand validation and competition pressure.

在中国城市市场里，咖啡不是天然高频日常消费。

Therefore, low coffee competition should not automatically be treated as a market opportunity.

如果一个区域有很多茶饮、甜品、便利店和餐饮，但咖啡店很少，这可能不是咖啡空白。

It may indicate that local consumers prefer non-coffee beverage and snack formats.

所以模型需要把直接咖啡门店作为咖啡需求验证信号。

### 1.1 Preflight Clarification

All thresholds, caps, weights, and category rules in this plan are provisional business assumptions. They are not statistically validated claims.

V2 is an explainable decision-support model, not a revenue prediction model.

Real calibration would require rent, store sales, measured foot traffic, store survival, or operator-level performance data. Those data and that calibration work are outside the current project scope.

## 2. Core Business Logic

本项目的核心判断不是“附近有什么”。

The core question is how nearby POIs combine to indicate coffee store fit.

一个候选点的价值来自周边 POI 网络。

The meaning of each POI depends on its category, distance, density, and relationship with other POIs.

模型需要区分以下几种信号。

### 2.1 Market Activity

Market activity measures whether the surrounding area has commercial, office, residential, transit, or lifestyle activity.

它表示一个区域热不热闹。

Market activity can come from offices, malls, residential communities, schools, transit stations, hotels, restaurants, and other consumption anchors.

但市场活跃不等于咖啡需求已经成立。

### 2.2 Coffee Market Validation

Coffee market validation measures whether direct coffee competitors already exist nearby.

直接咖啡门店不是单纯负面因素。

A moderate number of nearby coffee stores can prove that coffee demand exists in the area.

没有咖啡店不一定是机会。

It may mean the local coffee category is unvalidated.

### 2.3 Competition Pressure

Competition pressure measures whether direct coffee competitors are too dense, especially within the immediate walking range.

咖啡竞品太多会带来饱和风险。

However, competition pressure should be judged relative to market activity and demand strength.

同样数量的竞品，在强需求区和弱需求区含义不同。

Saturation risk must not be interpreted when coffee demand has not been validated. Low competition plus low market activity must not be rewarded as low risk; it indicates weak or unvalidated demand.

### 2.4 Indirect Consumption Support

Indirect consumption support comes from tea drinks, bakeries, dessert shops, convenience stores, restaurants, and similar light-consumption formats.

间接业态只能证明轻饮食消费场景存在。

It should not automatically validate coffee demand.

间接业态多但咖啡少，应被视为咖啡需求未验证，而不是直接视为咖啡机会。

High indirect support with low direct-coffee validation should be labeled conservatively as `Infrastructure-rich but coffee-weak`, not automatically treated as a strong opportunity.

### 2.5 Transit-Demand Synergy

Transit should amplify existing demand rather than replace demand.

地铁站本身不等于咖啡需求。

A transit-heavy site with offices, malls, or commercial anchors nearby may be strong.

但只有交通、没有消费场景的位置，可能只是路过型点位。

## 3. Distance Band Logic

距离圈层不应该统一处理。

Different POI types should use different distance weights.

All standard distance bands are cumulative unless explicitly stated otherwise:

```text
within_300m = all POIs with distance_m <= 300
within_800m = all POIs with distance_m <= 800
within_1500m = all POIs with distance_m <= 1500
```

Column names should make this meaning explicit, for example `direct_coffee_within_300m`, `direct_coffee_within_800m`, `office_within_300m`, `office_within_800m`, and `transit_within_800m`.

If an exclusive band is introduced later, its bounds must be named explicitly, for example `office_300m_to_800m`.

### 3.1 Office Demand

办公需求应该更偏向 300m。

White-collar coffee consumption is usually convenience-driven and close-range.

白领大概率不会为了日常咖啡走很远。

A suggested office demand formula is:

```text
office_demand = 0.75 * office_within_300m + 0.25 * office_within_800m
```

1500m 办公 POI 更适合作为片区背景，不应强烈计入门店即时需求。

### 3.2 Direct Coffee Competitors

Direct coffee competitors within 300m should be weighted heavily.

近距离咖啡竞品既能验证咖啡需求，也会造成直接竞争。

A moderate direct competitor count can be positive.

An excessive direct competitor count should increase saturation risk.

### 3.3 Commercial and Leisure Demand

商业休闲需求可以适当考虑 300m 和 800m。

Malls, shopping streets, restaurants, cinemas, and lifestyle retail can create broader walking-zone demand.

但这类区域也可能带来更高租金和更强竞争。

### 3.4 Residential Demand

社区需求适合 300m 和 800m。

Residential demand may be stable but not necessarily high-upside.

它更适合社区型、复购型、低到中价位咖啡店。

### 3.5 Transit Demand

交通需求需要和办公、商业或居住需求一起判断。

Transit alone should not receive a high score.

A strong transit score should only become meaningful when surrounding demand anchors exist.

## 4. Relational Database Structure

本项目应该从扁平 CSV 结构升级为 MySQL 关系型结构。

The database should preserve the relationship between candidate sites, POIs, categories, distance bands, and business meaning.

### 4.1 Core Tables

#### candidate_sites

This table stores possible cafe locations.

```sql
CREATE TABLE candidate_sites (
    site_id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    site_name VARCHAR(100),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    address VARCHAR(255),
    district VARCHAR(100),
    site_type_note VARCHAR(255)
);
```

#### pois

This table stores collected AMap POIs.

```sql
CREATE TABLE pois (
    poi_clean_id VARCHAR(255) PRIMARY KEY,
    amap_poi_id VARCHAR(100),
    poi_name VARCHAR(255),
    normalized_poi_name VARCHAR(255),
    city VARCHAR(50),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    amap_type VARCHAR(100),
    address VARCHAR(255)
);
```

#### poi_category_rules

This table stores business classification rules.

```sql
CREATE TABLE poi_category_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    keyword_or_type VARCHAR(100),
    core_category VARCHAR(100),
    sub_category VARCHAR(100),
    priority INT,
    business_meaning TEXT
);
```

#### poi_observations

This table stores raw imported search-result evidence. Repeated observations are preserved so the source keyword, search radius, and collection context remain auditable.

```sql
CREATE TABLE poi_observations (
    observation_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    site_id INT,
    poi_clean_id VARCHAR(255),
    source_keyword VARCHAR(100),
    source_bucket VARCHAR(100),
    search_radius_m INT,
    observed_distance_m INT,
    FOREIGN KEY (site_id) REFERENCES candidate_sites(site_id),
    FOREIGN KEY (poi_clean_id) REFERENCES pois(poi_clean_id)
);
```

#### site_poi_relationships

This table is derived from unique `(site_id, poi_clean_id)` pairs in `poi_observations`. It stores one deterministic relationship and its resolved scoring categories for each site and POI.

```sql
CREATE TABLE site_poi_relationships (
    relationship_id INT PRIMARY KEY AUTO_INCREMENT,
    site_id INT,
    poi_clean_id VARCHAR(255),
    distance_m INT,
    distance_band VARCHAR(20),
    resolved_core_category VARCHAR(100),
    resolved_sub_category VARCHAR(100),
    FOREIGN KEY (site_id) REFERENCES candidate_sites(site_id),
    FOREIGN KEY (poi_clean_id) REFERENCES pois(poi_clean_id)
);
```

### 4.2 Why This Structure Matters

候选点和 POI 是多对多关系。

One candidate site can have many nearby POIs.

一个 POI 也可能同时靠近多个候选点。

The `site_poi_relationships` table preserves this many-to-many relationship.

这比把所有结果压成一个宽表更清晰。

It also makes SQL aggregation, feature engineering, and explanation logic easier to trace.

### 4.3 POI Deduplication

Use a simple, deterministic strategy for V2:

- Primary deduplication key: AMap POI ID, when available.
- Fallback deduplication key: normalized POI name, rounded latitude/longitude, and city.

The resulting primary or fallback key becomes the canonical `poi_clean_id` used by site-POI relationships.

Fuzzy matching, coordinate clustering, and advanced duplicate resolution are future improvements and are not required for this version.

### 4.4 Category Conflict Resolution

A POI may retain multiple descriptive meanings, but it must not double-count inside the same core scoring feature.

Core scoring category assignment must be deterministic, auditable, and favor specific business meanings over generic meanings. Use this priority:

1. `direct_coffee`
2. `indirect_competitor`
3. `demand_anchor`
4. `transit`
5. `other` / `generic_commercial`

`core_category` controls this broad conflict priority. `sub_category` provides the more specific business meaning used for feature columns, such as `office`, `commercial`, `residential`, `education`, `hotel`, `tea_drink`, `bakery`, or `convenience_store`.

The selected values are stored as `site_poi_relationships.resolved_core_category` and `site_poi_relationships.resolved_sub_category`. Original rule matches and descriptive context may remain available through observation evidence or diagnostic outputs.

For example, Starbucks resolves to `direct_coffee` for core coffee validation and must not also inflate the same core feature through generic commercial activity. A POI must not double-count inside one core feature, but its other descriptive context may still be retained for diagnostics or explanation.

## 5. Feature Engineering Layer

原始表不应该直接产生最终分数。

The project should first create intermediate feature views.

A suggested view is:

```text
site_feature_summary
```

This view should include base counts and distance-band features.

Example features:

```text
direct_coffee_within_300m
direct_coffee_within_800m
indirect_competitor_within_300m
indirect_competitor_within_800m
office_within_300m
office_within_800m
demand_anchor_within_300m
demand_anchor_within_800m
residential_within_300m
residential_within_800m
transit_within_300m
transit_within_800m
```

这些是基础统计特征。

They should be generated from SQL joins and grouped aggregation over `site_poi_relationships.resolved_core_category` and `resolved_sub_category`.

Feature views must not re-run conflict resolution or business scoring logic. They aggregate the stored resolved categories into raw, auditable counts; Python remains responsible for scoring transformations.

## 6. Interaction Feature Layer

项目的重点不是单独指标，而是交互特征。

Interaction features should explain how parameters change each other's meaning.

Suggested interaction features include:

```text
office_demand
market_activity
coffee_market_validation
competition_pressure
saturation_risk
indirect_consumption_support
transit_demand_synergy
unvalidated_coffee_demand_risk
```

### 6.1 Office Demand

```text
office_demand = 0.75 * office_within_300m + 0.25 * office_within_800m
```

办公需求应强烈偏向 300m。

### 6.2 Coffee Market Validation

Coffee market validation should come from moderate direct coffee presence.

```text
0 direct competitors = unvalidated coffee demand
1-3 direct competitors = validated coffee demand
4-8 direct competitors = mature but competitive
8+ direct competitors = validated demand with possible saturation pressure
```

These ranges are provisional business assumptions for fixture review, not statistically validated thresholds.

### 6.3 Saturation Risk

```text
if coffee_validation_score is low:
    saturation_risk = not_applicable or low_confidence
    primary_label = "Unvalidated coffee demand"
else:
    saturation_risk = competition_pressure adjusted by market_activity
```

竞争压力要相对市场活跃度判断。

High competition in a strong market may mean maturity.

High competition in a weak market may mean saturation.

Low competition plus low activity must not be rewarded as low saturation risk.

### 6.4 Transit-Demand Synergy

Transit amplifies existing nearby demand. Transit alone does not create coffee demand.

```text
transit_accessibility =
    normalized transit_within_800m

demand_strength =
    weighted office demand
  + weighted commercial/demand anchors
  + weighted coffee validation

transit_demand_synergy =
    transit_accessibility * demand_strength
```

交通要和真实消费场景一起判断。

Walking-network analysis, routing, and time-based accessibility are not required for V2.

### 6.5 Unvalidated Coffee Demand Risk

```text
unvalidated_coffee_demand_risk = high_market_activity + low_coffee_validation
```

热闹但没有咖啡验证，不应直接判断为机会。

It should be treated as uncertain coffee demand.

If indirect consumption support is high while direct-coffee validation remains low, use the conservative explanation `Infrastructure-rich but coffee-weak` rather than treating the site as an automatic opportunity.

### 6.6 Explanation Label Vocabulary

Standard V2 explanation labels are:

| English | Chinese |
| --- | --- |
| Validated coffee demand | 咖啡需求已验证 |
| Strong demand, high competition | 需求强但竞争高 |
| Unvalidated coffee demand | 咖啡需求未验证 |
| Infrastructure-rich but coffee-weak | 消费配套强但咖啡偏弱 |
| Low demand foundation | 需求基础不足 |
| Transit-supported demand | 交通放大型需求 |
| Oversaturated coffee cluster | 咖啡竞争过密 |

These labels are explanation aids derived from rule-based scoring. They are not separate machine-learning predictions.

## 7. Technical Workflow

本项目建议采用以下技术链路。

```text
AMap API collection
-> Python cleaning
-> MySQL relational storage
-> SQL feature views
-> Python scoring and interpretation
-> Streamlit dashboard
-> CSV and SQL export
```

MySQL and SQL handle:

- Raw imported POI observations.
- Deduplicated POIs.
- Deterministic site-POI relationships.
- Deterministic category assignments.
- Cumulative distance bands.
- Raw, auditable feature counts.
- Diagnostic views or equivalent manual-check outputs.

Python handles:

- Data collection and import orchestration.
- Score normalization.
- Coffee-validation curves.
- Competition-pressure transformations.
- Saturation-risk logic.
- Indirect-support gating.
- Transit-synergy calculation.
- Final score calculation.
- Explanation labels.
- Export-ready scoring tables.

SQL views must not embed final business scoring transformations such as validation plateaus, saturation-risk formulas, final score normalization, or explanation labels.

Streamlit handles visualization and site comparison.

## 8. Suggested Project Folder Structure

```text
db/
  schema.sql
  seed_category_rules.sql
  views.sql

scripts/
  import_candidate_sites.py
  import_pois.py
  import_relationships.py
  export_features.py

data/
  raw/
  processed/
  exports/
  sample/

docs/
  Cafe_Site_V2_Database_Scoring_Plan.md
  database_design.md
  methodology.md
```

`schema.sql` should define the database tables.

`seed_category_rules.sql` should define the POI classification rules.

`views.sql` should define SQL views for feature aggregation.

`database_design.md` should explain table relationships.

`methodology.md` should explain scoring assumptions and business logic.

## 9. What Should Be Exported

项目应该支持两种导出。

### 9.1 Database Backup

Use `mysqldump` to export full database backups.

```bash
mysqldump -u root -p cafe_site_db > exports/cafe_site_db_backup.sql
```

### 9.2 Analytical Feature Tables

Export final feature tables and score tables as CSV.

```text
site_feature_summary.csv
site_scores.csv
site_explanations.csv
```

CSV exports are useful for portfolio review and dashboard input.

SQL exports are useful for rebuilding the database.

### 9.3 CSV And MySQL Comparison

Migration comparison targets traceability, not identical scores:

- Raw site-POI relationships and feature counts must be auditable and explainable.
- Score differences are acceptable when caused by documented V2 scoring logic.
- Ranking changes must be reviewed and explained rather than automatically treated as bugs.
- Exact score parity with the existing CSV pipeline is not required.

## 10. What Should Not Be Uploaded

不要上传 `.env` 文件。

Do not upload API keys, database passwords, or private credentials.

不要上传过大的原始 API 数据。

Upload schema files, view definitions, methodology documents, and small sample data instead.

## 11. Portfolio Positioning

本项目的定位不是机器学习预测收入。

It is an explainable data analysis and decision-support project.

更准确的项目描述是：

```text
基于高德 POI 与 MySQL 关系建模的咖啡门店选址分析系统。
```

English description:

```text
An explainable coffee store site-selection analysis system using AMap POI data, MySQL relational modeling, SQL feature engineering, Python scoring logic, and Streamlit visualization.
```

## 12. Resume Direction

中文简历表述可以是：

```text
基于高德地图 POI 数据构建咖啡门店选址分析系统，使用 MySQL 设计候选点、周边 POI、距离圈层与业态分类关系表，并通过 SQL 聚合生成需求强度、咖啡需求验证、竞品压力、商圈饱和风险等可解释特征。
```

English resume version:

```text
Built an explainable coffee store site-selection analysis system using AMap POI data, MySQL relational modeling, SQL feature aggregation, Python scoring logic, and Streamlit visualization.
```

## 13. Future Build Priorities

后续构建不要急着增加新功能。

First priority is to build the database structure and verify the data flow.

Recommended build order:

```text
1. Create schema.sql
2. Create seed_category_rules.sql
3. Import small sample data
4. Build site_poi_relationships
5. Create site_feature_summary view
6. Calculate interaction features in Python
7. Export feature CSV
8. Connect results back to Streamlit
9. Update methodology documentation
```

每一步都应该能单独验证。

Do not over-engineer with machine learning before real store performance data exists.

This project should stay explainable, business-driven, and reproducible.

The current V2 roadmap does not include machine learning, revenue prediction, city-specific threshold calibration, PostGIS, Airflow, Docker, cloud deployment, real-time data pipelines, complex fuzzy matching, walking-route analysis, user login, or agent integration. These are future considerations only if later evidence establishes a clear need.
