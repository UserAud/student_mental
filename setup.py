from werkzeug.security import generate_password_hash
from app import app, db, User 

password = input("Enter password for admin: ")
email = input("Enter email for admin: ")

with app.app_context():
    db.create_all()

    # Create an admin user
    admin_user = User(username="admin", email=email, password=generate_password_hash(password), is_admin=True)

    # Add the user to the session and commit
    db.session.add(admin_user)
    db.session.commit()

print("Database and admin user created.")