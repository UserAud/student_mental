# Student Mental Health Portal

A web-based application designed to assess and monitor student mental health, providing personalized recommendations and administrative oversight for educational institutions.

## Features

### For Students
- **Mental Health Assessment**: Comprehensive questionnaire covering:
  - Anxiety indicators
  - Stress levels
  - Depression symptoms
- **Personal Dashboard**: Track assessment history and progress
- **Instant Results**: Receive immediate feedback and recommendations
- **Confidential Access**: Secure login and data protection

### For Administrators
- **Dashboard Analytics**: Monitor mental health trends across the student population
- **Risk Management**: Track high-risk cases and intervention status
- **Statistical Overview**: View depression, anxiety, and stress rates
- **Year-wise Analysis**: Break down mental health trends by academic year

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Bootstrap, HTML/CSS, JavaScript
- **Authentication**: Flask-Login
- **Additional Libraries**:
  - Pandas for data analysis
  - Plotly for visualization
  - PyTZ for timezone handling

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/student_mental.git
cd student_mental
```
2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Set up the database and create admin user:
```bash
python setup.py
```
5. Run the application:
```bash
python app.py
```


## Project Structure
- app.py : Main application file with routes and core logic
- models.py : Database models for User and Assessment
- setup.py : Database initialization and admin user creation
- templates/ : HTML templates
  - admin/ : Admin dashboard templates
  - student/ : Student interface templates
- static/ : CSS and JavaScript files
- data / : The datasets used throughout the data analysis and modeling pipeline.
- notebook/ : Jupyter notebook workspace for developing machine learning models.

## Assessment Components
### Demographics
- Age
- Gender
- University
- Department
- Academic Year
- CGPA
- Scholarship Status

### Mental Health Indicators
- Anxiety (7 indicators)
- Stress (10 indicators)
- Depression (9 indicators)

## Security Features
- Password hashing
- User session management
- Role-based access control
- Form validation and CSRF protection

## Contributing
This project is part of WQD7012 coursework at Universiti Malaya.

## License
[MIT License](LICENSE)
