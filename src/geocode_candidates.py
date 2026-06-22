from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from amap_client import AmapClient, AmapClientError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "manual" / "candidate_sites.csv"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_sites_geocoded.csv"

REQUIRED_COLUMNS = [
    "site_id",
    "city",
    "district",
    "area_name",
    "address",
    "business_type",
    "reason_for_selection",
]


def geocode_candidates(input_path: Path, output_path: Path) -> pd.DataFrame:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("AMAP_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "AMAP_API_KEY is missing. Create .env from .env.example and add a valid 高德 Web 服务 API key."
        )

    candidates = pd.read_csv(input_path, encoding="utf-8-sig", dtype=str).fillna("")
    _validate_columns(candidates)

    client = AmapClient(api_key=api_key)
    output_rows: list[dict[str, str | int]] = []

    for _, row in candidates.iterrows():
        base_row = row.to_dict()
        try:
            result = client.geocode(address=base_row["address"], city=base_row["city"])
            output_rows.append(
                {
                    **base_row,
                    "lng": result.lng,
                    "lat": result.lat,
                    "geocode_formatted_address": result.formatted_address,
                    "geocode_province": result.province,
                    "geocode_city": result.city,
                    "geocode_district": result.district,
                    "geocode_township": result.township,
                    "geocode_adcode": result.adcode,
                    "geocode_level": result.geocode_level,
                    "geocode_api_status": result.api_status,
                    "geocode_api_info": result.api_info,
                    "geocode_api_infocode": result.api_infocode,
                    "geocode_raw_match_count": result.raw_count,
                    "geocode_error": "",
                }
            )
        except (AmapClientError, requests.RequestException, ValueError) as exc:
            output_rows.append(_failed_row(base_row, str(exc)))

    output = pd.DataFrame(output_rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output


def _validate_columns(candidates: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in candidates.columns]
    if missing:
        raise ValueError(f"candidate_sites.csv is missing required columns: {', '.join(missing)}")


def _failed_row(base_row: dict[str, str], error: str) -> dict[str, str | int]:
    return {
        **base_row,
        "lng": "",
        "lat": "",
        "geocode_formatted_address": "",
        "geocode_province": "",
        "geocode_city": "",
        "geocode_district": "",
        "geocode_township": "",
        "geocode_adcode": "",
        "geocode_level": "",
        "geocode_api_status": "0",
        "geocode_api_info": "ERROR",
        "geocode_api_infocode": "",
        "geocode_raw_match_count": 0,
        "geocode_error": error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Geocode manual candidate sites with 高德 Web 服务 API.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = geocode_candidates(input_path=args.input, output_path=args.output)
    success_count = int(output["lng"].astype(bool).sum()) if "lng" in output.columns else 0
    print(f"Wrote {len(output)} rows to {args.output}")
    print(f"Successful geocodes: {success_count}")


if __name__ == "__main__":
    main()
