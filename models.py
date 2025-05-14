from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False) # Student ID
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    # Demographics
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Integer, nullable=False)  # 0: Female, 1: Male
    department = db.Column(db.String, nullable=False) 
    academic_year = db.Column(db.String, nullable=False) 
    cgpa = db.Column(db.Float, nullable=False)
    waiver_scholarship = db.Column(db.Boolean, nullable=False)  # 0: No, 1: Yes
    
    # Anxiety Indicators (0-4 scale)
    nervous_anxious = db.Column(db.Integer, nullable=False)
    worrying = db.Column(db.Integer, nullable=False)
    trouble_relaxing = db.Column(db.Integer, nullable=False)
    easily_annoyed = db.Column(db.Integer, nullable=False)
    excessive_worry = db.Column(db.Integer, nullable=False)
    restless = db.Column(db.Integer, nullable=False)
    fearful = db.Column(db.Integer, nullable=False)
    
    # Stress Indicators (0-4 scale)
    upset = db.Column(db.Integer, nullable=False)
    lack_of_control = db.Column(db.Integer, nullable=False)
    nervous_stress = db.Column(db.Integer, nullable=False)
    inadequate_coping = db.Column(db.Integer, nullable=False)
    confident = db.Column(db.Integer, nullable=False)
    things_going_well = db.Column(db.Integer, nullable=False)
    control_irritations = db.Column(db.Integer, nullable=False)
    top_performance = db.Column(db.Integer, nullable=False)
    angered_by_performance = db.Column(db.Integer, nullable=False)
    overwhelmed = db.Column(db.Integer, nullable=False)
    
    # Depression Indicators (0-4 scale)
    lack_of_interest = db.Column(db.Integer, nullable=False)
    feeling_down = db.Column(db.Integer, nullable=False)
    sleep_issues = db.Column(db.Integer, nullable=False)
    fatigue = db.Column(db.Integer, nullable=False)
    appetite_issues = db.Column(db.Integer, nullable=False)
    self_doubt = db.Column(db.Integer, nullable=False)
    concentration_issues = db.Column(db.Integer, nullable=False)
    movement_issues = db.Column(db.Integer, nullable=False)
    suicidal_thoughts = db.Column(db.Integer, nullable=False)

    # Predictions
    anxiety_score = db.Column(db.Integer, nullable=True)
    stress_score = db.Column(db.Integer, nullable=True)
    depression_score = db.Column(db.Integer, nullable=True)

    # Relationship with User
    user = db.relationship('User', backref=db.backref('assessments', lazy=True))