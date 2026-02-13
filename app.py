from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import init_db, SessionLocal
from auth import create_user, authenticate_user

# BLUEPRINT IMPORTS
from recommendation_routes import recommend_bp
from user_routes import user_bp
from diagnostic_routes import diagnostic_bp
from admin_routes import admin_bp
from survey_routes import survey_bp
from feedback_route import feedback_bp

# APP INIT
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "supersecret"  # use .env in production

# DB INIT
init_db()

# REGISTER BLUEPRINTS
app.register_blueprint(user_bp)
app.register_blueprint(survey_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(diagnostic_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(feedback_bp)

# ------------------------
# ROUTES
# ------------------------

@app.route('/')
def home():
    user_id = session.get('user_id')
    return render_template('home.html', user_id=user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user = create_user(name, email, password)
        if user is None:
            flash("Email already registered.", "warning")
            return redirect(url_for('register'))
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = authenticate_user(email, password)
        if user:
            session['user_id'] = user.user_id
            flash("Login successful!", "success")
            return redirect(url_for('survey.page2'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


# ------------------------
# RUN SERVER
# ------------------------
if __name__ == '__main__':
    app.run(debug=True)
