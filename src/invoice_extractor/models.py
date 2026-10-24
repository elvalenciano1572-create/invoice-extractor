"""Data model for an extracted invoice."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

# Totals may differ by rounding on each line; anything above this is a real mismatch.
TOLERANCE = Decimal("0.02")


@dataclass
class Invoice:
    source: str
    vendor: str | None = None
    number: str | None = None
    issue_date: date | None = None
    subtotal: Decimal | None = None
    tax_rate: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    currency: str | None = None
    issues: list[str] = field(default_factory=list)

    REQUIRED = ("vendor", "number", "issue_date", "total")

    def validate(self) -> None:
        """Fill ``issues`` with everything a person should double-check."""
        self.issues = [f"missing {name}" for name in self.REQUIRED if getattr(self, name) is None]

        if self.subtotal is not None and self.tax is not None and self.total is not None:
            diff = abs(self.subtotal + self.tax - self.total)
            if diff > TOLERANCE:
                self.issues.append(
                    f"subtotal {self.subtotal} + tax {self.tax} != total {self.total}"
                )

        if self.subtotal is not None and self.tax_rate is not None and self.tax is not None:
            expected = (self.subtotal * self.tax_rate / 100).quantize(Decimal("0.01"))
            if abs(expected - self.tax) > TOLERANCE:
                self.issues.append(f"tax {self.tax} is not {self.tax_rate}% of {self.subtotal}")

    @property
    def ok(self) -> bool:
        return not self.issues
