from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
# Static key for Vercel persistence
app.secret_key = os.environ.get("SECRET_KEY", "sat_hub_permanent_key_2024")

# ==========================
# DATABASE CONFIG
# ==========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except:
        return None

# ==========================
# QUESTION BANK
# ==========================
math_questions = [
    {"question": "Solve for x: 3x - 5 = 16", "options": ["7", "5", "3", "9"], "answer": "7"},
    {"question": "If x² = 49, what are the values of x?", "options": ["7", "-7", "7 and -7", "0"], "answer": "7 and -7"},
    {"question": "What is the slope of y = 4x + 2?", "options": ["4", "2", "-4", "0"], "answer": "4"},
    {"question": "Simplify: (x + 2)(x - 2)", "options": ["x² - 4", "x² + 4", "x² - 2", "x² + 2"], "answer": "x² - 4"},
    {"question": "What is 30% of 250?", "options": ["75", "60", "80", "90"], "answer": "75"},
    {"question": "Solve for x: 2x + 9 = 21", "options": ["6", "5", "7", "8"], "answer": "6"},
    {"question": "What is the value of 5² + 3?", "options": ["28", "25", "23", "30"], "answer": "28"},
    {"question": "If 4x = 36, what is x?", "options": ["8", "9", "7", "6"], "answer": "9"},
    {"question": "What is the median of 3, 7, 9, 11, 15?", "options": ["9", "7", "11", "10"], "answer": "9"},
    {"question": "Factor: x² + 5x + 6", "options": ["(x+2)(x+3)", "(x+1)(x+6)", "(x+2)(x+2)", "(x+3)(x+3)"], "answer": "(x+2)(x+3)"}
]

english_questions = [
    {"question": "Choose the correct sentence.", "options": ["She go to school.", "She goes to school.", "She going school.", "She gone school."], "answer": "She goes to school."},
    {"question": "Synonym of 'meticulous'?", "options": ["Careless", "Precise", "Lazy", "Rough"], "answer": "Precise"},
    {"question": "Fill blank: He ___ to the store yesterday.", "options": ["go", "went", "gone", "going"], "answer": "went"},
    {"question": "Antonym of 'optimistic'?", "options": ["Hopeful", "Cheerful", "Pessimistic", "Excited"], "answer": "Pessimistic"}
]

# ==========================
# ROUTES
# ==========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    
    results_list = []
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT subject, score, total_questions, timestamp FROM quiz_results WHERE username=%s ORDER BY timestamp DESC", (session['username'],))
        rows = cur.fetchall()
        for r in rows:
            results_list.append({'subject': r[0], 'score': r[1], 'total_questions': r[2], 'timestamp': r[3]})
        cur.close()
        conn.close()
    return render_template("dashboard.html", quiz_results=results_list)

@app.route("/quiz-options")
def quiz_options():
    return render_template("quiz-options.html")

@app.route("/start-quiz/<int:duration>", methods=["GET", "POST"])
def start_quiz(duration):
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        math_ans = session.get('m_ans', [])
        eng_ans = session.get('e_ans', [])
        
        results = []
        score = 0
        
        for i, correct in enumerate(math_ans, start=1):
            user_val = request.form.get(f"math_{i}")
            is_correct = (str(user_val).strip() == str(correct).strip())
            if is_correct: score += 1
            results.append({"cat": "Math", "user": user_val, "correct": correct, "is_correct": is_correct})

        for i, correct in enumerate(eng_ans, start=1):
            user_val = request.form.get(f"eng_{i}")
            is_correct = (str(user_val).strip() == str(correct).strip())
            if is_correct: score += 1
            results.append({"cat": "English", "user": user_val, "correct": correct, "is_correct": is_correct})

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO quiz_results (username, subject, score, total_questions) VALUES (%s, %s, %s, %s)", 
                        (session['username'], "SAT Mixed", score, len(results)))
            conn.commit()
            cur.close()
            conn.close()

        return render_template("quiz-results.html", results=results, total_score=score, total_questions=len(results))

    # GET Logic
    num = 7 if duration == 30 else 12
    sel_math = random.sample(math_questions, min(len(math_questions), num))
    sel_eng = random.sample(english_questions, min(len(english_questions), num))
    
    session['m_ans'] = [q['answer'] for q in sel_math]
    session['e_ans'] = [q['answer'] for q in sel_eng]

    for q in sel_math + sel_eng:
        random.shuffle(q['options'])

    return render_template("start-quiz.html", math_questions=sel_math, english_questions=sel_eng, duration=duration)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                session["username"] = u
                return redirect(url_for("dashboard"))
        flash("Invalid Login")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (u, p))
                conn.commit()
                return redirect(url_for("login"))
            except: flash("User exists")
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
