# AI-Hair-Assist
Here is your cleaned, professional **README.md** without emojis:

---

# AI Hair Assist – Web Application

AI Hair Assist is an intelligent web-based application designed to analyze user hair survey data and provide personalized hair care insights and recommendations using Machine Learning.

This project combines:

* Deep Learning (DNN Hair Health Classifier)
* Flask Web Framework
* MySQL Database
* HTML and CSS Frontend
* User Authentication System

---

## Features

* User Registration and Login
* Multi-Step Hair Survey (5 Pages)
* Secure Data Storage (MySQL)
* AI Hair Health Classification Model
* Personalized Hair Analysis
* Clean and Responsive UI

---

## Project Structure (Stage 1)

```
hair_app/
│
├── app.py
├── db.py
├── models.py
├── auth.py
├── user_routes.py
├── survey_encoder.py
├── survey_routes.py
├── diagnostic_route.py
├── feature_engineering.py
├── feedback_route.py
├── predictions.py
├── recommendation_route.py
├── .env
├── requirements.txt
│
├── templates/
│   ├── layout.html  
│   ├── page1.html  
│   ├── page2.html  
│   ├── page3.html  
│   ├── page4.html  
│   ├── page5.html  
│   ├── login.html  
│   ├── register.html  
│   ├── success.html  
│
└── static/
    ├── css/
    │   └── style.css
    └── images/
        └── background.png
        └── background2.png
        └── ai_icon.png
        └── hair_loss_classes.jpeg
        └── hair_type_chart.png
        └── progress_icon.png
        └── recommend_icon.png
        └── survey_icon.png
    └── uploads/
        └── 158.jpg
        └── 159.jpg
        └── 160.jpg

```

---

## Technologies Used

* Python 3.x
* Flask
* SQLAlchemy
* MySQL (pymysql)
* TensorFlow / Keras
* HTML5 and CSS3

---

## Machine Learning Model

The AI Hair Assist system includes a trained:

* DNN Hair Health Classifier
* Encoded using:

  * `survey_encoder.pkl`
  * `label_encoder.pkl`
* Saved model format:

  ```
  DNN_hair_Health_classifier_v1.h5
  ```

The model predicts hair health condition based on survey inputs.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-Hair-Assist.git
cd AI-Hair-Assist
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/AI_HAIR_ASSIST
SECRET_KEY=your_secret_key
```

### 5. Run the Application

```bash
flask run
```

Then open:

```
http://127.0.0.1:5000/
```

---

## Database

Database used: MySQL

Make sure MySQL is running and the database exists:

```sql
CREATE DATABASE AI_HAIR_ASSIST;
```

---

## Future Improvements (Stage 2 and 3)

* Product recommendation engine
* Image-based hair analysis (Computer Vision)
* Admin dashboard
* User hair progress tracking
* Deployment (AWS, Render, or Docker)

---

## Author

Developed as part of an AI-powered hair health assistant project.

---

## License

This project is for educational and research purposes.
