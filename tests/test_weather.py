"""Tests for MandiWeatherAdapter."""

import pytest
from src.sources.weather import MandiWeatherAdapter


def test_weather_adapter_structure():
    adapter = MandiWeatherAdapter()
    # Test coordinates for Lasalgaon (Nashik)
    res = adapter.get_mandi_rainfall(
        latitude=20.1472,
        longitude=74.2256,
        start_date="2026-08-01",
        end_date="2026-08-05",
    )
    assert "dates" in res
    assert "precipitation_mm" in res
    assert "temperature_max_c" in res
    if res["dates"]:
        assert len(res["dates"]) == 5
        assert len(res["precipitation_mm"]) == 5
