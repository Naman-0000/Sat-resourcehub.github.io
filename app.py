from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import psycopg2

app = Flask(__name__)

# Fixed key for Vercel
app.secret_key = os.environ.get("SECRET_KEY", "sat_hub_permanent_key_2024")

# ==========================
# NEON DATABASE CONFIG
# ==========================

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# ==========================
# SAT QUESTION BANK
# ==========================

math_questions = [
    {"question": "Solve for x: 3x - 5 = 16", "options": ["7", "5", "3", "9"], "answer": "7"},
    {"question": "If x² = 49, what are the values of x?", "options": ["7", "-7", "7 and -7", "0"], "answer": "7 and -7"},
    {"question": "What is 30% of 250?", "options": ["75", "60", "80", "90"], "answer": "75"}
]

english_questions = [
    {"question": "Choose the correct sentence.", "options": ["She go to school.", "She goes to school.", "She going school.", "She gone school."], "answer": "She goes to school."},
    {"question": "Synonym of 'meticulous'?", "options": ["Careless", "Precise", "Lazy", "Rough"], "answer": "Precise"}
]

# ==========================
# ROUTES
# ==========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    # If user isn't logged in, send them to login page
    if "username" not in session:
        flash("Please login to access your dashboard.")
        return redirect(url_for("login"))
    
    # We pass an empty list for now since we aren't saving scores yet
    return render_template("dashboard.html", quiz_results=[])

@app.route("/math")
def math():
    return render_template("math.html")

@app.route("/english")
def english():
    return render_template("english.html")

@app.route("/quiz")
def quiz():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("quiz.html")

@app.route("/quiz-options")
def quiz_options():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("quiz-options.html")

@app.route("/start-quiz/<int:duration>", methods=["GET", "POST"])
def start_quiz(duration):
    if "username" not in session:
        return redirect(url_for("login"))

    num_questions = 7 if duration == 30 else 12
    selected_math = random.sample(math_questions, min(len(math_questions), num_questions))
    selected_english = random.sample(english_questions, min(len(english_questions), num_questions))

    if request.method == "POST":
        results = []
        total_score = 0
        for i, q in enumerate(selected_math, start=1):
            user_ans = request.form.get(f"math_{i}")
            if user_ans == q["answer"]: total_score += 1
            results.append({"question": q["question"], "user_answer": user_ans, "correct_answer": q["answer"], "is_correct": (user_ans == q["answer"])})
        
        return render_template("quiz-results.html", results=results, total_score=total_score, total_questions=len(results))

    return render_template("start-quiz.html", math_questions=selected_math, english_questions=selected_english, duration=duration)

# ==========================
# LOGIN / REGISTER
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.")
            return redirect(url_for("login"))
        
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session["username"] = username
            # REDIRECT TO DASHBOARD AFTER LOGIN
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.")
            return redirect(url_for("register"))

        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            flash("Account created! You can now login.")
            return redirect(url_for("login"))
        except Exception:
            flash("User already exists or error occurred.")
        finally:
            cur.close()
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()
