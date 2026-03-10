import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import Invoice, EngineeredFeature, FraudAnalysis
from rule_engine import run_all_rules
from feature_engineering import compute_all_features
from ml_engine import train_model, predict_anomaly
from risk_scorer import compute_final_score
from datetime import datetime

def debug_analyze():
    db = SessionLocal()
    try:
        print("Step 1: Fetching invoices...")
        invoices = db.query(Invoice).all()
        if not invoices:
            print("No invoices found.")
            return

        print(f"Total invoices: {len(invoices)}")

        print("\nStep 2: Feature Engineering...")
        features = compute_all_features(db, invoices)
        print(f"Features computed: {len(features)}")

        print("\nStep 3: Training ML model...")
        try:
            model = train_model(db)
            print("Model trained successfully.")
        except ValueError as e:
            print(f"Model training skipped: {e}")
            model = None

        print("\nStep 4: ML Predictions...")
        ml_results = predict_anomaly(features, model)
        print(f"Predictions received: {len(ml_results)}")

        print("\nStep 5: Rule Engine + Risk Scoring...")
        analyzed = 0
        for i, inv in enumerate(invoices):
            if i % 50 == 0:
                print(f"Processing invoice {i}...")
            
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

        print("\nStep 6: Committing changes...")
        db.commit()
        print(f"Analysis complete. Total analyzed: {analyzed}")

    except Exception as e:
        print("\n!!! ERROR DETECTED !!!")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    debug_analyze()
