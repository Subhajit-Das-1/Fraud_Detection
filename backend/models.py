from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(String(50), index=True)
    seller_gstin = Column(String(15), index=True)
    buyer_gstin = Column(String(15), index=True)
    invoice_amount = Column(Float, nullable=False)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    hsn_code = Column(String(10))
    invoice_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    features = relationship("EngineeredFeature", back_populates="invoice", uselist=False, cascade="all, delete-orphan")
    analysis = relationship("FraudAnalysis", back_populates="invoice", uselist=False, cascade="all, delete-orphan")


class EngineeredFeature(Base):
    __tablename__ = "engineered_features"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True)
    tax_ratio = Column(Float, default=0.0)
    avg_seller_invoice = Column(Float, default=0.0)
    deviation_from_avg = Column(Float, default=0.0)
    transaction_frequency = Column(Integer, default=0)
    seller_risk_history = Column(Float, default=0.0)
    buyer_risk_history = Column(Float, default=0.0)
    invoice_time_gap = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="features")


class FraudAnalysis(Base):
    __tablename__ = "fraud_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True)
    rule_score = Column(Float, default=0.0)
    rule_flags = Column(JSON, default=list)
    ml_score = Column(Float, default=0.0)
    anomaly_prediction = Column(Integer, default=1)  # 1=normal, -1=anomaly
    final_score = Column(Float, default=0.0)
    risk_level = Column(String(10), default="Low")
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    invoice = relationship("Invoice", back_populates="analysis")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    is_active = Column(Integer, default=1)  # 1=True, 0=False
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
