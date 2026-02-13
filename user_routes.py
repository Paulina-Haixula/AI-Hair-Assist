# user_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import SessionLocal
from models import HairSurvey

user_bp = Blueprint("user", __name__, url_prefix="")

@user_bp.route("/user_type/<int:survey_id>")
def user_type(survey_id):
    """Landing: choose New or Returning user."""
    db = SessionLocal()
    survey = db.query(HairSurvey).filter_by(survey_id=survey_id).first()
    db.close()

    user_id = survey.user_id
    print("✅ user: MATCH FOUND →", user_id)
    print("✅ survey: MATCH FOUND →", survey_id)

    return render_template("user_types.html", survey_id=survey_id, user_id=user_id)