# survey_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from db import SessionLocal
from models import HairSurvey

survey_bp = Blueprint('survey', __name__, url_prefix='/survey')

def require_login_redirect():
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return False
    return True

@survey_bp.route('/page2', methods=['GET', 'POST'])
def page2():
    if not require_login_redirect():
        return redirect(url_for('login'))
    if request.method == 'POST':
        session['survey_data'] = session.get('survey_data', {})
        session['survey_data'].update({
            'Age': request.form.get('age'),
            'Race': request.form.get('race'),
            'Gender': request.form.get('gender'),
            'Country': request.form.get('country'),
        })
        return redirect(url_for('survey.page3'))
    return render_template('page2.html', survey=session.get('survey_data', {}))


@survey_bp.route('/page3', methods=['GET', 'POST'])
def page3():
    if not require_login_redirect():
        return redirect(url_for('login'))
    if request.method == 'POST':
        # load, update, then REASSIGN to session so Flask persists nested dict changes
        survey_data = session.get('survey_data', {})
        survey_data.update({
            'Hair_type': request.form.get('hair_type'),
            'Hair_porosity': request.form.get('hair_porosity'),
            'Hair_texture': request.form.get('hair_texture'),
            'Hair_density': request.form.get('hair_density'),
        })
        session['survey_data'] = survey_data  # <--- crucial
        # small log entry for debugging (won't affect DB)
        current_app.logger.info("Survey page3 saved to session: %s", survey_data)
        return redirect(url_for('survey.page4'))
    return render_template('page3.html', survey=session.get('survey_data', {}))


@survey_bp.route('/page4', methods=['GET', 'POST'])
def page4():
    if not require_login_redirect():
        return redirect(url_for('login'))
    if request.method == 'POST':
        # load, update, then REASSIGN to session so Flask persists nested dict changes
        survey_data = session.get('survey_data', {})
        survey_data.update({
            'Hair_edges_condition': request.form.get('hair_edges_condition'),
            'Hair_Loss_state': request.form.get('hair_loss_state'),
            'Hair_Breakage': request.form.get('hair_breakage'),
            'Current_Hair_condition': request.form.get('current_hair_condition'),
        })
        session['survey_data'] = survey_data  # <--- crucial
        # small log entry for debugging (won't affect DB)
        current_app.logger.info("Survey page4 saved to session: %s", survey_data)
        return redirect(url_for('survey.page5'))
    return render_template('page4.html', survey=session.get('survey_data', {}))


@survey_bp.route('/page5', methods=['GET', 'POST'])
def page5():


    if not require_login_redirect():
        return redirect(url_for('login'))

    if request.method == 'POST':
        session['survey_data'].update({
            'Eating_diet': request.form.get('Eating_diet'),
            'Consumed_water_per_day_L': request.form.get('Consumed_water_per_day_L'),
            'Hair_length_Current_Hair_Length': request.form.get('Hair_length_Current_Hair_Length'),
            'Hair_length_Hair_goal': request.form.get('Hair_length_Hair_goal'),
            'Satin_scarfbonnet_or_pillowcase': request.form.get('satin_scarfbonnet_or_pillowcase'),
        })

        survey_data = session.get('survey_data', {})
        survey_data['user_id'] = session.get('user_id')

        # persist to DB safely
        try:
            with SessionLocal() as db:
                survey_entry = HairSurvey(**survey_data)
                db.add(survey_entry)
                db.commit()
                db.refresh(survey_entry)
                saved_id = survey_entry.survey_id

        except Exception as e:
            flash(f"Error saving survey: {e}", "danger")
            return render_template('page5.html', survey=session.get('survey_data', {}))

        # clear session data
        session.pop('survey_data', None)
        flash("Survey saved successfully — thank you!", "success")

        # If user clicked Next -> go to diagnostic with real survey id
        if 'save' in request.form:
            return redirect(url_for('diagnostic.diagnostic_choice', survey_id=saved_id))

        # If user clicked Save -> send to a success page or dashboard (adjust as desired)
        return redirect(url_for('diagnostic.diagnostic_choice', survey_id=saved_id))

    return render_template('page5.html', survey=session.get('survey_data', {}))
