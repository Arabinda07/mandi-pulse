"""Tests for MandiWeatherAdapter and Live Weather Attribution Integration."""

from datetime import date
import pytest
from src.sources.weather import MandiWeatherAdapter
from src.registry import MandiRegistry
from src.attribution import (
    get_mandi_weather,
    fetch_all_mandis_weather_alerts,
    explain_price_movement,
)


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


def test_get_mandi_weather_live_lookup():
    """Verify live meteorological lookup for a canonical mandi ID."""
    weather = get_mandi_weather("mandi_lasalgaon", obs_date=date(2026, 8, 1))
    assert "precipitation_mm" in weather
    assert "max_temp_c" in weather
    assert weather["mandi_id"] == "mandi_lasalgaon"


def test_fetch_all_mandis_weather_alerts():
    """Verify weather alert synthesis across all 25 canonical mandis."""
    # Test on a specific target date
    alerts = fetch_all_mandis_weather_alerts(obs_date=date(2026, 8, 1))
    assert len(alerts) == len(MandiRegistry().get_canonical_mandis())
    assert len(alerts) >= 14
    first = alerts[0]
    assert "mandi_id" in first
    assert "canonical_name" in first
    assert "precipitation_mm" in first
    assert "severity" in first
    assert first["severity"] in ("NORMAL", "NOTICE", "WARNING", "CRITICAL")


def test_explain_price_movement_with_live_weather():
    """Verify explain_price_movement dynamically triggers live weather shock attribution."""
    attr = explain_price_movement(
        commodity="onion",
        mandi_name="Lasalgaon",
        trade_date=date(2026, 8, 1),
        price_today=3200.0,
        price_prior=2400.0, # +33% spike
        rainfall_mm=35.0,   # Heavy rain shock passed
        max_temp_c=28.0,
    )
    assert attr.primary_driver == "WEATHER_RAIN"
    assert "Weather Shock" in attr.headline
    assert "Heavy Rain" in attr.weather_flag


def test_generate_shopping_advice_and_basket_verdict():
    """Verify deterministic rule-based NLG advice and basket verdict generation."""
    from src.attribution import generate_shopping_advice, generate_basket_verdict

    # 1. Severe arrival shock / weather disruption
    onion_advice = generate_shopping_advice(
        commodity="onion",
        terminal_name="Azadpur (Delhi)",
        price_today_rs_kg=35.0,
        day_change_rs_kg=3.5,
        week_change_pct=15.0,
        origin_name="Lasalgaon",
        origin_arrival_shock_z=-2.4,
        weather_flag="Heavy Rain (35.0 mm)",
    )
    assert onion_advice.status == "shock"
    assert onion_advice.status_label == "Severe Spike"
    assert onion_advice.trend_status == "spike"
    assert "Heavy Rain" in onion_advice.advice
    assert "buffer" in onion_advice.advice

    # 2. Supply glut / cooling down
    tomato_advice = generate_shopping_advice(
        commodity="tomato",
        terminal_name="Azadpur (Delhi)",
        price_today_rs_kg=22.0,
        day_change_rs_kg=-2.0,
        week_change_pct=-12.0,
        origin_name="Kolar",
        origin_arrival_shock_z=1.2,
    )
    assert tomato_advice.status == "fair"
    assert tomato_advice.trend_status == "cooling"
    assert "Abundant arrivals" in tomato_advice.advice

    # 3. Stable corridor
    potato_advice = generate_shopping_advice(
        commodity="potato",
        terminal_name="Azadpur (Delhi)",
        price_today_rs_kg=18.0,
        day_change_rs_kg=0.2,
        week_change_pct=1.5,
        origin_name="Farrukhabad",
        origin_arrival_shock_z=-0.2,
    )
    assert potato_advice.status == "fair"
    assert potato_advice.trend_status == "stable"
    assert "Steady daily arrivals" in potato_advice.advice

    # 4. Consolidated Basket Verdict
    verdict = generate_basket_verdict([onion_advice, tomato_advice, potato_advice], weekly_total_rs=198.5, week_change_pct=8.4)
    assert verdict["verdict_status"] == "shock"
    assert "Onion" in verdict["verdict"]
    assert "Lasalgaon" in verdict["verdict"]

