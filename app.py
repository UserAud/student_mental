from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mental_health.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define TestUser ONCE properly here
class TestUser(UserMixin):
    def __init__(self, id, username):
        self.id = int(id)
        self.username = username
        self.is_admin = (self.username == 'admin')

@login_manager.user_loader
def load_user(user_id):
    # when Flask-Login calls this, we recreate a TestUser
    if int(user_id) == 1:
        return TestUser(1, 'admin')
    else:
        return TestUser(2, 'student')

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')

        # Reuse the same TestUser class
        user = TestUser(1 if username == 'admin' else 2, username)
        login_user(user, remember=True)
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student/home')
@login_required
def student_home():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return render_template('student/home.html')

@app.route('/student/assessment')
@login_required
def assessment():
    return render_template('student/assessment.html')

@app.route('/student/chatbot')
@login_required
def chatbot():
    return render_template('student/chatbot.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('student_home'))
    
    # Mock statistics data (replace with actual database queries later)
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
    
    return render_template('admin/dashboard.html', stats=statistics)

if __name__ == '__main__':
    app.run(debug=True)
