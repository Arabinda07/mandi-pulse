"""Tests for the VolatilityEngine statistical calculations."""

import pytest
from src.volatility import VolatilityEngine


def test_arrival_shock_anomaly_normal():
    # Baseline with mean = 100, std ~ 10
    history = [90, 100, 110, 95, 105]
    # Current volume 100 should be roughly 0 Z
    z = VolatilityEngine.compute_arrival_shock(100.0, history)
    assert abs(z) < 0.2


def test_arrival_shock_anomaly_slump():
    history = [100.0, 105.0, 95.0, 100.0, 102.0]
    # Current volume drops sharply to 40 (severe supply slump)
    z = VolatilityEngine.compute_arrival_shock(40.0, history)
    assert z < -2.0  # More than 2 standard deviations below baseline


def test_spatial_price_dispersion():
    # Identical prices -> CV = 0
    assert VolatilityEngine.compute_spatial_dispersion([2000, 2000, 2000]) == 0.0

    # Divergent prices -> high CV
    # e.g., 1000 in surplus area, 3000 in deficit area
    cv = VolatilityEngine.compute_spatial_dispersion([1000, 3000])
    assert cv > 0.45


def test_corridor_stress_classification():
    # Severe stress: origin supply crash (Z < -1.5) and terminal price doubled (>90% spread)
    spread_inr, spread_pct, level = VolatilityEngine.evaluate_corridor_stress(
        origin_price=1500.0,
        terminal_price=3200.0,
        origin_arrival_z=-2.2,
    )
    assert level == "SEVERE"
    assert spread_pct > 100.0

    # Normal conditions: small spread and healthy arrivals
    _, _, normal_level = VolatilityEngine.evaluate_corridor_stress(
        origin_price=2000.0,
        terminal_price=2300.0,
        origin_arrival_z=0.2,
    )
    assert normal_level == "NORMAL"
