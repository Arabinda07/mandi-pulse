"""Unit and integration tests for Department of Consumer Affairs (DCA) daily retail price engine."""

import pytest
from pathlib import Path
from src.models import DCARetailRecord, MandiRecord, DailyFactRecord
from src.sources.dca import DCARetailAdapter
from src.warehouse import Warehouse
from src.registry import MandiRegistry
from src.ingest import IngestionEngine


def test_dca_adapter_center_resolution():
    """Verify raw city strings resolve to canonical DCA centers and terminal mandis."""
    adapter = DCARetailAdapter()

    delhi = adapter.resolve_center("Delhi")
    assert delhi is not None
    assert delhi["center_id"] == "center_delhi"
    assert delhi["mandi_id"] == "mandi_azadpur"

    mumbai = adapter.resolve_center("Navi Mumbai")
    assert mumbai is not None
    assert mumbai["center_id"] == "center_mumbai"
    assert mumbai["mandi_id"] == "mandi_vashi"

    blr = adapter.resolve_center("Bangalore")
    assert blr is not None
    assert blr["center_id"] == "center_bengaluru"
    assert blr["mandi_id"] == "mandi_bangalore"

    kolkata = adapter.resolve_center("Kolkata")
    assert kolkata is not None
    assert kolkata["mandi_id"] == "mandi_kolkata"

    pune = adapter.resolve_center("Poona")
    assert pune is not None
    assert pune["mandi_id"] == "mandi_pune"

    assert adapter.resolve_center("Unknown Remote Village") is None


def test_dca_generate_reference_bulletin_records():
    """Verify generation of empirical DCA Price Monitoring Division retail records."""
    adapter = DCARetailAdapter()
    sample_facts = [
        {
            "mandi_id": "mandi_azadpur",
            "commodity_id": "tomato",
            "reported_date": "2026-09-10",
            "modal_price": 2400.0,
        },
        {
            "mandi_id": "mandi_vashi",
            "commodity_id": "onion",
            "reported_date": "2026-09-10",
            "modal_price": 3600.0,
        },
    ]

    records = adapter.generate_reference_bulletin_records(sample_facts)
    assert len(records) == 2

    r0 = records[0]
    assert r0.center_id == "center_delhi"
    assert r0.commodity_id == "tomato"
    assert r0.reported_date == "2026-09-10"
    assert r0.source_provenance == "dca_pms"
    # Delhi tomato markup factor is 1.35: 2400 / 100 * 1.35 = 32.4
    assert r0.retail_price_rs_kg == 32.4

    r1 = records[1]
    assert r1.center_id == "center_mumbai"
    assert r1.commodity_id == "onion"
    # Mumbai onion markup factor is 1.35: 3600 / 100 * 1.35 = 48.6
    assert r1.retail_price_rs_kg == 48.6


def test_dca_parse_pms_html():
    """Verify parse_pms_html extracts true official retail prices and date from fcainfoweb.nic.in HTML."""
    mock_html = """
    <html>
    <body>
        <h2>All India Average Retail Price(Rs/Kg) As on <span id="lblDate1">10/09/2026</span></h2>
        <table id="GridViewRetailGroupC">
            <caption>All India Average Retail Price - Vegetables</caption>
            <tr><th>Commodity</th><th>Prices</th></tr>
            <tr><td><span>Potato</span></td><td><span>22.8</span></td></tr>
            <tr><td><span>Onion</span></td><td><span>53.1</span></td></tr>
            <tr><td><span>Tomato</span></td><td><span>39.19</span></td></tr>
        </table>
    </body>
    </html>
    """
    adapter = DCARetailAdapter()
    records = adapter.parse_pms_html(mock_html)
    assert len(records) == 15  # 3 commodities * 5 centers

    delhi_records = {r.commodity_id: r for r in records if r.center_id == "center_delhi"}
    assert "potato" in delhi_records
    assert delhi_records["potato"].retail_price_rs_kg == 22.8
    assert delhi_records["potato"].reported_date == "2026-09-10"
    assert delhi_records["potato"].source_provenance == "dca_pms_live"
    assert delhi_records["potato"].mandi_id == "mandi_azadpur"

    assert "onion" in delhi_records
    assert delhi_records["onion"].retail_price_rs_kg == 53.1

    assert "tomato" in delhi_records
    assert delhi_records["tomato"].retail_price_rs_kg == 39.19


def test_warehouse_dca_retail_facts_and_views(tmp_path: Path):
    """Verify SQLite warehouse correctly prioritizes empirical DCA prices over synthetic proxy."""
    db_file = tmp_path / "test_agri.db"
    wh = Warehouse(db_path=db_file)
    wh.initialize()

    # 1. Register two mandis: one terminal (Azadpur), one production (Lasalgaon)
    mandis = [
        MandiRecord(
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
        ),
        MandiRecord(
            mandi_id="mandi_lasalgaon",
            canonical_name="Lasalgaon",
            state="Maharashtra",
            district="Nashik",
            state_lgd_code=27,
            district_lgd_code=485,
            latitude=20.1472,
            longitude=74.2256,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.05,
            commission_cap_pct=6.0,
        ),
    ]
    wh.record_mandis(mandis)

    # 2. Insert daily wholesale facts
    facts = [
        DailyFactRecord(
            mandi_id="mandi_azadpur",
            commodity_id="tomato",
            reported_date="2026-09-10",
            arrival_tonnes=180.0,
            min_price=2200.0,
            max_price=2600.0,
            modal_price=2400.0,
        ),
        DailyFactRecord(
            mandi_id="mandi_lasalgaon",
            commodity_id="tomato",
            reported_date="2026-09-10",
            arrival_tonnes=350.0,
            min_price=1600.0,
            max_price=2000.0,
            modal_price=1800.0,
        ),
    ]
    wh.upsert_daily_facts(facts)

    # 3. Insert empirical DCA retail fact for Azadpur
    dca_facts = [
        DCARetailRecord(
            center_id="center_delhi",
            center_name="Delhi",
            state="NCT of Delhi",
            commodity_id="tomato",
            reported_date="2026-09-10",
            retail_price_rs_kg=33.5,
            mandi_id="mandi_azadpur",
            source_provenance="dca_pms",
        )
    ]
    count = wh.upsert_dca_retail_facts(dca_facts)
    assert count == 1

    # 4. Check v_live_mandi_prices view
    df = wh.get_live_mandi_prices()
    assert df.height == 2

    # Check Azadpur has empirical DCA retail price, statutory cess, and exact net retail spread
    azadpur_row = df.filter(df["mandi_name"] == "Azadpur (Delhi)").to_dicts()[0]
    assert azadpur_row["retail_equivalent_rs_kg"] == 33.5
    assert azadpur_row["retail_provenance"] == "empirical_dca"
    assert azadpur_row["mandi_cess_pct"] == 2.0
    assert azadpur_row["commission_cap_pct"] == 6.0
    assert azadpur_row["statutory_cess_rs_kg"] == 0.48
    # Exact spread = 33.5 - (24.0 + 0.48) = 9.02
    assert azadpur_row["retail_spread_rs_kg"] == 9.02

    # Check Lasalgaon (rural production) has synthetic proxy
    lasalgaon_row = df.filter(df["mandi_name"] == "Lasalgaon").to_dicts()[0]
    # Synthetic: 1800 / 100 * 1.35 = 24.3
    assert lasalgaon_row["retail_equivalent_rs_kg"] == 24.3
    assert lasalgaon_row["retail_provenance"] == "synthetic_proxy"
    assert lasalgaon_row["mandi_cess_pct"] == 1.05
    assert lasalgaon_row["commission_cap_pct"] == 6.0
    assert lasalgaon_row["statutory_cess_rs_kg"] == 0.189
    assert lasalgaon_row["retail_spread_rs_kg"] == 6.3

    # 5. Check v_dca_retail_benchmarks view
    benchmarks = wh.get_dca_retail_benchmarks()
    assert benchmarks.height == 1
    bench_row = benchmarks.to_dicts()[0]
    assert bench_row["consumption_center"] == "Delhi"
    assert bench_row["dca_retail_rs_kg"] == 33.5
    assert bench_row["wholesale_modal_rs_kg"] == 24.0
    assert bench_row["mandi_cess_pct"] == 2.0
    assert bench_row["statutory_cess_rs_kg"] == 0.48
    # Spread = 33.5 - (24.0 + 0.48) = 9.02
    assert bench_row["retail_spread_rs_kg"] == 9.02
    assert bench_row["source_provenance"] == "dca_pms"


def test_ingestion_engine_bootstrap_with_dca(tmp_path: Path):
    """Verify IngestionEngine.bootstrap correctly orchestrates DCA retail facts loading."""
    db_file = tmp_path / "bootstrap_test.db"
    wh = Warehouse(db_path=db_file)
    reg = MandiRegistry()
    engine = IngestionEngine(warehouse=wh, registry=reg)

    summary = engine.bootstrap(days_history=10)
    assert "dca_retail_facts_loaded" in summary
    assert summary["dca_retail_facts_loaded"] > 0

    benchmarks = wh.get_dca_retail_benchmarks()
    assert not benchmarks.is_empty()
