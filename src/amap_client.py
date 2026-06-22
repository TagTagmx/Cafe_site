from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
AMAP_PLACE_AROUND_URL = "https://restapi.amap.com/v3/place/around"


class AmapClientError(RuntimeError):
    """Raised when 高德 Web 服务 API returns an error response."""


@dataclass(frozen=True)
class AmapGeocodeResult:
    api_status: str
    api_info: str
    api_infocode: str
    raw_count: int
    formatted_address: str
    province: str
    city: str
    district: str
    township: str
    adcode: str
    geocode_level: str
    lng: str
    lat: str


class AmapClient:
    def __init__(self, api_key: str, timeout_seconds: int = 10) -> None:
        if not api_key:
            raise ValueError("AMAP_API_KEY is required.")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def geocode(self, address: str, city: str | None = None) -> AmapGeocodeResult:
        params: dict[str, str] = {
            "key": self.api_key,
            "address": address,
            "output": "JSON",
        }
        if city:
            params["city"] = city

        response = requests.get(
            AMAP_GEOCODE_URL,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()

        status = str(payload.get("status", ""))
        info = str(payload.get("info", ""))
        infocode = str(payload.get("infocode", ""))
        raw_count = _parse_count(payload.get("count"))

        if status != "1":
            raise AmapClientError(
                f"Amap geocode failed: status={status}, infocode={infocode}, info={info}"
            )

        geocodes = payload.get("geocodes") or []
        if not geocodes:
            return AmapGeocodeResult(
                api_status=status,
                api_info=info,
                api_infocode=infocode,
                raw_count=raw_count,
                formatted_address="",
                province="",
                city="",
                district="",
                township="",
                adcode="",
                geocode_level="",
                lng="",
                lat="",
            )

        first = geocodes[0]
        lng, lat = _split_location(str(first.get("location", "")))

        return AmapGeocodeResult(
            api_status=status,
            api_info=info,
            api_infocode=infocode,
            raw_count=raw_count,
            formatted_address=_field(first, "formatted_address"),
            province=_field(first, "province"),
            city=_field(first, "city"),
            district=_field(first, "district"),
            township=_field(first, "township"),
            adcode=_field(first, "adcode"),
            geocode_level=_field(first, "level"),
            lng=lng,
            lat=lat,
        )

    def search_pois_around(
        self,
        lng: str,
        lat: str,
        keyword: str,
        radius: int,
        page: int = 1,
        offset: int = 25,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "key": self.api_key,
            "location": f"{lng},{lat}",
            "keywords": keyword,
            "radius": radius,
            "page": page,
            "offset": offset,
            "extensions": "base",
            "output": "JSON",
        }

        response = requests.get(
            AMAP_PLACE_AROUND_URL,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()

        status = str(payload.get("status", ""))
        info = str(payload.get("info", ""))
        infocode = str(payload.get("infocode", ""))
        if status != "1":
            raise AmapClientError(
                f"Amap POI search failed: status={status}, infocode={infocode}, info={info}"
            )

        return payload


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
