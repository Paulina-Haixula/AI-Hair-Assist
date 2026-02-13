from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, UTC

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HairSurvey(Base):
    __tablename__ = "hairsurvey"
    survey_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(String, default=lambda: datetime.now(UTC).strftime("%d/%m/%Y %H:%M:%S"), nullable=True)
    Score = Column(String(50), nullable=True)
    Age = Column(String(50), nullable=True)
    Race = Column(String(100), nullable=True)
    Gender = Column(String(50), nullable=True)
    Country = Column(String(100), nullable=True)
    Hair_type = Column(String(100), nullable=True)
    Hair_porosity = Column(String(100), nullable=True)
    Hair_texture = Column(String(100), nullable=True)
    Hair_density = Column(String(100), nullable=True)
    Harline_condition = Column(String(200), nullable=True)
    Hair_edges_condition = Column(String(200), nullable=True)
    Hair_Loss_state = Column(String(200), nullable=True)
    Hair_Breakage = Column(String(200), nullable=True)
    Hair_length_Current_Hair_Length = Column(String(200), nullable=True)
    Hair_length_Hair_goal = Column(String(200), nullable=True)
    Hair_look = Column(String(200), nullable=True)
    Current_Hair_condition = Column(String(200), nullable=True)
    Scalp_condition = Column(String(200), nullable=True)
    Ingredient_promotes_your_hair_health = Column(String(255), nullable=True)
    Is_your_hair_chemically_treated = Column(String(50), nullable=True)
    Keratin_Treatment = Column(String(100), nullable=True)
    Professional_treatments = Column(String(255), nullable=True)
    Protective_hairstyles_No_1 = Column(String(200), nullable=True)
    Protective_hairstyles_No_2 = Column(String(200), nullable=True)
    Condition_of_protective_hairstyles_used = Column(String(255), nullable=True)
    Protective_hairstyles_maintenance = Column(String(255), nullable=True)
    How_often_do_you_Heatstyling_tools = Column(String(100), nullable=True)
    How_often_do_you_Tight_hairstyle = Column(String(100), nullable=True)
    How_often_do_you_Hair_moisturizer = Column(String(100), nullable=True)
    How_often_do_you_Scalp_massages = Column(String(100), nullable=True)
    How_often_do_you_Hair_Wash = Column(String(100), nullable=True)
    Occurrence_of_hair_breakage = Column(String(255), nullable=True)
    Causes_of_hair_breakage = Column(String(255), nullable=True)
    Other_please_specify = Column(String(255), nullable=True)
    Comb_type = Column(String(200), nullable=True)
    Detangling_style = Column(String(200), nullable=True)
    Hair_Supplement_used = Column(String(255), nullable=True)
    medication_or_Condition_affecting_Hair_growth = Column(String(255), nullable=True)
    Hair_or_scalp_allergies = Column(String(255), nullable=True)
    Family_history_of_hair_loss_or_slow_growth = Column(String(255), nullable=True)
    Eating_diet = Column(String(255), nullable=True)
    Consumed_water_per_day_L = Column(Float, nullable=True)
    Satin_scarfbonnet_or_pillowcase = Column(String(50), nullable=True)
    Main_factor_influencing_your_hair_health_or_growth = Column(Text, nullable=True)
    Tips_or_products_have_worked_well_for_your_hair = Column(Text, nullable=True)
    Hair_state_and_their_cause_Hydrated__Healthy = Column(String(100), nullable=True)
    Hair_state_and_their_cause_Promote_Frizzy = Column(String(100), nullable=True)
    Hair_state_and_their_cause_Tangled = Column(String(100), nullable=True)
    Hair_state_and_their_cause_dryness__breaking = Column(String(100), nullable=True)
    Would_you_participate_in_followup_studies = Column(String(50), nullable=True)
    Email = Column(String(255), nullable=True)
    Email_address = Column(String(255), nullable=True)

    def to_dict(self):
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }
# --- Existing imports and Base definitions remain above ---

from sqlalchemy import ForeignKey, JSON

# =======================
#   NEW TABLES — STAGE 2
# =======================

class ModelVersion(Base):
    __tablename__ = "model_versions"
    model_id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=True)  # e.g., "DNN", "Breakage"
    trained_on = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)


class ModelRule(Base):
    __tablename__ = "model_rules"
    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("model_versions.model_id"), nullable=False)
    rule_name = Column(String(100), nullable=False)
    rule_json = Column(JSON, nullable=False)  # holds explainable rule text
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class Product(Base):
    __tablename__ = "products_clean"
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False) # Product Title
    brand = Column(String(255), nullable=True)
    ingredients = Column(Text, nullable=True)  #Ingredient
    functions = Column(Text, nullable=True)  # keywords or categories


class Recommendation(Base):
    __tablename__ = "recommendations"
    rec_id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("hairsurvey.survey_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    model_id = Column(Integer, ForeignKey("model_versions.model_id"))
    iteration = Column(Integer)
    model_prediction = Column(String(255), nullable=True)
    recommendation_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Feedback(Base):
    __tablename__ = "feedback"
    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    rec_id = Column(Integer, ForeignKey("recommendations.rec_id"))
    rating = Column(Integer, nullable=True)  # 1–5 stars
    #comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


