"""Command line: ``invoice-extract <folder> -o invoices.xlsx``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .batch import process_folder
from .export import to_csv, to_xlsx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="invoice-extract",
        description="Extract vendor, number, date and amounts from PDF invoices "
        "into a spreadsheet.",
    )
    ap.add_argument("folder", type=Path, help="folder with PDF invoices")
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("invoices.xlsx"),
        help="output file, .xlsx or .csv (default: invoices.xlsx)",
    )
    args = ap.parse_args(argv)

    if not args.folder.is_dir():
        print(f"error: {args.folder} is not a folder", file=sys.stderr)
        return 2

    invoices = process_folder(args.folder)
    if not invoices:
        print(f"no PDF files in {args.folder}", file=sys.stderr)
        return 2

    if args.out.suffix.lower() == ".csv":
        to_csv(invoices, args.out)
    else:
        to_xlsx(invoices, args.out)

    flagged = [i for i in invoices if not i.ok]
    print(
        f"{len(invoices)} invoices -> {args.out}  ({len(invoices) - len(flagged)} OK, "
        f"{len(flagged)} to check)"
    )
    for inv in flagged:
        print(f"  !! {inv.source}: {'; '.join(inv.issues)}")
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
