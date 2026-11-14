import os
import matplotlib

# Use a non-GUI backend for Flask
matplotlib.use("Agg")

import matplotlib.pyplot as plt



from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request,
    redirect, url_for, session,flash
)
from flask_wtf.csrf import CSRFProtect
import sqlite3
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[]
)
# Enable CSRF protection
csrf = CSRFProtect(app)

# Development secret key only.
# Set a strong SECRET_KEY environment variable before deployment.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-only-secret-key-change-before-deployment"
)
# Session Security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "false").lower() == "true"
)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


def get_db_connection():
    connection = sqlite3.connect("quiz.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if (
    not full_name
    or not email
    or len(password) < 8
    or not any(char.isupper() for char in password)
    or not any(char.islower() for char in password)
    or not any(char.isdigit() for char in password)
):
            return render_template(
                "register.html",
                error="Please enter valid details. Password must be at least 8 characters.",
                full_name=full_name,
                email=email
            )

        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                """INSERT INTO users
                (full_name, email, password_hash)
                VALUES (?, ?, ?)""",
                (full_name, email, password_hash)
            )

            connection.commit()

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return render_template(
                "register.html",
                error="This email is already registered.",
                full_name=full_name,
                email=email
            )

        finally:
            connection.close()

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if (
            user
            and user["role"] == "student"
            and check_password_hash(user["password_hash"], password)
        ):
            session.clear()
            # Enable permanent session
            session.permanent = True
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password. Please try again.",
            email=email
        )

    return render_template("login.html", email="")




@app.route("/dashboard")
def dashboard():

    if session.get("role") != "student":
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        full_name=session["full_name"]
    )




@app.route("/logout")
def logout():
    session.clear()
    response = redirect(url_for("home"))
    response.delete_cookie("session")
    return response


@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def admin_login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if (
            user
            and user["role"] == "admin"
            and check_password_hash(user["password_hash"], password)
        ):
            session.clear()
             # Enable permanent session
            session.permanent = True

            session["user_id"] = user["id"]
            session["role"] = "admin"

            return redirect(url_for("admin_dashboard"))

        return "Invalid admin email or password!"

    return render_template("admin_login.html")



@app.route("/admin/dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    # Fetch all quizzes
    quizzes = connection.execute(
        "SELECT * FROM quizzes ORDER BY id DESC"
    ).fetchall()

    # Count registered students
    total_students = connection.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'student'"
    ).fetchone()[0]

    # Count quizzes
    total_quizzes = connection.execute(
        "SELECT COUNT(*) FROM quizzes"
    ).fetchone()[0]

    # Count all quiz attempts
    total_attempts = connection.execute(
        "SELECT COUNT(*) FROM quiz_attempts"
    ).fetchone()[0]

    # Count submitted results
    total_submissions = connection.execute(
        "SELECT COUNT(*) FROM results"
    ).fetchone()[0]

    # Calculate average score percentage
    average_score = connection.execute(
        """
        SELECT AVG(
            score * 100.0 / NULLIF(total_questions, 0)
        )
        FROM results
        """
    ).fetchone()[0]

    connection.close()

    if average_score is None:
        average_score = 0

    return render_template(
        "admin_dashboard.html",
        quizzes=quizzes,
        total_students=total_students,
        total_quizzes=total_quizzes,
        total_attempts=total_attempts,
        total_submissions=total_submissions,
        average_score=round(average_score, 1)
    )




@app.route("/admin/logout")
def admin_logout():
    session.clear()
    response = redirect(url_for("home"))
    response.delete_cookie("session")
    return response


@app.route("/admin/quizzes/create", methods=["GET", "POST"])
def create_quiz():

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    if request.method == "POST":

        title = request.form["title"].strip()
        description = request.form["description"].strip()
        duration = request.form["duration_minutes"]

        if not title or not duration:
            return "Please enter all required details."

        try:
            duration = int(duration)

            if duration < 1:
                return "Duration must be at least 1 minute."

            connection = get_db_connection()

            connection.execute(
                """INSERT INTO quizzes
                (title, description, duration_minutes)
                VALUES (?, ?, ?)""",
                (title, description, duration)
            )

            connection.commit()
            connection.close()

            return redirect(url_for("admin_dashboard"))

        except ValueError:
            return "Please enter a valid duration."

    return render_template("create_quiz.html")


@app.route("/admin/quizzes")
def admin_quizzes():

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    quizzes = connection.execute(
        "SELECT * FROM quizzes ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "admin_dashboard.html",
        quizzes=quizzes
    )


@app.route("/admin/quizzes/<int:quiz_id>/add-question",
           methods=["GET", "POST"])
def add_question(quiz_id):

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    quiz = connection.execute(
        "SELECT * FROM quizzes WHERE id = ?",
        (quiz_id,)
    ).fetchone()

    if quiz is None:
        connection.close()
        return "Quiz not found!", 404

    if request.method == "POST":

        question_text = request.form["question_text"].strip()
        option_a = request.form["option_a"].strip()
        option_b = request.form["option_b"].strip()
        option_c = request.form["option_c"].strip()
        option_d = request.form["option_d"].strip()
        correct_answer = request.form["correct_answer"]

        if not all([
            question_text, option_a, option_b,
            option_c, option_d
        ]):
            connection.close()
            return "All fields are required!"

        if correct_answer not in ["A", "B", "C", "D"]:
            connection.close()
            return "Invalid correct answer!"

        connection.execute(
            """INSERT INTO questions
            (quiz_id, question_text, option_a, option_b,
             option_c, option_d, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                quiz_id, question_text, option_a, option_b,
                option_c, option_d, correct_answer
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("admin_dashboard"))

    connection.close()

    return render_template("add_question.html", quiz=quiz)

@app.route("/admin/results")
def admin_results():

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    # Fetch all submitted quiz results
    results = connection.execute(
        """
        SELECT
            results.id,
            users.full_name,
            users.email,
            quizzes.title,
            results.score,
            results.total_questions,
            results.submitted_at
        FROM results
        JOIN users ON results.user_id = users.id
        JOIN quizzes ON results.quiz_id = quizzes.id
        ORDER BY results.submitted_at DESC
        """
    ).fetchall()

    # Fetch all quiz attempts, including expired attempts
    attempts = connection.execute(
        """
        SELECT
            quiz_attempts.id,
            users.full_name,
            users.email,
            quizzes.title,
            quiz_attempts.started_at,
            quiz_attempts.submitted_at,
            quiz_attempts.status
        FROM quiz_attempts
        JOIN users ON quiz_attempts.user_id = users.id
        JOIN quizzes ON quiz_attempts.quiz_id = quizzes.id
        ORDER BY quiz_attempts.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_results.html",
        results=results,
        attempts=attempts
    )
@app.route("/admin/analytics")
def admin_analytics():

    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    # Get quiz-wise average percentages
    quiz_data = connection.execute(
        """
        SELECT
            quizzes.title,
            AVG(
                results.score * 100.0 /
                NULLIF(results.total_questions, 0)
            ) AS average
        FROM quizzes
        LEFT JOIN results
            ON quizzes.id = results.quiz_id
        GROUP BY quizzes.id, quizzes.title
        """
    ).fetchall()

    # Get attempt statuses
    status_data = connection.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM quiz_attempts
        GROUP BY status
        """
    ).fetchall()

    connection.close()

    # Prepare chart data
    quiz_names = [row["title"] for row in quiz_data]
    averages = [
        row["average"] if row["average"] is not None else 0
        for row in quiz_data
    ]

    # Create static folder if it doesn't exist
    os.makedirs("static", exist_ok=True)

    # Bar chart
    plt.figure(figsize=(9, 5))
    plt.bar(quiz_names, averages)
    plt.title("Quiz-wise Average Performance")
    plt.xlabel("Quiz Name")
    plt.ylabel("Average Score (%)")
    plt.ylim(0, 100)
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig("static/quiz_performance.png")
    plt.close()

    # Pie chart
    statuses = [row["status"] for row in status_data]
    counts = [row["total"] for row in status_data]

    plt.figure(figsize=(7, 5))

    if counts and sum(counts) > 0:
        plt.pie(
            counts,
            labels=statuses,
            autopct="%1.1f%%",
            startangle=90
        )
        plt.title("Quiz Attempt Status")
    else:
        plt.text(0.5, 0.5, "No attempts available",
                 ha="center", va="center")
        plt.axis("off")

    plt.tight_layout()
    plt.savefig("static/attempt_status.png")
    plt.close()

    return render_template("admin_analytics.html")

@app.route("/student/quizzes")
def available_quizzes():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    connection = get_db_connection()

    quiz_rows = connection.execute(
        """
        SELECT
            q.*,
            a.id AS attempt_id,
            a.status AS attempt_status,
            a.expires_at
        FROM quizzes q
        LEFT JOIN quiz_attempts a
            ON a.id = (
                SELECT MAX(id)
                FROM quiz_attempts
                WHERE quiz_id = q.id
                AND user_id = ?
            )
        ORDER BY q.id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    quizzes = []
    now = datetime.now()

    for row in quiz_rows:
        quiz = dict(row)

        if row["attempt_id"] is None:
            quiz["display_status"] = "Not Attempted"

        elif row["attempt_status"] == "submitted":
            quiz["display_status"] = "Completed"

        elif row["attempt_status"] == "expired":
            quiz["display_status"] = "Expired"

        elif row["attempt_status"] == "active":
            expires = datetime.fromisoformat(row["expires_at"])

            if now >= expires:
                connection.execute(
                    """
                    UPDATE quiz_attempts
                    SET status = 'expired'
                    WHERE id = ? AND status = 'active'
                    """,
                    (row["attempt_id"],)
                )
                quiz["display_status"] = "Expired"
            else:
                quiz["display_status"] = "In Progress"

        else:
            quiz["display_status"] = "Not Attempted"

        quizzes.append(quiz)

    connection.commit()
    connection.close()

    return render_template(
        "available_quizzes.html",
        quizzes=quizzes
    )





@app.route("/student/quiz/<int:quiz_id>")
def start_quiz(quiz_id):

    if session.get("role") != "student":
        return redirect(url_for("login"))

    connection = get_db_connection()
    connection.execute("BEGIN IMMEDIATE")

    quiz = connection.execute(
        "SELECT * FROM quizzes WHERE id = ?",
        (quiz_id,)
    ).fetchone()

    if quiz is None:
        connection.rollback()
        connection.close()
        return "Quiz not found!", 404

    questions = connection.execute(
        """SELECT id, question_text, option_a, option_b,
        option_c, option_d FROM questions WHERE quiz_id = ?""",
        (quiz_id,)
    ).fetchall()

    if not questions:
        connection.rollback()
        connection.close()
        return "This quiz has no questions yet."

    now = datetime.now()

    # Check the student's previous attempt
    attempt = connection.execute(
        """SELECT * FROM quiz_attempts
        WHERE user_id = ? AND quiz_id = ?
        ORDER BY id DESC LIMIT 1""",
        (session["user_id"], quiz_id)
    ).fetchone()

    if attempt is not None:

        if attempt["status"] == "active":

            expires = datetime.fromisoformat(
                attempt["expires_at"]
            )

            if now >= expires:

                connection.execute(
                    """UPDATE quiz_attempts
                    SET status = 'expired', submitted_at = ?
                    WHERE id = ? AND status = 'active'""",
                    (now.isoformat(), attempt["id"])
                )

                connection.commit()
                connection.close()

                return "Your exam time has expired. Retakes are not allowed."

        else:
            connection.rollback()
            connection.close()

            return "You have already attempted this quiz. Retakes are not allowed."

        expires = datetime.fromisoformat(
            attempt["expires_at"]
        )

    else:

        # Create a new attempt only if no previous attempt exists
        expires = now + timedelta(
            minutes=quiz["duration_minutes"]
        )

        connection.execute(
            """INSERT INTO quiz_attempts
            (user_id, quiz_id, started_at, expires_at)
            VALUES (?, ?, ?, ?)""",
            (
                session["user_id"],
                quiz_id,
                now.isoformat(),
                expires.isoformat()
            )
        )

    connection.commit()
    connection.close()

    return render_template(
        "attempt_quiz.html",
        quiz=quiz,
        questions=questions,
        expires_at_ms=int(expires.timestamp() * 1000)
    )


@app.route("/student/quiz/<int:quiz_id>/submit",
           methods=["POST"])
def submit_quiz(quiz_id):

    if session.get("role") != "student":
        return redirect(url_for("login"))

    connection = get_db_connection()

    # Lock the database transaction while checking the attempt.
    connection.execute("BEGIN IMMEDIATE")

    attempt = connection.execute(
        """SELECT * FROM quiz_attempts
        WHERE user_id = ? AND quiz_id = ? AND status = 'active'
        ORDER BY id DESC LIMIT 1""",
        (session["user_id"], quiz_id)
    ).fetchone()

    if attempt is None:
        connection.rollback()
        connection.close()
        return "No active attempt found. You may have already submitted."

    now = datetime.now()
    expires = datetime.fromisoformat(attempt["expires_at"])

    questions = connection.execute(
        """SELECT id, correct_answer FROM questions
        WHERE quiz_id = ?""",
        (quiz_id,)
    ).fetchall()

    total_questions = len(questions)

    if total_questions == 0:
        connection.rollback()
        connection.close()
        return "No questions found!", 404

    score = 0

    # Allow a small grace period for network delay.
    grace_period = timedelta(seconds=10)

    if now <= expires + grace_period:

        for question in questions:

            selected_answer = request.form.get(
                f"question_{question['id']}"
            )

            if selected_answer == question["correct_answer"]:
                score += 1

        status = "submitted"

    else:
        # Submissions beyond the grace period receive zero marks.
        status = "expired"

    connection.execute(
        """UPDATE quiz_attempts
        SET status = ?, submitted_at = ?
        WHERE id = ? AND status = 'active'""",
        (status, now.isoformat(), attempt["id"])
    )

    connection.execute(
        """INSERT INTO results
        (user_id, quiz_id, score, total_questions)
        VALUES (?, ?, ?, ?)""",
        (
            session["user_id"],
            quiz_id,
            score,
            total_questions
        )
    )

    connection.commit()
    connection.close()

    return render_template(
        "result.html",
        score=score,
        total_questions=total_questions
    )

@app.route("/student/results")
def student_results():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    connection = get_db_connection()

    results = connection.execute(
        """
        SELECT
            results.id,
            results.score,
            results.total_questions,
            results.submitted_at,
            quizzes.title
        FROM results
        JOIN quizzes
            ON results.quiz_id = quizzes.id
        WHERE results.user_id = ?
        ORDER BY results.submitted_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "student_results.html",
        results=results
    )
@app.errorhandler(429)
def ratelimit_error(error):
    return render_template("429.html"), 429

if __name__ == "__main__":
    app.run(debug=False)
