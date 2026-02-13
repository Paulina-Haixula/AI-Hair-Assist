# feature_engineering.py
import pandas as pd
import numpy as np
import os
import pickle
import joblib
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, LabelBinarizer


# ===============================
# Load Pretrained Encoder Once
# ===============================

class SurveyEncoder:
    def __init__(self, numeric_columns, ordinal_columns, nominal_columns, binary_columns):
        self.numeric_columns = numeric_columns
        self.ordinal_columns = ordinal_columns
        self.nominal_columns = nominal_columns
        self.binary_columns = binary_columns

        self.scaler = StandardScaler()
        self.ordinal_encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        self.nominal_encoders = {}
        self.feature_columns_ = None
        self.fitted = False

    # --- helper for label binarizer ---
    def _fit_label_binarizer(self, series, col):
        """Fit LabelBinarizer and store encoder"""
        series = series.astype(str).str.lower().str.strip()
        lb = LabelBinarizer()
        lb.fit(series)
        self.nominal_encoders[col] = lb

    def _transform_label_binarizer(self, series, col):
        """Transform series using already fitted LabelBinarizer"""
        lb = self.nominal_encoders[col]
        series = series.astype(str).str.lower().str.strip()
        # unseen categories → mark as zero vector
        known_classes = set(lb.classes_)
        mask_unknown = ~series.isin(known_classes)
        series[mask_unknown] = lb.classes_[0]  # fallback to first known class
        arr = lb.transform(series)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        # consistent column names
        if len(lb.classes_) == 2:
            col_names = [f"{col}_{lb.classes_[1]}"]
        else:
            col_names = [f"{col}_{cls}" for cls in lb.classes_]
        df_enc = pd.DataFrame(arr, columns=col_names, index=series.index)
        return df_enc

    # --- fitting ---
    def fit(self, df):
        # Fit numeric scaler
        self.scaler.fit(df[self.numeric_columns])
        # Fit ordinal encoder
        self.ordinal_encoder.fit(df[self.ordinal_columns])
        # Fit label binarizers for col in self.nominal_columns + self.binary_columns:
        for col in self.nominal_columns + self.binary_columns:
            self._fit_label_binarizer(df[col], col)
        # Create feature column order for reference
        X_encoded = self._transform_internal(df)
        self.feature_columns_ = X_encoded.columns.tolist()
        self.fitted = True
        return self

    # --- internal transform (no column reindex) ---
    def _transform_internal(self, df):
        parts = []
        # Numeric
        num_scaled = self.scaler.transform(df[self.numeric_columns])
        parts.append(pd.DataFrame(num_scaled, columns=self.numeric_columns, index=df.index))
        # Ordinal
        ord_enc = self.ordinal_encoder.transform(df[self.ordinal_columns])
        parts.append(pd.DataFrame(ord_enc, columns=self.ordinal_columns, index=df.index))
        # Nominal + Binary
        for col in self.nominal_columns + self.binary_columns:
            df_enc = self._transform_label_binarizer(df[col], col)
            parts.append(df_enc)
        encoded_df = pd.concat(parts, axis=1)
        return encoded_df

    # --- public transform ---
    def transform(self, df):
        if not self.fitted:
            raise ValueError("Encoder must be fitted before transform.")
        encoded_df = self._transform_internal(df)
        # Ensure same columns and order as training
        encoded_df = encoded_df.reindex(columns=self.feature_columns_, fill_value=0)
        return encoded_df

    def fit_transform(self, df):
        self.fit(df)
        return self.transform(df)

    # --- save/load helpers ---
    def save(self, path):
        """Save encoder to disk."""
        joblib.dump(self, path)

    @staticmethod
    def load(path):
        """Load encoder from disk."""
        return joblib.load(path)

    # return encoded_df


# Part 2: Define columns, fit encoder, save encoder, reload and transform a single row




    # Define columns to encode,
    numeric_columns = ['Consumed_water_per_day_L']
    ordinal_columns = [
        'Current_Hair_condition', 'Age', 'Hair_porosity', 'Hair_texture', 'Hair_density',
        'Harline_condition', 'Hair_Breakage', 'Hair_Loss_state',
        'Hair_length_Current_Hair_Length', 'Hair_length_Hair_goal', 'Country',
        'Hair_type', 'How_often_do_you_Heatstyling_tools', 'How_often_do_you_Tight_hairstyle',
        'How_often_do_you_Hair_moisturizer', 'How_often_do_you_Scalp_massages',
        'How_often_do_you_Hair_Wash', 'Occurrence_of_hair_breakage', 'Causes_of_hair_breakage'
    ]
    nominal_columns = [
        'Race', 'Gender', 'Hair_edges_condition', 'Hair_look', 'Scalp_condition',
        'Is_your_hair_chemically_treated', 'Professional_treatments', 'Protective_hairstyles_No_1',
        'Protective_hairstyles_No_2', 'Condition_of_protective_hairstyles_used',
        'Protective_hairstyles_maintenance', 'Causes_of_hair_breakage', 'Comb_type',
        'Detangling_style', 'Eating_diet', 'Hair_state_and_their_cause_Hydrated__Healthy',
        'Hair_state_and_their_cause_Promote_Frizzy', 'Hair_state_and_their_cause_Tangled',
        'Hair_state_and_their_cause_dryness__breaking'
    ]
    sentence_columns = [
        'Ingredient_promotes_your_hair_health', 'Other_please_specify', 'Hair_Supplement_used',
        'medication_or_Condition_affecting_Hair_growth', 'Hair_or_scalp_allergies',
        'Tips_or_products_have_worked_well_for_your_hair', 'Main_factor_influencing_your_hair_health_or_growth'
    ]
    binary_columns = [
        'Keratin_Treatment', 'Family_history_of_hair_loss_or_slow_growth', 'Satin_scarfbonnet_or_pillowcase'
    ]

# ---------------------------
# Load Survey Encoder
# ---------------------------
def load_encoder():
    return SurveyEncoder.load("survey_encoder.pkl")   # EXACTLY like your notebook


# ---------------------------
# Encode Survey Response
# ---------------------------
def encode_survey_data(data: dict):
    """
    Accept raw survey JSON → encode using SurveyEncoder → return numpy array
    """
    encoder = load_encoder()
    df = pd.DataFrame([data])

    # Ensure numeric column is numeric
    if "Consumed_water_per_day_L" in df.columns:
        df["Consumed_water_per_day_L"] = pd.to_numeric(df["Consumed_water_per_day_L"], errors="coerce").fillna(0)

    encoded_df = encoder.transform(df)   # EXACTLY same as Jupyter

    # The model was trained on X which is df_final with Current_Hair_condition dropped.
    # So drop target column if present in encoded_single, then reindex columns to match X_train
    encoded_for_pred = encoded_df.drop(columns=['Current_Hair_condition'], errors='ignore')
    encoded_for_pred = encoded_for_pred.reindex(columns=encoded_for_pred.columns, fill_value=0)
    print("Encoded single row shape after dropping target and reindexing:", encoded_for_pred.shape)

    encoded_array = encoded_for_pred.to_numpy().reshape(1, -1)
    print("Encoded shape:", encoded_array.shape)

    return encoded_array


# -----------------------------
# LOAD ALL MODELS
# -----------------------------
MODEL_DIR = "models/"

def load_models():
    """Load DNN (.h5), disease CNN (.h5), porosity (.pkl), breakage (.pkl)."""
    models = {}

    # DNN
    dnn_path = os.path.join(MODEL_DIR, "DNN_hair_Health_classifier_v1.h5")
    if os.path.exists(dnn_path):
        models["dnn_model"] = tf.keras.models.load_model(dnn_path)

    # Disease CNN
    disease_path = os.path.join(MODEL_DIR, "hair_disease_classifier_accur_v1.h5")
    if os.path.exists(disease_path):
        models["disease_model"] = tf.keras.models.load_model(disease_path)

    # POROSITY MODEL
    porosity_model = os.path.join(MODEL_DIR, "porosity_v1.pkl")
    if os.path.exists(porosity_model):
        with open(porosity_model, "rb") as f:
            models["porosity_model"] = pickle.load(f)

    # BREAKAGE MODEL
    breakage_model = os.path.join(MODEL_DIR, "breakage_v1.pkl")
    if os.path.exists(breakage_model):
        with open(breakage_model, "rb") as f:
            models["breakage_model"] = pickle.load(f)

    return models
