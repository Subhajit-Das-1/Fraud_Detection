"""
Feature Engineering Layer — Compute derived features for each invoice.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta
from models import Invoice, EngineeredFeature, FraudAnalysis


def compute_features(db: Session, invoice: Invoice) -> EngineeredFeature:
    """Compute all derived features for a single invoice."""

    total_tax = (invoice.cgst or 0) + (invoice.sgst or 0) + (invoice.igst or 0)

    # 1. Tax ratio
    tax_ratio = total_tax / invoice.invoice_amount if invoice.invoice_amount > 0 else 0.0

    # 2. Average seller invoice amount
    avg_result = db.query(func.avg(Invoice.invoice_amount)).filter(
        Invoice.seller_gstin == invoice.seller_gstin
    ).scalar()
    avg_seller_invoice = float(avg_result) if avg_result else invoice.invoice_amount

    # 3. Deviation from average
    deviation_from_avg = abs(invoice.invoice_amount - avg_seller_invoice) / avg_seller_invoice if avg_seller_invoice > 0 else 0.0

    # 4. Transaction frequency (last 30 days)
    transaction_frequency = 0
    if invoice.invoice_date:
        thirty_days_ago = invoice.invoice_date - timedelta(days=30)
        transaction_frequency = db.query(Invoice).filter(
            Invoice.seller_gstin == invoice.seller_gstin,
            Invoice.invoice_date >= thirty_days_ago,
            Invoice.invoice_date <= invoice.invoice_date
        ).count()

    # 5. Seller risk history (avg final_score of previous invoices from this seller)
    seller_risk = db.query(func.avg(FraudAnalysis.final_score)).join(Invoice).filter(
        Invoice.seller_gstin == invoice.seller_gstin,
        Invoice.id != invoice.id
    ).scalar()
    seller_risk_history = float(seller_risk) if seller_risk else 0.0

    # 6. Buyer risk history
    buyer_risk = db.query(func.avg(FraudAnalysis.final_score)).join(Invoice).filter(
        Invoice.buyer_gstin == invoice.buyer_gstin,
        Invoice.id != invoice.id
    ).scalar()
    buyer_risk_history = float(buyer_risk) if buyer_risk else 0.0

    # 7. Invoice time gap (days since last invoice from this seller)
    last_invoice = db.query(Invoice).filter(
        Invoice.seller_gstin == invoice.seller_gstin,
        Invoice.id != invoice.id,
        Invoice.invoice_date < invoice.invoice_date if invoice.invoice_date else True
    ).order_by(Invoice.invoice_date.desc()).first()

    invoice_time_gap = 0.0
    if last_invoice and last_invoice.invoice_date and invoice.invoice_date:
        gap = invoice.invoice_date - last_invoice.invoice_date
        invoice_time_gap = max(gap.total_seconds() / 86400.0, 0)  # in days

    feature = EngineeredFeature(
        invoice_id=invoice.id,
        tax_ratio=tax_ratio,
        avg_seller_invoice=avg_seller_invoice,
        deviation_from_avg=deviation_from_avg,
        transaction_frequency=transaction_frequency,
        seller_risk_history=seller_risk_history,
        buyer_risk_history=buyer_risk_history,
        invoice_time_gap=invoice_time_gap
    )

    return feature


def compute_all_features(db: Session, invoices: list[Invoice]) -> list[EngineeredFeature]:
    """Compute features for a batch of invoices."""
    features = []
    for inv in invoices:
        # Remove existing feature if any
        existing = db.query(EngineeredFeature).filter(EngineeredFeature.invoice_id == inv.id).first()
        if existing:
            db.delete(existing)

        feat = compute_features(db, inv)
        db.add(feat)
        features.append(feat)

    db.commit()
    return features
