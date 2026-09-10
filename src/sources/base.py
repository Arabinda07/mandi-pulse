"""Source seam definition for external and local commodity market adapters."""

from __future__ import annotations
from typing import Protocol, List, Optional
from src.models import RawCommodityRecord


class CommoditySource(Protocol):
    """Port defining the interface for fetching raw commodity market records."""

    def fetch_records(
        self,
        commodity: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[RawCommodityRecord]:
        """Retrieve wholesale arrival and price observations across mandis."""
        ...
