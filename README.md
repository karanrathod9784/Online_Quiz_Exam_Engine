# Online Quiz and Exam Engine

A web-based quiz and examination platform developed using Python and Flask. It allows students to attempt quizzes, receive automatically calculated scores, and track their performance.

## Live Demo

https://online-quiz-exam-engine.onrender.com

## GitHub Repository

https://github.com/karanrathod9784/Online_Quiz_Exam_Engine

## Features

- Student Registration and Login
- Admin Authentication
- Quiz Creation and Management
- Question Management
- Online Quiz Attempts
- Automatic Score Calculation
- Student Result History
- Admin Analytics and Performance Charts

## Technologies Used

- Python
- Flask
- PostgreSQL
- Supabase
- HTML
- CSS
- Git and GitHub
- Render

## Project Structure

```text
Online_Quiz_Exam_Engine/
│
├── app.py
├── database.py
├── requirements.txt
├── Procfile
├── templates/
├── static/
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/karanrathod9784/Online_Quiz_Exam_Engine.git
```

### 2. Open the project folder

```bash
cd Online_Quiz_Exam_Engine
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Set the following environment variables:

- `SECRET_KEY`
- `DATABASE_URL`
- `COOKIE_SECURE`

Use your own Supabase PostgreSQL connection details. Never upload passwords or secret keys to GitHub.

For local development, configure `COOKIE_SECURE` according to your local HTTP/HTTPS setup.

### 7. Run the application

```bash
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000

## Deployment

The application is deployed using Render, with Supabase PostgreSQL as the database.

## Author

Developed as a student project to gain practical experience in Python web development, database integration and application deployment.