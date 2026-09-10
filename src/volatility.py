"""Mathematical and statistical calculations for the Dual-Pillar Volatility Engine."""

from __future__ import annotations
import math
from typing import List, Sequence, Tuple, Dict


class VolatilityEngine:
    """Pure mathematical and statistical computations for food supply chain volatility."""

    @staticmethod
    def compute_arrival_shock(current_volume: float, historical_volumes: Sequence[float]) -> float:
        """
        Compute the Arrival Shock Anomaly (Z-score) against a historical baseline.
        Negative Z indicates a supply slump. Z < -1.5 is a critical supply shock.
        """
        if not historical_volumes:
            return 0.0

        n = len(historical_volumes)
        mean = sum(historical_volumes) / n

        variance = sum((x - mean) ** 2 for x in historical_volumes) / n
        std_dev = math.sqrt(variance)

        # Minimum threshold to prevent division by zero or inflated Z on tiny volumes
        if std_dev < 1e-4:
            return 0.0

        z_score = (current_volume - mean) / std_dev
        return round(z_score, 3)

    @staticmethod
    def compute_spatial_dispersion(prices: Sequence[float]) -> float:
        """
        Compute Spatial Price Dispersion using the Coefficient of Variation (CV = sigma / mu).
        Higher CV (> 0.25) signifies inter-market friction, transport failure, or local hoarding.
        """
        valid_prices = [p for p in prices if p > 0]
        if len(valid_prices) < 2:
            return 0.0

        n = len(valid_prices)
        mean = sum(valid_prices) / n
        if mean <= 0:
            return 0.0

        variance = sum((p - mean) ** 2 for p in valid_prices) / n
        std_dev = math.sqrt(variance)

        cv = std_dev / mean
        return round(cv, 4)

    @staticmethod
    def evaluate_corridor_stress(
        origin_price: float,
        terminal_price: float,
        origin_arrival_z: float,
    ) -> Tuple[float, float, str]:
        """
        Evaluate corridor price spread and classify supply-chain stress level.
        Returns: (spread_inr, spread_pct, stress_level)
        """
        if origin_price <= 0:
            return 0.0, 0.0, "NORMAL"

        spread_inr = terminal_price - origin_price
        spread_pct = round((spread_inr / origin_price) * 100, 1)

        # Stress classification based on both terminal spread and farmgate arrival slump
        if spread_pct > 90.0 and origin_arrival_z < -1.5:
            stress = "SEVERE"
        elif spread_pct > 65.0 or origin_arrival_z < -1.8:
            stress = "HIGH"
        elif spread_pct > 40.0 or origin_arrival_z < -1.0:
            stress = "MODERATE"
        else:
            stress = "NORMAL"

        return round(spread_inr, 2), spread_pct, stress
