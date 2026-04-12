"""Tests for TalentOS v3 geocoding helpers."""

from __future__ import annotations

from app.services.geocoding_service import GeocodingService


def test_haversine_km_returns_small_distance_for_nearby_points() -> None:
    """Nearby Ahmedabad coordinates should produce a realistic short distance."""

    service = GeocodingService()
    distance = service.haversine_km(23.0225, 72.5714, 23.0300, 72.5800)

    assert 0.5 < distance < 2.0
