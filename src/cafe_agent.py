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
    "Why is this site ranked this way?",
    "What are the biggest risks?",
    "What data is missing before making a decision?",
    "What should I check on-site next?",
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
        return "unknown"
    if reverse:
        if numeric <= medium:
            return "low"
        if numeric <= high:
            return "moderate"
        return "high"
    if numeric >= high:
        return "strong"
    if numeric >= medium:
        return "moderate"
    return "weak"


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
        "### AI Site Analyst",
        "",
        _site_snapshot(site_context),
        "",
        "#### Main read",
        _main_read(site_context),
        "",
        "#### Score drivers",
        *_score_driver_lines(site_context),
        "",
        "#### Risk flags",
        *_risk_lines(site_context),
        "",
        "#### Recommendation",
        _recommendation(site_context),
    ]
    return "\n".join(lines)


def answer_site_question(question: str, site_context: dict[str, Any]) -> str:
    question_text = (question or "").strip()
    question_lower = question_text.lower()

    if not question_text:
        return explain_site(site_context)

    if any(keyword in question_lower for keyword in ["risk", "competitor", "competition", "saturation"]):
        return "\n".join(["### Risk Review", "", *_risk_lines(site_context), "", _recommendation(site_context)])

    if any(keyword in question_lower for keyword in ["missing", "data", "limitation", "need"]):
        return _missing_data_answer()

    if any(keyword in question_lower for keyword in ["next", "check", "visit", "on-site", "onsite", "action"]):
        return _next_checks_answer(site_context)

    if any(keyword in question_lower for keyword in ["why", "rank", "score", "driver", "because"]):
        return "\n".join(
            [
                "### Score Explanation",
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

    rank_text = f"Rank {rank}"
    if total != "N/A":
        rank_text = f"{rank_text} of {total}"

    parts = [f"**Site:** {name}", f"**{rank_text}**", f"**Score:** {score}"]
    if district != "N/A":
        parts.insert(1, f"**District:** {district}")
    return "  \n".join(parts)


def _main_read(context: dict[str, Any]) -> str:
    demand = _level(context.get("demand_score"), 75, 45)
    access = _level(context.get("accessibility_score"), 75, 45)
    maturity = _level(context.get("commercial_maturity_score"), 75, 45)
    pressure = _level(context.get("competitor_pressure_score"), 75, 45)
    fit = _level(context.get("competition_fit_score"), 65, 35)

    return (
        f"This location has {demand} demand signals, {access} accessibility, "
        f"and {maturity} commercial maturity. Competition pressure is {pressure}, "
        f"while competition fit is {fit}. Treat the result as a prioritization signal "
        "for field validation, not as a lease decision."
    )


def _score_driver_lines(context: dict[str, Any]) -> list[str]:
    lines = []
    component_labels = {
        "demand_score": "Demand",
        "accessibility_score": "Accessibility",
        "commercial_maturity_score": "Commercial maturity",
        "competition_fit_score": "Competition fit",
    }

    for column, label in component_labels.items():
        if column in context:
            lines.append(f"- **{label}:** {_format_number(context[column])}")

    if "score_gap_to_best" in context:
        lines.append(f"- **Gap to best site:** {_format_number(context['score_gap_to_best'])} points")
    if "score_gap_to_median" in context:
        lines.append(f"- **Gap to city median:** {_format_number(context['score_gap_to_median'])} points")

    if not lines:
        lines.append("- Score component columns were not available for this selected row.")
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
            f"- **High competitive pressure:** pressure score is {_format_number(pressure)}, so nearby direct competition may be crowded."
        )
    elif pressure is not None:
        lines.append(f"- **Competition pressure:** {_format_number(pressure)}. This is not the same as competition fit.")

    if fit is not None and fit < 30:
        lines.append(
            f"- **Poor competition fit:** fit score is {_format_number(fit)}, which can indicate too little validation or too much saturation."
        )

    if direct_300 is not None and direct_300 > 0:
        lines.append(f"- **Close competitors:** {int(direct_300)} direct competitor(s) within 300m.")
    elif nearest is not None:
        lines.append(f"- **Nearest direct competitor:** {_format_number(nearest, decimals=0, suffix=' m')} away.")

    if direct_800 is not None or direct_1500 is not None:
        lines.append(
            "- **Competitor count:** "
            f"{_format_number(direct_800, decimals=0)} within 800m and "
            f"{_format_number(direct_1500, decimals=0)} within 1500m."
        )

    if not lines:
        lines.append("- Direct competition metrics were not available, so saturation risk needs manual review.")

    return lines


def _recommendation(context: dict[str, Any]) -> str:
    score = _number(context.get("site_score"))
    pressure = _number(context.get("competitor_pressure_score"))
    demand = _number(context.get("demand_score"))

    if score is not None and score >= 80 and (pressure is None or pressure < 90):
        return "Shortlist this site for fieldwork. Validate rent, frontage, pedestrian flow, and whether nearby competitors are serving the same customer segment."

    if demand is not None and demand >= 75 and pressure is not None and pressure >= 90:
        return "Keep this site as a high-demand but high-saturation candidate. It needs stronger differentiation or better unit economics before moving forward."

    return "Do not make a final decision from the model alone. Use this site as a comparison point and verify the missing operating data before prioritizing it."


def _missing_data_answer() -> str:
    return (
        "### Missing Data / Limitations\n\n"
        "- Rent, deposit, lease term, and renovation constraints are not included.\n"
        "- Store size, frontage, visibility, corner access, and floor position are not included.\n"
        "- Real pedestrian counts, daypart flow, and customer spending power are not included.\n"
        "- Brand fit, menu positioning, delivery radius, and cannibalization are not modeled.\n"
        "- POI data can miss newly opened or recently closed stores.\n\n"
        "The current model is useful for narrowing the shortlist, but it should be paired with fieldwork and unit economics."
    )


def _next_checks_answer(context: dict[str, Any]) -> str:
    site = _safe_value(_get_first(context, "area_name", "name", "site_name"))
    return (
        f"### On-Site Checks For {site}\n\n"
        "1. Count pedestrian flow in morning, lunch, afternoon, and evening periods.\n"
        "2. Record visible competitors within a 5 to 10 minute walk and note their price bands.\n"
        "3. Check storefront visibility from the main walking path and transit exits.\n"
        "4. Ask for rent, usable area, lease term, transfer fee, and renovation restrictions.\n"
        "5. Compare the site against the next two ranked candidates before making a shortlist decision."
    )
