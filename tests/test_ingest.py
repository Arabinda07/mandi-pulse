"""Tests for the IngestionEngine and end-to-end bootstrap flow."""

import pytest
from src.warehouse import Warehouse
from src.registry import MandiRegistry
from src.ingest import IngestionEngine
from src.sources.seed import BootstrapSeedAdapter


def test_end_to_end_bootstrap(tmp_path):
    db_file = tmp_path / "bootstrap_test.db"
    wh = Warehouse(db_file)
    registry = MandiRegistry()
    source = BootstrapSeedAdapter(days_history=60)

    engine = IngestionEngine(wh, registry, source)
    summary = engine.bootstrap(days_history=60)

    assert summary["mandis_registered"] > 0
    assert summary["facts_loaded"] > 100
    assert summary["corridor_metrics_computed"] > 0

    # Verify timeseries retrieval
    df = wh.get_corridor_timeseries("onion", "mandi_lasalgaon", "mandi_azadpur")
    assert not df.is_empty()
    assert "price_spread" in df.columns
    assert "spread_pct" in df.columns
    assert df.height >= 50
