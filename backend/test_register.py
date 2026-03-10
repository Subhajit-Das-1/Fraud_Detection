import traceback
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database import engine, SessionLocal, Base
from models import User
from auth import get_password_hash

def test_register():
    print("Testing registration logic...")
    db = SessionLocal()
    try:
        username = "admin_test"
        email = "admin_test@example.com"
        password = "test_password"

        print(f"Checking if user {username} exists...")
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            print("User already exists.")
            return

        print("Hashing password...")
        hashed_pwd = get_password_hash(password)
        
        print("Checking user count...")
        user_count = db.query(User).count()
        is_admin = 1 if user_count == 0 else 0
        print(f"Total users: {user_count}, New user is admin: {is_admin}")

        print("Creating User object...")
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_pwd,
            is_admin=is_admin
        )
        
        print("Adding to DB...")
        db.add(new_user)
        
        print("Committing...")
        db.commit()
        
        print("Refreshing...")
        db.refresh(new_user)
        print(f"Success! Registered user ID: {new_user.id}")
        
    except Exception:
        print("\n--- TRACEBACK ---")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_register()
