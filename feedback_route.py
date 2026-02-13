#feedback route.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import SessionLocal
from models import Recommendation, Feedback, HairSurvey
import json

feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback_bp.route("/<int:survey_id>")
def feedback_page(survey_id):
    db = SessionLocal()
    try:
        # ➤ Fetch the survey
        survey = db.query(HairSurvey).filter_by(survey_id=survey_id).first()
        if not survey:
            flash("Survey not found", "warning")
            return redirect(url_for("home"))

        user_id = survey.user_id

        # ➤ Get the last 4 saved recommendations
        results = (
            db.query(Recommendation)
            .filter_by(user_id=user_id)
            .order_by(Recommendation.rec_id.desc())
            .limit(4)
            .all()
        )

        if not results:
            flash("No previous recommendations found", "warning")
            return redirect(url_for("home"))

        records = []

        # ───────────────────────────────────────────────
        # FORMAT EACH RECOMMENDATION FOR DISPLAY
        # ───────────────────────────────────────────────
        for rec in results:

            # load JSON safely
            try:
                data_json = json.loads(rec.recommendation_json)
            except:
                data_json = {}

            formatted = {
                "rec_id": rec.rec_id,
                "type": None,
                "prediction": None,              # first column
                "model_prediction": rec.model_prediction,   # second column
                "recommendation": None           # third column
            }

            # MODEL 1 — DNN Health
            if rec.model_id == 1:
                formatted["type"] = "DNN Hair Health"
                formatted["prediction"] = data_json.get("score", "N/A")
                formatted["recommendation"] = json.dumps(data_json, indent=2)

            # MODEL 2 — Porosity
            elif rec.model_id == 2:
                formatted["type"] = "Porosity"
                formatted["prediction"] = data_json.get("description", "Unknown")
                formatted["recommendation"] = ", ".join(data_json.get("care_tips", []))

            # MODEL 3 — Breakage
            elif rec.model_id == 3:
                formatted["type"] = "Breakage"
                formatted["prediction"] = data_json.get("Why", "Unknown")
                formatted["recommendation"] = data_json.get("Recommendation", "")

            # MODEL 4 — Disease Detector  (your example)
            elif rec.model_id == 4:
                formatted["type"] = "Disease Detector"
                formatted["prediction"] = data_json.get("Why", "Unknown")
                formatted["recommendation"] = data_json.get("Recommendation", "")

            # fallback
            else:
                formatted["type"] = "Unknown Model"

            records.append(formatted)

        return render_template("feedback.html", records=records, user_id=user_id)

    except Exception as e:
        db.rollback()
        print("❌ error in feedback_page:", e)
        flash("Error loading feedback page", "danger")
        return redirect(url_for("home"))

    finally:
        db.close()



# ================= 2. SUBMIT FEEDBACK ================= #
@feedback_bp.route("/submit/<int:user_id>", methods=["POST"])
def submit_feedback(user_id):
    db = SessionLocal()
    try:
        for key, value in request.form.items():
            if key.startswith("rec_"):
                rec_id_str = key.split("_")[1].strip()
                if not rec_id_str.isdigit():
                    continue

                rec_id = int(rec_id_str)
                rating = int(value)

                # Save feedback
                fb = Feedback(
                    user_id=user_id,
                    rec_id=rec_id,
                    rating=rating
                )
                db.add(fb)
                db.commit()

                # Fetch related recommendation
                rec = db.query(Recommendation).filter_by(rec_id=rec_id).first()

                # If thumbs down → increment iteration
                if rating == 0:
                    rec.iteration = (rec.iteration or 1) + 1
                    db.commit()

        flash("Feedback submitted successfully!", "success")
        return redirect(url_for("recommend.improved_recommendation", user_id=user_id))

    except Exception as e:
        db.rollback()
        print("❌ Error:", e)
        flash("Error submitting feedback.", "danger")
        return redirect(url_for("home"))
    finally:
        db.close()




# ================= 3. FETCH LATEST SURVEY ID ================= #
def get_latest_survey(user_id):
    db = SessionLocal()
    survey = (
        db.query(HairSurvey)
        .filter_by(user_id=user_id)
        .order_by(HairSurvey.survey_id.desc())
        .first()
    )
    db.close()
    return survey.survey_id
