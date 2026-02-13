# admin_routes.py
from flask import Blueprint, render_template, request
from db import SessionLocal
from models import Recommendation, Feedback, Product, ModelVersion
from sqlalchemy import desc

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
def dashboard():
    db = SessionLocal()
    try:
        recs = db.query(Recommendation).order_by(desc(Recommendation.created_at)).limit(50).all()
        feedbacks = db.query(Feedback).order_by(desc(Feedback.created_at)).limit(50).all()
        models = db.query(ModelVersion).all()
        return render_template("admin_dashboard.html", recs=recs, feedbacks=feedbacks, models=models)
    finally:
        db.close()
