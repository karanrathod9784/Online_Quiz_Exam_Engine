
import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("quiz.db")

print("Create Admin Account")

full_name = input("Enter admin name: ").strip()
email = input("Enter admin email: ").strip().lower()
password = input("Enter admin password (minimum 8 characters): ")

if not full_name or not email or len(password) < 8:
    print("Invalid details. Please try again.")

else:
    password_hash = generate_password_hash(password)

    try:
        connection.execute(
            """
            INSERT INTO users
            (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, email, password_hash, "admin")
        )

        connection.commit()
        print("Admin account created successfully!")

    except sqlite3.IntegrityError:
        print("This email is already registered.")

connection.close()
