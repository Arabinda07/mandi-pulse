"""
Automated Daily Ingestion and Attribution Job.

Executed by GitHub Actions cron or local scheduler:
1. Validates API credentials.
2. Ingests fresh APMC Mandi wholesale prices.
3. Fetches district weather observations (precipitation, temperature).
4. Evaluates corridor volatility and supply-chain stress.
5. Computes and materializes plain-English price movement attributions.
"""

from __future__ import annotations
import os
import sys
import logging
from datetime import date
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("daily_job")


def run_daily_job() -> None:
    logger.info("================ STARTING DAILY INGESTION JOB ================")
    
    # 1. Verify credentials
    api_key = os.getenv("DATA_GOV_IN_API_KEY")
    if not api_key:
        env_file = ROOT_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("DATA_GOV_IN_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    os.environ["DATA_GOV_IN_API_KEY"] = api_key

    if not api_key:
        logger.error("DATA_GOV_IN_API_KEY environment variable is not set!")
        sys.exit(1)

    from src.warehouse import Warehouse
    from src.registry import MandiRegistry
    from src.ingest import IngestionEngine
    from src.sources.datagov import DataGovInAdapter
    from src.sources.weather import MandiWeatherAdapter
    from src.volatility import VolatilityEngine

    db_path = ROOT_DIR / "data" / "agri_engine.db"
    wh = Warehouse(db_path)
    wh.initialize()
    reg = MandiRegistry()
    vol = VolatilityEngine()

    # 2. Ingest Mandi Wholesale Prices
    logger.info("Fetching live APMC Mandi prices from data.gov.in...")
    gov_source = DataGovInAdapter(api_key=api_key)
    engine = IngestionEngine(wh, reg, source=gov_source)

    target_commodities = ["onion", "tomato", "potato", "garlic", "ginger"]
    total_facts = 0
    for comm in target_commodities:
        try:
            count = engine.ingest_commodity(comm)
            logger.info(f"  Processed {count} facts for {comm}.")
            total_facts += count
        except Exception as e:
            logger.warning(f"  Live ingestion note for {comm}: {e}")

    logger.info(f"Total live mandi facts processed: {total_facts}")

    # 3. Fetch Weather Shocks for Active Production Districts
    logger.info("Fetching district meteorological records from Open-Meteo...")
    weather_adapter = MandiWeatherAdapter()
    today_str = date.today().isoformat()
    
    # Sample top production hubs
    key_hubs = [
        reg.resolve("Lasalgaon"),
        reg.resolve("Kolar"),
        reg.resolve("Agra"),
        reg.resolve("Azadpur"),
        reg.resolve("Vashi"),
        reg.resolve("Madanapalle"),
    ]

    for hub in key_hubs:
        if hub and hub.latitude and hub.longitude:
            try:
                w_data = weather_adapter.get_mandi_rainfall(
                    hub.latitude, hub.longitude, today_str, today_str
                )
                if w_data and w_data.get("precipitation_mm"):
                    rain = w_data["precipitation_mm"][0] if w_data["precipitation_mm"] else 0.0
                    temp = w_data["temperature_max_c"][0] if w_data["temperature_max_c"] else 0.0
                    logger.info(f"  Weather for {hub.canonical_name}: Rain {rain}mm, Max Temp {temp}°C")
            except Exception as e:
                logger.warning(f"Could not fetch weather for {hub.canonical_name}: {e}")

    # 4. Materialize Strategic Corridor Stress Metrics
    logger.info("Evaluating strategic inter-mandi corridor volatility...")
    try:
        corridor_count = engine.refresh_corridor_stress_metrics()
        logger.info(f"Corridor volatility metrics refreshed: {corridor_count} records.")
    except Exception as e:
        logger.warning(f"Corridor volatility calculation note: {e}")

    # 5. Compute & Persist Price Movement Attributions
    logger.info("Computing automated price attributions (Cultural Festivals + Weather + Harvest Cycles)...")
    attr_count = wh.materialize_attributions()
    logger.info(f"Materialized {attr_count} price attribution reports.")

    logger.info("================ DAILY INGESTION JOB COMPLETED SUCCESSFULLY ================")


if __name__ == "__main__":
    run_daily_job()
