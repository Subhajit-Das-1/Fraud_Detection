"""
Synthetic GST Dataset Generator — Creates ~500 invoices with ~15% planted fraud patterns.
"""

import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Invoice


# Valid GSTIN state codes
STATE_CODES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
               "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
               "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]

# Sample HSN codes
HSN_CODES = ["8471", "6109", "3004", "8517", "2710", "3401", "6203", "8504", "7308", "3926"]

# Company name parts for generating GSTINs
COMPANY_PARTS = list(string.ascii_uppercase)


def _generate_gstin(valid: bool = True) -> str:
    """Generate a random GSTIN (valid or invalid format)."""
    if valid:
        state = random.choice(STATE_CODES)
        pan = "".join(random.choices(string.ascii_uppercase, k=5))
        pan += "".join(random.choices(string.digits, k=4))
        pan += random.choice(string.ascii_uppercase)
        entity = random.choice(string.ascii_uppercase + string.digits)
        checksum = random.choice(string.ascii_uppercase + string.digits)
        return f"{state}{pan}{entity}Z{checksum}"
    else:
        # Generate invalid GSTIN
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=15))


def _generate_invoice_id(index: int) -> str:
    """Generate a unique invoice ID."""
    prefix = random.choice(["INV", "GST", "TAX", "BIL"])
    return f"{prefix}-{2024}-{index:06d}"


def generate_synthetic_data(db: Session, count: int = 500) -> dict:
    """
    Generate synthetic GST invoices with planted fraud.
    ~85% normal, ~15% various fraud patterns.
    """
    # Generate a pool of seller/buyer GSTINs
    seller_pool = [_generate_gstin(True) for _ in range(30)]
    buyer_pool = [_generate_gstin(True) for _ in range(50)]

    invoices = []
    start_date = datetime(2024, 1, 1)
    fraud_count = 0

    for i in range(count):
        is_fraud = random.random() < 0.15
        fraud_type = None

        if is_fraud:
            fraud_type = random.choice(["tax_mismatch", "duplicate", "circular",
                                         "invalid_gstin", "abnormal_ratio", "high_frequency"])
            fraud_count += 1

        # Base invoice
        seller = random.choice(seller_pool)
        buyer = random.choice(buyer_pool)
        while buyer == seller:
            buyer = random.choice(buyer_pool)

        amount = round(random.uniform(1000, 500000), 2)
        date = start_date + timedelta(days=random.randint(0, 365))

        # Normal tax calculation (18%)
        if random.random() < 0.5:
            # Intra-state (CGST+SGST)
            cgst = round(amount * 0.09, 2)
            sgst = round(amount * 0.09, 2)
            igst = 0.0
        else:
            # Inter-state (IGST)
            cgst = 0.0
            sgst = 0.0
            igst = round(amount * 0.18, 2)

        invoice_id = _generate_invoice_id(i)
        hsn = random.choice(HSN_CODES)

        # Apply fraud patterns
        if fraud_type == "tax_mismatch":
            # Significantly wrong tax
            multiplier = random.choice([0.01, 0.05, 0.35, 0.50])
            if igst > 0:
                igst = round(amount * multiplier, 2)
            else:
                cgst = round(amount * multiplier / 2, 2)
                sgst = round(amount * multiplier / 2, 2)

        elif fraud_type == "duplicate":
            # Use an existing invoice's ID
            if invoices:
                existing = random.choice(invoices)
                invoice_id = existing["invoice_id"]
                seller = existing["seller_gstin"]
                buyer = existing["buyer_gstin"]

        elif fraud_type == "circular":
            # Swap seller/buyer to create circular pattern
            if invoices:
                existing = random.choice(invoices[-20:])
                seller = existing["buyer_gstin"]
                buyer = existing["seller_gstin"]

        elif fraud_type == "invalid_gstin":
            if random.random() < 0.5:
                seller = _generate_gstin(False)
            else:
                buyer = _generate_gstin(False)

        elif fraud_type == "abnormal_ratio":
            # Very high or zero tax
            if random.random() < 0.5:
                cgst = round(amount * 0.25, 2)
                sgst = round(amount * 0.25, 2)
                igst = 0.0
            else:
                cgst = 0.0
                sgst = 0.0
                igst = 0.0

        elif fraud_type == "high_frequency":
            # Use same seller for many invoices in short period
            seller = seller_pool[0]  # Always use first seller
            date = start_date + timedelta(days=random.randint(0, 15))

        inv_data = {
            "invoice_id": invoice_id,
            "seller_gstin": seller,
            "buyer_gstin": buyer,
            "invoice_amount": amount,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "hsn_code": hsn,
            "invoice_date": date,
        }
        invoices.append(inv_data)

    # Insert into database
    db_invoices = []
    for inv_data in invoices:
        inv = Invoice(**inv_data)
        db.add(inv)
        db_invoices.append(inv)

    db.commit()

    return {
        "total_generated": count,
        "fraud_planted": fraud_count,
        "fraud_percentage": round(fraud_count / count * 100, 1)
    }
