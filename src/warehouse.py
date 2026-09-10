"""Shared SQLite Warehouse with WAL mode, indexing, views, and Polars integrations."""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import polars as pl

from src.models import MandiRecord, CommodityRecord, DailyFactRecord, CorridorStress
from src.volatility import VolatilityEngine


class Warehouse:
    """Deep module for persistent storage, WAL concurrency, and analytical query execution."""

    DEFAULT_DB_PATH = Path("data/agri_engine.db")

    # Core Tier 1 Commodity catalog
    TIER_1_COMMODITIES: List[CommodityRecord] = [
        CommodityRecord("tomato", "Tomato", "vegetable", 1, "quintal", 0.57),
        CommodityRecord("onion", "Onion", "vegetable", 1, "quintal", 0.64),
        CommodityRecord("potato", "Potato", "vegetable", 1, "quintal", 1.00),
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
                    hub_type TEXT NOT NULL DEFAULT 'production'
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

                -- High-readability primary market price explorer view
                CREATE VIEW IF NOT EXISTS v_live_mandi_prices AS
                SELECT 
                    f.reported_date AS reported_date,
                    c.name AS commodity,
                    m.state AS state,
                    m.district AS district,
                    m.canonical_name AS mandi_name,
                    ROUND(f.modal_price, 2) AS wholesale_price_rs_qtl,
                    ROUND(f.modal_price / 100.0, 2) AS retail_equivalent_rs_kg,
                    ROUND(f.min_price, 2) AS min_price_rs_qtl,
                    ROUND(f.max_price, 2) AS max_price_rs_qtl,
                    ROUND(f.max_price - f.min_price, 2) AS intraday_spread_rs_qtl,
                    ROUND(f.arrival_tonnes, 1) AS arrival_tonnes,
                    m.hub_type AS market_type,
                    m.latitude AS latitude,
                    m.longitude AS longitude
                FROM daily_mandi_facts f
                JOIN mandi_registry m ON f.mandi_id = m.mandi_id
                JOIN commodity_registry c ON f.commodity_id = c.commodity_id
                WHERE f.modal_price >= 100.0
                ORDER BY f.reported_date DESC, f.modal_price DESC;

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

    def record_mandis(self, mandis: List[MandiRecord]) -> None:
        """Upsert canonical Mandi records."""
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT INTO mandi_registry 
                (mandi_id, canonical_name, state, district, state_lgd_code, district_lgd_code, latitude, longitude, is_consumption_hub, hub_type)
                VALUES (:mandi_id, :canonical_name, :state, :district, :state_lgd_code, :district_lgd_code, :latitude, :longitude, :is_consumption_hub, :hub_type)
                ON CONFLICT(mandi_id) DO UPDATE SET
                    canonical_name=excluded.canonical_name,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    is_consumption_hub=excluded.is_consumption_hub,
                    hub_type=excluded.hub_type;
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

