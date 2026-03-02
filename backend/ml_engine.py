"""
ML Engine — Isolation Forest anomaly detection.
Trains on engineered features, returns normalized anomaly scores (0-100).
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from models import EngineeredFeature

MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest_model.pkl")

FEATURE_COLUMNS = [
    "tax_ratio",
    "avg_seller_invoice",
    "deviation_from_avg",
    "transaction_frequency",
    "seller_risk_history",
    "buyer_risk_history",
    "invoice_time_gap"
]


def _extract_feature_matrix(features: list[EngineeredFeature]) -> np.ndarray:
    """Convert EngineeredFeature list to numpy matrix."""
    matrix = []
    for f in features:
        row = [
            f.tax_ratio or 0,
            f.avg_seller_invoice or 0,
            f.deviation_from_avg or 0,
            f.transaction_frequency or 0,
            f.seller_risk_history or 0,
            f.buyer_risk_history or 0,
            f.invoice_time_gap or 0
        ]
        matrix.append(row)
    return np.array(matrix)


def train_model(db: Session, contamination: float = 0.15) -> IsolationForest:
    """Train Isolation Forest on all available engineered features."""
    all_features = db.query(EngineeredFeature).all()
    if len(all_features) < 10:
        raise ValueError("Not enough data to train model (need at least 10 records)")

    X = _extract_feature_matrix(all_features)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    model.fit(X)

    # Save model
    joblib.dump(model, MODEL_PATH)
    return model


def load_model() -> IsolationForest | None:
    """Load persisted model."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def predict_anomaly(features: list[EngineeredFeature], model: IsolationForest = None) -> list[dict]:
    """
    Predict anomaly scores for a list of features.
    Returns list of { 'ml_score': 0-100, 'prediction': 1 or -1 }
    """
    if model is None:
        model = load_model()
    if model is None:
        # No trained model, return neutral scores
        return [{"ml_score": 25.0, "prediction": 1} for _ in features]

    X = _extract_feature_matrix(features)
    predictions = model.predict(X)
    raw_scores = model.decision_function(X)

    # Normalize decision_function scores to 0-100
    # decision_function returns negative for anomalies, positive for normal
    # We invert and normalize: more negative = higher risk
    min_score = raw_scores.min()
    max_score = raw_scores.max()
    score_range = max_score - min_score if max_score != min_score else 1.0

    results = []
    for i in range(len(features)):
        # Invert: lower decision score → higher risk score
        normalized = (1 - (raw_scores[i] - min_score) / score_range) * 100
        normalized = max(0, min(100, normalized))
        results.append({
            "ml_score": round(float(normalized), 2),
            "prediction": int(predictions[i])
        })

    return results
