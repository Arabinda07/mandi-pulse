"""Curated Mandi Master Registry with LGD administrative codes and entity resolution."""

from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional
from src.models import MandiRecord, ResolvedMandi


class MandiRegistry:
    """Deep module for APMC Mandi master data, spatial coordinates, and entity resolution."""

    # Official State APMC Act Fee Schedules & Statutory Cess Schedules
    # Source: State Agricultural Marketing Boards (MSAMB, DAMB, KSAMB, UPSAMB, etc.)
    STATE_STATUTORY_FEES: Dict[str, Dict[str, float]] = {
        "maharashtra": {
            "mandi_cess_pct": 1.05,  # MSAMB 1.05% market fee
            "commission_cap_pct": 6.0,  # MSAMB Fruits & Vegetables commission cap (payable by buyer)
        },
        "delhi": {
            "mandi_cess_pct": 2.0,  # DAMB: 1.0% mandi fee + 1.0% rural development cess
            "commission_cap_pct": 6.0,  # DAMB F&V commission agent cap
        },
        "nct of delhi": {
            "mandi_cess_pct": 2.0,  # DAMB: 1.0% mandi fee + 1.0% rural development cess
            "commission_cap_pct": 6.0,
        },
        "karnataka": {
            "mandi_cess_pct": 1.5,  # KSAMB: 1.5% market fee
            "commission_cap_pct": 2.0,  # KSAMB commission cap
        },
        "uttar pradesh": {
            "mandi_cess_pct": 2.0,  # UPSAMB: 1.5% mandi fee + 0.5% development cess
            "commission_cap_pct": 2.0,  # UPSAMB commission cap
        },
        "andhra pradesh": {
            "mandi_cess_pct": 1.0,  # APSAMB: 1.0% market fee
            "commission_cap_pct": 4.0,  # Commission cap
        },
        "madhya pradesh": {
            "mandi_cess_pct": 1.5,  # MP Mandi Board: 1.5% market fee
            "commission_cap_pct": 2.0,
        },
        "west bengal": {
            "mandi_cess_pct": 1.0,  # WBSAMB: 1.0% market fee
            "commission_cap_pct": 2.0,
        },
    }

    # Canonical APMC hubs across India's primary production corridors & terminal consumption centers
    _CANONICAL_MANDIS: List[MandiRecord] = [
        # Maharashtra - Onion & Perishable Capital (MSAMB: 1.05% market fee, 6.0% commission cap)
        MandiRecord(
            mandi_id="mandi_lasalgaon",
            canonical_name="Lasalgaon",
            state="Maharashtra",
            district="Nashik",
            state_lgd_code=27,
            district_lgd_code=485,
            latitude=20.1472,
            longitude=74.2256,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.05,
            commission_cap_pct=6.0,
        ),
        MandiRecord(
            mandi_id="mandi_pimpalgaon",
            canonical_name="Pimpalgaon",
            state="Maharashtra",
            district="Nashik",
            state_lgd_code=27,
            district_lgd_code=485,
            latitude=20.1706,
            longitude=73.9856,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.05,
            commission_cap_pct=6.0,
        ),
        MandiRecord(
            mandi_id="mandi_pune",
            canonical_name="Pune",
            state="Maharashtra",
            district="Pune",
            state_lgd_code=27,
            district_lgd_code=490,
            latitude=18.5204,
            longitude=73.8567,
            is_consumption_hub=True,
            hub_type="consumption",
            mandi_cess_pct=1.05,
            commission_cap_pct=6.0,
        ),
        MandiRecord(
            mandi_id="mandi_vashi",
            canonical_name="Vashi (Navi Mumbai)",
            state="Maharashtra",
            district="Thane",
            state_lgd_code=27,
            district_lgd_code=499,
            latitude=19.0760,
            longitude=73.0030,
            is_consumption_hub=True,
            hub_type="consumption",
            mandi_cess_pct=1.05,
            commission_cap_pct=6.0,
        ),
        MandiRecord(
            mandi_id="mandi_solapur",
            canonical_name="Solapur",
            state="Maharashtra",
            district="Solapur",
            state_lgd_code=27,
            district_lgd_code=495,
            latitude=17.6599,
            longitude=75.9064,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.05,
            commission_cap_pct=6.0,
        ),
        # Karnataka & Andhra Pradesh - Tomato & Pulse Belts (KSAMB: 1.5%, APSAMB: 1.0%)
        MandiRecord(
            mandi_id="mandi_kolar",
            canonical_name="Kolar",
            state="Karnataka",
            district="Kolar",
            state_lgd_code=29,
            district_lgd_code=542,
            latitude=13.1367,
            longitude=78.1292,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.5,
            commission_cap_pct=2.0,
        ),
        MandiRecord(
            mandi_id="mandi_bangalore",
            canonical_name="Bangalore (Yeshwanthpur)",
            state="Karnataka",
            district="Bangalore Urban",
            state_lgd_code=29,
            district_lgd_code=529,
            latitude=13.0238,
            longitude=77.5516,
            is_consumption_hub=True,
            hub_type="consumption",
            mandi_cess_pct=1.5,
            commission_cap_pct=2.0,
        ),
        MandiRecord(
            mandi_id="mandi_madanapalle",
            canonical_name="Madanapalle",
            state="Andhra Pradesh",
            district="Annamayya",
            state_lgd_code=28,
            district_lgd_code=503,
            latitude=13.5560,
            longitude=78.5010,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.0,
            commission_cap_pct=4.0,
        ),
        # National Capital Region - Megacity Consumption Terminals (DAMB: 1.0% fee + 1.0% cess = 2.0%)
        MandiRecord(
            mandi_id="mandi_azadpur",
            canonical_name="Azadpur (Delhi)",
            state="NCT of Delhi",
            district="North Delhi",
            state_lgd_code=7,
            district_lgd_code=138,
            latitude=28.7163,
            longitude=77.1772,
            is_consumption_hub=True,
            hub_type="consumption",
            mandi_cess_pct=2.0,
            commission_cap_pct=6.0,
        ),
        MandiRecord(
            mandi_id="mandi_ghazipur",
            canonical_name="Ghazipur (Delhi)",
            state="NCT of Delhi",
            district="East Delhi",
            state_lgd_code=7,
            district_lgd_code=139,
            latitude=28.6276,
            longitude=77.3326,
            is_consumption_hub=True,
            hub_type="consumption",
            mandi_cess_pct=2.0,
            commission_cap_pct=6.0,
        ),
        # Uttar Pradesh & Madhya Pradesh - Potato & Wheat Belts (UPSAMB: 1.5% + 0.5% = 2.0%, MPSAMB: 1.5%)
        MandiRecord(
            mandi_id="mandi_agra",
            canonical_name="Agra",
            state="Uttar Pradesh",
            district="Agra",
            state_lgd_code=9,
            district_lgd_code=129,
            latitude=27.1767,
            longitude=78.0081,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=2.0,
            commission_cap_pct=2.0,
        ),
        MandiRecord(
            mandi_id="mandi_farrukhabad",
            canonical_name="Farrukhabad",
            state="Uttar Pradesh",
            district="Farrukhabad",
            state_lgd_code=9,
            district_lgd_code=150,
            latitude=27.3826,
            longitude=79.5828,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=2.0,
            commission_cap_pct=2.0,
        ),
        MandiRecord(
            mandi_id="mandi_indore",
            canonical_name="Indore",
            state="Madhya Pradesh",
            district="Indore",
            state_lgd_code=23,
            district_lgd_code=407,
            latitude=22.7196,
            longitude=75.8577,
            is_consumption_hub=False,
            hub_type="production",
            mandi_cess_pct=1.5,
            commission_cap_pct=2.0,
        ),
        # West Bengal - Eastern Potato & Rice Corridor (WBSAMB: 1.0%)
        MandiRecord(
            mandi_id="mandi_kolkata",
            canonical_name="Kolkata (Koley Market)",
            state="West Bengal",
            district="Kolkata",
            state_lgd_code=19,
            district_lgd_code=314,
            latitude=22.5697,
            longitude=88.3697,
            is_consumption_hub=True,
            hub_type="consumption",
            mandi_cess_pct=1.0,
            commission_cap_pct=2.0,
        ),
    ]

    # Pre-compiled aliases for variations seen in Agmarknet reports
    _ALIASES: Dict[str, str] = {
        "lasalgaon": "mandi_lasalgaon",
        "lasalgaon(niphad)": "mandi_lasalgaon",
        "pimpalgaon": "mandi_pimpalgaon",
        "pimpalgaon baswant": "mandi_pimpalgaon",
        "pune": "mandi_pune",
        "pune(gultekdi)": "mandi_pune",
        "vashi": "mandi_vashi",
        "mumbai": "mandi_vashi",
        "apmc vashi": "mandi_vashi",
        "solapur": "mandi_solapur",
        "kolar": "mandi_kolar",
        "kolar apmc": "mandi_kolar",
        "bangalore": "mandi_bangalore",
        "bengaluru": "mandi_bangalore",
        "yeshwanthpur": "mandi_bangalore",
        "binny mill": "mandi_bangalore",
        "madanapalle": "mandi_madanapalle",
        "madanapalli": "mandi_madanapalle",
        "azadpur": "mandi_azadpur",
        "delhi": "mandi_azadpur",
        "ghazipur": "mandi_ghazipur",
        "agra": "mandi_agra",
        "farrukhabad": "mandi_farrukhabad",
        "indore": "mandi_indore",
        "kolkata": "mandi_kolkata",
        "koley market": "mandi_kolkata",
    }

    def __init__(self) -> None:
        self._by_id: Dict[str, MandiRecord] = {m.mandi_id: m for m in self._CANONICAL_MANDIS}
        self._by_name: Dict[str, MandiRecord] = {
            self._normalize_token(m.canonical_name): m for m in self._CANONICAL_MANDIS
        }

    @staticmethod
    def _normalize_token(text: str) -> str:
        """Strip non-alphanumeric punctuation and lower-case text."""
        if not text:
            return ""
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        return " ".join(cleaned.lower().split())

    @classmethod
    def get_statutory_fees(cls, state: Optional[str]) -> Dict[str, float]:
        """Look up statutory APMC market fee + cess and commission cap for a state."""
        st_key = (state or "").strip().lower()
        return cls.STATE_STATUTORY_FEES.get(
            st_key,
            {"mandi_cess_pct": 1.0, "commission_cap_pct": 2.0}
        )

    def get_canonical_mandis(self) -> List[MandiRecord]:
        """Return all verified APMC master records."""
        return list(self._CANONICAL_MANDIS)

    def get_mandi(self, mandi_id: str) -> Optional[MandiRecord]:
        """Lookup mandi by canonical ID."""
        return self._by_id.get(mandi_id)

    def resolve(
        self,
        raw_market: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> ResolvedMandi:
        """
        Deep entity resolution:
        1. Exact canonical name match
        2. Curated alias dictionary match
        3. Fuzzy token similarity scoring (>0.72 threshold)
        4. Fallback to clean geocoded regional market entity
        """
        norm_market = self._normalize_token(raw_market)

        # 1. Exact canonical match
        if norm_market in self._by_name:
            m = self._by_name[norm_market]
            return ResolvedMandi(
                mandi_id=m.mandi_id,
                canonical_name=m.canonical_name,
                state=m.state,
                district=m.district,
                district_lgd_code=m.district_lgd_code,
                latitude=m.latitude,
                longitude=m.longitude,
                is_consumption_hub=m.is_consumption_hub,
                match_type="exact",
                confidence=1.0,
                mandi_cess_pct=m.mandi_cess_pct,
                commission_cap_pct=m.commission_cap_pct,
            )

        # 2. Curated alias dictionary match
        alias_key = raw_market.strip().lower()
        if alias_key in self._ALIASES:
            m_id = self._ALIASES[alias_key]
            m = self._by_id[m_id]
            return ResolvedMandi(
                mandi_id=m.mandi_id,
                canonical_name=m.canonical_name,
                state=m.state,
                district=m.district,
                district_lgd_code=m.district_lgd_code,
                latitude=m.latitude,
                longitude=m.longitude,
                is_consumption_hub=m.is_consumption_hub,
                match_type="alias",
                confidence=0.98,
                mandi_cess_pct=m.mandi_cess_pct,
                commission_cap_pct=m.commission_cap_pct,
            )

        # 3. Fuzzy matching against canonical names and aliases
        best_match_id: Optional[str] = None
        best_ratio: float = 0.0

        for alias, m_id in self._ALIASES.items():
            ratio = SequenceMatcher(None, norm_market, self._normalize_token(alias)).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match_id = m_id

        if best_match_id and best_ratio >= 0.72:
            m = self._by_id[best_match_id]
            return ResolvedMandi(
                mandi_id=m.mandi_id,
                canonical_name=m.canonical_name,
                state=m.state,
                district=m.district,
                district_lgd_code=m.district_lgd_code,
                latitude=m.latitude,
                longitude=m.longitude,
                is_consumption_hub=m.is_consumption_hub,
                match_type="fuzzy",
                confidence=round(best_ratio, 2),
                mandi_cess_pct=m.mandi_cess_pct,
                commission_cap_pct=m.commission_cap_pct,
            )

        # 4. Fallback: Clean, human-readable geocoded regional market
        from src.geo import get_coordinates
        clean_state = (state or "General").strip().title()
        clean_district = (district or "General").strip().title()
        clean_market = raw_market.strip().title()

        slug_market = self._normalize_token(raw_market).replace(" ", "_")[:30]
        slug_district = self._normalize_token(clean_district).replace(" ", "_")[:20]
        m_id = f"mandi_{slug_district}_{slug_market}" if slug_district else f"mandi_{slug_market}"
        lat, lon = get_coordinates(clean_district, clean_state)
        stat_fee = self.get_statutory_fees(clean_state)

        return ResolvedMandi(
            mandi_id=m_id,
            canonical_name=clean_market,
            state=clean_state,
            district=clean_district,
            district_lgd_code=0,
            latitude=lat,
            longitude=lon,
            is_consumption_hub=False,
            match_type="regional",
            confidence=0.70,
            mandi_cess_pct=stat_fee["mandi_cess_pct"],
            commission_cap_pct=stat_fee["commission_cap_pct"],
        )
