from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Assessment
import traceback
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Statistics data for dashboard
statistics = {
    'depression_rate': 22,
    'anxiety_rate': 30,
    'panic_rate': 15,
    'high_risk_cases': [
        {'date': '2529', 'student_id': '20158561', 'depression_risk': 88, 'panic_risk': 12},
        {'date': '56123', 'student_id': '20158564', 'depression_risk': 83, 'panic_risk': 83},
        {'date': '5590', 'student_id': '20158562', 'depression_risk': 77, 'panic_risk': 77},
        {'date': '3242', 'student_id': '20158562', 'depression_risk': 48, 'panic_risk': 21},
        {'date': '3521', 'student_id': '20158566', 'depression_risk': 56, 'panic_risk': 41}
    ],
    'year_breakdown': {
        'Year 1': 75,
        'Year 2': 65,
        'Year 3': 60
    }
}

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
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            # Redirect user based on their role
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password') 

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username)
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
    
    return render_template('student/home.html', stats=statistics)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Ensure only admin can access this route
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))

    return render_template('admin/dashboard.html', stats=statistics)


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
    if depression_score in [0, 1, 4]:
        depression_label = "No or Mild Depression"
    elif depression_score in [2, 3]:
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
            required_fields = ['age', 'gender', 'university', 'department', 'academic_year', 
                             'cgpa', 'waiver_scholarship', 'nervous_anxious', 'worrying', 
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
                # Demographics
                age=int(request.form.get('age')),
                gender=int(request.form.get('gender')),
                university=int(request.form.get('university')),
                department=int(request.form.get('department')),
                academic_year=int(request.form.get('academic_year')),
                cgpa=float(request.form.get('cgpa')),
                waiver_scholarship=bool(int(request.form.get('waiver_scholarship'))),
                
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

            # Calculate scores
            anxiety_score = new_assessment.calculate_anxiety_score()
            stress_score = new_assessment.calculate_stress_score()
            depression_score = new_assessment.calculate_depression_score()

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

@app.route('/student/chatbot')
@login_required
def chatbot():
    return render_template('student/chatbot.html')

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
        assessment.anxiety_label = calculate_anxiety_label(assessment.calculate_anxiety_score())
        assessment.stress_label = calculate_stress_label(assessment.calculate_stress_score())
        assessment.depression_label = calculate_depression_label(assessment.calculate_depression_score())
    
    return render_template('student/history.html', assessments=assessments)

def calculate_anxiety_label(score):
    if score == 0:
        return "Mild"
    elif score == 1:
        return "Minimal"
    elif score == 2:
        return "Moderate"
    else:
        return "Severe"

def calculate_stress_label(score):
    if score == 0:
        return "High Perceived Stress"
    elif score == 1:
        return "Low Stress"
    else:
        return "Moderate Stress"

def calculate_depression_label(score):
    if score in [0, 1, 4]:
        return "No or Mild Depression"
    elif score in [2, 3]:
        return "Moderate Depression"
    else:
        return "Severe Depression"

if __name__ == '__main__':
    app.run(debug=True)


