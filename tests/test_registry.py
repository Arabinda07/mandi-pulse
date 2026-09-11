"""Tests for Mandi entity resolution and spatial registry."""

import pytest
from src.registry import MandiRegistry


@pytest.fixture
def registry():
    return MandiRegistry()


def test_canonical_mandis_exist(registry):
    mandis = registry.get_canonical_mandis()
    assert len(mandis) >= 10
    lasalgaon = next((m for m in mandis if m.mandi_id == "mandi_lasalgaon"), None)
    assert lasalgaon is not None
    assert lasalgaon.district_lgd_code == 485
    assert lasalgaon.state == "Maharashtra"


def test_exact_resolution(registry):
    res = registry.resolve("Lasalgaon")
    assert res.mandi_id == "mandi_lasalgaon"
    assert res.match_type == "exact"
    assert res.confidence == 1.0


def test_alias_resolution(registry):
    res = registry.resolve("LASALGAON(NIPHAD)")
    assert res.mandi_id == "mandi_lasalgaon"
    assert res.match_type == "alias"
    assert res.confidence >= 0.95


def test_fuzzy_resolution(registry):
    # Minor misspelling / casing
    res = registry.resolve("Pimpalgaon Baswnt")
    assert res.mandi_id == "mandi_pimpalgaon"
    assert res.match_type in ("fuzzy", "alias")
    assert res.confidence > 0.70


def test_unmapped_fallback(registry):
    res = registry.resolve("Some Remote Nonexistent Bazaar", state="Goa")
    assert res.match_type in ("regional", "unmapped")
    assert res.canonical_name == "Some Remote Nonexistent Bazaar"
    assert res.state == "Goa"


def test_statutory_state_apmc_cess_schedules(registry):
    """Verify official State APMC market fees and commission caps are properly codified."""
    # Maharashtra (MSAMB): 1.05% market fee, 6% commission cap
    lasalgaon = registry.get_mandi("mandi_lasalgaon")
    assert lasalgaon.mandi_cess_pct == 1.05
    assert lasalgaon.commission_cap_pct == 6.0

    pune = registry.get_mandi("mandi_pune")
    assert pune.mandi_cess_pct == 1.05
    assert pune.commission_cap_pct == 6.0

    # Delhi (DAMB): 1.0% mandi fee + 1.0% rural development cess = 2.0%
    azadpur = registry.get_mandi("mandi_azadpur")
    assert azadpur.mandi_cess_pct == 2.0
    assert azadpur.commission_cap_pct == 6.0

    # Karnataka (KSAMB): 1.5% market fee, 2% commission cap
    kolar = registry.get_mandi("mandi_kolar")
    assert kolar.mandi_cess_pct == 1.5
    assert kolar.commission_cap_pct == 2.0

    bangalore = registry.get_mandi("mandi_bangalore")
    assert bangalore.mandi_cess_pct == 1.5
    assert bangalore.commission_cap_pct == 2.0

    # Uttar Pradesh (UPSAMB): 1.5% mandi fee + 0.5% development cess = 2.0%
    agra = registry.get_mandi("mandi_agra")
    assert agra.mandi_cess_pct == 2.0
    assert agra.commission_cap_pct == 2.0


def test_regional_fallback_statutory_fees(registry):
    """Verify regional fallback inherits state-specific statutory fee schedules."""
    # Maharashtra unmapped market
    res_mh = registry.resolve("Unknown Nashik Yard", state="Maharashtra")
    assert res_mh.mandi_cess_pct == 1.05
    assert res_mh.commission_cap_pct == 6.0

    # Karnataka unmapped market
    res_ka = registry.resolve("Unknown Mandya Yard", state="Karnataka")
    assert res_ka.mandi_cess_pct == 1.5
    assert res_ka.commission_cap_pct == 2.0

    # Uttar Pradesh unmapped market
    res_up = registry.resolve("Unknown Mathura Yard", state="Uttar Pradesh")
    assert res_up.mandi_cess_pct == 2.0
    assert res_up.commission_cap_pct == 2.0

    # Default fallback for unlisted state
    res_def = registry.resolve("Unknown Yard", state="Sikkim")
    assert res_def.mandi_cess_pct == 1.0
    assert res_def.commission_cap_pct == 2.0
