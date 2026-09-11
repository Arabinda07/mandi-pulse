"""Live API adapter for the Open Government Data (data.gov.in) platform."""

from __future__ import annotations
import os
import logging
from typing import List, Optional, Dict, Any
import requests
import urllib3

from src.models import RawCommodityRecord
from src.sources.base import CommoditySource

urllib3.disable_warnings()
logger = logging.getLogger(__name__)


class DataGovInAdapter(CommoditySource):
    """
    Adapter communicating with the official OGD Platform India (data.gov.in).
    
    Verified Real Portals & Endpoints:
    - User Registration: https://www.data.gov.in/user/register
    - Dataset Catalog: https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi
    - API Endpoint: https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
    """

    CATALOG_URL = "https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi"
    REGISTER_URL = "https://www.data.gov.in/user/register"
    BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = (api_key or os.getenv("DATA_GOV_IN_API_KEY", "")).strip()
        if not self.api_key:
            self.api_key = self._load_from_env_file()

    @staticmethod
    def _load_from_env_file() -> str:
        """Scan project root for .env file to extract DATA_GOV_IN_API_KEY."""
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent.parent
        env_file = root / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("DATA_GOV_IN_API_KEY=") and not line.startswith("#"):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
        return ""

    def fetch_records(
        self,
        commodity: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[RawCommodityRecord]:
        """Query api.data.gov.in with pagination and format normalization."""
        if not self.api_key:
            logger.warning(
                "DATA_GOV_IN_API_KEY is not configured.\n"
                "To get an official free key, register at: %s\n"
                "Dataset catalog: %s",
                self.REGISTER_URL,
                self.CATALOG_URL,
            )
            return []

        records: List[RawCommodityRecord] = []
        offset = 0
        page_size = 500

        try:
            while True:
                params: Dict[str, Any] = {
                    "api-key": self.api_key,
                    "format": "json",
                    "offset": offset,
                    "limit": page_size,
                    "filters[commodity]": commodity.capitalize(),
                }
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MandiPulse/1.0"},
                    timeout=25,
                    verify=False,
                )

                if response.status_code == 400:
                    logger.error("data.gov.in returned 400: Check if your API key is valid. Key passed: %s...", self.api_key[:4] if self.api_key else "None")
                    break

                response.raise_for_status()
                payload = response.json()
                raw_rows = payload.get("records", [])
                if not raw_rows:
                    break

                for row in raw_rows:
                    raw_date = row.get("arrival_date", "")
                    iso_date = raw_date
                    if "/" in raw_date:
                        parts = raw_date.split("/")
                        if len(parts) == 3:
                            iso_date = f"{parts[2]}-{parts[1]}-{parts[0]}"

                    def clean_price(val: Any) -> float:
                        try:
                            p = float(val or 0.0)
                            if p <= 1.0:
                                return 0.0
                            if 1.0 < p < 120.0:  # Price entered per kg instead of per quintal
                                return p * 100.0
                            return p
                        except (ValueError, TypeError):
                            return 0.0

                    min_p = clean_price(row.get("min_price"))
                    max_p = clean_price(row.get("max_price"))
                    modal_p = clean_price(row.get("modal_price"))

                    if modal_p <= 0.0:
                        continue

                    if min_p <= 0.0:
                        min_p = modal_p * 0.9
                    if max_p <= 0.0 or max_p < modal_p:
                        max_p = modal_p * 1.1

                    raw_arr = row.get("arrival_tonnes") or row.get("arrivals")
                    try:
                        arr_val = float(raw_arr) if raw_arr else 0.0
                    except (ValueError, TypeError):
                        arr_val = 0.0

                    records.append(
                        RawCommodityRecord(
                            raw_state=row.get("state", "Unknown").strip(),
                            raw_district=row.get("district", "Unknown").strip(),
                            raw_market=row.get("market", "Unknown").strip(),
                            raw_commodity=row.get("commodity", commodity).strip(),
                            raw_variety=row.get("variety", "Normal").strip(),
                            reported_date=iso_date,
                            arrival_tonnes=round(arr_val, 2),
                            min_price=round(min_p, 2),
                            max_price=round(max_p, 2),
                            modal_price=round(modal_p, 2),
                        )
                    )

                offset += len(raw_rows)
                total_available = payload.get("total", 0)
                if len(raw_rows) < page_size or (total_available and offset >= total_available):
                    break

        except requests.exceptions.RequestException as e:
            logger.error("Failed to query data.gov.in: %s", e)

        return records
