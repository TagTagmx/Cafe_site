"""
Local cafe site analyst.

The agent is intentionally read-only. It explains the selected dashboard row using
the metrics already loaded by Streamlit, without changing data or scoring logic.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


SCORE_COLUMNS = [
    "site_score",
    "demand_score",
    "accessibility_score",
    "commercial_maturity_score",
    "competition_fit_score",
    "competitor_pressure_score",
]

KEY_METRICS = [
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

QUESTION_PRESETS = [
    "为什么这个点位是这个排名？",
    "最大的风险是什么？",
    "做决策前还缺哪些数据？",
    "下一步实地应该检查什么？",
]


def _safe_value(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass
    return str(value)


def _number(value: Any) -> float | None:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return None
    return float(numeric)


def _format_number(value: Any, decimals: int = 2, suffix: str = "") -> str:
    numeric = _number(value)
    if numeric is None:
        return "N/A"
    if float(numeric).is_integer():
        return f"{int(numeric)}{suffix}"
    return f"{numeric:.{decimals}f}{suffix}"


def _get_first(context: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in context and _safe_value(context[key]) != "N/A":
            return context[key]
    return None


def _level(value: Any, high: float, medium: float, reverse: bool = False) -> str:
    numeric = _number(value)
    if numeric is None:
        return "未知"
    if reverse:
        if numeric <= medium:
            return "低"
        if numeric <= high:
            return "中等"
        return "高"
    if numeric >= high:
        return "强"
    if numeric >= medium:
        return "中等"
    return "弱"


def build_site_context(selected_row: pd.Series, ranking_df: pd.DataFrame | None = None) -> dict[str, Any]:
    """
    Build a compact context object from one selected dashboard row.

    The returned dict is safe to pass to answer_site_question and contains only
    available row values plus a few derived ranking fields.
    """
    context: dict[str, Any] = {}

    for column in selected_row.index:
        value = selected_row[column]
        if _safe_value(value) != "N/A":
            context[str(column)] = value

    if "site_rank" in context:
        context["rank"] = context["site_rank"]

    if ranking_df is not None and "rank" not in context:
        rank = _infer_rank(selected_row, ranking_df)
        if rank is not None:
            context["rank"] = rank

    if ranking_df is not None:
        context["candidate_count"] = len(ranking_df)
        score = _number(context.get("site_score"))
        if score is not None and "site_score" in ranking_df.columns:
            scores = pd.to_numeric(ranking_df["site_score"], errors="coerce").dropna()
            if not scores.empty:
                context["score_gap_to_best"] = float(scores.max() - score)
                context["score_gap_to_median"] = float(score - scores.median())

    return context


def _infer_rank(selected_row: pd.Series, ranking_df: pd.DataFrame) -> int | None:
    if "site_score" not in ranking_df.columns:
        return None

    ranked = ranking_df.sort_values("site_score", ascending=False).reset_index(drop=False)
    selected_site_id = selected_row.get("site_id")
    selected_area = selected_row.get("area_name")

    if selected_site_id is not None and "site_id" in ranked.columns:
        matches = ranked.index[ranked["site_id"] == selected_site_id].tolist()
        if matches:
            return int(matches[0]) + 1

    if selected_area is not None and "area_name" in ranked.columns:
        matches = ranked.index[ranked["area_name"] == selected_area].tolist()
        if matches:
            return int(matches[0]) + 1

    return None


def suggested_questions() -> list[str]:
    return QUESTION_PRESETS.copy()


def explain_site(site_context: dict[str, Any]) -> str:
    lines = [
        "### AI 点位分析师",
        "",
        _site_snapshot(site_context),
        "",
        "#### 综合判断",
        _main_read(site_context),
        "",
        "#### 分数驱动因素",
        *_score_driver_lines(site_context),
        "",
        "#### 风险提示",
        *_risk_lines(site_context),
        "",
        "#### 建议",
        _recommendation(site_context),
    ]
    return "\n".join(lines)


def answer_site_question(question: str, site_context: dict[str, Any]) -> str:
    question_text = (question or "").strip()
    question_lower = question_text.lower()

    if not question_text:
        return explain_site(site_context)

    if any(keyword in question_lower for keyword in ["risk", "competitor", "competition", "saturation", "风险", "竞品", "竞争", "饱和"]):
        return "\n".join(["### 风险复核", "", *_risk_lines(site_context), "", _recommendation(site_context)])

    if any(keyword in question_lower for keyword in ["missing", "data", "limitation", "need", "缺", "数据", "限制", "还需要"]):
        return _missing_data_answer()

    if any(keyword in question_lower for keyword in ["next", "check", "visit", "on-site", "onsite", "action", "下一步", "检查", "实地", "行动"]):
        return _next_checks_answer(site_context)

    if any(keyword in question_lower for keyword in ["why", "rank", "score", "driver", "because", "为什么", "排名", "分数", "原因"]):
        return "\n".join(
            [
                "### 分数解释",
                "",
                _site_snapshot(site_context),
                "",
                _main_read(site_context),
                "",
                *_score_driver_lines(site_context),
            ]
        )

    return explain_site(site_context)


def _site_snapshot(context: dict[str, Any]) -> str:
    name = _safe_value(_get_first(context, "area_name", "name", "site_name", "address"))
    district = _safe_value(context.get("district"))
    rank = _format_number(_get_first(context, "rank", "site_rank"), decimals=0)
    total = _safe_value(context.get("candidate_count"))
    score = _format_number(context.get("site_score"))

    rank_text = f"排名第 {rank}"
    if total != "N/A":
        rank_text = f"{rank_text} / 共 {total} 个候选点"

    parts = [f"**点位：** {name}", f"**{rank_text}**", f"**总分：** {score}"]
    if district != "N/A":
        parts.insert(1, f"**区县：** {district}")
    return "  \n".join(parts)


def _main_read(context: dict[str, Any]) -> str:
    demand = _level(context.get("demand_score"), 75, 45)
    access = _level(context.get("accessibility_score"), 75, 45)
    maturity = _level(context.get("commercial_maturity_score"), 75, 45)
    pressure = _level(context.get("competitor_pressure_score"), 75, 45)
    fit = _level(context.get("competition_fit_score"), 65, 35)

    return (
        f"这个点位的需求信号为{demand}，交通可达性为{access}，商业成熟度为{maturity}。"
        f"实际竞争压力为{pressure}，竞争适配表现为{fit}。"
        "这个结果适合用来确定实地复核优先级，不应直接等同于租铺决策。"
    )


def _score_driver_lines(context: dict[str, Any]) -> list[str]:
    lines = []
    component_labels = {
        "demand_score": "需求强度",
        "accessibility_score": "交通可达性",
        "commercial_maturity_score": "商业成熟度",
        "competition_fit_score": "竞争适配分",
    }

    for column, label in component_labels.items():
        if column in context:
            lines.append(f"- **{label}：** {_format_number(context[column])}")

    if "score_gap_to_best" in context:
        lines.append(f"- **与最高分点位差距：** {_format_number(context['score_gap_to_best'])} 分")
    if "score_gap_to_median" in context:
        lines.append(f"- **高于/低于本城中位数：** {_format_number(context['score_gap_to_median'])} 分")

    if not lines:
        lines.append("- 当前行缺少分项得分列，无法拆解主要驱动因素。")
    return lines


def _risk_lines(context: dict[str, Any]) -> list[str]:
    direct_300 = _number(context.get("direct_competitor_count_300m"))
    direct_800 = _number(context.get("direct_competitor_count_800m"))
    direct_1500 = _number(context.get("direct_competitor_count_1500m"))
    nearest = _number(context.get("nearest_direct_competitor_distance_m"))
    pressure = _number(context.get("competitor_pressure_score"))
    fit = _number(context.get("competition_fit_score"))

    lines: list[str] = []

    if pressure is not None and pressure >= 75:
        lines.append(
            f"- **竞争压力较高：** 竞争压力分为 {_format_number(pressure)}，周边直接竞品可能较拥挤。"
        )
    elif pressure is not None:
        lines.append(f"- **竞争压力：** {_format_number(pressure)}。注意它和竞争适配分不是同一个指标。")

    if fit is not None and fit < 30:
        lines.append(
            f"- **竞争适配偏低：** 适配分为 {_format_number(fit)}，可能表示需求未被竞品验证，也可能表示竞争过度饱和。"
        )

    if direct_300 is not None and direct_300 > 0:
        lines.append(f"- **近距离竞品：** 300m 内有 {int(direct_300)} 个直接竞品。")
    elif nearest is not None:
        lines.append(f"- **最近直接竞品：** 距离约 {_format_number(nearest, decimals=0, suffix=' m')}。")

    if direct_800 is not None or direct_1500 is not None:
        lines.append(
            "- **竞品数量：** "
            f"800m 内 {_format_number(direct_800, decimals=0)} 个，"
            f"1500m 内 {_format_number(direct_1500, decimals=0)} 个。"
        )

    if not lines:
        lines.append("- 当前缺少直接竞品指标，饱和风险需要人工实地复核。")

    return lines


def _recommendation(context: dict[str, Any]) -> str:
    score = _number(context.get("site_score"))
    pressure = _number(context.get("competitor_pressure_score"))
    demand = _number(context.get("demand_score"))

    if score is not None and score >= 80 and (pressure is None or pressure < 90):
        return "建议把该点位放入实地复核短名单。下一步重点核验租金、门头可见性、实际人流，以及周边竞品是否服务同一客群。"

    if demand is not None and demand >= 75 and pressure is not None and pressure >= 90:
        return "该点位属于高需求但高饱和候选点。继续推进前，需要确认品牌差异化、租金承受能力和单店模型是否足够强。"

    return "不要只根据模型做最终决策。建议把它作为对比点位，并先补齐关键经营数据后再决定优先级。"


def _missing_data_answer() -> str:
    return (
        "### 缺失数据 / 使用边界\n\n"
        "- 当前未纳入租金、押金、租期、转让费和装修限制。\n"
        "- 当前未纳入铺位面积、门头宽度、可见性、拐角位置和楼层位置。\n"
        "- 当前未纳入真实人流、分时段客流和周边消费能力。\n"
        "- 当前未建模品牌定位、菜单价格带、外卖半径和同品牌 cannibalization 风险。\n"
        "- POI 数据可能遗漏新开或刚关闭的门店。\n\n"
        "因此，当前模型适合缩小候选范围，但必须结合实地踏勘和单店经济模型一起判断。"
    )


def _next_checks_answer(context: dict[str, Any]) -> str:
    site = _safe_value(_get_first(context, "area_name", "name", "site_name"))
    return (
        f"### {site} 的实地检查清单\n\n"
        "1. 分别在早高峰、午间、下午和晚间记录实际人流。\n"
        "2. 步行 5 到 10 分钟范围内记录可见竞品，并标注价格带和客群。\n"
        "3. 检查门头从主步行动线、地铁口或公交站是否容易被看到。\n"
        "4. 询问租金、可用面积、租期、转让费和装修限制。\n"
        "5. 与当前排名相邻的两个候选点做横向对比后，再决定是否进入短名单。"
    )
