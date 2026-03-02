from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Invoice Schemas ---
class InvoiceCreate(BaseModel):
    invoice_id: str
    seller_gstin: str
    buyer_gstin: str
    invoice_amount: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    hsn_code: str = ""
    invoice_date: Optional[datetime] = None


class InvoiceResponse(BaseModel):
    id: int
    invoice_id: str
    seller_gstin: str
    buyer_gstin: str
    invoice_amount: float
    cgst: float
    sgst: float
    igst: float
    hsn_code: str
    invoice_date: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class FeatureResponse(BaseModel):
    tax_ratio: float
    avg_seller_invoice: float
    deviation_from_avg: float
    transaction_frequency: int
    seller_risk_history: float
    buyer_risk_history: float
    invoice_time_gap: float

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    rule_score: float
    rule_flags: list
    ml_score: float
    anomaly_prediction: int
    final_score: float
    risk_level: str
    analyzed_at: Optional[datetime]

    class Config:
        from_attributes = True


class InvoiceDetailResponse(BaseModel):
    invoice: InvoiceResponse
    features: Optional[FeatureResponse] = None
    analysis: Optional[AnalysisResponse] = None


class InvoiceListItem(BaseModel):
    id: int
    invoice_id: str
    seller_gstin: str
    buyer_gstin: str
    invoice_amount: float
    total_tax: float
    invoice_date: Optional[datetime]
    risk_level: Optional[str] = None
    final_score: Optional[float] = None


# --- Dashboard Schemas ---
class DashboardStats(BaseModel):
    total_invoices: int
    high_risk: int
    medium_risk: int
    low_risk: int
    fraud_percentage: float
    total_amount: float
    flagged_amount: float


class RiskDistribution(BaseModel):
    risk_level: str
    count: int


class RiskTrend(BaseModel):
    date: str
    high: int
    medium: int
    low: int
    total: int


class SellerHeatmapItem(BaseModel):
    seller_gstin: str
    invoice_count: int
    avg_risk_score: float
    total_amount: float
    risk_level: str
