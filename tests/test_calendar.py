"""Tests for Indian Festival Calendar & Automated Attribution Engine."""

import pytest
from datetime import date

from src.calendar import (
    get_active_festivals,
    get_crop_season_phase,
    get_commodity_calendar_context,
    CropPhase,
    DemandImpact,
)
from src.attribution import explain_price_movement, PriceAttribution
from src.warehouse import Warehouse


def test_festival_detection_navratri():
    """Verify Sharad Navratri is detected in October with onion slump impact."""
    # Test during Sharad Navratri 2024 (Oct 3 to Oct 12, 2024)
    active = get_active_festivals(date(2024, 10, 5), lookaround_days=3)
    names = [f["name"] for f in active]
    assert any("Navratri" in n for n in names)
    
    # Check impact on Onion
    nav = [f for f in active if "Navratri" in f["name"]][0]
    assert nav["impacts"]["Onion"] == DemandImpact.SLUMP.value
    assert nav["impacts"]["Potato"] == DemandImpact.FASTING_SWAP.value


def test_crop_season_onion():
    """Verify biological seasons for Onion (Rabi vs Pre-Kharif)."""
    # March = Rabi Harvest Glut
    rabi = get_crop_season_phase("Onion", date(2024, 3, 20))
    assert rabi["phase"] == CropPhase.HARVEST_GLUT.value
    assert "Rabi" in rabi["season"]

    # September = Pre-Kharif Scarcity
    scarcity = get_crop_season_phase("Onion", date(2024, 9, 15))
    assert scarcity["phase"] == CropPhase.PRE_HARVEST_SCARCITY.value


def test_attribution_weather_rain_shock():
    """Verify price spike with heavy rain is attributed to weather inundation."""
    attr = explain_price_movement(
        commodity="Tomato",
        mandi_name="Kolar APMC",
        trade_date=date(2024, 7, 15),
        price_today=3500.0,
        price_prior=2500.0,  # +40% jump
        rainfall_mm=45.0,     # Heavy rain
        max_temp_c=28.0
    )
    assert attr.primary_driver == "WEATHER_RAIN"
    assert attr.severity == "CRITICAL"
    assert "Rain" in attr.headline
    assert "disrupted harvesting" in attr.explanation


def test_attribution_cultural_fasting():
    """Verify onion price slump during Navratri is attributed to fasting."""
    attr = explain_price_movement(
        commodity="Onion",
        mandi_name="Lasalgaon",
        trade_date=date(2024, 10, 6), # During Sharad Navratri
        price_today=1500.0,
        price_prior=2200.0, # -31.8% drop
        rainfall_mm=0.0,
        max_temp_c=30.0
    )
    assert attr.primary_driver == "CULTURAL_FASTING"
    assert "Fasting" in attr.headline
    assert "Navratri" in attr.explanation


def test_attribution_quality_dispersion():
    """Verify wide Min-Max spread flags quality divergence."""
    attr = explain_price_movement(
        commodity="Tomato",
        mandi_name="Madanapalle",
        trade_date=date(2024, 8, 10),
        price_today=2000.0,
        price_prior=2050.0, # Stable modal price
        min_price=500.0,    # Wide gap (500 to 3200)
        max_price=3200.0,
        rainfall_mm=0.0,
        max_temp_c=32.0
    )
    assert attr.primary_driver == "QUALITY_DISPERSION"
    assert "Quality" in attr.headline


def test_warehouse_materialize_attributions(tmp_path):
    """Verify end-to-end materialization of attributions in SQLite warehouse."""
    wh = Warehouse(tmp_path / "test_attr.db")
    wh.initialize()

    # Seed two days of facts for a mandi
    from src.models import DailyFactRecord, MandiRecord
    wh.record_mandis([
        MandiRecord("m_test_1", "Test Mandi", "Maharashtra", "Nashik", 27, 516, 20.0, 74.0, True, "production")
    ])
    wh.upsert_daily_facts([
        DailyFactRecord("m_test_1", "onion", "2024-09-01", 100.0, 2000.0, 2400.0, 2200.0),
        DailyFactRecord("m_test_1", "onion", "2024-09-08", 60.0, 3000.0, 3600.0, 3300.0), # +50%
    ])

    count = wh.materialize_attributions("2024-09-08")
    assert count >= 1

    df = wh.get_attribution_reports(commodity="onion")
    assert df.height >= 1
    assert "Test Mandi" in df["mandi_name"].to_list()
