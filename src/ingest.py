"""Ingestion orchestrator coordinating sources, entity resolution, and warehouse writes."""

from __future__ import annotations
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from src.models import (
    MandiRecord,
    DailyFactRecord,
    CorridorStress,
    RawCommodityRecord,
)
from src.registry import MandiRegistry
from src.warehouse import Warehouse
from src.volatility import VolatilityEngine
from src.sources.base import CommoditySource
from src.sources.seed import BootstrapSeedAdapter

logger = logging.getLogger(__name__)


class IngestionEngine:
    """Deep module orchestrating data extraction, entity resolution, and warehouse loading."""

    # Pre-defined strategic trade corridors for stress monitoring
    STRATEGIC_CORRIDORS: List[Tuple[str, str, str]] = [
        # (commodity_id, origin_mandi_id, terminal_mandi_id)
        ("onion", "mandi_lasalgaon", "mandi_azadpur"),
        ("onion", "mandi_pimpalgaon", "mandi_azadpur"),
        ("onion", "mandi_lasalgaon", "mandi_vashi"),
        ("onion", "mandi_solapur", "mandi_kolkata"),
        ("tomato", "mandi_kolar", "mandi_azadpur"),
        ("tomato", "mandi_madanapalle", "mandi_azadpur"),
        ("tomato", "mandi_kolar", "mandi_bangalore"),
        ("potato", "mandi_agra", "mandi_azadpur"),
        ("potato", "mandi_farrukhabad", "mandi_azadpur"),
        ("potato", "mandi_agra", "mandi_kolkata"),
    ]

    def __init__(
        self,
        warehouse: Warehouse,
        registry: MandiRegistry,
        source: Optional[CommoditySource] = None,
    ) -> None:
        self.warehouse = warehouse
        self.registry = registry
        self.source = source or BootstrapSeedAdapter()

    def bootstrap(self, days_history: int = 180) -> Dict[str, int]:
        """
        Idempotent bootstrap:
        1. Initialize SQLite schema in WAL mode
        2. Load canonical Mandi Master Registry
        3. Ingest Tier 1 seed observations (Tomato, Onion, Potato)
        4. Calculate & materialize corridor stress metrics
        """
        self.warehouse.initialize()
        self.warehouse.record_mandis(self.registry.get_canonical_mandis())

        commodities = ["onion", "tomato", "potato"]
        total_facts = 0

        for comm in commodities:
            facts_count = self.ingest_commodity(comm)
            total_facts += facts_count

        # Compute & materialize corridor stress
        stress_count = self.refresh_corridor_stress_metrics()

        return {
            "mandis_registered": len(self.registry.get_canonical_mandis()),
            "facts_loaded": total_facts,
            "corridor_metrics_computed": stress_count,
        }

    def ingest_commodity(self, commodity: str) -> int:
        """Fetch records from source, resolve mandis, and load into warehouse."""
        raw_records = self.source.fetch_records(commodity)
        if not raw_records:
            return 0

        fact_records: List[DailyFactRecord] = []
        mandis_to_register: Dict[str, MandiRecord] = {}
        comm_id = commodity.lower().strip()

        for raw in raw_records:
            resolved = self.registry.resolve(raw.raw_market, raw.raw_state, raw.raw_district)
            if resolved.mandi_id not in mandis_to_register:
                mandis_to_register[resolved.mandi_id] = MandiRecord(
                    mandi_id=resolved.mandi_id,
                    canonical_name=resolved.canonical_name,
                    state=resolved.state,
                    district=resolved.district,
                    state_lgd_code=0,
                    district_lgd_code=resolved.district_lgd_code,
                    latitude=resolved.latitude,
                    longitude=resolved.longitude,
                    is_consumption_hub=resolved.is_consumption_hub,
                    hub_type="regional" if resolved.match_type == "regional" else ("consumption" if resolved.is_consumption_hub else "production"),
                )
            fact_records.append(
                DailyFactRecord(
                    mandi_id=resolved.mandi_id,
                    commodity_id=comm_id,
                    reported_date=raw.reported_date,
                    arrival_tonnes=raw.arrival_tonnes,
                    min_price=raw.min_price,
                    max_price=raw.max_price,
                    modal_price=raw.modal_price,
                )
            )

        if mandis_to_register:
            self.warehouse.record_mandis(list(mandis_to_register.values()))

        return self.warehouse.upsert_daily_facts(fact_records)

    def refresh_corridor_stress_metrics(self) -> int:
        """Compute dual-pillar volatility and stress metrics across all strategic corridors."""
        all_mandis = {m.mandi_id: m for m in self.registry.get_canonical_mandis()}
        evaluated_records: List[CorridorStress] = []

        for comm_id, origin_id, term_id in self.STRATEGIC_CORRIDORS:
            orig_mandi = all_mandis.get(origin_id)
            term_mandi = all_mandis.get(term_id)
            if not orig_mandi or not term_mandi:
                continue

            df = self.warehouse.get_corridor_timeseries(comm_id, origin_id, term_id)
            if df.is_empty() or df.height < 5:
                continue

            # Compute historical seasonal arrival volumes baseline (rolling list)
            arrival_list = df["origin_arrival"].to_list()

            for i in range(df.height):
                row = df.row(i, named=True)
                rep_date = row["reported_date"]
                orig_price = float(row["origin_price"])
                term_price = float(row["terminal_price"])
                curr_arrival = float(row["origin_arrival"])

                # Baseline arrival slice (up to 30 days window)
                window_start = max(0, i - 30)
                baseline_arrivals = arrival_list[window_start:i] if i > 0 else [curr_arrival]

                # Arrival Shock Anomaly
                arrival_z = VolatilityEngine.compute_arrival_shock(curr_arrival, baseline_arrivals)

                # Corridor Stress
                spread_inr, spread_pct, stress_level = VolatilityEngine.evaluate_corridor_stress(
                    orig_price, term_price, arrival_z
                )

                evaluated_records.append(
                    CorridorStress(
                        origin_mandi_id=origin_id,
                        origin_name=orig_mandi.canonical_name,
                        terminal_mandi_id=term_id,
                        terminal_name=term_mandi.canonical_name,
                        commodity_id=comm_id,
                        reported_date=rep_date,
                        origin_modal_price=orig_price,
                        terminal_modal_price=term_price,
                        price_spread=spread_inr,
                        spread_pct=spread_pct,
                        origin_arrival_shock_z=arrival_z,
                        stress_level=stress_level,
                    )
                )

        self.warehouse.upsert_corridor_stress(evaluated_records)
        return len(evaluated_records)
