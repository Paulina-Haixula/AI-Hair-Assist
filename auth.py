# auth.py
from werkzeug.security import generate_password_hash, check_password_hash
from db import SessionLocal
from models import User

def create_user(name, email, password):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            return None
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        print(f"❌ DB Error in create_user: {e}")
        return None
    finally:
        db.close()

def authenticate_user(email, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
    except Exception as e:
        print(f"❌ DB Error in authenticate_user: {e}")
        return None
    finally:
        db.close()
