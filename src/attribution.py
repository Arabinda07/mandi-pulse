"""
Automated Price Attribution Engine ("Why Did Prices Move?").

Synthesizes:
1. Wholesale price velocity (week-on-week or intraday change).
2. Localized meteorological shocks (heavy rain, extreme heat).
3. Cultural demand cycles (Navratri fasting, Diwali feasts, Wedding banquets).
4. Agricultural harvest phases (Rabi glut, Pre-Kharif scarcity).
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, Optional, List

from src.calendar import get_commodity_calendar_context, DemandImpact, CropPhase
from src.sources.weather import MandiWeatherAdapter
from src.registry import MandiRegistry

logger = logging.getLogger(__name__)

# Module-level instances and cache to prevent redundant external API requests
_WEATHER_ADAPTER = MandiWeatherAdapter()
_REGISTRY = MandiRegistry()
_WEATHER_CACHE: Dict[tuple, Dict[str, float]] = {}


@dataclass
class ShoppingAdvice:
    commodity: str
    advice: str
    status: str            # 'fair' | 'warning' | 'shock'
    status_label: str      # 'Fair Price' | 'Elevated Margin' | 'Severe Spike'
    trend_signal: str      # '🟢 Cooling Down in ~7d' | '🔴 Spike in ~10d' | '⚪ Stable Corridor'
    trend_status: str      # 'cooling' | 'spike' | 'stable'
    weather_context: str
    headline: str
    origin_name: str
    arrival_z_score: float


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
    shopping_advice: str = ""


def get_mandi_weather(
    mandi_identifier: str,
    obs_date: Optional[date] = None,
    use_cache: bool = True,
    weather_adapter: Optional[MandiWeatherAdapter] = None,
) -> Dict[str, float]:
    """
    Fetch live / historical meteorological observations for a canonical Mandi.
    Resolves mandi_id or common name to exact GPS coordinates via MandiRegistry
    and queries Open-Meteo (ERA5 / IMD equivalent) without requiring an API key.
    """
    global _WEATHER_CACHE
    adapter = weather_adapter or _WEATHER_ADAPTER
    target_date = obs_date or date.today()
    date_str = target_date.isoformat()

    # 1. Resolve Mandi coordinates
    mandi_record = _REGISTRY.get_mandi(mandi_identifier)
    if not mandi_record:
        resolved = _REGISTRY.resolve(mandi_identifier)
        mandi_record = _REGISTRY.get_mandi(resolved.mandi_id)

    if not mandi_record or not mandi_record.latitude or not mandi_record.longitude:
        return {"precipitation_mm": 0.0, "max_temp_c": 0.0, "status": "COORDINATES_MISSING"}

    cache_key = (mandi_record.mandi_id, date_str)
    if use_cache and cache_key in _WEATHER_CACHE:
        return _WEATHER_CACHE[cache_key]

    # 2. Fetch from Open-Meteo via MandiWeatherAdapter
    try:
        data = adapter.get_mandi_rainfall(
            latitude=mandi_record.latitude,
            longitude=mandi_record.longitude,
            start_date=date_str,
            end_date=date_str,
        )
        precip_list = data.get("precipitation_mm", [])
        temp_list = data.get("temperature_max_c", [])

        precip = float(precip_list[0]) if precip_list and precip_list[0] is not None else 0.0
        temp = float(temp_list[0]) if temp_list and temp_list[0] is not None else 0.0

        res = {
            "mandi_id": mandi_record.mandi_id,
            "canonical_name": mandi_record.canonical_name,
            "precipitation_mm": precip,
            "max_temp_c": temp,
            "status": "LIVE_OPEN_METEO"
        }
        _WEATHER_CACHE[cache_key] = res
        return res
    except Exception as err:
        logger.warning("Failed to fetch live weather for mandi %s: %s", mandi_identifier, err)
        return {"precipitation_mm": 0.0, "max_temp_c": 0.0, "status": "ERROR"}


def fetch_all_mandis_weather_alerts(
    obs_date: Optional[date] = None,
    weather_adapter: Optional[MandiWeatherAdapter] = None,
) -> List[Dict[str, Any]]:
    """
    Query live weather conditions across all 25 canonical APMC Mandis in the registry.
    Detects heavy rainfall, cloudburst inundation, and severe heatwave conditions.
    """
    alerts = []
    target_date = obs_date or date.today()
    date_str = target_date.isoformat()

    for mandi in _REGISTRY.get_canonical_mandis():
        weather = get_mandi_weather(mandi.mandi_id, obs_date=target_date, weather_adapter=weather_adapter)
        rain = weather.get("precipitation_mm", 0.0)
        temp = weather.get("max_temp_c", 0.0)

        flag = None
        severity = "NORMAL"

        if rain >= 30.0:
            flag = f"🌧️ Severe Inundation ({rain:.1f} mm)"
            severity = "CRITICAL"
        elif rain >= 15.0:
            flag = f"🌧️ Heavy Rainfall ({rain:.1f} mm)"
            severity = "WARNING"
        elif rain >= 5.0:
            flag = f"🌦️ Moderate Rain ({rain:.1f} mm)"
            severity = "NOTICE"
        elif temp >= 40.0:
            flag = f"☀️ Severe Heatwave ({temp:.1f}°C)"
            severity = "CRITICAL"
        elif temp >= 38.0:
            flag = f"☀️ High Temperature ({temp:.1f}°C)"
            severity = "WARNING"

        alerts.append({
            "mandi_id": mandi.mandi_id,
            "canonical_name": mandi.canonical_name,
            "state": mandi.state,
            "district": mandi.district,
            "latitude": mandi.latitude,
            "longitude": mandi.longitude,
            "observation_date": date_str,
            "precipitation_mm": rain,
            "max_temp_c": temp,
            "weather_flag": flag,
            "severity": severity,
        })

    return alerts


def explain_price_movement(
    commodity: str,
    mandi_name: str,
    trade_date: date,
    price_today: float,
    price_prior: float,
    min_price: float = 0.0,
    max_price: float = 0.0,
    rainfall_mm: Optional[float] = None,
    max_temp_c: Optional[float] = None,
    mandi_id: Optional[str] = None,
    fetch_live_weather: bool = True,
) -> PriceAttribution:
    """
    Explain the primary driver behind a commodity price observation in plain English.
    Dynamically pulls live Open-Meteo weather if rainfall/temp are not explicitly provided.
    """
    comm = commodity.capitalize()

    # If weather metrics were not explicitly passed, query live Open-Meteo adapter
    if (rainfall_mm is None or (rainfall_mm == 0.0 and max_temp_c in (None, 0.0))) and fetch_live_weather:
        live_w = get_mandi_weather(mandi_id or mandi_name, obs_date=trade_date)
        rainfall_mm = live_w.get("precipitation_mm", 0.0)
        max_temp_c = live_w.get("max_temp_c", 0.0)
    else:
        rainfall_mm = rainfall_mm or 0.0
        max_temp_c = max_temp_c or 0.0
    
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

    advice_res = generate_shopping_advice(
        commodity=comm,
        terminal_name=mandi_name,
        price_today_rs_kg=price_today / 100.0,
        day_change_rs_kg=((price_today - price_prior) / 100.0) if price_prior > 0 else 0.0,
        week_change_pct=pct_change,
        origin_name=mandi_name,
        origin_arrival_shock_z=0.0,
        weather_flag=weather_flag,
        crop_season=crop_season,
    )

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
        shopping_advice=advice_res.advice,
    )


def generate_shopping_advice(
    commodity: str,
    terminal_name: str,
    price_today_rs_kg: float,
    day_change_rs_kg: float = 0.0,
    week_change_pct: float = 0.0,
    origin_name: Optional[str] = None,
    origin_arrival_shock_z: float = 0.0,
    weather_flag: Optional[str] = None,
    crop_season: Optional[str] = None,
) -> ShoppingAdvice:
    """
    Deterministic rule-based NLG engine:
    Synthesizes origin arrival shock (ASA Z-scores), weather flags from Open-Meteo,
    and DoD/WoW price velocity into consumer-facing household buying recommendations.
    """
    comm = commodity.capitalize()
    default_origin = "Lasalgaon" if comm.lower() == "onion" else ("Kolar" if comm.lower() == "tomato" else "Farrukhabad")
    origin = origin_name or default_origin

    # 1. Severe Supply Contraction (Shock)
    if origin_arrival_shock_z <= -1.5 or (weather_flag and ("Rain" in weather_flag or "Inundation" in weather_flag)):
        status = "shock"
        status_label = "Severe Spike"
        trend_signal = "🔴 Spike in ~10d"
        trend_status = "spike"
        if weather_flag and ("Rain" in weather_flag or "Inundation" in weather_flag):
            advice = (
                f"{weather_flag} in {origin} farming belt disrupted arrivals (ASA {origin_arrival_shock_z:+.2f}Z). "
                f"Wholesale prices up ₹{abs(day_change_rs_kg):.2f}/kg—buy 3-5 day weekly buffer before retail markups peak."
            )
            weather_context = f"{weather_flag} recorded across {origin} producing basin."
        else:
            advice = (
                f"{origin} arrivals contracted sharply ({origin_arrival_shock_z:+.2f}Z shock). "
                f"Daily wholesale moved by ₹{day_change_rs_kg:+.2f}/kg—stock weekly cooking essentials early."
            )
            weather_context = f"Arrival contraction at {origin} dispatch yards."
        headline = f"Severe Supply Crunch in {origin}"

    # 2. Moderate Pressure / Elevated Margin (Warning)
    elif origin_arrival_shock_z <= -0.8 or week_change_pct >= 5.0 or day_change_rs_kg >= 1.5:
        status = "warning"
        status_label = "Elevated Margin"
        trend_signal = "🔴 Spike in ~10d"
        trend_status = "spike"
        advice = (
            f"{comm} arrivals from {origin} down {abs(origin_arrival_shock_z):.1f}Z with prices up {week_change_pct:+.1f}% WoW. "
            f"Consider purchasing bulk crate lots to bypass intermediary retail markups."
        )
        weather_context = f"Moderate dispatch variability in {origin}; transit corridors experiencing slight friction."
        headline = f"Elevated Margins for {comm}"

    # 3. Supply Glut / Favorable Cooling Market (Fair / Cooling)
    elif origin_arrival_shock_z >= 0.8 or week_change_pct <= -5.0 or day_change_rs_kg <= -1.5:
        status = "fair"
        status_label = "Fair Price"
        trend_signal = "🟢 Cooling Down in ~7d"
        trend_status = "cooling"
        advice = (
            f"Abundant arrivals flowing smoothly from {origin} (DoD ₹{day_change_rs_kg:+.2f}/kg). "
            f"Favorable market conditions—buy only what you need for daily consumption."
        )
        weather_context = f"Favorable harvest conditions and clear highway transit across {origin} belt."
        headline = f"Favorable Supply from {origin}"

    # 4. Seasonal Equilibrium / Stable Corridor (Fair / Stable)
    else:
        status = "fair"
        status_label = "Fair Price"
        trend_signal = "⚪ Stable Corridor"
        trend_status = "stable"
        advice = (
            f"Steady daily arrivals from {origin} maintaining normal price equilibrium in {terminal_name} ({week_change_pct:+.1f}% WoW). "
            f"Stable cooking budget."
        )
        weather_context = f"Normal seasonal climate and steady dispatches across {origin} agricultural belt."
        headline = f"Stable Market Corridor"

    return ShoppingAdvice(
        commodity=comm,
        advice=advice,
        status=status,
        status_label=status_label,
        trend_signal=trend_signal,
        trend_status=trend_status,
        weather_context=weather_context,
        headline=headline,
        origin_name=origin,
        arrival_z_score=origin_arrival_shock_z,
    )


def generate_basket_verdict(
    advices: List[ShoppingAdvice],
    weekly_total_rs: float,
    week_change_pct: float,
) -> Dict[str, str]:
    """
    Generate an executive household market verdict across the consolidated kitchen basket.
    Synthesizes multiple commodity pressure points into a unified recommendation.
    """
    shocks = [a for a in advices if a.status == "shock"]
    warnings = [a for a in advices if a.status == "warning"]
    cooling = [a for a in advices if a.trend_status == "cooling"]

    if shocks:
        spiking_names = " & ".join(s.commodity for s in shocks)
        origins = " and ".join(dict.fromkeys(s.origin_name for s in shocks if s.origin_name))
        verdict = f"Vegetable basket elevated due to {spiking_names} supply contraction at {origins or 'key farmgate hubs'}."
        verdict_status = "shock"
    elif warnings:
        warn_names = " & ".join(w.commodity for w in warnings)
        verdict = f"Moderate upward pressure on {warn_names} ({week_change_pct:+.1f}% WoW); stable supplies on remaining staples."
        verdict_status = "warning"
    elif cooling:
        cool_names = " & ".join(c.commodity for c in cooling)
        verdict = f"Kitchen basket easing across {cool_names} ({week_change_pct:+.1f}% WoW); prices favorable for household staples."
        verdict_status = "fair"
    else:
        verdict = f"Kitchen basket steady at ₹{weekly_total_rs:.1f}/week; all strategic supply corridors operating in normal seasonal equilibrium."
        verdict_status = "fair"

    return {
        "verdict": verdict,
        "verdict_status": verdict_status,
    }

