"""
GST Fraud Detection System — FastAPI Backend
"""

import io
import csv
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract

from database import engine, get_db, Base
from models import Invoice, EngineeredFeature, FraudAnalysis, User
from schemas import (
    InvoiceCreate, InvoiceResponse, InvoiceDetailResponse, InvoiceListItem,
    DashboardStats, RiskDistribution, RiskTrend, SellerHeatmapItem,
    UserCreate, UserResponse, Token
)
from rule_engine import run_all_rules
from feature_engineering import compute_all_features
from ml_engine import train_model, predict_anomaly, load_model
from risk_scorer import compute_final_score
from generate_data import generate_synthetic_data
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, get_current_admin_user
)
from fastapi.security import OAuth2PasswordRequestForm

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GST Fraud Detection System",
    description="Intelligent GST Fraud Pattern Detection with Rule Engine + ML",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Auth Endpoints ==========

@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pwd = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd,
        is_admin=1 if db.query(User).count() == 0 else 0  # First user is admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return current_user


# ========== Invoice Endpoints ==========

@app.post("/api/invoices", response_model=InvoiceResponse)
def create_invoice(
    invoice: InvoiceCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a single invoice via manual entry."""
    db_invoice = Invoice(
        invoice_id=invoice.invoice_id,
        seller_gstin=invoice.seller_gstin,
        buyer_gstin=invoice.buyer_gstin,
        invoice_amount=invoice.invoice_amount,
        cgst=invoice.cgst,
        sgst=invoice.sgst,
        igst=invoice.igst,
        hsn_code=invoice.hsn_code,
        invoice_date=invoice.invoice_date or datetime.utcnow(),
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


@app.post("/api/invoices/upload-csv")
def upload_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload invoices via CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    count = 0
    errors = []
    for i, row in enumerate(reader):
        try:
            inv = Invoice(
                invoice_id=row.get("invoice_id", f"CSV-{i}"),
                seller_gstin=row.get("seller_gstin", ""),
                buyer_gstin=row.get("buyer_gstin", ""),
                invoice_amount=float(row.get("invoice_amount", 0)),
                cgst=float(row.get("cgst", 0)),
                sgst=float(row.get("sgst", 0)),
                igst=float(row.get("igst", 0)),
                hsn_code=row.get("hsn_code", ""),
                invoice_date=datetime.strptime(row["invoice_date"], "%Y-%m-%d") if row.get("invoice_date") else datetime.utcnow(),
            )
            db.add(inv)
            count += 1
        except Exception as e:
            errors.append({"row": i + 1, "error": str(e)})

    db.commit()
    return {"uploaded": count, "errors": errors}


@app.post("/api/invoices/bulk")
def bulk_create(
    invoices: list[InvoiceCreate], 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk create invoices via JSON array."""
    created = []
    for inv_data in invoices:
        inv = Invoice(
            invoice_id=inv_data.invoice_id,
            seller_gstin=inv_data.seller_gstin,
            buyer_gstin=inv_data.buyer_gstin,
            invoice_amount=inv_data.invoice_amount,
            cgst=inv_data.cgst,
            sgst=inv_data.sgst,
            igst=inv_data.igst,
            hsn_code=inv_data.hsn_code,
            invoice_date=inv_data.invoice_date or datetime.utcnow(),
        )
        db.add(inv)
        created.append(inv)
    db.commit()
    return {"created": len(created)}


@app.get("/api/invoices")
def list_invoices(
    skip: int = 0,
    limit: int = 50,
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List invoices with optional filtering."""
    query = db.query(Invoice)

    if search:
        query = query.filter(
            (Invoice.invoice_id.contains(search)) |
            (Invoice.seller_gstin.contains(search)) |
            (Invoice.buyer_gstin.contains(search))
        )

    invoices = query.order_by(Invoice.id.desc()).offset(skip).limit(limit).all()
    total = query.count()

    result = []
    for inv in invoices:
        total_tax = (inv.cgst or 0) + (inv.sgst or 0) + (inv.igst or 0)
        analysis = db.query(FraudAnalysis).filter(FraudAnalysis.invoice_id == inv.id).first()

        result.append({
            "id": inv.id,
            "invoice_id": inv.invoice_id,
            "seller_gstin": inv.seller_gstin,
            "buyer_gstin": inv.buyer_gstin,
            "invoice_amount": inv.invoice_amount,
            "total_tax": total_tax,
            "invoice_date": inv.invoice_date,
            "risk_level": analysis.risk_level if analysis else None,
            "final_score": analysis.final_score if analysis else None,
        })

    # Filter by risk_level after join
    if risk_level:
        result = [r for r in result if r["risk_level"] == risk_level]

    return {"invoices": result, "total": total}


@app.get("/api/invoices/{invoice_id}")
def get_invoice(
    invoice_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed invoice with features and analysis."""
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    features = db.query(EngineeredFeature).filter(EngineeredFeature.invoice_id == inv.id).first()
    analysis = db.query(FraudAnalysis).filter(FraudAnalysis.invoice_id == inv.id).first()

    return {
        "invoice": {
            "id": inv.id,
            "invoice_id": inv.invoice_id,
            "seller_gstin": inv.seller_gstin,
            "buyer_gstin": inv.buyer_gstin,
            "invoice_amount": inv.invoice_amount,
            "cgst": inv.cgst,
            "sgst": inv.sgst,
            "igst": inv.igst,
            "hsn_code": inv.hsn_code,
            "invoice_date": inv.invoice_date,
            "created_at": inv.created_at,
        },
        "features": {
            "tax_ratio": features.tax_ratio,
            "avg_seller_invoice": features.avg_seller_invoice,
            "deviation_from_avg": features.deviation_from_avg,
            "transaction_frequency": features.transaction_frequency,
            "seller_risk_history": features.seller_risk_history,
            "buyer_risk_history": features.buyer_risk_history,
            "invoice_time_gap": features.invoice_time_gap,
        } if features else None,
        "analysis": {
            "rule_score": analysis.rule_score,
            "rule_flags": analysis.rule_flags,
            "ml_score": analysis.ml_score,
            "anomaly_prediction": analysis.anomaly_prediction,
            "final_score": analysis.final_score,
            "risk_level": analysis.risk_level,
            "analyzed_at": analysis.analyzed_at,
        } if analysis else None,
    }


# ========== Fraud Analysis Endpoints ==========

@app.post("/api/analyze")
def analyze_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Run the full fraud detection pipeline on all invoices."""
    invoices = db.query(Invoice).all()
    if not invoices:
        raise HTTPException(status_code=400, detail="No invoices to analyze")

    # Step 1: Feature Engineering
    features = compute_all_features(db, invoices)

    # Step 2: Train ML model
    try:
        model = train_model(db)
    except ValueError:
        model = None

    # Step 3: ML Predictions
    ml_results = predict_anomaly(features, model)

    # Step 4: Rule Engine + Risk Scoring
    analyzed = 0
    for i, inv in enumerate(invoices):
        # Run rule engine
        rule_score, rule_flags = run_all_rules(db, inv)

        # Get ML score
        ml_score = ml_results[i]["ml_score"]
        prediction = ml_results[i]["prediction"]

        # Compute final score
        final_score, risk_level = compute_final_score(rule_score, ml_score)

        # Store / update analysis
        existing = db.query(FraudAnalysis).filter(FraudAnalysis.invoice_id == inv.id).first()
        if existing:
            existing.rule_score = rule_score
            existing.rule_flags = rule_flags
            existing.ml_score = ml_score
            existing.anomaly_prediction = prediction
            existing.final_score = final_score
            existing.risk_level = risk_level
            existing.analyzed_at = datetime.utcnow()
        else:
            analysis = FraudAnalysis(
                invoice_id=inv.id,
                rule_score=rule_score,
                rule_flags=rule_flags,
                ml_score=ml_score,
                anomaly_prediction=prediction,
                final_score=final_score,
                risk_level=risk_level,
            )
            db.add(analysis)
        analyzed += 1

    db.commit()
    return {"analyzed": analyzed, "message": "Fraud analysis complete"}


@app.post("/api/train-model")
def retrain_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Retrain the Isolation Forest model."""
    try:
        model = train_model(db)
        return {"message": "Model trained successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Data Generation ==========

@app.post("/api/generate-data")
def generate_data(
    count: int = 500, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Generate synthetic GST dataset."""
    result = generate_synthetic_data(db, count)
    return result


# ========== Data Reset ==========

@app.delete("/api/reset-data")
def reset_data(db: Session = Depends(get_db)):
    """Delete all generated data from the database."""
    import os

    # Delete in correct order for FK constraints
    fa_count = db.query(FraudAnalysis).delete()
    ef_count = db.query(EngineeredFeature).delete()
    inv_count = db.query(Invoice).delete()
    db.commit()

    # Remove trained model file
    model_path = os.path.join(os.path.dirname(__file__), "isolation_forest_model.pkl")
    if os.path.exists(model_path):
        os.remove(model_path)

    return {
        "deleted_invoices": inv_count,
        "deleted_features": ef_count,
        "deleted_analyses": fa_count,
        "message": "All data has been reset successfully",
    }


# ========== Dashboard Endpoints ==========

@app.get("/api/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Overview statistics."""
    total = db.query(Invoice).count()

    high = db.query(FraudAnalysis).filter(FraudAnalysis.risk_level == "High").count()
    medium = db.query(FraudAnalysis).filter(FraudAnalysis.risk_level == "Medium").count()
    low = db.query(FraudAnalysis).filter(FraudAnalysis.risk_level == "Low").count()

    total_amount = db.query(func.sum(Invoice.invoice_amount)).scalar() or 0

    # Flagged amount (High + Medium risk invoices)
    flagged_amount = db.query(func.sum(Invoice.invoice_amount)).join(
        FraudAnalysis, FraudAnalysis.invoice_id == Invoice.id
    ).filter(
        FraudAnalysis.risk_level.in_(["High", "Medium"])
    ).scalar() or 0

    fraud_pct = ((high + medium) / total * 100) if total > 0 else 0

    return {
        "total_invoices": total,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "fraud_percentage": round(fraud_pct, 1),
        "total_amount": round(total_amount, 2),
        "flagged_amount": round(flagged_amount, 2),
    }


@app.get("/api/dashboard/risk-distribution")
def risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Risk level distribution."""
    results = db.query(
        FraudAnalysis.risk_level,
        func.count(FraudAnalysis.id)
    ).group_by(FraudAnalysis.risk_level).all()

    return [{"risk_level": r[0], "count": r[1]} for r in results]


@app.get("/api/dashboard/risk-trend")
def risk_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Daily risk trend over time."""
    results = db.query(
        func.date(Invoice.invoice_date).label("date"),
        func.sum(case((FraudAnalysis.risk_level == "High", 1), else_=0)).label("high"),
        func.sum(case((FraudAnalysis.risk_level == "Medium", 1), else_=0)).label("medium"),
        func.sum(case((FraudAnalysis.risk_level == "Low", 1), else_=0)).label("low"),
        func.count(Invoice.id).label("total"),
    ).join(
        FraudAnalysis, FraudAnalysis.invoice_id == Invoice.id
    ).group_by(
        func.date(Invoice.invoice_date)
    ).order_by(
        func.date(Invoice.invoice_date)
    ).all()

    return [
        {"date": str(r.date), "high": r.high, "medium": r.medium, "low": r.low, "total": r.total}
        for r in results
    ]


@app.get("/api/dashboard/seller-heatmap")
def seller_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Seller risk heatmap data."""
    results = db.query(
        Invoice.seller_gstin,
        func.count(Invoice.id).label("invoice_count"),
        func.avg(FraudAnalysis.final_score).label("avg_risk_score"),
        func.sum(Invoice.invoice_amount).label("total_amount"),
    ).join(
        FraudAnalysis, FraudAnalysis.invoice_id == Invoice.id
    ).group_by(
        Invoice.seller_gstin
    ).order_by(
        func.avg(FraudAnalysis.final_score).desc()
    ).limit(30).all()

    data = []
    for r in results:
        avg_score = float(r.avg_risk_score) if r.avg_risk_score else 0
        if avg_score >= 61:
            level = "High"
        elif avg_score >= 31:
            level = "Medium"
        else:
            level = "Low"

        data.append({
            "seller_gstin": r.seller_gstin,
            "invoice_count": r.invoice_count,
            "avg_risk_score": round(avg_score, 2),
            "total_amount": round(float(r.total_amount), 2),
            "risk_level": level,
        })

    return data


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "GST Fraud Detection System"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
