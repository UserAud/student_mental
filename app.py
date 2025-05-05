from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User

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
    
    return render_template('student/assessment.html', stats=statistics)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Ensure only admin can access this route
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))

    return render_template('admin/dashboard.html', stats=statistics)

@app.route('/student/assessment')
@login_required
def assessment():
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

if __name__ == '__main__':
    app.run(debug=True)