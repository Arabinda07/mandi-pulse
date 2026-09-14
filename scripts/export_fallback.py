"""
Export latest SQLite warehouse market snapshot into frontend/src/api/fallbackData.js.
Ensures static frontend deployments (Vercel, Netlify, GitHub Pages) and offline modes
remain perfectly synchronized with the latest daily data ingestion.
"""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "agri_engine.db"
TARGET_FILE = ROOT_DIR / "frontend" / "src" / "api" / "fallbackData.js"

METRO_HUBS = [
    {"id": "delhi", "name": "Delhi NCR", "terminal_mandi": "Azadpur APMC", "district": "North Delhi", "lgd_code": 93, "mandi_id": "mandi_azadpur"},
    {"id": "mumbai", "name": "Mumbai MMR", "terminal_mandi": "Vashi (Navi Mumbai)", "district": "Thane", "lgd_code": 499, "mandi_id": "mandi_vashi"},
    {"id": "bengaluru", "name": "Bengaluru", "terminal_mandi": "Yeshwanthpur APMC", "district": "Bengaluru Urban", "lgd_code": 529, "mandi_id": "mandi_bangalore"},
    {"id": "kolkata", "name": "Kolkata", "terminal_mandi": "Mechua Fruit & Veg Market", "district": "Kolkata", "lgd_code": 318, "mandi_id": "mandi_kolkata"},
    {"id": "pune", "name": "Pune", "terminal_mandi": "Gultekdi Market Yard", "district": "Pune", "lgd_code": 490, "mandi_id": "mandi_pune"},
]

COMMODITY_METAS = {
    "tomato": {
        "id": "tomato",
        "name": "Tomato",
        "variety_default": "Hybrid Red",
        "icon": "🍅",
        "packaging_type": "20 kg Crate",
        "package_size_kg": 20,
        "basket_weight_kg": 1.0,
        "default_distance_km": 400,
        "default_crop_season": "Kharif Mid-Harvest",
    },
    "onion": {
        "id": "onion",
        "name": "Onion",
        "variety_default": "Nashik Red",
        "icon": "🧅",
        "packaging_type": "50 kg Sack",
        "package_size_kg": 50,
        "basket_weight_kg": 2.0,
        "default_distance_km": 600,
        "default_crop_season": "Late Kharif Transition",
    },
    "potato": {
        "id": "potato",
        "name": "Potato",
        "variety_default": "Pukhraj / Jyoti",
        "icon": "🥔",
        "packaging_type": "50 kg Sack",
        "package_size_kg": 50,
        "basket_weight_kg": 2.0,
        "default_distance_km": 300,
        "default_crop_season": "Rabi Cold Storage Dispatches",
    },
}

def format_date_str(iso_date: str) -> str:
    """Format YYYY-MM-DD into '13 Sep 2026'."""
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        return dt.strftime("%d %b %Y").lstrip("0")
    except Exception:
        return iso_date

def sync_fallback_data() -> None:
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    market_data = {}

    for metro in METRO_HUBS:
        m_id = metro["id"]
        mandi_id = metro["mandi_id"]

        # Fetch latest reported rows for tomato, onion, potato in this terminal mandi
        rows = cursor.execute("""
            SELECT * FROM v_live_mandi_prices
            WHERE mandi_id = ?
              AND commodity_id IN ('tomato', 'onion', 'potato')
            ORDER BY reported_date DESC, wholesale_price_rs_qtl DESC
        """, (mandi_id,)).fetchall()

        # Group by commodity_id, keeping freshest observation
        latest_comm_rows = {}
        for r in rows:
            cid = r["commodity_id"]
            if cid not in latest_comm_rows:
                latest_comm_rows[cid] = dict(r)

        # Fallback to nearest regional mandi if a terminal mandi is missing data
        if len(latest_comm_rows) < 3:
            regional_rows = cursor.execute("""
                SELECT * FROM v_live_mandi_prices
                WHERE state = (SELECT state FROM mandi_registry WHERE mandi_id = ?)
                  AND commodity_id IN ('tomato', 'onion', 'potato')
                ORDER BY reported_date DESC, wholesale_price_rs_qtl DESC
            """, (mandi_id,)).fetchall()
            for r in regional_rows:
                cid = r["commodity_id"]
                if cid not in latest_comm_rows:
                    latest_comm_rows[cid] = dict(r)

        # Determine reporting date
        dates = [r["reported_date"] for r in latest_comm_rows.values() if r.get("reported_date")]
        max_date = max(dates) if dates else "2026-09-13"
        display_date = format_date_str(max_date)

        commodities_list = []
        weekly_basket_total = 0.0
        weighted_wow_sum = 0.0
        total_basket_weight = 5.0 # 1kg tomato + 2kg onion + 2kg potato

        for cid in ["tomato", "onion", "potato"]:
            meta = COMMODITY_METAS[cid]
            row = latest_comm_rows.get(cid, {})

            wholesale_qtl = float(row.get("wholesale_price_rs_qtl") or 2500.0)
            retail_kg = float(row.get("retail_equivalent_rs_kg") or round((wholesale_qtl / 100.0) * 1.35, 1))
            retail_provenance = row.get("retail_provenance") or "synthetic_proxy"

            day_change = float(row.get("day_change_rs") or 0.0)
            week_pct = float(row.get("week_change_pct") or 0.0)

            pkg_size = meta["package_size_kg"]
            crate_rate = int(round((wholesale_qtl / 100.0) * pkg_size))
            retail_box = int(round(retail_kg * pkg_size))
            bulk_savings = max(0, retail_box - crate_rate)
            bulk_savings_pct = round((bulk_savings / retail_box) * 100, 1) if retail_box > 0 else 25.0

            # Determine status & trend
            if week_pct > 15.0:
                status = "shock"
                status_label = "Severe Spike"
                trend_signal = "🔴 Spike in ~10d"
                trend_status = "spike"
            elif week_pct < -5.0:
                status = "fair"
                status_label = "Fair Price"
                trend_signal = "🟢 Cooling Down in ~7d"
                trend_status = "cooling"
            else:
                status = "fair"
                status_label = "Fair Price"
                trend_signal = "⚪ Stable Corridor"
                trend_status = "stable"

            # Rupee journey breakdown
            cess_rs_kg = float(row.get("statutory_cess_rs_kg") or round((wholesale_qtl / 100.0) * 0.02, 2))
            origin_name = row.get("origin_mandi_name") or "Regional Producer Hub"
            origin_modal_rs_kg = float(row.get("origin_modal_price_rs_kg") or round(wholesale_qtl / 100.0, 1))
            origin_shock_z = float(row.get("origin_arrival_shock_z") or 0.0)

            farmgate_est = round(origin_modal_rs_kg * 0.85, 2)
            transit_fee_est = round(origin_modal_rs_kg * 0.15, 2)
            retail_margin_est = round(max(1.0, retail_kg - origin_modal_rs_kg - cess_rs_kg), 2)

            # Accumulate basket metrics
            weekly_basket_total += retail_kg * meta["basket_weight_kg"]
            weighted_wow_sum += week_pct * (meta["basket_weight_kg"] / total_basket_weight)

            # Generate concise advice
            if status == "shock":
                advice = f"{origin_name} arrivals slumped {abs(origin_shock_z):.1f}σ against seasonal averages. Procure buffer before weekend."
            elif status_label == "Fair Price" and week_pct < -5.0:
                advice = f"Bumper inflows from {origin_name} stabilizing corridor supply. Favorable pricing for volume buying."
            else:
                advice = f"Supply from {origin_name} steady along the transit corridor. Stable wholesale arrivals expected."

            comm_obj = {
                "id": cid,
                "name": meta["name"],
                "variety": f"{meta['variety_default']} ({origin_name})",
                "icon": meta["icon"],
                "wholesale_price_rs_qtl": round(wholesale_qtl, 1),
                "retail_provenance": retail_provenance,
                "retail_equivalent_rs_kg": round(retail_kg, 1),
                "day_change_rs": round(day_change, 2),
                "week_change_pct": round(week_pct, 1),
                "status": status,
                "status_label": status_label,
                "trend_signal": trend_signal,
                "trend_status": trend_status,
                "advice": advice,
                "packaging_type": meta["packaging_type"],
                "package_size_kg": pkg_size,
                "crate_rate_rs": crate_rate,
                "retail_box_equivalent_rs": retail_box,
                "bulk_savings_rs": bulk_savings,
                "bulk_savings_pct": bulk_savings_pct,
                "rupee_journey": {
                    "farmgate_rs_kg": farmgate_est,
                    "transit_fee_rs_kg": transit_fee_est,
                    "retail_margin_rs_kg": retail_margin_est,
                    "statutory_cess_pct": 2.0,
                    "statutory_cess_rs_kg": cess_rs_kg,
                    "statutory_cess_label": f"{metro['name']} APMC Cess & Market Fees",
                    "origin_mandi": origin_name,
                    "distance_km": meta["default_distance_km"],
                    "arrival_z_score": origin_shock_z,
                    "weather_context": f"Monsoon transitions across {origin_name} agricultural basin.",
                    "crop_season": meta["default_crop_season"]
                }
            }
            commodities_list.append(comm_obj)

        weekly_basket_total = round(weekly_basket_total, 2)
        weighted_wow_pct = round(weighted_wow_sum, 1)

        if weighted_wow_pct > 8.0:
            verdict = "The basket is up this week due to corridor arrival bottlenecks in primary production basins."
            verdict_status = "warning"
        elif weighted_wow_pct > 15.0:
            verdict = "Severe supply-chain shock across the vegetable corridor. Expect elevated retail spreads."
            verdict_status = "shock"
        else:
            verdict = f"Stable arrivals across primary Mandis keep the {metro['name']} kitchen basket balanced."
            verdict_status = "fair"

        market_data[m_id] = {
            "metro_name": metro["name"],
            "reporting_date": display_date,
            "terminal_mandi": metro["terminal_mandi"],
            "basket_hero": {
                "weekly_total_rs": weekly_basket_total,
                "week_change_pct": weighted_wow_pct,
                "verdict": verdict,
                "verdict_status": verdict_status,
                "composition": "Based on weekly staple needs: 1 kg Tomato, 2 kg Onion, 2 kg Potato"
            },
            "commodities": commodities_list
        }

    # Generate JavaScript file content
    hubs_json = json.dumps([
        {"id": m["id"], "name": m["name"], "terminal_mandi": m["terminal_mandi"], "district": m["district"], "lgd_code": m["lgd_code"]}
        for m in METRO_HUBS
    ], indent=2)

    market_json = json.dumps(market_data, indent=2)

    js_content = f"""/**
 * Mandi Pulse - Reference Market Snapshot & Fallback Provider
 * Synchronized automatically from SQLite Warehouse (v_live_mandi_prices).
 * Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
 */

export const METRO_HUBS = {hubs_json};

export const REFERENCE_MARKET_DATA = {market_json};
"""

    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_FILE.write_text(js_content, encoding="utf-8")
    print(f"Successfully synchronized fallback data to {TARGET_FILE}")
    print(f"Reporting dates across metros: {[m['reporting_date'] for m in market_data.values()]}")

if __name__ == "__main__":
    sync_fallback_data()
