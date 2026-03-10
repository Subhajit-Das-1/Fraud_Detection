import traceback
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database import engine, SessionLocal, Base
from models import User, Invoice, FraudAnalysis, EngineeredFeature

def verify():
    print("Attempting to create tables and initialize mappers...")
    try:
        # This will trigger mapper initialization
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        # Trigger actual query to check if mappers work
        user_count = db.query(User).count()
        print(f"Success! Users in DB: {user_count}")
        db.close()
    except Exception:
        print("\n--- TRACEBACK ---")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify()
