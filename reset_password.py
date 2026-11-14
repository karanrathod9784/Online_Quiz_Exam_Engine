
import sqlite3
from werkzeug.security import generate_password_hash

email = "rahul123@example.com"
new_password = input("Enter your new password: ")

if len(new_password) < 8:
    print("Password must be at least 8 characters.")
else:
    connection = sqlite3.connect("quiz.db")

    connection.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (generate_password_hash(new_password), email)
    )

    connection.commit()

    if connection.total_changes > 0:
        print("Student password reset successfully!")
    else:
        print("Student account not found!")

    connection.close()
