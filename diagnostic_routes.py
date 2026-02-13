# diagnostic_routes.py
import os
import uuid
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

from db import SessionLocal
from models import HairSurvey, Recommendation, ModelVersion
from feature_engineering import load_models

import numpy as np
from PIL import Image


diagnostic_bp = Blueprint("diagnostic", __name__)

# -------------------------
#   CONFIG
# -------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
UPLOAD_FOLDER = "static/uploads"


# -------------------------
#  HELPERS
# -------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path):
    """
    Must match your real disease model pipeline.
    Default assumptions:
      - RGB
      - 224x224
      - /255
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    arr = np.array(img).astype("float32") / 255.0
    return np.expand_dims(arr, axis=0)


# ============================================================
#  1) AFTER PAGE 5 → Ask if User wants Diagnostic (NEW/RETURN)
# ============================================================
@diagnostic_bp.route("/diagnostic_choice/<int:survey_id>")
def diagnostic_choice(survey_id):

    db = SessionLocal()
    survey = db.query(HairSurvey).filter_by(survey_id=survey_id).first()
    db.close()

    if not survey:
        flash("Survey not found.", "error")
        return redirect(url_for("survey.page1"))

    # Returning user detection
    is_returning = survey.user_id is not None

    return render_template(
        "diagnostic_choice.html",
        survey_id=survey_id,
        is_returning=is_returning,
    )


# ============================================================
#  2) SHOW IMAGE UPLOAD PAGE
# ============================================================
@diagnostic_bp.route("/diagnostic_upload/<int:survey_id>")
def diagnostic_upload(survey_id):
    return render_template("diagnostic_upload.html", survey_id=survey_id)

# ============================================================
#  3) SKIP TO ASK IF USER NEW OR RETURNED USER
# ============================================================
@diagnostic_bp.route("/diagnostic_skip/<int:survey_id>")
def diagnostic_skip(survey_id):
# Go to choose new user/return user?
    return render_template("user_types.html", survey_id=survey_id)

# ============================================================
#  4) UPLOADING IMAGE
# ============================================================

@diagnostic_bp.route("/imagesaved/<int:survey_id>", methods=["POST"])
def imagesaved(survey_id):
    survey_id = request.form.get("survey_id")
    file = request.files.get("image_file")

    if not file:
        return render_template(
            "diagnostic_upload.html",
            survey_id=survey_id,
            error="No image selected"
        )

    # save file with name = survey_id.jpg
    filename = f"{survey_id}.jpg"
    save_path = os.path.join("static", "uploads", filename)
    file.save(save_path)

    # After saving → redirect to user_types.html
    return redirect(url_for("user.user_type", survey_id=survey_id))

# ============================================================
#  5) PROCESS IMAGE + RUN MODEL + SAVE RECOMMENDATION
# ============================================================
@diagnostic_bp.route("/diagnostic_process/<int:survey_id>", methods=["POST"])
def diagnostic_process(survey_id):

    if "image" not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("diagnostic.diagnostic_upload", survey_id=survey_id))

    file = request.files["image"]

    if file.filename == "":
        flash("No selected file.", "error")
        return redirect(url_for("diagnostic.diagnostic_upload", survey_id=survey_id))

    if not allowed_file(file.filename):
        flash("Invalid image format.", "error")
        return redirect(url_for("diagnostic.diagnostic_upload", survey_id=survey_id))

    # Ensure folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Save file
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Preprocess
    arr = preprocess_image(filepath)

    # Load disease model
    models = load_models()
    disease_model = models.get("disease_model")

    if disease_model is None:
        flash("Disease diagnostic model not loaded.", "error")
        return redirect(url_for("diagnostic.diagnostic_upload", survey_id=survey_id))

    # Run prediction
    pred = disease_model.predict(arr)
    disease_score = float(pred[0][0])

    # ---------------------------------------------------------
    #  SAVE DIAGNOSTIC OUTPUT AS A Recommendation ENTRY
    # ---------------------------------------------------------
    db = SessionLocal()

    model_ver = (
        db.query(ModelVersion)
        .filter_by(model_name="Disease Diagnostic", model_type="diagnostic")
        .order_by(ModelVersion.trained_on.desc())
        .first()
    )

    if not model_ver:
        flash("Diagnostic model metadata missing in DB.", "error")
        db.close()
        return redirect(url_for("diagnostic.diagnostic_upload", survey_id=survey_id))

    rec = Recommendation(
        survey_id=survey_id,
        model_id=model_ver.model_id,
        recommendation_json={
            "diagnostic_score": disease_score,
            "confidence": round(disease_score * 100, 2),
            "image_file": filename,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    db.add(rec)
    db.commit()
    rec_id = rec.rec_id
    db.close()

    return redirect(url_for("diagnostic.diagnostic_result", rec_id=rec_id))


# ============================================================
#  4) SHOW DIAGNOSTIC RESULT PAGE
# ============================================================
@diagnostic_bp.route("/diagnostic_result/<int:rec_id>")
def diagnostic_result(rec_id):

    db = SessionLocal()
    rec = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.model))
        .filter_by(rec_id=rec_id)
        .first()
    )
    db.close()

    if not rec:
        flash("Diagnostic result not found.", "error")
        return redirect("/")

    return render_template("diagnostic_result.html", rec=rec)
