from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

from amap_client import AmapClient, AmapClientError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_sites_geocoded.csv"
DEFAULT_KEYWORDS_PATH = PROJECT_ROOT / "data" / "manual" / "poi_keywords.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_RADII = [300, 800, 1500]
DEFAULT_OFFSET = 25
DEFAULT_MAX_PAGES = 4

REQUIRED_CANDIDATE_COLUMNS = [
    "site_id",
    "city",
    "district",
    "area_name",
    "address",
    "business_type",
    "lng",
    "lat",
]

REQUIRED_KEYWORD_COLUMNS = [
    "keyword_id",
    "bucket",
    "keyword",
    "poi_type_hint",
    "description",
]


def collect_poi_snapshots(
    candidates_path: Path,
    keywords_path: Path,
    output_dir: Path,
    radii: list[int],
    max_pages: int,
    offset: int,
) -> Path:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("AMAP_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "AMAP_API_KEY is missing. Create .env from .env.example and add a valid 高德 Web 服务 API key."
        )

    candidates = pd.read_csv(candidates_path, encoding="utf-8-sig", dtype=str).fillna("")
    keywords = pd.read_csv(keywords_path, encoding="utf-8-sig", dtype=str).fillna("")
    _validate_columns(candidates, REQUIRED_CANDIDATE_COLUMNS, candidates_path)
    _validate_columns(keywords, REQUIRED_KEYWORD_COLUMNS, keywords_path)
    _validate_coordinates(candidates)

    client = AmapClient(api_key=api_key)
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict[str, Any]] = []

    for _, candidate in candidates.iterrows():
        for _, keyword in keywords.iterrows():
            for radius in radii:
                rows.extend(
                    _collect_one_search(
                        client=client,
                        candidate=candidate.to_dict(),
                        keyword=keyword.to_dict(),
                        radius=radius,
                        max_pages=max_pages,
                        offset=offset,
                        collected_at=collected_at,
                    )
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"poi_snapshot_{timestamp}.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def _collect_one_search(
    client: AmapClient,
    candidate: dict[str, str],
    keyword: dict[str, str],
    radius: int,
    max_pages: int,
    offset: int,
    collected_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        try:
            payload = client.search_pois_around(
                lng=candidate["lng"],
                lat=candidate["lat"],
                keyword=keyword["keyword"],
                radius=radius,
                page=page,
                offset=offset,
            )
        except (AmapClientError, requests.RequestException, ValueError) as exc:
            rows.append(
                _base_row(
                    candidate=candidate,
                    keyword=keyword,
                    radius=radius,
                    page=page,
                    collected_at=collected_at,
                    api_status="0",
                    api_info="ERROR",
                    api_infocode="",
                    api_count=0,
                    error=str(exc),
                )
            )
            break

        pois = payload.get("pois") or []
        api_count = _parse_count(payload.get("count"))
        if not pois:
            if page == 1:
                rows.append(
                    _base_row(
                        candidate=candidate,
                        keyword=keyword,
                        radius=radius,
                        page=page,
                        collected_at=collected_at,
                        api_status=str(payload.get("status", "")),
                        api_info=str(payload.get("info", "")),
                        api_infocode=str(payload.get("infocode", "")),
                        api_count=api_count,
                        error="",
                    )
                )
            break

        for poi in pois:
            rows.append(
                {
                    **_base_row(
                        candidate=candidate,
                        keyword=keyword,
                        radius=radius,
                        page=page,
                        collected_at=collected_at,
                        api_status=str(payload.get("status", "")),
                        api_info=str(payload.get("info", "")),
                        api_infocode=str(payload.get("infocode", "")),
                        api_count=api_count,
                        error="",
                    ),
                    **_poi_fields(poi),
                }
            )

        if len(pois) < offset or page * offset >= api_count:
            break

    return rows


def _base_row(
    candidate: dict[str, str],
    keyword: dict[str, str],
    radius: int,
    page: int,
    collected_at: str,
    api_status: str,
    api_info: str,
    api_infocode: str,
    api_count: int,
    error: str,
) -> dict[str, Any]:
    return {
        "collected_at": collected_at,
        "site_id": candidate["site_id"],
        "city": candidate["city"],
        "district": candidate["district"],
        "area_name": candidate["area_name"],
        "candidate_address": candidate["address"],
        "candidate_lng": candidate["lng"],
        "candidate_lat": candidate["lat"],
        "radius_m": radius,
        "page": page,
        "keyword_id": keyword["keyword_id"],
        "bucket": keyword["bucket"],
        "keyword": keyword["keyword"],
        "poi_type_hint": keyword["poi_type_hint"],
        "api_status": api_status,
        "api_info": api_info,
        "api_infocode": api_infocode,
        "api_count": api_count,
        "error": error,
        "poi_id": "",
        "poi_name": "",
        "poi_type": "",
        "poi_typecode": "",
        "poi_address": "",
        "poi_lng": "",
        "poi_lat": "",
        "poi_distance_m": "",
        "poi_province": "",
        "poi_city": "",
        "poi_district": "",
    }


def _poi_fields(poi: dict[str, Any]) -> dict[str, str]:
    lng, lat = _split_location(_field(poi, "location"))
    return {
        "poi_id": _field(poi, "id"),
        "poi_name": _field(poi, "name"),
        "poi_type": _field(poi, "type"),
        "poi_typecode": _field(poi, "typecode"),
        "poi_address": _field(poi, "address"),
        "poi_lng": lng,
        "poi_lat": lat,
        "poi_distance_m": _field(poi, "distance"),
        "poi_province": _field(poi, "pname"),
        "poi_city": _field(poi, "cityname"),
        "poi_district": _field(poi, "adname"),
    }


def _validate_columns(frame: pd.DataFrame, required_columns: list[str], path: Path) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def _validate_coordinates(candidates: pd.DataFrame) -> None:
    missing_coordinates = candidates[(candidates["lng"] == "") | (candidates["lat"] == "")]
    if not missing_coordinates.empty:
        site_ids = ", ".join(missing_coordinates["site_id"].tolist())
        raise ValueError(f"Geocoded candidate file has missing lng/lat for: {site_ids}")


def _parse_count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _field(row: dict[str, Any], key: str) -> str:
    value = row.get(key, "")
    if isinstance(value, list):
        return ""
    return str(value)


def _split_location(location: str) -> tuple[str, str]:
    if not location or "," not in location:
        return "", ""
    lng, lat = location.split(",", 1)
    return lng.strip(), lat.strip()


def _parse_radii(value: str) -> list[int]:
    radii = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not radii:
        raise ValueError("At least one radius is required.")
    return radii


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect 高德 nearby POI snapshots for geocoded candidate sites.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--radii", default=",".join(str(radius) for radius in DEFAULT_RADII))
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--offset", type=int, default=DEFAULT_OFFSET)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = collect_poi_snapshots(
        candidates_path=args.candidates,
        keywords_path=args.keywords,
        output_dir=args.output_dir,
        radii=_parse_radii(args.radii),
        max_pages=args.max_pages,
        offset=args.offset,
    )
    print(f"Wrote POI snapshot to {output_path}")


if __name__ == "__main__":
    main()
