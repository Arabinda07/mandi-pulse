"""Shared SQLite Warehouse with WAL mode, indexing, views, and Polars integrations."""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import polars as pl

from src.models import (
    MandiRecord,
    CommodityRecord,
    DailyFactRecord,
    CorridorStress,
    DCARetailRecord,
)
from src.volatility import VolatilityEngine


class Warehouse:
    """Deep module for persistent storage, WAL concurrency, and analytical query execution."""

    DEFAULT_DB_PATH = Path("data/agri_engine.db")

    # Core Tier 1 Commodity catalog
    TIER_1_COMMODITIES: List[CommodityRecord] = [
        CommodityRecord("tomato", "Tomato", "vegetable", 1, "quintal", 0.57),
        CommodityRecord("onion", "Onion", "vegetable", 1, "quintal", 0.64),
        CommodityRecord("potato", "Potato", "vegetable", 1, "quintal", 1.00),
        CommodityRecord("garlic", "Garlic", "spice/vegetable", 1, "quintal", 0.25),
        CommodityRecord("ginger", "Ginger (Green)", "spice/vegetable", 1, "quintal", 0.20),
        CommodityRecord("chana_dal", "Gram Dal (Chana)", "pulse", 1, "quintal", 0.72),
        CommodityRecord("tur_arhar_dal", "Tur/Arhar Dal", "pulse", 1, "quintal", 0.79),
        CommodityRecord("wheat", "Wheat", "cereal", 1, "quintal", 3.03),
        CommodityRecord("rice", "Rice / Paddy", "cereal", 1, "quintal", 4.39),
        CommodityRecord("mustard_oil", "Mustard Oil", "oilseed", 1, "quintal", 1.34),
    ]

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        self.db_path = Path(db_path or self.DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with WAL and busy timeout configured."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 10000;")
        return conn

    def initialize(self) -> None:
        """Idempotently create tables, constraints, indices, and views."""
        with self._get_connection() as conn:
            # Handle schema evolution for existing SQLite databases
            cur = conn.execute("PRAGMA table_info(mandi_registry);")
            cols = {row[1] for row in cur.fetchall()}
            if cols:
                if "mandi_cess_pct" not in cols:
                    conn.execute("ALTER TABLE mandi_registry ADD COLUMN mandi_cess_pct REAL NOT NULL DEFAULT 1.0;")
                if "commission_cap_pct" not in cols:
                    conn.execute("ALTER TABLE mandi_registry ADD COLUMN commission_cap_pct REAL NOT NULL DEFAULT 0.0;")

            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mandi_registry (
                    mandi_id TEXT PRIMARY KEY,
                    canonical_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    district TEXT NOT NULL,
                    state_lgd_code INTEGER NOT NULL,
                    district_lgd_code INTEGER NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    is_consumption_hub INTEGER NOT NULL DEFAULT 0,
                    hub_type TEXT NOT NULL DEFAULT 'production',
                    mandi_cess_pct REAL NOT NULL DEFAULT 1.0,
                    commission_cap_pct REAL NOT NULL DEFAULT 0.0
                );

                CREATE TABLE IF NOT EXISTS commodity_registry (
                    commodity_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tier INTEGER NOT NULL DEFAULT 1,
                    unit TEXT NOT NULL DEFAULT 'quintal',
                    cpi_weight REAL NOT NULL DEFAULT 0.0
                );

                CREATE TABLE IF NOT EXISTS daily_mandi_facts (
                    mandi_id TEXT NOT NULL,
                    commodity_id TEXT NOT NULL,
                    reported_date TEXT NOT NULL,
                    arrival_tonnes REAL NOT NULL,
                    min_price REAL NOT NULL,
                    max_price REAL NOT NULL,
                    modal_price REAL NOT NULL,
                    PRIMARY KEY (mandi_id, commodity_id, reported_date),
                    FOREIGN KEY (mandi_id) REFERENCES mandi_registry(mandi_id),
                    FOREIGN KEY (commodity_id) REFERENCES commodity_registry(commodity_id)
                );

                CREATE INDEX IF NOT EXISTS idx_facts_date_commodity 
                ON daily_mandi_facts(reported_date, commodity_id);

                CREATE INDEX IF NOT EXISTS idx_facts_commodity_mandi
                ON daily_mandi_facts(commodity_id, mandi_id, reported_date);

                CREATE TABLE IF NOT EXISTS corridor_stress_metrics (
                    corridor_id TEXT NOT NULL,
                    origin_mandi_id TEXT NOT NULL,
                    terminal_mandi_id TEXT NOT NULL,
                    commodity_id TEXT NOT NULL,
                    reported_date TEXT NOT NULL,
                    origin_modal_price REAL NOT NULL,
                    terminal_modal_price REAL NOT NULL,
                    price_spread REAL NOT NULL,
                    spread_pct REAL NOT NULL,
                    origin_arrival_shock_z REAL NOT NULL,
                    stress_level TEXT NOT NULL,
                    PRIMARY KEY (corridor_id, commodity_id, reported_date)
                );

                CREATE TABLE IF NOT EXISTS mandi_weather_facts (
                    mandi_id TEXT NOT NULL,
                    observation_date TEXT NOT NULL,
                    precipitation_mm REAL NOT NULL,
                    max_temp_c REAL NOT NULL,
                    weather_flag TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (mandi_id, observation_date),
                    FOREIGN KEY (mandi_id) REFERENCES mandi_registry(mandi_id)
                );

                -- Department of Consumer Affairs (DCA) Price Monitoring Division daily retail prices
                CREATE TABLE IF NOT EXISTS dca_retail_facts (
                    center_id TEXT NOT NULL,
                    mandi_id TEXT,
                    center_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    commodity_id TEXT NOT NULL,
                    reported_date TEXT NOT NULL,
                    retail_price_rs_kg REAL NOT NULL,
                    source_provenance TEXT NOT NULL DEFAULT 'dca_pms',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (center_id, commodity_id, reported_date),
                    FOREIGN KEY (commodity_id) REFERENCES commodity_registry(commodity_id)
                );

                CREATE INDEX IF NOT EXISTS idx_dca_date_comm 
                ON dca_retail_facts(reported_date, commodity_id);

                CREATE INDEX IF NOT EXISTS idx_dca_mandi_comm 
                ON dca_retail_facts(mandi_id, commodity_id, reported_date);

                -- View for quick national daily overview
                CREATE VIEW IF NOT EXISTS v_daily_national_summary AS
                SELECT 
                    f.reported_date,
                    f.commodity_id,
                    c.name AS commodity_name,
                    ROUND(AVG(f.modal_price), 2) AS avg_modal_price,
                    ROUND(MIN(f.min_price), 2) AS min_modal_price,
                    ROUND(MAX(f.max_price), 2) AS max_modal_price,
                    ROUND(SUM(f.arrival_tonnes), 2) AS total_arrival_tonnes,
                    COUNT(DISTINCT f.mandi_id) AS reporting_mandis_count
                FROM daily_mandi_facts f
                JOIN commodity_registry c ON f.commodity_id = c.commodity_id
                GROUP BY f.reported_date, f.commodity_id, c.name;

                -- View for active market price arbitrage across production vs terminal
                CREATE VIEW IF NOT EXISTS v_active_corridor_stress AS
                SELECT 
                    m.reported_date,
                    c.name AS commodity_name,
                    orig.canonical_name AS origin_mandi,
                    term.canonical_name AS terminal_mandi,
                    m.origin_modal_price,
                    m.terminal_modal_price,
                    m.price_spread,
                    m.spread_pct,
                    m.origin_arrival_shock_z,
                    m.stress_level
                FROM corridor_stress_metrics m
                JOIN commodity_registry c ON m.commodity_id = c.commodity_id
                JOIN mandi_registry orig ON m.origin_mandi_id = orig.mandi_id
                JOIN mandi_registry term ON m.terminal_mandi_id = term.mandi_id
                ORDER BY m.reported_date DESC, m.spread_pct DESC;

                -- Windowed day-over-day and week-over-week price movements
                DROP VIEW IF EXISTS v_live_price_deltas;
                CREATE VIEW v_live_price_deltas AS
                SELECT 
                    mandi_id,
                    commodity_id,
                    reported_date,
                    modal_price,
                    LAG(modal_price, 1) OVER (
                        PARTITION BY commodity_id, mandi_id 
                        ORDER BY reported_date ASC
                    ) AS prev_day_price,
                    LAG(reported_date, 1) OVER (
                        PARTITION BY commodity_id, mandi_id 
                        ORDER BY reported_date ASC
                    ) AS prev_day_date,
                    ROUND(modal_price - LAG(modal_price, 1) OVER (
                        PARTITION BY commodity_id, mandi_id 
                        ORDER BY reported_date ASC
                    ), 2) AS day_change_rs_qtl,
                    ROUND((modal_price - LAG(modal_price, 1) OVER (
                        PARTITION BY commodity_id, mandi_id 
                        ORDER BY reported_date ASC
                    )) / 100.0, 2) AS day_change_rs_kg,
                    CASE 
                        WHEN LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        ) > 0 
                        THEN ROUND(((modal_price - LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        )) / LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        )) * 100.0, 2)
                        ELSE 0.0 
                    END AS day_change_pct,
                    LAG(modal_price, 7) OVER (
                        PARTITION BY commodity_id, mandi_id 
                        ORDER BY reported_date ASC
                    ) AS prev_week_price,
                    LAG(reported_date, 7) OVER (
                        PARTITION BY commodity_id, mandi_id 
                        ORDER BY reported_date ASC
                    ) AS prev_week_date,
                    CASE 
                        WHEN LAG(modal_price, 7) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        ) > 0 
                        THEN ROUND(((modal_price - LAG(modal_price, 7) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        )) / LAG(modal_price, 7) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        )) * 100.0, 2)
                        WHEN LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        ) > 0 
                        THEN ROUND(((modal_price - LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        )) / LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        )) * 100.0, 2)
                        ELSE 0.0 
                    END AS week_change_pct,
                    CASE
                        WHEN modal_price > LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        ) * 1.05 THEN 'Spike in ~10d'
                        WHEN modal_price < LAG(modal_price, 1) OVER (
                            PARTITION BY commodity_id, mandi_id 
                            ORDER BY reported_date ASC
                        ) * 0.95 THEN 'Cooling Down in ~7d'
                        ELSE 'Stable Corridor'
                    END AS trend_signal
                FROM daily_mandi_facts;

                -- Ranked corridor attributions for terminal consumption mandis
                DROP VIEW IF EXISTS v_corridor_attributions;
                CREATE VIEW v_corridor_attributions AS
                WITH ranked_terminal AS (
                    SELECT 
                        csm.corridor_id,
                        csm.commodity_id,
                        csm.terminal_mandi_id,
                        csm.reported_date,
                        csm.origin_mandi_id,
                        orig.canonical_name AS origin_name,
                        orig.latitude AS origin_latitude,
                        orig.longitude AS origin_longitude,
                        csm.origin_modal_price,
                        csm.price_spread,
                        csm.spread_pct,
                        csm.origin_arrival_shock_z,
                        csm.stress_level,
                        ROW_NUMBER() OVER (
                            PARTITION BY csm.commodity_id, csm.terminal_mandi_id, csm.reported_date 
                            ORDER BY ABS(csm.origin_arrival_shock_z) DESC
                        ) AS rn
                    FROM corridor_stress_metrics csm
                    JOIN mandi_registry orig ON csm.origin_mandi_id = orig.mandi_id
                )
                SELECT * FROM ranked_terminal WHERE rn = 1;

                -- Ranked corridor attributions for origin production mandis
                DROP VIEW IF EXISTS v_origin_corridor_attributions;
                CREATE VIEW v_origin_corridor_attributions AS
                WITH ranked_origin AS (
                    SELECT 
                        csm.corridor_id,
                        csm.commodity_id,
                        csm.origin_mandi_id,
                        csm.reported_date,
                        orig.canonical_name AS origin_name,
                        orig.latitude AS origin_latitude,
                        orig.longitude AS origin_longitude,
                        csm.origin_modal_price,
                        csm.origin_arrival_shock_z,
                        csm.stress_level,
                        ROW_NUMBER() OVER (
                            PARTITION BY csm.commodity_id, csm.origin_mandi_id, csm.reported_date 
                            ORDER BY ABS(csm.origin_arrival_shock_z) DESC
                        ) AS rn
                    FROM corridor_stress_metrics csm
                    JOIN mandi_registry orig ON csm.origin_mandi_id = orig.mandi_id
                )
                SELECT * FROM ranked_origin WHERE rn = 1;

                -- High-readability primary market price explorer view with empirical DCA retail integration
                DROP VIEW IF EXISTS v_live_mandi_prices;
                CREATE VIEW v_live_mandi_prices AS
                SELECT 
                    f.reported_date AS reported_date,
                    c.name AS commodity,
                    f.commodity_id AS commodity_id,
                    m.mandi_id AS mandi_id,
                    m.state AS state,
                    m.district AS district,
                    m.canonical_name AS mandi_name,
                    ROUND(f.modal_price, 2) AS wholesale_price_rs_qtl,
                    COALESCE(d.retail_price_rs_kg, ROUND((f.modal_price / 100.0) * 1.35, 2)) AS retail_equivalent_rs_kg,
                    ROUND(f.modal_price / 100.0, 2) AS wholesale_rs_kg,
                    m.mandi_cess_pct AS mandi_cess_pct,
                    m.commission_cap_pct AS commission_cap_pct,
                    ROUND((f.modal_price / 100.0) * (m.mandi_cess_pct / 100.0), 3) AS statutory_cess_rs_kg,
                    COALESCE(
                        ROUND(d.retail_price_rs_kg - (f.modal_price / 100.0) - ((f.modal_price / 100.0) * (m.mandi_cess_pct / 100.0)), 2),
                        ROUND((f.modal_price / 100.0) * 0.35, 2)
                    ) AS retail_spread_rs_kg,
                    CASE 
                        WHEN d.retail_price_rs_kg IS NOT NULL THEN 'empirical_dca'
                        ELSE 'synthetic_proxy'
                    END AS retail_provenance,
                    ROUND(f.min_price, 2) AS min_price_rs_qtl,
                    ROUND(f.max_price, 2) AS max_price_rs_qtl,
                    ROUND(f.max_price - f.min_price, 2) AS intraday_spread_rs_qtl,
                    ROUND(f.arrival_tonnes, 1) AS arrival_tonnes,
                    m.hub_type AS market_type,
                    m.latitude AS latitude,
                    m.longitude AS longitude,

                    -- Dynamic Price Movements (Windowed deltas)
                    COALESCE(pdel.day_change_rs_kg, 0.0) AS day_change_rs,
                    COALESCE(pdel.day_change_pct, 0.0) AS day_change_pct,
                    COALESCE(pdel.week_change_pct, 0.0) AS week_change_pct,
                    COALESCE(pdel.trend_signal, 'Stable Corridor') AS trend_signal,

                    -- Origin Production Mandi & Corridor Metrics
                    COALESCE(tc.origin_mandi_id, oc.origin_mandi_id, 
                        CASE f.commodity_id 
                            WHEN 'onion' THEN 'mandi_lasalgaon' 
                            WHEN 'tomato' THEN 'mandi_kolar' 
                            WHEN 'potato' THEN 'mandi_farrukhabad' 
                            ELSE 'mandi_lasalgaon' 
                        END
                    ) AS origin_mandi_id,
                    COALESCE(tc.origin_name, oc.origin_name,
                        CASE f.commodity_id 
                            WHEN 'onion' THEN 'Lasalgaon' 
                            WHEN 'tomato' THEN 'Kolar' 
                            WHEN 'potato' THEN 'Farrukhabad' 
                            ELSE 'Primary Production Hub' 
                        END
                    ) AS origin_mandi_name,
                    COALESCE(tc.origin_latitude, oc.origin_latitude,
                        CASE f.commodity_id 
                            WHEN 'onion' THEN 20.1472 
                            WHEN 'tomato' THEN 13.1367 
                            WHEN 'potato' THEN 27.3826 
                            ELSE 20.0 
                        END
                    ) AS origin_latitude,
                    COALESCE(tc.origin_longitude, oc.origin_longitude,
                        CASE f.commodity_id 
                            WHEN 'onion' THEN 74.2253 
                            WHEN 'tomato' THEN 78.1292 
                            WHEN 'potato' THEN 79.5828 
                            ELSE 74.0 
                        END
                    ) AS origin_longitude,
                    COALESCE(tc.origin_modal_price, oc.origin_modal_price, f.modal_price) AS origin_modal_price_rs_qtl,
                    ROUND(COALESCE(tc.origin_modal_price, oc.origin_modal_price, f.modal_price) / 100.0, 2) AS origin_modal_price_rs_kg,
                    COALESCE(tc.origin_arrival_shock_z, oc.origin_arrival_shock_z, 0.0) AS origin_arrival_shock_z,
                    COALESCE(tc.stress_level, oc.stress_level, 'NORMAL') AS corridor_stress_level
                FROM daily_mandi_facts f
                JOIN mandi_registry m ON f.mandi_id = m.mandi_id
                JOIN commodity_registry c ON f.commodity_id = c.commodity_id
                LEFT JOIN dca_retail_facts d 
                    ON d.mandi_id = f.mandi_id 
                    AND d.commodity_id = f.commodity_id 
                    AND d.reported_date = f.reported_date
                LEFT JOIN v_live_price_deltas pdel
                    ON pdel.mandi_id = f.mandi_id
                    AND pdel.commodity_id = f.commodity_id
                    AND pdel.reported_date = f.reported_date
                LEFT JOIN v_corridor_attributions tc
                    ON tc.terminal_mandi_id = f.mandi_id
                    AND tc.commodity_id = f.commodity_id
                    AND tc.reported_date = f.reported_date
                LEFT JOIN v_origin_corridor_attributions oc
                    ON oc.origin_mandi_id = f.mandi_id
                    AND oc.commodity_id = f.commodity_id
                    AND oc.reported_date = f.reported_date
                WHERE f.modal_price >= 100.0
                ORDER BY f.reported_date DESC, f.modal_price DESC;

                -- Official DCA Retail Price Benchmarks vs Terminal Wholesale Modal Prices
                DROP VIEW IF EXISTS v_dca_retail_benchmarks;
                CREATE VIEW v_dca_retail_benchmarks AS
                SELECT
                    d.reported_date,
                    c.name AS commodity,
                    d.center_name AS consumption_center,
                    d.state,
                    m.canonical_name AS terminal_mandi,
                    d.retail_price_rs_kg AS dca_retail_rs_kg,
                    ROUND(f.modal_price, 2) AS wholesale_modal_rs_qtl,
                    ROUND(f.modal_price / 100.0, 2) AS wholesale_modal_rs_kg,
                    COALESCE(m.mandi_cess_pct, 1.0) AS mandi_cess_pct,
                    COALESCE(m.commission_cap_pct, 0.0) AS commission_cap_pct,
                    ROUND((f.modal_price / 100.0) * (COALESCE(m.mandi_cess_pct, 1.0) / 100.0), 3) AS statutory_cess_rs_kg,
                    ROUND(d.retail_price_rs_kg - (f.modal_price / 100.0) - ((f.modal_price / 100.0) * (COALESCE(m.mandi_cess_pct, 1.0) / 100.0)), 2) AS retail_spread_rs_kg,
                    ROUND(((d.retail_price_rs_kg - (f.modal_price / 100.0) - ((f.modal_price / 100.0) * (COALESCE(m.mandi_cess_pct, 1.0) / 100.0))) / (f.modal_price / 100.0)) * 100.0, 1) AS retail_spread_pct,
                    d.source_provenance
                FROM dca_retail_facts d
                JOIN commodity_registry c ON d.commodity_id = c.commodity_id
                LEFT JOIN mandi_registry m ON d.mandi_id = m.mandi_id
                LEFT JOIN daily_mandi_facts f 
                    ON d.mandi_id = f.mandi_id 
                    AND d.commodity_id = f.commodity_id 
                    AND d.reported_date = f.reported_date
                ORDER BY d.reported_date DESC, d.center_name ASC;


                -- Attribution reports table storing evaluated driver behind price moves
                CREATE TABLE IF NOT EXISTS attribution_reports (
                    mandi_id TEXT NOT NULL,
                    commodity_id TEXT NOT NULL,
                    reported_date TEXT NOT NULL,
                    modal_price REAL NOT NULL,
                    price_change_pct REAL NOT NULL,
                    primary_driver TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    crop_season TEXT NOT NULL,
                    cultural_context TEXT NOT NULL,
                    weather_flag TEXT,
                    PRIMARY KEY (mandi_id, commodity_id, reported_date),
                    FOREIGN KEY (mandi_id) REFERENCES mandi_registry(mandi_id),
                    FOREIGN KEY (commodity_id) REFERENCES commodity_registry(commodity_id)
                );

                -- High-level view for human-readable price movement attribution
                CREATE VIEW IF NOT EXISTS v_price_movement_attribution AS
                SELECT 
                    a.reported_date,
                    c.name AS commodity,
                    m.state,
                    m.district,
                    m.canonical_name AS mandi_name,
                    ROUND(a.modal_price / 100.0, 2) AS price_rs_kg,
                    ROUND(a.price_change_pct, 1) AS change_pct,
                    a.severity,
                    a.headline,
                    a.explanation,
                    a.crop_season,
                    a.cultural_context,
                    a.weather_flag
                FROM attribution_reports a
                JOIN mandi_registry m ON a.mandi_id = m.mandi_id
                JOIN commodity_registry c ON a.commodity_id = c.commodity_id
                ORDER BY a.reported_date DESC, ABS(a.price_change_pct) DESC;
            """)

            # Seed default commodities if empty
            for c in self.TIER_1_COMMODITIES:
                conn.execute("""
                    INSERT OR IGNORE INTO commodity_registry 
                    (commodity_id, name, category, tier, unit, cpi_weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (c.commodity_id, c.name, c.category, c.tier, c.unit, c.cpi_weight))

    def ensure_commodity(self, commodity_id: str, name: Optional[str] = None, category: str = "vegetable") -> None:
        """Ensure a commodity is present in commodity_registry to satisfy foreign keys."""
        display_name = name or commodity_id.replace("_", " ").title()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO commodity_registry 
                (commodity_id, name, category, tier, unit, cpi_weight)
                VALUES (?, ?, ?, 1, 'quintal', 0.50)
            """, (commodity_id, display_name, category))

    def record_mandis(self, mandis: List[MandiRecord]) -> None:
        """Upsert canonical Mandi records."""
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT INTO mandi_registry 
                (mandi_id, canonical_name, state, district, state_lgd_code, district_lgd_code, latitude, longitude, is_consumption_hub, hub_type, mandi_cess_pct, commission_cap_pct)
                VALUES (:mandi_id, :canonical_name, :state, :district, :state_lgd_code, :district_lgd_code, :latitude, :longitude, :is_consumption_hub, :hub_type, :mandi_cess_pct, :commission_cap_pct)
                ON CONFLICT(mandi_id) DO UPDATE SET
                    canonical_name=excluded.canonical_name,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    is_consumption_hub=excluded.is_consumption_hub,
                    hub_type=excluded.hub_type,
                    mandi_cess_pct=excluded.mandi_cess_pct,
                    commission_cap_pct=excluded.commission_cap_pct;
            """, [m.__dict__ for m in mandis])

    def upsert_daily_facts(self, facts: List[DailyFactRecord]) -> int:
        """Batch upsert daily market facts."""
        if not facts:
            return 0
        with self._get_connection() as conn:
            cursor = conn.executemany("""
                INSERT INTO daily_mandi_facts
                (mandi_id, commodity_id, reported_date, arrival_tonnes, min_price, max_price, modal_price)
                VALUES (:mandi_id, :commodity_id, :reported_date, :arrival_tonnes, :min_price, :max_price, :modal_price)
                ON CONFLICT(mandi_id, commodity_id, reported_date) DO UPDATE SET
                    arrival_tonnes=excluded.arrival_tonnes,
                    min_price=excluded.min_price,
                    max_price=excluded.max_price,
                    modal_price=excluded.modal_price;
            """, [f.__dict__ for f in facts])
            return len(facts)

    def upsert_dca_retail_facts(self, facts: List[DCARetailRecord]) -> int:
        """Batch upsert Department of Consumer Affairs daily retail observations."""
        if not facts:
            return 0
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT INTO dca_retail_facts
                (center_id, mandi_id, center_name, state, commodity_id, reported_date, retail_price_rs_kg, source_provenance)
                VALUES (:center_id, :mandi_id, :center_name, :state, :commodity_id, :reported_date, :retail_price_rs_kg, :source_provenance)
                ON CONFLICT(center_id, commodity_id, reported_date) DO UPDATE SET
                    retail_price_rs_kg=excluded.retail_price_rs_kg,
                    mandi_id=excluded.mandi_id,
                    source_provenance=excluded.source_provenance;
            """, [f.__dict__ for f in facts])
            return len(facts)


    def upsert_corridor_stress(self, records: List[CorridorStress]) -> None:
        """Materialize evaluated corridor stress metrics."""
        if not records:
            return
        with self._get_connection() as conn:
            payload = []
            for r in records:
                corridor_id = f"{r.origin_mandi_id}->{r.terminal_mandi_id}"
                payload.append({
                    "corridor_id": corridor_id,
                    "origin_mandi_id": r.origin_mandi_id,
                    "terminal_mandi_id": r.terminal_mandi_id,
                    "commodity_id": r.commodity_id,
                    "reported_date": r.reported_date,
                    "origin_modal_price": r.origin_modal_price,
                    "terminal_modal_price": r.terminal_modal_price,
                    "price_spread": r.price_spread,
                    "spread_pct": r.spread_pct,
                    "origin_arrival_shock_z": r.origin_arrival_shock_z,
                    "stress_level": r.stress_level,
                })
            conn.executemany("""
                INSERT INTO corridor_stress_metrics
                (corridor_id, origin_mandi_id, terminal_mandi_id, commodity_id, reported_date, 
                 origin_modal_price, terminal_modal_price, price_spread, spread_pct, 
                 origin_arrival_shock_z, stress_level)
                VALUES (:corridor_id, :origin_mandi_id, :terminal_mandi_id, :commodity_id, :reported_date,
                        :origin_modal_price, :terminal_modal_price, :price_spread, :spread_pct,
                        :origin_arrival_shock_z, :stress_level)
                ON CONFLICT(corridor_id, commodity_id, reported_date) DO UPDATE SET
                    origin_modal_price=excluded.origin_modal_price,
                    terminal_modal_price=excluded.terminal_modal_price,
                    price_spread=excluded.price_spread,
                    spread_pct=excluded.spread_pct,
                    origin_arrival_shock_z=excluded.origin_arrival_shock_z,
                    stress_level=excluded.stress_level;
            """, payload)

    def get_corridor_timeseries(
        self, commodity_id: str, origin_mandi_id: str, terminal_mandi_id: str
    ) -> pl.DataFrame:
        """Fetch joined daily timeseries for an origin-terminal corridor."""
        query = """
            SELECT 
                f_orig.reported_date,
                f_orig.commodity_id,
                f_orig.modal_price AS origin_price,
                f_orig.arrival_tonnes AS origin_arrival,
                f_term.modal_price AS terminal_price,
                f_term.arrival_tonnes AS terminal_arrival,
                (f_term.modal_price - f_orig.modal_price) AS price_spread,
                ROUND(((f_term.modal_price - f_orig.modal_price) / f_orig.modal_price) * 100, 1) AS spread_pct
            FROM daily_mandi_facts f_orig
            JOIN daily_mandi_facts f_term 
                ON f_orig.reported_date = f_term.reported_date 
                AND f_orig.commodity_id = f_term.commodity_id
            WHERE f_orig.commodity_id = ?
              AND f_orig.mandi_id = ?
              AND f_term.mandi_id = ?
            ORDER BY f_orig.reported_date ASC;
        """
        with self._get_connection() as conn:
            df = pl.read_database(query, conn, execute_options={"parameters": [commodity_id, origin_mandi_id, terminal_mandi_id]})
            return df

    def get_spatial_dispersion_timeseries(self, commodity_id: str) -> pl.DataFrame:
        """Calculate daily spatial price dispersion across all reporting mandis."""
        query = """
            SELECT 
                reported_date,
                COUNT(mandi_id) as mandis_count,
                AVG(modal_price) as mean_price,
                SUM(arrival_tonnes) as total_arrivals
            FROM daily_mandi_facts
            WHERE commodity_id = ?
            GROUP BY reported_date
            ORDER BY reported_date ASC;
        """
        with self._get_connection() as conn:
            summary_df = pl.read_database(query, conn, execute_options={"parameters": [commodity_id]})

            # Also fetch all prices per day to compute exact CV
            all_prices_query = """
                SELECT reported_date, modal_price
                FROM daily_mandi_facts
                WHERE commodity_id = ?
                ORDER BY reported_date ASC;
            """
            prices_df = pl.read_database(all_prices_query, conn, execute_options={"parameters": [commodity_id]})

        if prices_df.is_empty():
            return pl.DataFrame()

        # Compute daily CV
        daily_cvs = (
            prices_df.group_by("reported_date")
            .agg([
                pl.col("modal_price").mean().alias("mean_p"),
                pl.col("modal_price").std().alias("std_p"),
            ])
            .with_columns(
                (pl.col("std_p") / pl.col("mean_p")).round(4).alias("spatial_dispersion_cv")
            )
            .sort("reported_date")
        )

        return daily_cvs

    def get_all_mandis(self) -> pl.DataFrame:
        """Return all registered mandis."""
        with self._get_connection() as conn:
            return pl.read_database("SELECT * FROM mandi_registry ORDER BY canonical_name ASC;", conn)

    def get_latest_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the latest corridor stress alerts."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM v_active_corridor_stress
                WHERE stress_level IN ('HIGH', 'SEVERE')
                LIMIT ?;
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_available_states(self) -> List[str]:
        """Return unique states that have reporting mandis in the database."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT state FROM mandi_registry 
                WHERE state NOT IN ('General', 'Unknown')
                ORDER BY state ASC;
            """)
            return [row[0] for row in cursor.fetchall()]

    def get_live_mandi_prices(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 200,
    ) -> pl.DataFrame:
        """Query human-readable live mandi prices with optional filtering."""
        clauses = ["1=1"]
        params = []
        if commodity and commodity.lower() != "all":
            clauses.append("LOWER(commodity) = LOWER(?)")
            params.append(commodity)
        if state and state.lower() != "all india":
            clauses.append("state = ?")
            params.append(state)
        if date:
            clauses.append("reported_date = ?")
            params.append(date)

        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT * FROM v_live_mandi_prices
            WHERE {where_sql}
            LIMIT ?;
        """
        params.append(limit)

        with self._get_connection() as conn:
            return pl.read_database(query, conn, execute_options={"parameters": params})

    def get_live_price_deltas(
        self,
        commodity_id: Optional[str] = None,
        mandi_id: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> pl.DataFrame:
        """Query windowed price movements and trend signals from v_live_price_deltas."""
        clauses = ["1=1"]
        params = []
        if commodity_id and commodity_id.lower() != "all":
            clauses.append("LOWER(commodity_id) = LOWER(?)")
            params.append(commodity_id)
        if mandi_id:
            clauses.append("mandi_id = ?")
            params.append(mandi_id)
        if date:
            clauses.append("reported_date = ?")
            params.append(date)

        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT * FROM v_live_price_deltas
            WHERE {where_sql}
            ORDER BY reported_date DESC, ABS(day_change_rs_kg) DESC
            LIMIT ?;
        """
        params.append(limit)

        with self._get_connection() as conn:
            return pl.read_database(query, conn, execute_options={"parameters": params})

    def get_dca_retail_benchmarks(
        self,
        commodity: Optional[str] = None,
        center: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100,
    ) -> pl.DataFrame:
        """Query retail benchmarks with wholesale spread from v_dca_retail_benchmarks."""
        clauses = ["1=1"]
        params = []
        if commodity and commodity.lower() != "all":
            clauses.append("LOWER(commodity) = LOWER(?)")
            params.append(commodity)
        if center and center.lower() != "all":
            clauses.append("LOWER(consumption_center) = LOWER(?)")
            params.append(center)
        if date:
            clauses.append("reported_date = ?")
            params.append(date)

        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT * FROM v_dca_retail_benchmarks
            WHERE {where_sql}
            LIMIT ?;
        """
        params.append(limit)

        with self._get_connection() as conn:
            return pl.read_database(query, conn, execute_options={"parameters": params})


    def materialize_attributions(self, target_date: Optional[str] = None) -> int:
        """
        Evaluate and persist price attribution reports for reporting mandis.
        Compares each mandi's modal price against its previous price record,
        evaluates cultural and seasonal calendars and weather flags,
        and saves into attribution_reports.
        """
        from datetime import datetime, date
        from src.attribution import explain_price_movement

        with self._get_connection() as conn:
            # Find target date if not provided
            if not target_date:
                cur = conn.execute("SELECT MAX(reported_date) FROM daily_mandi_facts;")
                row = cur.fetchone()
                if not row or not row[0]:
                    return 0
                target_date = row[0]

            # Query facts for target date joined with previous observations
            query = """
                WITH ranked_facts AS (
                    SELECT 
                        f.mandi_id,
                        f.commodity_id,
                        f.reported_date,
                        f.modal_price,
                        f.min_price,
                        f.max_price,
                        m.canonical_name AS mandi_name,
                        LAG(f.modal_price, 1) OVER (
                            PARTITION BY f.mandi_id, f.commodity_id 
                            ORDER BY f.reported_date ASC
                        ) AS prev_modal_price
                    FROM daily_mandi_facts f
                    JOIN mandi_registry m ON f.mandi_id = m.mandi_id
                    WHERE f.modal_price >= 100.0
                )
                SELECT * FROM ranked_facts
                WHERE reported_date = ?;
            """
            rows = conn.execute(query, (target_date,)).fetchall()
            
            # Also check if weather facts exist
            has_weather = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='mandi_weather_facts';
            """).fetchone()

            weather_map = {}
            if has_weather:
                w_rows = conn.execute("""
                    SELECT mandi_id, precipitation_mm, max_temp_c 
                    FROM mandi_weather_facts 
                    WHERE observation_date = ?;
                """, (target_date,)).fetchall()
                
                # If no weather records yet for target_date, pull from Open-Meteo
                if not w_rows:
                    self.sync_live_weather(target_date)
                    w_rows = conn.execute("""
                        SELECT mandi_id, precipitation_mm, max_temp_c 
                        FROM mandi_weather_facts 
                        WHERE observation_date = ?;
                    """, (target_date,)).fetchall()

                for wr in w_rows:
                    weather_map[wr[0]] = (wr[1] or 0.0, wr[2] or 0.0)

            attributions = []
            try:
                t_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                t_date = date.today()

            for r in rows:
                mandi_id = r["mandi_id"]
                comm_id = r["commodity_id"]
                curr_price = float(r["modal_price"])
                prev_price = float(r["prev_modal_price"]) if r["prev_modal_price"] else curr_price
                min_p = float(r["min_price"]) if r["min_price"] else curr_price
                max_p = float(r["max_price"]) if r["max_price"] else curr_price
                
                rain, temp = weather_map.get(mandi_id, (0.0, 0.0))
                
                attr = explain_price_movement(
                    commodity=comm_id,
                    mandi_name=r["mandi_name"],
                    trade_date=t_date,
                    price_today=curr_price,
                    price_prior=prev_price,
                    min_price=min_p,
                    max_price=max_p,
                    rainfall_mm=rain,
                    max_temp_c=temp
                )
                attributions.append({
                    "mandi_id": mandi_id,
                    "commodity_id": comm_id,
                    "reported_date": target_date,
                    "modal_price": curr_price,
                    "price_change_pct": attr.price_change_pct,
                    "primary_driver": attr.primary_driver,
                    "severity": attr.severity,
                    "headline": attr.headline,
                    "explanation": attr.explanation,
                    "crop_season": attr.crop_season,
                    "cultural_context": attr.cultural_context,
                    "weather_flag": attr.weather_flag
                })

            if attributions:
                conn.executemany("""
                    INSERT INTO attribution_reports 
                    (mandi_id, commodity_id, reported_date, modal_price, price_change_pct,
                     primary_driver, severity, headline, explanation, crop_season, cultural_context, weather_flag)
                    VALUES (:mandi_id, :commodity_id, :reported_date, :modal_price, :price_change_pct,
                            :primary_driver, :severity, :headline, :explanation, :crop_season, :cultural_context, :weather_flag)
                    ON CONFLICT(mandi_id, commodity_id, reported_date) DO UPDATE SET
                        modal_price=excluded.modal_price,
                        price_change_pct=excluded.price_change_pct,
                        primary_driver=excluded.primary_driver,
                        severity=excluded.severity,
                        headline=excluded.headline,
                        explanation=excluded.explanation,
                        crop_season=excluded.crop_season,
                        cultural_context=excluded.cultural_context,
                        weather_flag=excluded.weather_flag;
                """, attributions)

            return len(attributions)

    def get_attribution_reports(
        self,
        commodity: Optional[str] = None,
        limit: int = 50
    ) -> pl.DataFrame:
        """Fetch human-readable price movement attribution records."""
        clauses = ["1=1"]
        params = []
        if commodity and commodity.lower() != "all":
            clauses.append("LOWER(commodity) = LOWER(?)")
            params.append(commodity)

        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT * FROM v_price_movement_attribution
            WHERE {where_sql}
            LIMIT ?;
        """
        params.append(limit)

        with self._get_connection() as conn:
            return pl.read_database(query, conn, execute_options={"parameters": params})

    def sync_live_weather(self, target_date: Optional[str] = None) -> int:
        """
        Query Open-Meteo live weather observations across all 25 canonical Mandis
        and persist them into mandi_weather_facts table.
        """
        from datetime import datetime, date
        from src.attribution import fetch_all_mandis_weather_alerts

        if not target_date:
            with self._get_connection() as conn:
                cur = conn.execute("SELECT MAX(reported_date) FROM daily_mandi_facts;")
                row = cur.fetchone()
                target_date = row[0] if row and row[0] else date.today().isoformat()

        try:
            t_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            t_date = date.today()

        alerts = fetch_all_mandis_weather_alerts(obs_date=t_date)
        if not alerts:
            return 0

        with self._get_connection() as conn:
            # Enforce foreign key safety: only insert for mandis registered in this warehouse
            cur = conn.execute("SELECT mandi_id FROM mandi_registry;")
            registered_ids = {row[0] for row in cur.fetchall()}

            filtered_alerts = [a for a in alerts if a["mandi_id"] in registered_ids]
            if not filtered_alerts:
                return 0

            conn.executemany("""
                INSERT INTO mandi_weather_facts 
                (mandi_id, observation_date, precipitation_mm, max_temp_c, weather_flag)
                VALUES (:mandi_id, :observation_date, :precipitation_mm, :max_temp_c, :weather_flag)
                ON CONFLICT(mandi_id, observation_date) DO UPDATE SET
                    precipitation_mm=excluded.precipitation_mm,
                    max_temp_c=excluded.max_temp_c,
                    weather_flag=excluded.weather_flag;
            """, filtered_alerts)

        return len(filtered_alerts)


