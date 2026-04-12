"""Geocoding and distance helpers for location-aware matching."""

from __future__ import annotations

import asyncio
import json
import math

try:
    from geopy.geocoders import Nominatim
except ImportError:  # pragma: no cover - optional in local environments without geopy
    Nominatim = None

from app.core.config import get_settings
from app.core.redis_client import get_redis


class GeocodingService:
    """Resolve location strings to coordinates with Redis caching."""

    FALLBACK_COORDINATES = {
        "ahmedabad, gujarat, india": (23.0225, 72.5714),
        "ahmedabad, india": (23.0225, 72.5714),
        "mumbai, maharashtra, india": (19.0760, 72.8777),
        "pune, maharashtra, india": (18.5204, 73.8567),
        "bengaluru, karnataka, india": (12.9716, 77.5946),
        "delhi, india": (28.6139, 77.2090),
    }

    def __init__(self) -> None:
        """Prepare optional geocoder and settings."""

        self.settings = get_settings()
        self.geocoder = Nominatim(user_agent=self.settings.geocoding_user_agent) if Nominatim else None

    async def geocode(self, location_string: str) -> tuple[float, float] | None:
        """Geocode a location string, using cached or fallback coordinates when available."""

        normalized = self._normalize(location_string)
        if not normalized:
            return None

        redis = await get_redis()
        cache_key = f"geocode:{normalized}"
        cached = await redis.get(cache_key)
        if cached:
            lat, lng = json.loads(cached)
            return float(lat), float(lng)

        if normalized in self.FALLBACK_COORDINATES:
            coords = self.FALLBACK_COORDINATES[normalized]
            await redis.setex(cache_key, 60 * 60 * 24, json.dumps(coords))
            return coords

        if not self.geocoder:
            return None

        location = await asyncio.to_thread(self.geocoder.geocode, normalized)
        if location is None:
            return None
        coords = (float(location.latitude), float(location.longitude))
        await redis.setex(cache_key, 60 * 60 * 24, json.dumps(coords))
        return coords

    def haversine_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Return great-circle distance in kilometers between two coordinates."""

        radius_km = 6371.0
        lat1_rad, lng1_rad, lat2_rad, lng2_rad = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
        return radius_km * 2 * math.asin(math.sqrt(a))

    def _normalize(self, location_string: str) -> str:
        """Normalize location text for cache keys and fallback lookups."""

        return " ".join(part.strip().lower() for part in location_string.replace("|", ",").split(",") if part.strip())
