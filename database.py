
import sqlite3

connection = sqlite3.connect("quiz.db")

connection.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

print("Database created successfully!")
print("Users table created successfully!")

connection.close()
