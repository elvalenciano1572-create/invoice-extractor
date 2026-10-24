"""Generate the sample invoices used by the demo and the tests.

All vendors and amounts are invented. Run: ``python examples/make_samples.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAMPLES: dict[str, list[str]] = {
    # Clean Spanish invoice, European number format
    "suministros_levante.pdf": [
        "Suministros Levante S.L.",
        "C/ Colón 12, 46004 Valencia",
        "FACTURA",
        "Nº Factura: F-2026-0142",
        "Fecha: 03/10/2026",
        "Fecha de vencimiento: 02/11/2026",
        "Papel A4 (50 cajas)          1.250,00 €",
        "Base imponible               1.250,00 €",
        "IVA (21%)                      262,50 €",
        "Total                        1.512,50 €",
    ],
    # Clean English invoice, US number format
    "northwind_office.pdf": [
        "Northwind Office Supplies Ltd",
        "INVOICE",
        "Invoice No: INV-88213",
        "Invoice date: 2026-10-07",
        "Due date: 2026-11-06",
        "Subtotal                 $2,480.00",
        "Tax (8.5%)                 $210.80",
        "Total due                $2,690.80",
    ],
    # Total does not add up: must be flagged, not silently accepted
    "imprenta_turia.pdf": [
        "Imprenta Turia",
        "Factura número: 2026/317",
        "Fecha de emisión: 15.10.2026",
        "Base imponible     640,00",
        "IVA 21%            134,40",
        "Total a pagar      784,40 EUR",
    ],
    # Same vendor and number as the first one: a double-payment risk
    "suministros_levante_reenvio.pdf": [
        "Suministros Levante S.L.",
        "FACTURA",
        "Nº Factura: F-2026-0142",
        "Fecha: 03/10/2026",
        "Base imponible               1.250,00 €",
        "IVA (21%)                      262,50 €",
        "Total                        1.512,50 €",
    ],
    # No issue date anywhere
    "cafeteria_ruzafa.pdf": [
        "Cafetería Ruzafa",
        "Factura simplificada",
        "Factura nº: 0098",
        "Base imponible     41,80 €",
        "IVA (10%)           4,18 €",
        "Total              45,98 €",
    ],
}

SCANNED = "escaneada.pdf"  # image-only PDF, no text layer


def write_pdf(path: Path, lines: list[str]) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800
    for line in lines:
        c.drawString(60, y, line)
        y -= 22
    c.save()


def write_scanned(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.rect(60, 600, 400, 200, fill=1)
    c.save()


def generate(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, lines in SAMPLES.items():
        write_pdf(folder / name, lines)
    write_scanned(folder / SCANNED)


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "invoices"
    generate(target)
    print(f"{len(SAMPLES) + 1} sample invoices written to {target}")
