"""Real, live Weather & Climate Shock adapter using Open-Meteo historical reanalysis API."""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class MandiWeatherAdapter:
    """
    Adapter fetching live and historical rainfall / temperature shocks directly from
    Open-Meteo's free, verified open API (ERA5 reanalysis / IMD grid equivalent).
    Endpoint: https://archive-api.open-meteo.com/v1/archive
    Requires NO API Key. 100% open and live.
    """

    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def get_mandi_rainfall(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Fetch daily precipitation (mm) and max temperature (°C) for Mandi coordinates."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "precipitation_sum,temperature_2m_max",
            "timezone": "Asia/Kolkata",
        }

        try:
            resp = requests.get(self.ARCHIVE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("daily", {})
            return {
                "dates": data.get("time", []),
                "precipitation_mm": data.get("precipitation_sum", []),
                "temperature_max_c": data.get("temperature_2m_max", []),
            }
        except Exception as e:
            logger.error("Failed to fetch weather for coordinates (%s, %s): %s", latitude, longitude, e)
            return {"dates": [], "precipitation_mm": [], "temperature_max_c": []}
