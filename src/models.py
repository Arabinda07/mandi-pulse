"""Domain models and data structures for the Food Inflation & Volatility Engine."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MandiRecord:
    """Canonical APMC Mandi master entity."""
    mandi_id: str
    canonical_name: str
    state: str
    district: str
    state_lgd_code: int
    district_lgd_code: int
    latitude: float
    longitude: float
    is_consumption_hub: bool = False
    hub_type: str = "production"  # "production" | "consumption" | "transit"


@dataclass(frozen=True)
class ResolvedMandi:
    """Result of entity resolution for a raw incoming market name."""
    mandi_id: str
    canonical_name: str
    state: str
    district: str
    district_lgd_code: int
    latitude: float
    longitude: float
    is_consumption_hub: bool
    match_type: str  # "exact" | "alias" | "fuzzy" | "unmapped"
    confidence: float


@dataclass(frozen=True)
class CommodityRecord:
    """Commodity catalog record with inflation weighting."""
    commodity_id: str
    name: str
    category: str  # "vegetable" | "pulse" | "cereal" | "oilseed"
    tier: int  # 1 = daily core, 2 = snapshot/on-demand
    unit: str = "quintal"  # Agmarknet prices are INR / quintal (100 kg)
    cpi_weight: float = 0.0  # Weight in CPI Food basket (%)


@dataclass(frozen=True)
class DailyFactRecord:
    """Atomic daily wholesale market observation."""
    mandi_id: str
    commodity_id: str
    reported_date: str  # ISO YYYY-MM-DD
    arrival_tonnes: float
    min_price: float
    max_price: float
    modal_price: float


@dataclass(frozen=True)
class RawCommodityRecord:
    """Raw record received from external API or seed adapter prior to resolution."""
    raw_state: str
    raw_district: str
    raw_market: str
    raw_commodity: str
    raw_variety: str
    reported_date: str  # ISO YYYY-MM-DD
    arrival_tonnes: float
    min_price: float
    max_price: float
    modal_price: float


@dataclass(frozen=True)
class CorridorStress:
    """Evaluated supply-chain friction between production and consumption hubs."""
    origin_mandi_id: str
    origin_name: str
    terminal_mandi_id: str
    terminal_name: str
    commodity_id: str
    reported_date: str
    origin_modal_price: float
    terminal_modal_price: float
    price_spread: float
    spread_pct: float
    origin_arrival_shock_z: float
    stress_level: str  # "NORMAL" | "MODERATE" | "HIGH" | "SEVERE"
