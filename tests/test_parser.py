from datetime import date
from decimal import Decimal

import pytest

from invoice_extractor import parse_amount, parse_date, parse_invoice


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.234,56", "1234.56"),
        ("1,234.56", "1234.56"),
        ("1 234,56", "1234.56"),
        ("1234,5", "1234.50"),
        ("1234.56", "1234.56"),
        ("1.234", "1234.00"),
        ("1,234", "1234.00"),
        ("1.234.567,89", "1234567.89"),
        ("€ 45,98", "45.98"),
        ("$2,690.80", "2690.80"),
        ("12", "12.00"),
    ],
)
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", ["", "abc", "€"])
def test_parse_amount_rejects_non_numbers(raw):
    assert parse_amount(raw) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Fecha: 03/10/2026", date(2026, 10, 3)),
        ("Invoice date: 2026-10-07", date(2026, 10, 7)),
        ("15.10.2026", date(2026, 10, 15)),
        ("1-2-2026", date(2026, 2, 1)),
    ],
)
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


def test_parse_date_rejects_impossible_dates():
    assert parse_date("31/02/2026") is None
    assert parse_date("no date here") is None


SPANISH = """Suministros Levante S.L.
FACTURA
Nº Factura: F-2026-0142
Fecha: 03/10/2026
Fecha de vencimiento: 02/11/2026
Base imponible 1.250,00 €
IVA (21%) 262,50 €
Total 1.512,50 €
"""

ENGLISH = """INVOICE
Northwind Office Supplies Ltd
Invoice No: INV-88213
Due date: 2026-11-06
Invoice date: 2026-10-07
Subtotal $2,480.00
Tax (8.5%) $210.80
Total due $2,690.80
"""


def test_spanish_invoice():
    inv = parse_invoice(SPANISH, "a.pdf")
    assert inv.vendor == "Suministros Levante S.L."
    assert inv.number == "F-2026-0142"
    assert inv.issue_date == date(2026, 10, 3)
    assert inv.subtotal == Decimal("1250.00")
    assert inv.tax_rate == Decimal("21.00")
    assert inv.tax == Decimal("262.50")
    assert inv.total == Decimal("1512.50")
    assert inv.currency == "EUR"
    assert inv.ok, inv.issues


def test_english_invoice_skips_title_and_due_date():
    inv = parse_invoice(ENGLISH)
    assert inv.vendor == "Northwind Office Supplies Ltd"
    assert inv.number == "INV-88213"
    assert inv.issue_date == date(2026, 10, 7), "due date must not be taken as issue date"
    assert inv.tax_rate == Decimal("8.50")
    assert inv.total == Decimal("2690.80")
    assert inv.currency == "USD"
    assert inv.ok, inv.issues


def test_subtotal_line_is_not_taken_as_total():
    inv = parse_invoice("Acme\nInvoice no: 1\nDate: 2026-01-01\nSubtotal 100.00\nTotal 121.00")
    assert inv.subtotal == Decimal("100.00")
    assert inv.total == Decimal("121.00")


def test_tax_rate_percentage_is_not_read_as_amount():
    inv = parse_invoice("Acme\nIVA 21% 21,00\nTotal 121,00")
    assert inv.tax == Decimal("21.00")


def test_mismatched_total_is_flagged():
    text = "Acme\nInvoice no: 7\nDate: 2026-01-01\nSubtotal 100.00\nTax 21.00\nTotal 131.00"
    inv = parse_invoice(text)
    assert not inv.ok
    assert any("!= total" in issue for issue in inv.issues)


def test_wrong_tax_rate_is_flagged():
    text = "Acme\nInvoice no: 7\nDate: 2026-01-01\nSubtotal 100.00\nVAT 21% 10.00\nTotal 110.00"
    inv = parse_invoice(text)
    assert any("is not 21.00%" in issue for issue in inv.issues)


def test_rounding_within_tolerance_is_accepted():
    text = "Acme\nInvoice no: 7\nDate: 2026-01-01\nSubtotal 99.99\nTax 21.00\nTotal 121.00"
    assert parse_invoice(text).ok


def test_single_character_invoice_number():
    assert parse_invoice("Acme\nInvoice no: 7\nTotal 1.00").number == "7"


def test_missing_fields_are_listed():
    inv = parse_invoice("Some shop\nTotal 10,00")
    assert "missing number" in inv.issues
    assert "missing issue_date" in inv.issues
    assert "missing total" not in inv.issues


def test_empty_text():
    inv = parse_invoice("")
    assert inv.vendor is None
    assert "missing total" in inv.issues
