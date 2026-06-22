from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CITY_OPTIONS = {
    "徐州": {
        "city_id": "xuzhou",
        "city_name": "徐州",
        "scores_path": PROJECT_ROOT / "data" / "processed" / "site_scores.csv",
        "metrics_path": PROJECT_ROOT / "data" / "processed" / "site_metrics.csv",
        "caption": "徐州 MVP 基于人工候选点、高德 POI、半径统计和可解释 v2 权重模型。",
    },
    "南京": {
        "city_id": "nanjing",
        "city_name": "南京",
        "scores_path": PROJECT_ROOT / "data" / "processed" / "nanjing" / "site_scores.csv",
        "metrics_path": PROJECT_ROOT / "data" / "processed" / "nanjing" / "site_metrics.csv",
        "caption": "南京首轮结果复用冻结的 v2 评分模型，用于第二城市验证。",
    },
}

COMPONENT_COLUMNS = [
    "demand_score",
    "accessibility_score",
    "commercial_maturity_score",
    "competition_fit_score",
]

COMPONENT_LABELS = {
    "demand_score": "需求强度",
    "accessibility_score": "交通可达性",
    "commercial_maturity_score": "商业成熟度",
    "competition_fit_score": "竞争适配分",
}

METRIC_COLUMNS = [
    "direct_competitor_count_300m",
    "direct_competitor_count_800m",
    "direct_competitor_count_1500m",
    "demand_anchor_count_300m",
    "demand_anchor_count_800m",
    "demand_anchor_count_1500m",
    "transit_count_300m",
    "transit_count_800m",
    "transit_count_1500m",
    "nearest_direct_competitor_distance_m",
]


st.set_page_config(
    page_title="咖啡选址评分",
    layout="wide",
)


@st.cache_data
def load_scores(scores_path: Path, metrics_path: Path) -> pd.DataFrame:
    if not scores_path.exists():
        st.error(f"Missing score file: {scores_path}")
        st.stop()

    data = pd.read_csv(scores_path, encoding="utf-8-sig")
    if metrics_path.exists():
        metrics = pd.read_csv(metrics_path, encoding="utf-8-sig")
        metric_columns = [
            column
            for column in metrics.columns
            if column != "site_id" and column not in data.columns
        ]
        if metric_columns:
            data = data.merge(
                metrics.loc[:, ["site_id", *metric_columns]],
                on="site_id",
                how="left",
            )

    numeric_columns = [
        "site_rank",
        "site_score",
        "v1_site_rank",
        "v1_site_score",
        "rank_change_vs_v1",
        "competitor_pressure_score",
        "competitor_density_raw",
        *COMPONENT_COLUMNS,
        *METRIC_COLUMNS,
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    return data.sort_values("site_rank")


def format_score(value: object) -> str:
    numeric_value = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric_value):
        return "N/A"
    return f"{float(numeric_value):.2f}"


def metric_value(row: pd.Series, column: str, suffix: str = "") -> str:
    if column not in row.index:
        return "N/A"
    value = pd.to_numeric(row[column], errors="coerce")
    if pd.isna(value):
        return "N/A"
    return f"{int(value)}{suffix}"


def available_columns(data: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in data.columns]


def numeric_value(row: pd.Series, column: str) -> float | None:
    if column not in row.index:
        return None
    value = pd.to_numeric(row[column], errors="coerce")
    if pd.isna(value):
        return None
    return float(value)


def describe_level(value: float | None, high: float, medium: float) -> str:
    if value is None:
        return "数据不足"
    if value >= high:
        return "较强"
    if value >= medium:
        return "中等"
    return "偏弱"


def build_preliminary_conclusion(scores: pd.DataFrame) -> str:
    top_three = scores.head(3)["area_name"].tolist()
    top_names = "、".join(top_three)
    leader = scores.iloc[0]
    fifth_score = numeric_value(scores.iloc[min(4, len(scores) - 1)], "site_score")
    leader_score = numeric_value(leader, "site_score")
    score_gap = ""
    if leader_score is not None and fifth_score is not None:
        score_gap = f"第一名与第五名分差约 {leader_score - fifth_score:.1f} 分，说明核心商圈与非核心候选点之间已有明显梯度。"

    return (
        f"当前 v2 模型下，{top_names} 位于前列，优势主要来自需求锚点、交通可达性、商业成熟度和竞争适配分的共同支撑。"
        f"{score_gap}"
        " 该结果适合作为下一轮人工踏勘和租金核验的优先级参考，不应直接等同于最终开店决策。"
    )


def build_site_interpretation(row: pd.Series) -> dict[str, str]:
    rank = metric_value(row, "site_rank")
    site_score = format_score(row.get("site_score"))
    demand = numeric_value(row, "demand_score")
    transit = numeric_value(row, "accessibility_score")
    maturity = numeric_value(row, "commercial_maturity_score")
    competition_fit = numeric_value(row, "competition_fit_score")
    competition_pressure = numeric_value(row, "competitor_pressure_score")
    competitor_density = numeric_value(row, "competitor_density_raw")

    direct_800 = metric_value(row, "direct_competitor_count_800m")
    direct_1500 = metric_value(row, "direct_competitor_count_1500m")
    demand_1500 = metric_value(row, "demand_anchor_count_1500m")
    transit_1500 = metric_value(row, "transit_count_1500m")
    nearest_competitor = metric_value(row, "nearest_direct_competitor_distance_m", " m")

    overall = (
        f"当前排名第 {rank}，v2 总分 {site_score}。"
        f"需求强度{describe_level(demand, 75, 40)}，交通可达性{describe_level(transit, 75, 40)}，"
        f"商业成熟度{describe_level(maturity, 75, 40)}。"
    )

    demand_text = (
        f"1500m 内需求锚点为 {demand_1500} 个。"
        f"需求分为 {format_score(demand)}，反映办公、购物、居住、学校、酒店等潜在客流的综合密度。"
    )
    transit_text = (
        f"1500m 内交通相关 POI 为 {transit_1500} 个。"
        f"可达性分为 {format_score(transit)}，用于判断通勤、换乘、自驾停车等到店便利性。"
    )
    competitor_text = (
        f"800m / 1500m 内直接竞品分别为 {direct_800} / {direct_1500} 个，最近直接竞品距离为 {nearest_competitor}。"
        f"竞争强度为 {format_score(competition_pressure)}（高=更拥挤），加权竞品密度为 {format_score(competitor_density)}。"
        f"竞争适配分为 {format_score(competition_fit)}（高=更接近适中竞争），该项在 v2 中为正向分：竞品过少可能代表需求未被验证，竞品过多则可能代表过度拥挤。"
    )

    return {
        "overall": overall,
        "demand": demand_text,
        "transit": transit_text,
        "competitor": competitor_text,
    }


def horizontal_score_chart(scores: pd.DataFrame) -> alt.Chart:
    chart_data = scores.loc[:, ["area_name", "site_score"]].copy()
    chart_data["site_score"] = pd.to_numeric(chart_data["site_score"], errors="coerce")
    return (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X("site_score:Q", title="v2 总分"),
            y=alt.Y("area_name:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("area_name:N", title="候选区域"),
                alt.Tooltip("site_score:Q", title="v2 总分", format=".2f"),
            ],
            color=alt.Color("site_score:Q", legend=None, scale=alt.Scale(scheme="blues")),
        )
        .properties(height=280)
    )


def main() -> None:
    selected_city_name = st.sidebar.radio(
        "城市",
        list(CITY_OPTIONS.keys()),
        index=0,
        help="切换城市会加载对应城市的评分与指标文件。",
    )
    selected_city = CITY_OPTIONS[selected_city_name]

    scores = load_scores(
        selected_city["scores_path"],
        selected_city["metrics_path"],
    )
    top_site = scores.iloc[0]

    st.title(f"{selected_city['city_name']}咖啡店选址评估")
    st.caption(selected_city["caption"])

    metric_cols = st.columns(4)
    metric_cols[0].metric("候选点", f"{len(scores)}")
    metric_cols[1].metric("最高分", format_score(scores["site_score"].max()))
    metric_cols[2].metric("第一名", str(top_site.get("area_name", "N/A")))
    metric_cols[3].metric(
        "最近竞品距离",
        metric_value(top_site, "nearest_direct_competitor_distance_m", " m"),
    )

    st.subheader("初步结论")
    st.info(build_preliminary_conclusion(scores))

    st.subheader("候选点总分对比")
    st.altair_chart(horizontal_score_chart(scores), width="stretch")

    st.subheader("候选点排名")
    ranking_columns = [
        "site_rank",
        "area_name",
        "district",
        "site_score",
        "v1_site_rank",
        "rank_change_vs_v1",
        "demand_score",
        "accessibility_score",
        "commercial_maturity_score",
        "competition_fit_score",
        "competitor_pressure_score",
        "direct_competitor_count_1500m",
        "demand_anchor_count_1500m",
        "transit_count_1500m",
        "nearest_direct_competitor_distance_m",
    ]
    st.dataframe(
        scores.loc[:, available_columns(scores, ranking_columns)],
        width="stretch",
        hide_index=True,
        column_config={
            "site_rank": st.column_config.NumberColumn("排名", format="%d"),
            "area_name": "候选区域",
            "district": "区县",
            "site_score": st.column_config.NumberColumn("v2 总分", format="%.2f"),
            "v1_site_rank": st.column_config.NumberColumn("v1 排名", format="%d"),
            "rank_change_vs_v1": st.column_config.NumberColumn("排名变化", format="%d"),
            "demand_score": st.column_config.NumberColumn("需求", format="%.2f"),
            "accessibility_score": st.column_config.NumberColumn("可达性", format="%.2f"),
            "commercial_maturity_score": st.column_config.NumberColumn("商业成熟度", format="%.2f"),
            "competition_fit_score": st.column_config.NumberColumn("竞争适配分", format="%.2f"),
            "competitor_pressure_score": st.column_config.NumberColumn("竞争强度", format="%.2f"),
            "direct_competitor_count_1500m": "1500m 直接竞品",
            "demand_anchor_count_1500m": "1500m 需求锚点",
            "transit_count_1500m": "1500m 交通点",
            "nearest_direct_competitor_distance_m": "最近直接竞品 m",
        },
    )

    left, right = st.columns([1.15, 0.85])

    with left:
        st.subheader("单点详情")
        selected_area = st.selectbox(
            "候选区域",
            scores["area_name"].tolist(),
            index=0,
            label_visibility="collapsed",
        )
        selected = scores[scores["area_name"] == selected_area].iloc[0]

        st.markdown(f"**{selected.get('area_name', 'N/A')}**")
        st.write(selected.get("address", "N/A"))
        st.metric("v2 总分", format_score(selected.get("site_score")), f"排名 {metric_value(selected, 'site_rank')}")

        component_cards = st.columns(4)
        for index, column in enumerate(COMPONENT_COLUMNS):
            component_cards[index].metric(
                COMPONENT_LABELS[column],
                format_score(selected.get(column)),
            )

        detail = pd.DataFrame(
            [
                {"指标": "300m 直接竞品", "数值": metric_value(selected, "direct_competitor_count_300m")},
                {"指标": "800m 直接竞品", "数值": metric_value(selected, "direct_competitor_count_800m")},
                {"指标": "1500m 直接竞品", "数值": metric_value(selected, "direct_competitor_count_1500m")},
                {"指标": "竞争强度（高=拥挤）", "数值": format_score(selected.get("competitor_pressure_score"))},
                {"指标": "竞争适配分（高=适中）", "数值": format_score(selected.get("competition_fit_score"))},
                {"指标": "1500m 需求锚点", "数值": metric_value(selected, "demand_anchor_count_1500m")},
                {"指标": "1500m 交通点", "数值": metric_value(selected, "transit_count_1500m")},
                {
                    "指标": "最近直接竞品 m",
                    "数值": metric_value(selected, "nearest_direct_competitor_distance_m"),
                },
            ]
        )
        st.dataframe(detail, width="stretch", hide_index=True)

    with right:
        st.subheader("业务解读")
        interpretation = build_site_interpretation(selected)
        st.markdown(f"**综合判断**  \n{interpretation['overall']}")
        st.markdown(f"**需求情况**  \n{interpretation['demand']}")
        st.markdown(f"**交通情况**  \n{interpretation['transit']}")
        st.markdown(f"**竞品情况**  \n{interpretation['competitor']}")

    st.subheader("方法说明")
    note_cols = st.columns(2)
    with note_cols[0]:
        st.markdown(
            """
**模型口径**

- 候选点是人工提出的商业假设，不是最终开店建议。
- 所有坐标保持在高德 / GCJ-02 坐标系。
- v2 分数由需求、交通可达性、商业成熟度和竞争适配分组成。
"""
        )
    with note_cols[1]:
        st.markdown(
            """
**使用边界**

- 竞争强度表示实际拥挤程度；竞争适配分是正向分，竞品过少和过多都会降低该项表现。
- 当前模型尚未纳入租金、铺位面积、门头可见性和合同约束。
- 下一步应结合人工踏勘和租金信息复核排序。
"""
        )


if __name__ == "__main__":
    main()
