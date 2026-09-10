"""
Indian Cultural Festivals and Agricultural Seasonality Engine.

Tracks:
1. Major demand festivals (Navratri, Diwali, Eid, Pongal, Makar Sankranti, Wedding/Lagan seasons).
2. The 3 primary Indian agricultural seasons (Kharif, Late Kharif, Rabi, Zaid).
3. Commodity-specific demand and supply phase impacts.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum


class DemandImpact(str, Enum):
    SHARP_SURGE = "SHARP_SURGE"       # e.g. Diwali feast vegetables
    MODERATE_SURGE = "MODERATE_SURGE" # e.g. Eid onion/tomato base
    SLUMP = "SLUMP"                   # e.g. Navratri onion/garlic fasting
    FASTING_SWAP = "FASTING_SWAP"     # e.g. potato/fruit surge during fasting
    NEUTRAL = "NEUTRAL"


class CropPhase(str, Enum):
    HARVEST_GLUT = "HARVEST_GLUT"           # New crop flooding mandis (lowest prices)
    PEAK_ARRIVAL = "PEAK_ARRIVAL"           # Active harvest season (stable, fair prices)
    LEAN_STORAGE = "LEAN_STORAGE"           # Consuming cold-storage stocks (gradual price climb)
    PRE_HARVEST_SCARCITY = "PRE_HARVEST"    # Old stocks depleted before new harvest (yearly price peaks)


@dataclass(frozen=True)
class Festival:
    name: str
    start_date: date
    end_date: date
    category: str
    impacts: Dict[str, DemandImpact]
    description: str


# Pre-computed multi-year festival dates (2024–2027)
FESTIVALS_DB: List[Festival] = [
    # 2024
    Festival("Makar Sankranti / Pongal", date(2024, 1, 14), date(2024, 1, 16), "Harvest",
             {"Potato": DemandImpact.MODERATE_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Winter harvest festival."),
    Festival("Winter Wedding Season", date(2024, 1, 18), date(2024, 3, 5), "Wedding",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Peak North Indian lagan catering demand."),
    Festival("Holi", date(2024, 3, 24), date(2024, 3, 26), "Cultural",
             {"Potato": DemandImpact.MODERATE_SURGE}, "Spring festival of colors."),
    Festival("Eid-ul-Fitr", date(2024, 4, 10), date(2024, 4, 12), "Religious",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Feast celebrations following Ramadan."),
    Festival("Chaitra Navratri", date(2024, 4, 9), date(2024, 4, 17), "Fasting",
             {"Onion": DemandImpact.SLUMP, "Potato": DemandImpact.FASTING_SWAP}, "Spring fasting period (low onion consumption, high potato demand)."),
    Festival("Eid-ul-Adha (Bakrid)", date(2024, 6, 16), date(2024, 6, 18), "Religious",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Feast cooking demand across meat and gravy staples."),
    Festival("Ganesh Chaturthi", date(2024, 9, 7), date(2024, 9, 17), "Cultural",
             {"Potato": DemandImpact.MODERATE_SURGE}, "10-day community feast celebrations."),
    Festival("Pitru Paksha", date(2024, 9, 18), date(2024, 10, 2), "Fasting",
             {"Onion": DemandImpact.SLUMP}, "Fortnight of remembrance; reduced allium consumption."),
    Festival("Sharad Navratri", date(2024, 10, 3), date(2024, 10, 12), "Fasting",
             {"Onion": DemandImpact.SLUMP, "Potato": DemandImpact.FASTING_SWAP}, "Major autumn fasting; severe drop in onion demand, high potato consumption."),
    Festival("Diwali / Dhanteras", date(2024, 10, 29), date(2024, 11, 3), "Feasting",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Peak annual consumer sweets and feasting demand."),
    Festival("Post-Diwali Wedding Season", date(2024, 11, 12), date(2024, 12, 16), "Wedding",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Heavy mass-scale banquet catering."),

    # 2025
    Festival("Makar Sankranti / Pongal", date(2025, 1, 14), date(2025, 1, 16), "Harvest",
             {"Potato": DemandImpact.MODERATE_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Winter harvest festival."),
    Festival("Winter Wedding Season", date(2025, 1, 16), date(2025, 3, 2), "Wedding",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Peak North Indian lagan catering demand."),
    Festival("Holi", date(2025, 3, 13), date(2025, 3, 15), "Cultural",
             {"Potato": DemandImpact.MODERATE_SURGE}, "Spring festival of colors."),
    Festival("Eid-ul-Fitr", date(2025, 3, 30), date(2025, 4, 1), "Religious",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Post-Ramadan feasting."),
    Festival("Chaitra Navratri", date(2025, 3, 30), date(2025, 4, 7), "Fasting",
             {"Onion": DemandImpact.SLUMP, "Potato": DemandImpact.FASTING_SWAP}, "Spring fasting (low onion, high potato)."),
    Festival("Eid-ul-Adha (Bakrid)", date(2025, 6, 6), date(2025, 6, 8), "Religious",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "High feast demand."),
    Festival("Ganesh Chaturthi", date(2025, 8, 27), date(2025, 9, 6), "Cultural",
             {"Potato": DemandImpact.MODERATE_SURGE}, "10-day community feast celebrations."),
    Festival("Pitru Paksha", date(2025, 9, 8), date(2025, 9, 21), "Fasting",
             {"Onion": DemandImpact.SLUMP}, "Fortnight of remembrance; reduced allium consumption."),
    Festival("Sharad Navratri", date(2025, 9, 22), date(2025, 10, 1), "Fasting",
             {"Onion": DemandImpact.SLUMP, "Potato": DemandImpact.FASTING_SWAP}, "Autumn fasting window."),
    Festival("Diwali / Dhanteras", date(2025, 10, 19), date(2025, 10, 24), "Feasting",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Annual peak feast season."),
    Festival("Post-Diwali Wedding Season", date(2025, 11, 2), date(2025, 12, 15), "Wedding",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Heavy banquet catering."),

    # 2026
    Festival("Makar Sankranti / Pongal", date(2026, 1, 14), date(2026, 1, 16), "Harvest",
             {"Potato": DemandImpact.MODERATE_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Winter harvest festival."),
    Festival("Winter Wedding Season", date(2026, 1, 15), date(2026, 3, 5), "Wedding",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Peak North Indian lagan catering demand."),
    Festival("Holi", date(2026, 3, 3), date(2026, 3, 5), "Cultural",
             {"Potato": DemandImpact.MODERATE_SURGE}, "Spring festival of colors."),
    Festival("Eid-ul-Fitr", date(2026, 3, 20), date(2026, 3, 22), "Religious",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "Post-Ramadan feasting."),
    Festival("Chaitra Navratri", date(2026, 3, 19), date(2026, 3, 27), "Fasting",
             {"Onion": DemandImpact.SLUMP, "Potato": DemandImpact.FASTING_SWAP}, "Spring fasting."),
    Festival("Eid-ul-Adha (Bakrid)", date(2026, 5, 27), date(2026, 5, 29), "Religious",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.MODERATE_SURGE}, "High feast demand."),
    Festival("Ganesh Chaturthi", date(2026, 9, 14), date(2026, 9, 24), "Cultural",
             {"Potato": DemandImpact.MODERATE_SURGE}, "Community feast celebrations."),
    Festival("Pitru Paksha", date(2026, 9, 26), date(2026, 10, 10), "Fasting",
             {"Onion": DemandImpact.SLUMP}, "Fortnight of remembrance; reduced onion consumption."),
    Festival("Sharad Navratri", date(2026, 10, 11), date(2026, 10, 20), "Fasting",
             {"Onion": DemandImpact.SLUMP, "Potato": DemandImpact.FASTING_SWAP}, "Autumn fasting window."),
    Festival("Diwali / Dhanteras", date(2026, 11, 8), date(2026, 11, 13), "Feasting",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Peak annual consumer demand."),
    Festival("Post-Diwali Wedding Season", date(2026, 11, 20), date(2026, 12, 16), "Wedding",
             {"Onion": DemandImpact.SHARP_SURGE, "Tomato": DemandImpact.SHARP_SURGE, "Potato": DemandImpact.SHARP_SURGE}, "Peak banquet catering.")
]


def get_active_festivals(dt: date, lookaround_days: int = 7) -> List[Dict[str, Any]]:
    """
    Return all festivals active on this date or occurring within lookaround_days.
    Includes status: 'ACTIVE', 'UPCOMING', or 'RECENT'.
    """
    results = []
    for fest in FESTIVALS_DB:
        # Currently active
        if fest.start_date <= dt <= fest.end_date:
            results.append({
                "name": fest.name,
                "status": "ACTIVE",
                "category": fest.category,
                "description": fest.description,
                "impacts": {k: v.value for k, v in fest.impacts.items()},
                "days_offset": 0
            })
        # Upcoming within window
        elif dt < fest.start_date <= dt + timedelta(days=lookaround_days):
            days_until = (fest.start_date - dt).days
            results.append({
                "name": fest.name,
                "status": "UPCOMING",
                "category": fest.category,
                "description": fest.description,
                "impacts": {k: v.value for k, v in fest.impacts.items()},
                "days_offset": days_until
            })
        # Recently concluded
        elif dt - timedelta(days=lookaround_days) <= fest.end_date < dt:
            days_ago = (dt - fest.end_date).days
            results.append({
                "name": fest.name,
                "status": "RECENT",
                "category": fest.category,
                "description": fest.description,
                "impacts": {k: v.value for k, v in fest.impacts.items()},
                "days_offset": -days_ago
            })
    return results


def get_crop_season_phase(commodity: str, dt: date) -> Dict[str, Any]:
    """
    Returns the biological agricultural season and harvest supply phase for a commodity.
    
    Crops:
    - Onion:
        - Rabi (Mar-May): Major winter crop, 65% of national production, stored in chawls.
        - Kharif (Oct-Dec): Monsoon crop, 20% of production, high moisture, cannot store.
        - Late Kharif (Jan-Feb): 15% of production, bridge crop.
    - Tomato:
        - Multi-crop, but major flush in Nov-Mar (Winter) and Jul-Aug (Monsoon).
        - Lean peak in May-Jun and Sep-Oct (Transition gaps).
    - Potato:
        - Single massive Rabi harvest (Jan-Apr), kept in cold storage rest of year.
    """
    comm = commodity.capitalize()
    m = dt.month

    if comm == "Onion":
        if m in (3, 4, 5):
            return {
                "season": "Rabi Harvest",
                "phase": CropPhase.HARVEST_GLUT.value,
                "summary": "Golden harvest: fresh Rabi onions flooding markets. Highest supply, lowest annual prices.",
                "price_expectation": "LOW / STABLE"
            }
        elif m in (6, 7, 8):
            return {
                "season": "Monsoon Storage Phase",
                "phase": CropPhase.LEAN_STORAGE.value,
                "summary": "Consuming Rabi storage onions. Gradual spoilage in storage leads to price firming.",
                "price_expectation": "GRADUAL INCREASE"
            }
        elif m in (9, 10):
            return {
                "season": "Pre-Kharif Scarcity",
                "phase": CropPhase.PRE_HARVEST_SCARCITY.value,
                "summary": "Storage stocks depleted; new Kharif crop not yet ready. Annual price volatility peak.",
                "price_expectation": "HIGH VOLATILITY / PEAK"
            }
        else: # 11, 12, 1, 2
            return {
                "season": "Kharif & Late Kharif Harvest",
                "phase": CropPhase.PEAK_ARRIVAL.value,
                "summary": "Fresh red Kharif harvest arriving. High moisture onions easing market tightness.",
                "price_expectation": "COOLING DOWN"
            }

    elif comm == "Tomato":
        if m in (12, 1, 2, 3):
            return {
                "season": "Winter Flush",
                "phase": CropPhase.HARVEST_GLUT.value,
                "summary": "Bumper winter crop across southern and western belts. Heavy arrivals, lowest prices.",
                "price_expectation": "LOW / STABLE"
            }
        elif m in (4, 5, 6):
            return {
                "season": "Summer Lean Gap",
                "phase": CropPhase.PRE_HARVEST_SCARCITY.value,
                "summary": "Summer heatwave transition. Flower drop reduces yields; prices start rising.",
                "price_expectation": "RISING"
            }
        elif m in (7, 8):
            return {
                "season": "Monsoon Crop Transition",
                "phase": CropPhase.PRE_HARVEST_SCARCITY.value,
                "summary": "Monsoon rains disrupt picking and transit. Frequent sudden price spikes.",
                "price_expectation": "HIGH VOLATILITY"
            }
        else: # 9, 10, 11
            return {
                "season": "Early Winter Arrivals",
                "phase": CropPhase.PEAK_ARRIVAL.value,
                "summary": "Post-monsoon harvest starting to reach major terminal markets.",
                "price_expectation": "MODERATE"
            }

    elif comm == "Potato":
        if m in (1, 2, 3, 4):
            return {
                "season": "Main Rabi Harvest",
                "phase": CropPhase.HARVEST_GLUT.value,
                "summary": "Fresh harvest in UP, Bengal, Punjab. Heavy arrivals entering cold storages.",
                "price_expectation": "ANNUAL TROUGH (CHEAPEST)"
            }
        elif m in (5, 6, 7, 8, 9):
            return {
                "season": "Cold Storage Release",
                "phase": CropPhase.LEAN_STORAGE.value,
                "summary": "Markets supplied entirely from cold storage facilities. Stable margins.",
                "price_expectation": "STEADY / CONTROLLED"
            }
        else: # 10, 11, 12
            return {
                "season": "Pre-Harvest Lean Window",
                "phase": CropPhase.PRE_HARVEST_SCARCITY.value,
                "summary": "Storage stocks running low before new crop arrives in January.",
                "price_expectation": "MILD PEAK"
            }

    # Default generic
    return {
        "season": "Regular Agricultural Season",
        "phase": CropPhase.PEAK_ARRIVAL.value,
        "summary": "Normal seasonal operations.",
        "price_expectation": "MODERATE"
    }


def get_commodity_calendar_context(commodity: str, dt: date) -> Dict[str, Any]:
    """
    Combined helper returning active crop phase, upcoming festivals, and net demand forecast.
    """
    festivals = get_active_festivals(dt, lookaround_days=7)
    crop_info = get_crop_season_phase(commodity, dt)

    comm = commodity.capitalize()
    active_impacts = []
    for f in festivals:
        imp = f["impacts"].get(comm)
        if imp:
            active_impacts.append({
                "festival": f["name"],
                "status": f["status"],
                "impact": imp,
                "days_offset": f["days_offset"]
            })

    return {
        "date": dt.isoformat(),
        "commodity": comm,
        "crop_season": crop_info["season"],
        "supply_phase": crop_info["phase"],
        "season_summary": crop_info["summary"],
        "base_price_trend": crop_info["price_expectation"],
        "active_festivals": festivals,
        "cultural_demand_impacts": active_impacts
    }
