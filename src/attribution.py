"""
Automated Price Attribution Engine ("Why Did Prices Move?").

Synthesizes:
1. Wholesale price velocity (week-on-week or intraday change).
2. Localized meteorological shocks (heavy rain, extreme heat).
3. Cultural demand cycles (Navratri fasting, Diwali feasts, Wedding banquets).
4. Agricultural harvest phases (Rabi glut, Pre-Kharif scarcity).
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, Optional

from src.calendar import get_commodity_calendar_context, DemandImpact, CropPhase


@dataclass
class PriceAttribution:
    commodity: str
    mandi_name: str
    trade_date: date
    price_today: float
    price_change_pct: float
    primary_driver: str
    severity: str
    headline: str
    explanation: str
    crop_season: str
    cultural_context: str
    weather_flag: Optional[str]


def explain_price_movement(
    commodity: str,
    mandi_name: str,
    trade_date: date,
    price_today: float,
    price_prior: float,
    min_price: float = 0.0,
    max_price: float = 0.0,
    rainfall_mm: float = 0.0,
    max_temp_c: float = 0.0,
) -> PriceAttribution:
    """
    Explain the primary driver behind a commodity price observation in plain English.
    """
    comm = commodity.capitalize()
    
    # 1. Calculate price velocity
    if price_prior > 0:
        pct_change = ((price_today - price_prior) / price_prior) * 100.0
    else:
        pct_change = 0.0

    # 2. Retrieve calendar & crop context
    cal_ctx = get_commodity_calendar_context(comm, trade_date)
    crop_season = cal_ctx["crop_season"]
    supply_phase = cal_ctx["supply_phase"]
    cultural_impacts = cal_ctx["cultural_demand_impacts"]

    # 3. Assess Weather Shocks
    weather_flag = None
    if rainfall_mm >= 30.0:
        weather_flag = f"Heavy Rain ({rainfall_mm:.1f} mm)"
    elif rainfall_mm >= 15.0:
        weather_flag = f"Moderate Rain ({rainfall_mm:.1f} mm)"
    elif max_temp_c >= 40.0:
        weather_flag = f"Severe Heatwave ({max_temp_c:.1f}°C)"
    elif max_temp_c >= 38.0:
        weather_flag = f"High Temperature ({max_temp_c:.1f}°C)"

    # 4. Assess Quality Spread (Spoilage)
    intraday_gap_pct = 0.0
    if price_today > 0 and max_price > min_price:
        intraday_gap_pct = ((max_price - min_price) / price_today) * 100.0

    # 5. Rule Attribution Hierarchy
    primary_driver = "STABLE"
    severity = "NORMAL"
    headline = f"{comm} Trading Steadily"
    explanation = f"{comm} prices in {mandi_name} are trading normally within expected seasonal ranges."

    # Check for Cultural Fasting Drop (e.g. Navratri for Onion)
    active_slump = [ci for ci in cultural_impacts if ci["impact"] == DemandImpact.SLUMP.value]
    active_slump.sort(key=lambda x: 0 if x.get("status") == "ACTIVE" else (1 if x.get("status") == "UPCOMING" else 2))

    active_surge = [ci for ci in cultural_impacts if ci["impact"] in (DemandImpact.SHARP_SURGE.value, DemandImpact.MODERATE_SURGE.value)]
    active_surge.sort(key=lambda x: 0 if x.get("status") == "ACTIVE" else (1 if x.get("status") == "UPCOMING" else 2))

    if pct_change >= 20.0:
        # Significant price spike
        if weather_flag and "Rain" in weather_flag:
            primary_driver = "WEATHER_RAIN"
            severity = "CRITICAL"
            headline = f"🌧️ Weather Shock: Rain Inundation (+{pct_change:.1f}%)"
            explanation = (
                f"{weather_flag} in the farming district disrupted harvesting and highway transport, "
                f"causing arrivals to drop and wholesale prices to spike to ₹{price_today/100:.1f}/kg."
            )
        elif weather_flag and "Heat" in weather_flag:
            primary_driver = "WEATHER_HEAT"
            severity = "WARNING"
            headline = f"☀️ Heatwave Crop Damage (+{pct_change:.1f}%)"
            explanation = (
                f"Extreme heat ({max_temp_c:.1f}°C) increased field spoilage, tightening good-quality supply "
                f"and pushing prices up to ₹{price_today/100:.1f}/kg."
            )
        elif active_surge:
            fest_name = active_surge[0]["festival"]
            primary_driver = "FESTIVAL_DEMAND"
            severity = "WARNING"
            headline = f"🪔 Festival Demand Surge (+{pct_change:.1f}%)"
            explanation = (
                f"Pre-festival feasting and procurement for {fest_name} triggered rapid demand surge across mandis."
            )
        elif supply_phase == CropPhase.PRE_HARVEST_SCARCITY.value:
            primary_driver = "SEASONAL_SCARCITY"
            severity = "WARNING"
            headline = f"🌾 Pre-Harvest Lean Season (+{pct_change:.1f}%)"
            explanation = (
                f"Old crop storage reserves are depleted while the new {crop_season} harvest is not yet in full swing."
            )
        else:
            primary_driver = "SUPPLY_SHORTAGE"
            severity = "WARNING"
            headline = f"⚠️ Sudden Wholesale Price Spike (+{pct_change:.1f}%)"
            explanation = f"Sudden wholesale price increase of {pct_change:.1f}% observed in {mandi_name}."

    elif pct_change <= -20.0:
        # Significant price drop
        if active_slump:
            fest_name = active_slump[0]["festival"]
            primary_driver = "CULTURAL_FASTING"
            severity = "NORMAL"
            headline = f"🪔 Fasting Demand Slump ({pct_change:.1f}%)"
            explanation = (
                f"Temporary drop in retail and restaurant consumption during {fest_name} reduced wholesale demand."
            )
        elif supply_phase == CropPhase.HARVEST_GLUT.value:
            primary_driver = "HARVEST_GLUT"
            severity = "GLUT"
            headline = f"🚜 Peak Harvest Glut ({pct_change:.1f}%)"
            explanation = (
                f"Heavy bumper arrivals from the {crop_season} flooded the market, driving wholesale prices down to ₹{price_today/100:.1f}/kg."
            )
        elif weather_flag and "Rain" in weather_flag:
            primary_driver = "DISTRESS_SELLING"
            severity = "CRITICAL"
            headline = f"🌧️ Wet Produce Distress Sale ({pct_change:.1f}%)"
            explanation = (
                f"Heavy rains forced farmers into emergency early harvest of wet crops, temporarily crashing prices before future rot sets in."
            )
        else:
            primary_driver = "SUPPLY_SURPLUS"
            severity = "GLUT"
            headline = f"📉 Wholesale Price Drop ({pct_change:.1f}%)"
            explanation = f"Arrival volume surge in {mandi_name} softened wholesale prices by {abs(pct_change):.1f}%."

    elif intraday_gap_pct >= 50.0:
        # Moderate modal price, but huge Min vs Max spread
        primary_driver = "QUALITY_DISPERSION"
        severity = "WARNING"
        headline = f"⚠️ High Crop Quality Divergence"
        explanation = (
            f"Wide intraday spread (Min ₹{min_price/100:.1f}/kg vs Max ₹{max_price/100:.1f}/kg) "
            f"indicates damaged/spoiled batches trading at steep discounts alongside premium stock."
        )

    cultural_summary = "No major holiday demand anomaly."
    if cultural_impacts:
        cultural_summary = f"{cultural_impacts[0]['festival']} ({cultural_impacts[0]['status']}) - {cultural_impacts[0]['impact']}"

    return PriceAttribution(
        commodity=comm,
        mandi_name=mandi_name,
        trade_date=trade_date,
        price_today=price_today,
        price_change_pct=pct_change,
        primary_driver=primary_driver,
        severity=severity,
        headline=headline,
        explanation=explanation,
        crop_season=crop_season,
        cultural_context=cultural_summary,
        weather_flag=weather_flag,
    )
