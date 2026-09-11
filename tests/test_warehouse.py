"""Tests for the Warehouse storage and WAL configuration."""

import pytest
import sqlite3
from pathlib import Path
from src.warehouse import Warehouse
from src.models import MandiRecord, DailyFactRecord


@pytest.fixture
def temp_warehouse(tmp_path):
    db_file = tmp_path / "test_engine.db"
    wh = Warehouse(db_file)
    wh.initialize()
    return wh


def test_warehouse_wal_mode(temp_warehouse):
    # Verify WAL mode is active
    conn = sqlite3.connect(str(temp_warehouse.db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"


def test_warehouse_fact_upsert_and_views(temp_warehouse):
    # Add a mandi
    mandi = MandiRecord(
        mandi_id="m_test",
        canonical_name="Test Mandi",
        state="Test State",
        district="Test District",
        state_lgd_code=1,
        district_lgd_code=10,
        latitude=20.0,
        longitude=75.0,
    )
    temp_warehouse.record_mandis([mandi])

    # Add facts
    facts = [
        DailyFactRecord("m_test", "onion", "2026-01-01", 100.0, 1500.0, 1700.0, 1600.0),
        DailyFactRecord("m_test", "onion", "2026-01-02", 120.0, 1550.0, 1750.0, 1650.0),
    ]
    inserted = temp_warehouse.upsert_daily_facts(facts)
    assert inserted == 2

    # Verify idempotency (re-upserting same date updates rather than crashes)
    updated_facts = [
        DailyFactRecord("m_test", "onion", "2026-01-01", 110.0, 1500.0, 1700.0, 1620.0),
    ]
    re_inserted = temp_warehouse.upsert_daily_facts(updated_facts)
    assert re_inserted == 1

    conn = sqlite3.connect(str(temp_warehouse.db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT modal_price FROM daily_mandi_facts WHERE reported_date='2026-01-01';")
    price = cursor.fetchone()[0]
    conn.close()
    assert price == 1620.0


def test_statutory_cess_persistence_and_views(temp_warehouse):
    """Verify that mandi_cess_pct and commission_cap_pct persist and propagate to v_live_mandi_prices."""
    from src.models import DCARetailRecord

    mandi = MandiRecord(
        mandi_id="m_mh_test",
        canonical_name="MH Test Yard",
        state="Maharashtra",
        district="Nashik",
        state_lgd_code=27,
        district_lgd_code=485,
        latitude=20.0,
        longitude=74.0,
        mandi_cess_pct=1.05,
        commission_cap_pct=6.0,
    )
    temp_warehouse.record_mandis([mandi])

    # Insert daily wholesale facts
    facts = [
        DailyFactRecord("m_mh_test", "onion", "2026-09-10", 50.0, 2000.0, 2200.0, 2000.0),
    ]
    temp_warehouse.upsert_daily_facts(facts)

    # Insert DCA retail price
    dca = [
        DCARetailRecord(
            center_id="c_mh",
            center_name="Nashik",
            state="Maharashtra",
            commodity_id="onion",
            reported_date="2026-09-10",
            retail_price_rs_kg=28.0,
            mandi_id="m_mh_test",
            source_provenance="dca_pms",
        )
    ]
    temp_warehouse.upsert_dca_retail_facts(dca)

    df = temp_warehouse.get_live_mandi_prices()
    row = df.filter(df["mandi_id"] == "m_mh_test").to_dicts()[0]

    assert row["mandi_cess_pct"] == 1.05
    assert row["commission_cap_pct"] == 6.0
    # Wholesale: 2000 / 100 = 20.0 Rs/kg
    # Statutory cess: 20.0 * 1.05% = 0.21 Rs/kg
    assert row["statutory_cess_rs_kg"] == 0.21
    # Retail spread: 28.0 - (20.0 + 0.21) = 7.79 Rs/kg
    assert row["retail_spread_rs_kg"] == 7.79


def test_live_price_deltas_and_corridor_attributions(temp_warehouse):
    """Verify v_live_price_deltas computes windowed movements and v_live_mandi_prices joins corridor attributions."""
    from src.models import CorridorStress

    # 1. Register origin (Lasalgaon) and terminal (Azadpur) mandis
    orig_mandi = MandiRecord(
        mandi_id="mandi_lasalgaon",
        canonical_name="Lasalgaon",
        state="Maharashtra",
        district="Nashik",
        state_lgd_code=27,
        district_lgd_code=485,
        latitude=20.1472,
        longitude=74.2253,
        is_consumption_hub=False,
        hub_type="production",
        mandi_cess_pct=1.05,
        commission_cap_pct=6.0,
    )
    term_mandi = MandiRecord(
        mandi_id="mandi_azadpur",
        canonical_name="Azadpur (Delhi)",
        state="NCT of Delhi",
        district="North Delhi",
        state_lgd_code=7,
        district_lgd_code=138,
        latitude=28.7163,
        longitude=77.1772,
        is_consumption_hub=True,
        hub_type="consumption",
        mandi_cess_pct=2.0,
        commission_cap_pct=6.0,
    )
    temp_warehouse.record_mandis([orig_mandi, term_mandi])

    # 2. Insert sequential daily facts
    facts = [
        # Lasalgaon
        DailyFactRecord("mandi_lasalgaon", "onion", "2026-09-01", 100.0, 1500.0, 1700.0, 1600.0),
        DailyFactRecord("mandi_lasalgaon", "onion", "2026-09-02", 120.0, 1600.0, 1800.0, 1700.0),
        DailyFactRecord("mandi_lasalgaon", "onion", "2026-09-08", 110.0, 1700.0, 1900.0, 1800.0),
        # Azadpur
        DailyFactRecord("mandi_azadpur", "onion", "2026-09-01", 150.0, 2000.0, 2400.0, 2200.0),
        DailyFactRecord("mandi_azadpur", "onion", "2026-09-02", 140.0, 2200.0, 2600.0, 2420.0),
        DailyFactRecord("mandi_azadpur", "onion", "2026-09-08", 130.0, 2600.0, 3000.0, 2800.0),
    ]
    temp_warehouse.upsert_daily_facts(facts)

    # 3. Insert corridor stress metric
    csm = [
        CorridorStress(
            origin_mandi_id="mandi_lasalgaon",
            origin_name="Lasalgaon",
            terminal_mandi_id="mandi_azadpur",
            terminal_name="Azadpur (Delhi)",
            commodity_id="onion",
            reported_date="2026-09-08",
            origin_modal_price=1800.0,
            terminal_modal_price=2800.0,
            price_spread=1000.0,
            spread_pct=55.6,
            origin_arrival_shock_z=-2.45,
            stress_level="HIGH",
        )
    ]
    temp_warehouse.upsert_corridor_stress(csm)

    # 4. Check v_live_price_deltas
    deltas = temp_warehouse.get_live_price_deltas(commodity_id="onion", mandi_id="mandi_azadpur")
    assert deltas.height == 3
    
    # Check 2026-09-02: 2420 - 2200 = +220 qtl = +2.20 Rs/kg, +10%
    d_sep2 = deltas.filter(deltas["reported_date"] == "2026-09-02").to_dicts()[0]
    assert d_sep2["prev_day_price"] == 2200.0
    assert d_sep2["day_change_rs_qtl"] == 220.0
    assert d_sep2["day_change_rs_kg"] == 2.20
    assert d_sep2["day_change_pct"] == 10.0
    assert d_sep2["trend_signal"] == "Spike in ~10d"

    # Check 2026-09-08: 2800 - 2420 = +380 qtl = +3.80 Rs/kg
    d_sep8 = deltas.filter(deltas["reported_date"] == "2026-09-08").to_dicts()[0]
    assert d_sep8["prev_day_price"] == 2420.0
    assert d_sep8["day_change_rs_kg"] == 3.80
    assert d_sep8["day_change_pct"] == 15.70
    assert d_sep8["trend_signal"] == "Spike in ~10d"

    # 5. Check v_live_mandi_prices joined corridor attribution
    prices = temp_warehouse.get_live_mandi_prices(commodity="onion", date="2026-09-08")
    azadpur_row = prices.filter(prices["mandi_id"] == "mandi_azadpur").to_dicts()[0]

    assert azadpur_row["day_change_rs"] == 3.80
    assert azadpur_row["day_change_pct"] == 15.70
    assert azadpur_row["trend_signal"] == "Spike in ~10d"
    assert azadpur_row["origin_mandi_id"] == "mandi_lasalgaon"
    assert azadpur_row["origin_mandi_name"] == "Lasalgaon"
    assert azadpur_row["origin_arrival_shock_z"] == -2.45
    assert azadpur_row["corridor_stress_level"] == "HIGH"
    assert azadpur_row["origin_modal_price_rs_qtl"] == 1800.0
    assert azadpur_row["origin_modal_price_rs_kg"] == 18.0

