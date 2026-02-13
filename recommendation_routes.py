# recommendation_routes.py
from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from models import  ModelRule, HairSurvey, Recommendation
from db import SessionLocal
from feature_engineering import encode_survey_data, load_models
from predictions import recommend_ingredients_grouped, predict_dnn, predict_disease, predict_porosity, predict_breakage
import json
from datetime import datetime, UTC
from flask import render_template


recommend_bp = Blueprint("recommend", __name__, url_prefix="/recommend")

LABEL_MAP = {
    "porosity_model": { 0: "low", 1: "medium", 2: "high"
    },
    "breakage_model": { 0: "Extreme- High Breakage", 1: "Extreme- Low Breakage",
        2: "High Breakage", 3: "Low Breakage",4: "Medium Breakage"
    },
    "dnn_model": { 3: "Healthy", 2: "Moisturized",
        1: "Dry", 0: "Damaged"
    },

    "disease_model": { 0: 'Alopecia Areata', 1: 'Contact Dermatitis', 2: 'Folliculitis',
        3: 'Head Lice', 4: 'Lichen Planus', 5: 'Male Pattern Baldness', 6: 'Psoriasis',
        7: 'Seborrheic Dermatitis', 8: 'Telogen Effluvium', 9: 'Tinea Capitis'
    }
}

def fetch_rule(model_type, cls_index):
    if cls_index is None:
        return None

    db = SessionLocal()
    try:
        # get label name e.g. 3 → "Healthy"
        label = LABEL_MAP.get(model_type, {}).get(cls_index)

        print("\n🔍 MODEL TYPE:", model_type)
        print("🔍 CLASS INDEX:", cls_index)
        print("🔍 LABEL MAP RESULT:", label)

        row = db.query(ModelRule).filter_by(rule_name=model_type).first()

        if not row:
            print("❌ No rule row found in DB")
            return None

        data = row.rule_json  # already dict from SQLAlchemy

        print("📌 AVAILABLE KEYS IN JSON:", list(data.keys()))

        # fallback to key as string or index if needed
        result = data.get(label) or data.get(str(label)) or data.get(cls_index)

        if result:
            print("✅ MATCH FOUND →", result)
            return result
        else:
            print(f"⚠ NO MATCH FOR '{label}' (or '{str(label)}')")
            return None

    finally:
        db.close()

#@recommend_bp.route("/build_all_recommendations/<int:survey_id>")
def build_all_recommendations(models, survey):
    # Run predictions
    dnn_cls = predict_dnn(models, survey)
    por_cls = predict_porosity(models, survey)             # numeric
    brk_cls = predict_breakage(models, survey)             # numeric
    dis_cls = predict_disease(models, survey.survey_id)    # string/integer depending on model

    return {
        "classes": {
            "dnn": dnn_cls,
            "porosity": por_cls,
            "breakage": brk_cls,
            "disease": dis_cls
        },
        "labels": {
            "dnn": LABEL_MAP["dnn_model"].get(dnn_cls),
            "porosity": LABEL_MAP["porosity_model"].get(por_cls),
            "breakage": LABEL_MAP["breakage_model"].get(brk_cls),
            "disease": LABEL_MAP["disease_model"].get(dis_cls)
        },
        "recommendations": {
            "dnn": recommend_ingredients_grouped("dnn_model",dnn_cls, top_n=3),
            "porosity": fetch_rule("porosity_model", por_cls),
            "breakage": fetch_rule("breakage_model", brk_cls),
            "disease": fetch_rule("disease_model", dis_cls)
        }
    }

# ──────────────────────────────────────────────
# SAVE recommendations to DB
# ──────────────────────────────────────────────
def save_recommendations_to_db(db, survey_id, user_id, rec_dict):
    """
    Stores 4 recommendations into the database:
    - Hair Health (DNN)
    - Porosity
    - Breakage
    - Disease
    """

    model_map = {
        "dnn": 1,
        "porosity": 2,
        "breakage": 3,
        "disease": 4     # YOUR DB uses model_id = 5 for disease
    }

    for key in ["dnn", "porosity", "breakage", "disease"]:
        rec_content = rec_dict["recommendations"].get(key)
        model_pred_label = rec_dict["labels"].get(key)

        if rec_content is None:
            continue  # safeguard

        new_rec = Recommendation(
            survey_id=survey_id,
            user_id=user_id,
            model_id=model_map[key],
            model_prediction=model_pred_label,  # <-- SAVED HERE
            recommendation_json=json.dumps(rec_content),
            created_at=datetime.now()
        )

        db.add(new_rec)

    db.commit()


# ──────────────────────────────────────────────
# PUBLIC ROUTE
# /recommend/build_all_recommendations/<survey_id>
# ──────────────────────────────────────────────
@recommend_bp.route("/build_all_recommendations/<int:survey_id>")
def build_recommendations_route(survey_id):
    db = SessionLocal()
    try:
        survey = db.query(HairSurvey).filter_by(survey_id=survey_id).first()
        if not survey:
            return jsonify({"error": "Survey not found"}), 404

        models = load_models()
        result = build_all_recommendations(models, survey)
        user_id = survey.user_id
        # Save to database
        save_recommendations_to_db(db, survey_id, user_id, result)

        # Instead of returning JSON → Render template & pass result
        return render_template("results.html", result=result, survey=survey)

    finally:
        db.close()

@recommend_bp.route("/improved/<int:user_id>")
def improved_recommendation(user_id):

    db = SessionLocal()
    try:
        # ───────── 1. Get latest survey (ALWAYS NEW) ─────────
        latest_survey = (
            db.query(HairSurvey)
            .filter_by(user_id=user_id)
            .order_by(HairSurvey.survey_id.desc())
            .first()
        )

        if not latest_survey:
            flash("No survey found.", "warning")
            return redirect(url_for("home"))

        # ───────── 2. Get latest recommendation per model ─────────
        latest_recs = (
            db.query(Recommendation)
            .filter_by(user_id=user_id)
            .order_by(Recommendation.rec_id.desc())
            .all()
        )

        model_latest = {}
        for rec in latest_recs:
            if rec.model_id not in model_latest:
                model_latest[rec.model_id] = rec

        # ───────── 3. Run predictions on NEW survey ─────────
        models = load_models()
        dnn_cls = predict_dnn(models, latest_survey)
        por_cls = predict_porosity(models, latest_survey)
        brk_cls = predict_breakage(models, latest_survey)
        dis_cls = predict_disease(models, latest_survey.survey_id)

        improved_results = {
            "labels": {},
            "recommendations": {}
        }

        # ───────── 4. Generate recommendations ─────────
        for model_id, rec in model_latest.items():

            iteration = rec.iteration or 1

            # 🔁 DNN — feedback-adaptive
            if model_id == 1:
                improved_results["labels"]["dnn"] = LABEL_MAP["dnn_model"].get(dnn_cls)
                improved_results["recommendations"]["dnn"] = recommend_ingredients_grouped(
                    model_type="dnn_model",
                    condition=dnn_cls,
                    iteration=iteration,
                    top_n=3
                )



            # 📘 POROSITY — rules
            elif model_id == 2:
                improved_results["labels"]["porosity"] = LABEL_MAP["porosity_model"].get(por_cls)
                improved_results["recommendations"]["porosity"] = fetch_rule(
                    "porosity_model", por_cls
                )

            # 📘 BREAKAGE — rules
            elif model_id == 3:
                improved_results["labels"]["breakage"] = LABEL_MAP["breakage_model"].get(brk_cls)
                improved_results["recommendations"]["breakage"] = fetch_rule(
                    "breakage_model", brk_cls
                )

            # 📘 DISEASE — rules
            elif model_id == 4:
                improved_results["labels"]["disease"] = LABEL_MAP["disease_model"].get(dis_cls)
                improved_results["recommendations"]["disease"] = fetch_rule(
                    "disease_model", dis_cls
                )

        # ───────── 5. Save NEW recommendations ─────────
        save_recommendations_to_db(
            db=db,
            survey_id=latest_survey.survey_id,
            user_id=user_id,
            rec_dict=improved_results
        )

        return render_template(
            "results.html",
            result=improved_results,
            survey=latest_survey
        )

    except Exception as e:
        db.rollback()
        print("❌ Error in improved_recommendation:", e)
        flash("Could not generate improved recommendations.", "danger")
        return redirect(url_for("home"))

    finally:
        db.close()



