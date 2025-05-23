from werkzeug.security import generate_password_hash
from app import app, db, User
import os
from dotenv import load_dotenv

load_dotenv()

# Load admin credentials from environment variables
password = os.getenv("ADMIN_PASSWORD")
email = os.getenv("ADMIN_EMAIL")

with app.app_context():
    db.create_all()

    # Remove any existing user with the same username or email
    existing_user = User.query.filter(
        (User.username == "admin") | (User.email == email)
    ).first()
    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()
        print("Deleted existing admin user.")

    # Create an admin user
    admin_user = User(username="admin", email=email, password=generate_password_hash(password), is_admin=True)

    # Add the user to the session and commit
    db.session.add(admin_user)
    db.session.commit()

print("Database and admin user created.")
