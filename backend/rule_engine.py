"""
Rule Engine — 6 deterministic fraud detection rules.
Each rule returns a score (0-20) and a flag description.
Total rule_score is capped at 100.
"""

import re
from datetime import timedelta
from sqlalchemy.orm import Session
from models import Invoice


GSTIN_PATTERN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$")


def check_gstin_format(invoice: Invoice) -> tuple[float, str | None]:
    """Rule 1: Validate GSTIN format for both seller and buyer."""
    flags = []
    score = 0.0

    if not GSTIN_PATTERN.match(invoice.seller_gstin or ""):
        flags.append("Invalid seller GSTIN format")
        score += 10
    if not GSTIN_PATTERN.match(invoice.buyer_gstin or ""):
        flags.append("Invalid buyer GSTIN format")
        score += 10

    return score, flags


def check_tax_mismatch(invoice: Invoice) -> tuple[float, list]:
    """Rule 2: Check if tax deviates significantly from expected 18%."""
    actual_tax = (invoice.cgst or 0) + (invoice.sgst or 0) + (invoice.igst or 0)
    expected_tax = invoice.invoice_amount * 0.18
    flags = []
    score = 0.0

    if expected_tax > 0:
        deviation = abs(actual_tax - expected_tax) / expected_tax
        if deviation > 0.5:  # >50% deviation
            score = 20
            flags.append(f"Major tax mismatch: expected ₹{expected_tax:.2f}, got ₹{actual_tax:.2f} ({deviation*100:.0f}% off)")
        elif deviation > 0.2:  # >20% deviation
            score = 10
            flags.append(f"Tax mismatch: expected ₹{expected_tax:.2f}, got ₹{actual_tax:.2f} ({deviation*100:.0f}% off)")

    return score, flags


def check_duplicate_invoice(db: Session, invoice: Invoice) -> tuple[float, list]:
    """Rule 3: Check for duplicate invoice_id + seller_gstin + buyer_gstin."""
    duplicates = db.query(Invoice).filter(
        Invoice.invoice_id == invoice.invoice_id,
        Invoice.seller_gstin == invoice.seller_gstin,
        Invoice.buyer_gstin == invoice.buyer_gstin,
        Invoice.id != invoice.id
    ).count()

    if duplicates > 0:
        return 20, [f"Duplicate invoice detected ({duplicates} copies found)"]
    return 0, []


def check_abnormal_tax_ratio(invoice: Invoice) -> tuple[float, list]:
    """Rule 4: Flag invoices with tax ratio outside normal range [1%, 30%]."""
    total_tax = (invoice.cgst or 0) + (invoice.sgst or 0) + (invoice.igst or 0)
    if invoice.invoice_amount <= 0:
        return 15, ["Zero or negative invoice amount"]

    ratio = total_tax / invoice.invoice_amount
    if ratio > 0.30:
        return 15, [f"Abnormally high tax ratio: {ratio*100:.1f}%"]
    elif ratio < 0.01 and total_tax > 0:
        return 10, [f"Suspiciously low tax ratio: {ratio*100:.1f}%"]
    elif total_tax == 0:
        return 15, ["Zero tax on invoice"]
    return 0, []


def check_unusual_frequency(db: Session, invoice: Invoice) -> tuple[float, list]:
    """Rule 5: Flag sellers with unusually high transaction frequency (>50 in 30 days)."""
    if not invoice.invoice_date:
        return 0, []

    thirty_days_ago = invoice.invoice_date - timedelta(days=30)
    count = db.query(Invoice).filter(
        Invoice.seller_gstin == invoice.seller_gstin,
        Invoice.invoice_date >= thirty_days_ago,
        Invoice.invoice_date <= invoice.invoice_date
    ).count()

    if count > 50:
        return 15, [f"Unusual frequency: {count} invoices from this seller in 30 days"]
    elif count > 30:
        return 8, [f"High frequency: {count} invoices from this seller in 30 days"]
    return 0, []


def check_circular_trading(db: Session, invoice: Invoice) -> tuple[float, list]:
    """Rule 6: Detect circular trading patterns (A sells to B AND B sells to A)."""
    reverse = db.query(Invoice).filter(
        Invoice.seller_gstin == invoice.buyer_gstin,
        Invoice.buyer_gstin == invoice.seller_gstin
    ).count()

    if reverse > 0:
        return 20, [f"Circular trading pattern detected: {reverse} reverse transactions found"]
    return 0, []


def run_all_rules(db: Session, invoice: Invoice) -> tuple[float, list]:
    """Execute all 6 rules and return combined score + flags."""
    total_score = 0.0
    all_flags = []

    rules = [
        check_gstin_format(invoice),
        check_tax_mismatch(invoice),
        check_duplicate_invoice(db, invoice),
        check_abnormal_tax_ratio(invoice),
        check_unusual_frequency(db, invoice),
        check_circular_trading(db, invoice),
    ]

    for score, flags in rules:
        total_score += score
        all_flags.extend(flags)

    # Cap at 100
    total_score = min(total_score, 100.0)
    return total_score, all_flags
