select *
from recommendations;

ALTER TABLE feedback DROP CHECK feedback_chk_1;
ALTER TABLE feedback ADD CONSTRAINT feedback_chk_1 CHECK (rating IN (0, 1));


UPDATE model_versions
SET model_name = 'hair_disease_classifier_accur_v1'
WHERE model_id = 4;

ALTER TABLE recommendations
DROP COLUMN user_id;

ALTER TABLE recommendations
add column iteration INT;


ADD COLUMN user_id INT,
ADD CONSTRAINT fk_recommendations_user
FOREIGN KEY (user_id) REFERENCES users(user_id);

recommendationsALTER TABLE feedback
ADD COLUMN  category ENUM('breakage','disease','dnn','porosity');

ALTER TABLE model_versions
MODIFY COLUMN model_name VARCHAR(255);

ALTER TABLE recommendations
ADD COLUMN model_prediction VARCHAR(255);

UPDATE model_rules
SET  rule_name= 'breakage_model'
WHERE model_id = 3;

INSERT INTO model_rules (rule_id, model_id, rule_name, rule_json, created_at)
VALUES (
    4,
    4,
    'disease_model',
    '{
        "Alopecia Areata": {
            "Recommendation": "Consult a dermatologist immediately. Early intervention can help manage symptoms.",
            "Why": "Autoimmune condition where the immune system attacks hair follicles."
        },
        "Contact Dermatitis": {
            "Recommendation": "Visit a dermatologist to identify and avoid triggers. Medical creams may be prescribed.",
            "Why": "Caused by allergic reactions or irritants leading to scalp inflammation."
        },
        "Folliculitis": {
            "Recommendation": "Seek medical advice. A doctor may prescribe antibiotics or antifungal treatment.",
            "Why": "Infection of hair follicles leading to bumps, itching, or pain."
        },
        "Head Lice": {
            "Recommendation": "See a doctor or pharmacist for proper medicated shampoos and treatment guidance.",
            "Why": "Parasitic infestation that causes intense itching and scalp irritation."
        },
        "Lichen Planus": {
            "Recommendation": "Consult a dermatologist for anti-inflammatory or immunosuppressive treatment.",
            "Why": "Chronic inflammatory condition that can cause scalp scarring and hair loss."
        },
        "Male Pattern Baldness": {
            "Recommendation": "Seek medical advice. Treatments like minoxidil or finasteride may help slow progression.",
            "Why": "Genetic hair loss condition common in men, often progressive."
        },
        "Psoriasis": {
            "Recommendation": "Visit a dermatologist for medicated shampoos and treatments to reduce scalp plaques.",
            "Why": "Chronic autoimmune condition causing flaky, itchy scalp."
        },
        "Seborrheic Dermatitis": {
            "Recommendation": "Consult a dermatologist. Antifungal shampoos or topical treatments may be required.",
            "Why": "Causes dandruff and inflamed, greasy scalp."
        },
        "Telogen Effluvium": {
            "Recommendation": "See a doctor to identify stressors or underlying conditions causing temporary shedding.",
            "Why": "Often triggered by stress, illness, or hormonal changes."
        },
        "Tinea Capitis": {
            "Recommendation": "Consult a doctor for antifungal medications. Early treatment prevents spreading.",
            "Why": "Fungal infection of the scalp leading to hair loss and scaly patches."
        }
    }',
    '2025-09-24 12:13:51'
);


UPDATE model_rules
SET rule_json = '{
    "Extreme- High Breakage": {
        "Why": "Hair cortex has severe structural loss and cuticle erosion.",
        "Recommendation": "Extreme breakage detected. Immediately reduce manipulation, avoid chemicals/heat, use protein reconstructors + protective styling."
    },
    "Extreme- Low Breakage": {
        "Why": "Minimal cuticle disruption but strands appear stressed.",
        "Recommendation": "Low breakage. Maintain moisture–protein balance. Gentle handling recommended."
    },
    "High Breakage": {
        "Why": "Hair fibers weakened heavily due to dryness or mechanical tension.",
        "Recommendation": "High breakage. Weekly protein treatment + strengthen routine. Reduce tight hairstyles."
    },
    "Low Breakage": {
        "Why": "Good structural integrity with slight dryness.",
        "Recommendation": "Low breakage. Maintain moisturizing deep conditioning bi-weekly."
    },
    "Medium Breakage": {
        "Why": "Cuticle moderately raised — prone to snapping under stress.",
        "Recommendation": "Medium breakage. Alternate moisture/protein routine, reduce combing while dry."
    }
}'
WHERE model_id = 3;

