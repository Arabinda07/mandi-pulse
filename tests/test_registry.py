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
