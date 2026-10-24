"""Turn the text of an invoice into an :class:`Invoice`.

Pure functions, no I/O. Handles English and Spanish labels and both
number styles (``1,234.56`` and ``1.234,56``).
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import Invoice

_AMOUNT = re.compile(r"\d[\d.,\s]*\d|\d")
_DATE_PATTERNS = (
    (re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"), ("y", "m", "d")),
    (re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b"), ("d", "m", "y")),
)

_NUMBER = re.compile(
    r"(?:invoice\s*(?:no\.?|number|#)|n[ºo°]\.?\s*(?:de\s+)?factura|"
    r"factura\s*(?:n[ºo°]\.?|n[uú]mero|num\.?))\s*[:#]?\s*([A-Z0-9](?:[A-Z0-9\-/.]*[A-Z0-9])?)",
    re.IGNORECASE,
)
_DATE_LABEL = re.compile(
    r"\b(?:invoice\s+date|issue\s+date|date|fecha(?:\s+de\s+(?:emisi[oó]n|factura))?)\b",
    re.IGNORECASE,
)
_NOT_ISSUE_DATE = re.compile(r"due|vencimiento|pago|payment", re.IGNORECASE)
_SUBTOTAL = re.compile(r"\b(?:subtotal|sub-total|base\s+imponible|net\s+amount)\b", re.IGNORECASE)
_TAX = re.compile(r"\b(?:vat|iva|tax|impuesto)\b", re.IGNORECASE)
_TAX_RATE = re.compile(r"(\d{1,2}(?:[.,]\d+)?)\s*%")
_TOTAL = re.compile(r"(?<!sub)(?<!sub-)\btotal\b", re.IGNORECASE)
_CURRENCIES = (
    ("€", "EUR"),
    ("EUR", "EUR"),
    ("$", "USD"),
    ("USD", "USD"),
    ("£", "GBP"),
    ("GBP", "GBP"),
)
_TITLE_WORDS = {"invoice", "factura", "tax invoice", "factura simplificada"}


def parse_amount(raw: str) -> Decimal | None:
    """Parse ``1.234,56``, ``1,234.56``, ``1 234,56`` or ``1234`` into a Decimal."""
    s = re.sub(r"[^\d.,-]", "", raw)
    if not s or not any(c.isdigit() for c in s):
        return None
    if "," in s and "." in s:
        decimal_sep = "," if s.rfind(",") > s.rfind(".") else "."
        thousands = "." if decimal_sep == "," else ","
        s = s.replace(thousands, "").replace(decimal_sep, ".")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = f"{head.replace(',', '')}.{tail}" if len(tail) in (1, 2) else s.replace(",", "")
    elif "." in s:
        head, _, tail = s.rpartition(".")
        if len(tail) == 3 or s.count(".") > 1:
            s = s.replace(".", "") if len(tail) == 3 else f"{head.replace('.', '')}.{tail}"
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def parse_date(raw: str) -> date | None:
    for pattern, order in _DATE_PATTERNS:
        match = pattern.search(raw)
        if not match:
            continue
        parts = dict(zip(order, (int(g) for g in match.groups()), strict=True))
        try:
            return date(parts["y"], parts["m"], parts["d"])
        except ValueError:
            return None
    return None


def _last_amount(line: str, after: int = 0) -> Decimal | None:
    tail = _TAX_RATE.sub("", line[after:])
    found = _AMOUNT.findall(tail)
    return parse_amount(found[-1]) if found else None


def _detect_currency(text: str) -> str | None:
    for symbol, code in _CURRENCIES:
        if symbol in text:
            return code
    return None


def parse_invoice(text: str, source: str = "") -> Invoice:
    inv = Invoice(source=source)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for ln in lines:
        if ln.lower() not in _TITLE_WORDS:
            inv.vendor = ln
            break

    for ln in lines:
        if inv.number is None and (m := _NUMBER.search(ln)):
            inv.number = m.group(1)

        if inv.issue_date is None and _DATE_LABEL.search(ln) and not _NOT_ISSUE_DATE.search(ln):
            inv.issue_date = parse_date(ln)

        if inv.subtotal is None and (m := _SUBTOTAL.search(ln)):
            inv.subtotal = _last_amount(ln, m.end())
        elif inv.tax is None and (m := _TAX.search(ln)) and not _NUMBER.search(ln):
            if rate := _TAX_RATE.search(ln):
                inv.tax_rate = parse_amount(rate.group(1))
            inv.tax = _last_amount(ln, m.end())
        elif (m := _TOTAL.search(ln)) and not _SUBTOTAL.search(ln):
            # The last "total" line wins: "Total" usually comes after any partial totals.
            amount = _last_amount(ln, m.end())
            if amount is not None:
                inv.total = amount

    inv.currency = _detect_currency(text)
    inv.validate()
    return inv
