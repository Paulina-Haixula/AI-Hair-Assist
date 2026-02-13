# predictions.py
import numpy as np
import pandas as pd
import cv2
import os
import json
from feature_engineering import encode_survey_data
from db import SessionLocal
from sqlalchemy import text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from models import ModelRule

LABEL_MAP = {
        "dnn_model": { 3: "Healthy", 2: "Moisturized",
        1: "Dry", 0: "Damaged"
    }
}

# -----------------------------
# 1) DNN prediction
# -----------------------------
def predict_dnn(models, survey):
    dnn = models.get("dnn_model")
    if dnn is None:
        return None

    raw_dict = survey.to_dict() if hasattr(survey, "to_dict") else (survey if isinstance(survey, dict) else dict(survey))
    encoded = encode_survey_data(raw_dict)

    # If encoder returned DataFrame with target column, drop it
    if isinstance(encoded, pd.DataFrame) and "Current_Hair_condition" in encoded.columns:
        encoded = encoded.drop(columns=["Current_Hair_condition"], errors="ignore")

    # ensure numpy shape (1, N)
    arr = encoded.values if isinstance(encoded, pd.DataFrame) else np.array(encoded)
    # handle tricky shapes like (N,1)
    if arr.ndim == 2 and arr.shape[1] == 1 and arr.shape[0] > 1:
        arr = arr.T
    arr = arr.reshape(1, -1)

    print("ENCODED SHAPE:", arr.shape)  # debug

    pred = dnn.predict(arr)
    cls = int(np.argmax(pred, axis=1)[0])

    return (cls)


# -----------------------------
# 2) DISEASE CNN PREDICTION
# -----------------------------
def predict_disease(models, survey_id):
    cnn = models.get("disease_model")
    if cnn is None:
        return None

    path = f"static/uploads/{survey_id}.jpg"
    if not os.path.exists(path):
        return None

    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    pred = cnn.predict(img)
    cls = int(np.argmax(pred, axis=1)[0])

    return cls


# -----------------------------
# 3) POROSITY MODEL
# -----------------------------
def predict_porosity(models, survey):
    model = models.get("porosity_model")
    if model is None:
        return None

    raw_value = None
    # Accept different attribute names (case sensitive in your DB)
    for attr in ("Hair_porosity", "hair_porosity", "Hair_porosity"):
        if hasattr(survey, attr):
            raw_value = getattr(survey, attr)
            break
    if raw_value is None:
        # try dict-style
        try:
            raw_value = survey.get("Hair_porosity")
        except Exception:
            raw_value = None

    if raw_value is None:
        return None

    label = model.transform([raw_value])[0]
    return int(label)


# -----------------------------
# 4) BREAKAGE MODEL
# -----------------------------
def predict_breakage(models, survey):
    model = models.get("breakage_model")
    if model is None:
        return None

    raw_value = None
    for attr in ("Hair_Breakage", "hair_breakage", "Hair_Breakage"):
        if hasattr(survey, attr):
            raw_value = getattr(survey, attr)
            break
    if raw_value is None:
        try:
            raw_value = survey.get("Hair_Breakage")
        except Exception:
            raw_value = None

    if raw_value is None:
        return None

    label = model.transform([raw_value])[0]
    return int(label)


# -----------------------------
# 5) FULL COMBINED RESULTS HELPER (DNN rule fetch for ingredients)
# -----------------------------
def fetch_rule_dnn(model_type, cls_index):
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

#---------------- INGREDIENT DATA LOADING ----------------#
def get_products():
    db = SessionLocal()
    try:
        return pd.read_sql(text("SELECT * FROM products_clean"), db.bind)
    finally:
        db.close()

df = get_products()

# Only keep necessary columns
df_filtered = df[["ingredients", "functions"]].dropna().drop_duplicates().reset_index(drop=True)

# TF-IDF on functions
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(df_filtered["functions"].fillna(""))


def recommend_ingredients_grouped(model_type, condition, iteration=1, top_n=3):
    target_functions = fetch_rule_dnn(model_type, condition)

    if not target_functions:
        return {"error": f"No ingredient rules found for: {condition}"}

    # Normalize target functions
    if isinstance(target_functions, str):
        try:
            target_functions = json.loads(target_functions)
        except Exception:
            target_functions = [
                t.strip() for t in target_functions.split(",") if t.strip()
            ]

    # Vector similarity
    target_vec = vectorizer.transform([" ".join(target_functions)])
    sim_scores = cosine_similarity(target_vec, tfidf_matrix).flatten()

    df_filtered["score"] = sim_scores
    ranked = df_filtered.sort_values(by="score", ascending=False).head(50)

    grouped_recs = defaultdict(list)

    # Group by function
    for _, row in ranked.iterrows():
        for func in str(row["functions"]).split(", "):
            if func in target_functions:
                grouped_recs[func].append(
                    (row["ingredients"], row["score"])
                )

    # ───────── Iteration-based slicing ─────────
    start_idx = (iteration - 1) * top_n
    end_idx = start_idx + top_n

    final_output = {}

    for func, items in grouped_recs.items():
        sorted_items = sorted(items, key=lambda x: x[1], reverse=True)

        # Slice based on iteration
        sliced_items = sorted_items[start_idx:end_idx]

        final_output[func] = [
            {"Ingredient": ing, "Score": round(score, 3)}
            for ing, score in sliced_items
        ]

    return final_output
