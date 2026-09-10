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
