"""Extension point for housing subsidies (for example the Bono del Buen Pagador).

Subsidies are NOT modelled in v1. `NoSubsidy` always returns 0. A later version can
implement `SubsidyProvider` and pass it to `model.simulate(..., subsidy=provider)`;
the amount returned reduces the loan the buyer needs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SubsidyProvider(ABC):
    @abstractmethod
    def amount(self, scenario: Any, price_paid: float) -> float:
        """Subsidy in soles applied at purchase for this scenario."""


class NoSubsidy(SubsidyProvider):
    def amount(self, scenario: Any, price_paid: float) -> float:
        return 0.0
