from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Assessment
from sqlalchemy import or_, and_
import traceback
from datetime import datetime
import pytz
import joblib

# Load models
model_anx = joblib.load('models/logistic_regression_anxiety_model.pkl')
model_str = joblib.load('models/logistic_regression_stress_model.pkl')
model_dep = joblib.load('models/logistic_regression_depression_model.pkl')

# Load scalers
scaler_anx = joblib.load('models/scaler_anxiety.pkl')
scaler_str = joblib.load('models/scaler_stress.pkl')
scaler_dep = joblib.load('models/scaler_depression.pkl')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect users to either the student or admin dashboard based on their role
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')

        user = User.query.filter_by(username=student_id).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard') if user.is_admin else url_for('student_dashboard'))
        else:
            flash('Invalid Student ID or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not student_id.isdigit() and student_id != "admin":
            print(student_id)
            flash('Student ID must be digits only.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=student_id).first()
        if existing_user:
            flash('Student ID already registered.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=student_id, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('student_dashboard'))

    return render_template('register.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    stats = calculate_dashboard_stats()  # <- Dynamic calculation
    return render_template('student/home.html', stats=stats)


def calculate_dashboard_stats():
    # Get all assessments
    assessments = Assessment.query.all()
    total = len(assessments)
    if total == 0:
        return {
            'depression_rate': 0,
            'anxiety_rate': 0,
            'stress_rate': 0,
            'high_risk_cases': [],
            'year_breakdown': {}
        }

    # Calculate high risk rates (Moderate or Severe)
    depression_high = [a for a in assessments if a.depression_score is not None and a.depression_score >= 2]
    anxiety_high = [a for a in assessments if a.anxiety_score is not None and a.anxiety_score >= 2]
    stress_high = [a for a in assessments if a.stress_score is not None and a.stress_score >= 1]  # Adjust threshold if needed

    depression_rate = int(len(depression_high) / total * 100)
    anxiety_rate = int(len(anxiety_high) / total * 100)
    stress_rate = int(len(stress_high) / total * 100)

    # High risk cases
    high_risk_cases = []
    risk_cases = [a for a in assessments if
                  (a.anxiety_score is not None and a.anxiety_score >= 2) or
                  (a.stress_score is not None and a.stress_score >= 1) or
                  (a.depression_score is not None and a.depression_score >= 2)]

    for a in risk_cases:
        high_risk_cases.append({
            'id': a.id,
            'date': a.timestamp.strftime('%Y-%m-%d'),
            'student_id': a.user.username if a.user else str(a.user_id),
            'email': a.user.email if a.user else '',   # <-- Add this line!
            'anxiety_risk': int((a.anxiety_score / 3) * 100) if a.anxiety_score is not None else 0,
            'stress_risk': int((a.stress_score / 2) * 100) if a.stress_score is not None else 0,
            'depression_risk': int((a.depression_score / 3) * 100) if a.depression_score is not None else 0,
            'status': getattr(a, 'status', 'Pending')
        })

    # Year breakdown (optional, based on your model)
    year_breakdown = {}
    years = ['1', '2', '3', '4']
    for year in years:
        year_cases = [a for a in assessments if hasattr(a, 'academic_year') and getattr(a, 'academic_year', '').endswith(year)]
        year_breakdown[f'Year {year}'] = len(year_cases)

    return {
        'depression_rate': depression_rate,
        'anxiety_rate': anxiety_rate,
        'stress_rate': stress_rate,
        'high_risk_cases': high_risk_cases,
        'year_breakdown': year_breakdown
    }

@app.route('/admin/all-assessments')
@login_required
def all_assessments():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    assessments = Assessment.query.order_by(Assessment.timestamp.desc()).all()
    return render_template(
        'admin/all_assessments.html',
        assessments=assessments,
        calculate_anxiety_label=calculate_anxiety_label,
        calculate_stress_label=calculate_stress_label,
        calculate_depression_label=calculate_depression_label
    )

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))

    stats = calculate_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)



def generate_recommendations(anxiety_score, stress_score, depression_score):
    # Label encoding for Anxiety
    if anxiety_score == 0:
        anxiety_label = "Mild Anxiety"
    elif anxiety_score == 1:
        anxiety_label = "Minimal Anxiety"
    elif anxiety_score == 2:
        anxiety_label = "Moderate Anxiety"
    else:
        anxiety_label = "Severe Anxiety"

    # Label encoding for Stress
    if stress_score == 0:
        stress_label = "High Perceived Stress"
    elif stress_score == 1:
        stress_label = "Low Stress"
    else:
        stress_label = "Moderate Stress"

    # Label encoding for Depression
    if depression_score == 0:
        depression_label = "No or Mild Depression"
    elif depression_score == 1:
        depression_label = "Moderate Depression"
    else:
        depression_label = "Severe Depression"

    recommendations = []

    if anxiety_score > 3:
        recommendations.append("Consider practicing mindfulness or meditation to manage anxiety.")
    if stress_score > 3:
        recommendations.append("Engage in regular physical activity to help reduce stress.")
    if depression_score > 3:
        recommendations.append("Seek support from a mental health professional for depression.")

    if not recommendations:
        recommendations.append("Keep up the good work maintaining your mental health!")

    return {
        "recommendations": " ".join(recommendations),
        "anxiety_label": anxiety_label,
        "stress_label": stress_label,
        "depression_label": depression_label
    }


@app.route('/student/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    if request.method == 'POST':
        try:
            # Validate all required fields are present
            required_fields = ['nervous_anxious', 'worrying', 
                             'trouble_relaxing', 'easily_annoyed', 'excessive_worry', 
                             'restless', 'fearful', 'upset', 'lack_of_control', 
                             'nervous_stress', 'inadequate_coping', 'confident', 
                             'things_going_well', 'control_irritations', 'top_performance', 
                             'angered_by_performance', 'overwhelmed', 'lack_of_interest', 
                             'feeling_down', 'sleep_issues', 'fatigue', 'appetite_issues', 
                             'self_doubt', 'concentration_issues', 'movement_issues', 
                             'suicidal_thoughts']
            
            for field in required_fields:
                if field not in request.form or request.form[field] == '':
                    raise ValueError(f"Missing required field: {field}")

            # Create new assessment instance with Malaysia timezone
            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
            current_time = datetime.now(malaysia_tz)

            new_assessment = Assessment(
                user_id=current_user.id,
                timestamp=current_time,  # Ensure this field exists in your model

                
                # Anxiety Indicators
                nervous_anxious=int(request.form.get('nervous_anxious')),
                worrying=int(request.form.get('worrying')),
                trouble_relaxing=int(request.form.get('trouble_relaxing')),
                easily_annoyed=int(request.form.get('easily_annoyed')),
                excessive_worry=int(request.form.get('excessive_worry')),
                restless=int(request.form.get('restless')),
                fearful=int(request.form.get('fearful')),
                
                # Stress Indicators
                upset=int(request.form.get('upset')),
                lack_of_control=int(request.form.get('lack_of_control')),
                nervous_stress=int(request.form.get('nervous_stress')),
                inadequate_coping=int(request.form.get('inadequate_coping')),
                confident=int(request.form.get('confident')),
                things_going_well=int(request.form.get('things_going_well')),
                control_irritations=int(request.form.get('control_irritations')),
                top_performance=int(request.form.get('top_performance')),
                angered_by_performance=int(request.form.get('angered_by_performance')),
                overwhelmed=int(request.form.get('overwhelmed')),
                
                # Depression Indicators
                lack_of_interest=int(request.form.get('lack_of_interest')),
                feeling_down=int(request.form.get('feeling_down')),
                sleep_issues=int(request.form.get('sleep_issues')),
                fatigue=int(request.form.get('fatigue')),
                appetite_issues=int(request.form.get('appetite_issues')),
                self_doubt=int(request.form.get('self_doubt')),
                concentration_issues=int(request.form.get('concentration_issues')),
                movement_issues=int(request.form.get('movement_issues')),
                suicidal_thoughts=int(request.form.get('suicidal_thoughts'))
            )
            
            # Add and commit to database
            db.session.add(new_assessment)
            db.session.commit()

            # Extract relevant input for each model
            input_dict_anxiety = {
                'Worrying': new_assessment.worrying,
                'Restless': new_assessment.restless,
                'Nervous/Anxious': new_assessment.nervous_anxious,
                'Excessive Worry ': new_assessment.excessive_worry,
                'Trouble Relaxing ': new_assessment.trouble_relaxing,
                'Easily Annoyed': new_assessment.easily_annoyed,
                'Fearful ': new_assessment.fearful
            }

            input_dict_stress = {
                'Overwhelmed': new_assessment.overwhelmed,
                'Inadequate Coping': new_assessment.inadequate_coping,
                'Angered by Performance': new_assessment.angered_by_performance,
                'Lack of Control': new_assessment.lack_of_control,
                'Confident': new_assessment.confident,
                'Top Performance': new_assessment.top_performance,
                'Nervous/Stress ': new_assessment.nervous_stress,
                'Things Going Well': new_assessment.things_going_well,
                'Control Irritations': new_assessment.control_irritations,
                'Upset': new_assessment.upset
            }

            input_dict_depression = {
                'Feeling Down': new_assessment.feeling_down,
                'Lack of Interest': new_assessment.lack_of_interest,
                'Suicidal Thoughts': new_assessment.suicidal_thoughts,
                'Appetite Issues': new_assessment.appetite_issues,
                'Fatigue': new_assessment.fatigue,
                'Self-Doubt': new_assessment.self_doubt,
                'Sleep Issues': new_assessment.sleep_issues,
                'Concentration Issues': new_assessment.concentration_issues,
                'Movement Issues': new_assessment.movement_issues
            }

            # Use models for prediction
            anxiety_score = predict_with_scaler(input_dict_anxiety, model_anx, scaler_anx)
            stress_score = predict_with_scaler(input_dict_stress, model_str, scaler_str)
            depression_score = predict_with_scaler(input_dict_depression, model_dep, scaler_dep)

            # Store predictions in the database model
            new_assessment.anxiety_score = anxiety_score
            new_assessment.stress_score = stress_score
            new_assessment.depression_score = depression_score

            # Add and commit to database
            db.session.add(new_assessment)
            db.session.commit()

            # Generate recommendations based on scores
            result = generate_recommendations(anxiety_score, stress_score, depression_score)

            # Redirect to result page with labels and recommendations
            return render_template(
                'student/result.html',
                recommendations=result["recommendations"],
                anxiety_label=result["anxiety_label"],
                stress_label=result["stress_label"],
                depression_label=result["depression_label"]
            )

        except ValueError as ve:
            flash(f'Validation error: {str(ve)}. Please complete all fields.', 'danger')
        except Exception as e:
            print(f"Database Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            db.session.rollback()
            flash(f'Error submitting assessment: {str(e)}. Please try again.', 'danger')
        return redirect(url_for('assessment'))

    return render_template('student/assessment.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/student/history')
@login_required
def view_history():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.timestamp.desc()).all()
    
    # Calculate labels for each assessment
    for assessment in assessments:
        assessment.anxiety_label = calculate_anxiety_label(assessment.anxiety_score)
        assessment.stress_label = calculate_stress_label(assessment.stress_score)
        assessment.depression_label = calculate_depression_label(assessment.depression_score)
    
    return render_template('student/history.html', assessments=assessments)

@app.route('/student/assessment/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    # Fetch the assessment or 404 if not found
    assessment = Assessment.query.get_or_404(assessment_id)

    # Check access control
    if assessment.user_id != current_user.id and not getattr(current_user, 'is_admin', False):
        return redirect(url_for('index'))

    # Calculate labels for the assessment
    assessment.anxiety_label = calculate_anxiety_label(assessment.anxiety_score)
    assessment.stress_label = calculate_stress_label(assessment.stress_score)
    assessment.depression_label = calculate_depression_label(assessment.depression_score)

    # Helper functions for labels
    def gender_label(code): return "Male" if code == 1 else "Female"
    def bool_label(b): return "Yes" if b else "No"
    def score_label(score): return ["Low", "Mild", "Moderate", "High", "Severe"][score] if score is not None else "N/A"
    def department_label(code):
        departments = {
            0: "Biological Sciences",
            1: "Business",
            2: "CS/IT",
            3: "Civil Eng",
            4: "EEE/ECE",
            5: "Env/Life Sci",
            6: "Mech Eng",
            7: "Other"
        }
        return departments.get(code, "N/A") if code is not None else "N/A"
    def academic_year_label(year): return f"Year {year}" if year is not None else "N/A"
    def cgpa_label(cgpa): return f"{cgpa:.2f}" if cgpa is not None else "N/A"

    # Get the user associated with this assessment
    user = User.query.get(assessment.user_id)

    return render_template(
        'view_assessment.html',
        assessment=assessment,
        user=user,
        gender_label=gender_label,
        bool_label=bool_label,
        score_label=score_label,
        department_label=department_label,
        academic_year_label=academic_year_label,
        cgpa_label=cgpa_label
    )

def calculate_anxiety_label(score):
    if score == 0:
        return "Mild Anxiety"
    elif score == 1:
        return "Minimal Anxiety"
    elif score == 2:
        return "Moderate Anxiety"
    else:
        return "Severe Anxiety"

def calculate_stress_label(score):
    if score == 0:
        return "High Perceived Stress"
    elif score == 1:
        return "Low Stress"
    else:
        return "Moderate Stress"

def calculate_depression_label(score):
    if score == 0:
        return "No or Mild Depression"
    elif score == 1:
        return "Moderate Depression"
    else:
        return "Severe Depression"
    
def predict_with_scaler(input_dict, model, scaler):
    import pandas as pd
    df_input = pd.DataFrame([input_dict])
    df_input = df_input[scaler.feature_names_in_]
    scaled_input = scaler.transform(df_input)
    return int(model.predict(scaled_input)[0])

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Get form data
            department = request.form.get('department')
            academic_year = request.form.get('academic_year')
            gender = request.form.get('gender')
            cgpa = request.form.get('cgpa')
            waiver_scholarship = request.form.get('waiver_scholarship')
            age = request.form.get('age') 

            # Update user profile
            current_user.department = int(department) if department else None
            current_user.academic_year = academic_year
            current_user.gender = int(gender) if gender else None
            current_user.cgpa = float(cgpa) if cgpa else None
            current_user.waiver_scholarship = int(waiver_scholarship) if waiver_scholarship else None
            current_user.age = int(age) if age else None  

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('profile'))

    return render_template('student/profile.html')

@app.route('/api/cases/<int:assessment_id>/review', methods=['POST'])
@login_required
def mark_case_reviewed(assessment_id):
    # Admin-only
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied.'}), 403

    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        return jsonify({'success': False, 'message': 'Assessment not found.'}), 404

    assessment.status = "Consulted"
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)

