"""Process a folder of invoices and flag problems across the whole batch."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .models import Invoice
from .parser import parse_invoice
from .pdf import NoTextError, pdf_text


def process_folder(folder: Path) -> list[Invoice]:
    invoices: list[Invoice] = []
    for path in sorted(folder.glob("*.pdf")):
        try:
            inv = parse_invoice(pdf_text(path), source=path.name)
        except NoTextError as exc:
            inv = Invoice(source=path.name, issues=[str(exc)])
        except Exception as exc:  # a broken file must not stop the batch
            inv = Invoice(source=path.name, issues=[f"could not read file: {exc}"])
        invoices.append(inv)
    flag_duplicates(invoices)
    return invoices


def flag_duplicates(invoices: list[Invoice]) -> None:
    """Same vendor and invoice number twice is almost always a double payment risk."""
    seen: dict[tuple[str, str], list[Invoice]] = defaultdict(list)
    for inv in invoices:
        if inv.vendor and inv.number:
            seen[(inv.vendor.lower(), inv.number.lower())].append(inv)
    for group in seen.values():
        if len(group) > 1:
            names = ", ".join(i.source for i in group)
            for inv in group:
                inv.issues.append(f"duplicate invoice number (files: {names})")
