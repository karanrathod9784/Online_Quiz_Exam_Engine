
import sqlite3

connection = sqlite3.connect("quiz.db")

users = connection.execute(
    "SELECT id, full_name, email, role FROM users"
).fetchall()

print("\nREGISTERED ACCOUNTS")

for user in users:
    print(user)

connection.close()
