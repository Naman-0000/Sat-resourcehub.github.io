from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
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
# FULL SAT QUESTION BANK
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
    {"question": "Factor: x² + 5x + 6", "options": ["(x+2)(x+3)", "(x+1)(x+6)", "(x+2)(x+2)", "(x+3)(x+3)"], "answer": "(x+2)(x+3)"},
    {"question": "What is 15% of 200?", "options": ["25", "30", "35", "40"], "answer": "30"},
    {"question": "If y = 3x and x = 4, what is y?", "options": ["12", "7", "9", "16"], "answer": "12"},
    {"question": "Solve: 5(x - 2) = 20", "options": ["6", "4", "5", "8"], "answer": "6"},
    {"question": "What is the slope of a horizontal line?", "options": ["0", "Undefined", "1", "-1"], "answer": "0"},
    {"question": "Simplify: √64", "options": ["6", "7", "8", "9"], "answer": "8"},
]

english_questions = [
    {"question": "Choose the correct sentence.", "options": ["She go to school.", "She goes to school.", "She going school.", "She gone school."], "answer": "She goes to school."},
    {"question": "Synonym of 'meticulous'?", "options": ["Careless", "Precise", "Lazy", "Rough"], "answer": "Precise"},
    {"question": "Fill blank: He ___ to the store yesterday.", "options": ["go", "went", "gone", "going"], "answer": "went"},
    {"question": "Choose the correct sentence.", "options": ["They was late.", "They were late.", "They is late.", "They be late."], "answer": "They were late."},
    {"question": "Synonym of 'abundant'?", "options": ["Scarce", "Plentiful", "Tiny", "Weak"], "answer": "Plentiful"},
    {"question": "Fill in the blank: She has lived here ___ 2019.", "options": ["since", "for", "from", "by"], "answer": "since"},
    {"question": "Antonym of 'optimistic'?", "options": ["Hopeful", "Cheerful", "Pessimistic", "Excited"], "answer": "Pessimistic"},
    {"question": "Choose the correct word: Their / There / They're going home.", "options": ["Their", "There", "They're", "None"], "answer": "They're"},
    {"question": "Fill blank: The book is ___ the table.", "options": ["on", "in", "at", "by"], "answer": "on"},
    {"question": "Meaning of 'inevitable'?", "options": ["Avoidable", "Uncertain", "Certain to happen", "Rare"], "answer": "Certain to happen"},
    {"question": "Choose the grammatically correct sentence.", "options": ["Me and him went.", "He and I went.", "Him and me went.", "I and he gone."], "answer": "He and I went."},
    {"question": "Synonym of 'rapid'?", "options": ["Slow", "Fast", "Weak", "Heavy"], "answer": "Fast"},
    {"question": "Fill blank: She is better ___ math than science.", "options": ["in", "at", "on", "with"], "answer": "at"},
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
    
    quiz_results = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT subject, score, total_questions, timestamp FROM quiz_results WHERE username=%s ORDER BY timestamp DESC", (session['username'],))
            rows = cur.fetchall()
            for r in rows:
                quiz_results.append({'subject': r[0], 'score': r[1], 'total_questions': r[2], 'timestamp': r[3]})
            cur.close()
            conn.close()
        except:
            pass
    return render_template("dashboard.html", quiz_results=quiz_results)

@app.route("/start-quiz/<int:duration>", methods=["GET", "POST"])
def start_quiz(duration):
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # GET THE QUESTIONS SAVED IN SESSION
        selected_math = session.get('quiz_math_active', [])
        selected_english = session.get('quiz_eng_active', [])
        
        results = []
        score = 0
        
        # Grade Math (matching math_1, math_2 etc)
        for i, q in enumerate(selected_math, start=1):
            user_ans = request.form.get(f"math_{i}")
            is_correct = (str(user_ans).strip() == str(q["answer"]).strip())
            if is_correct: score += 1
            results.append({"question": q["question"], "user_answer": user_ans, "correct_answer": q["answer"], "is_correct": is_correct})
        
        # Grade English (matching eng_1, eng_2 etc)
        for i, q in enumerate(selected_english, start=1):
            user_ans = request.form.get(f"eng_{i}")
            is_correct = (str(user_ans).strip() == str(q["answer"]).strip())
            if is_correct: score += 1
            results.append({"question": q["question"], "user_answer": user_ans, "correct_answer": q["answer"], "is_correct": is_correct})

        total_qs = len(results)
        
        # SAVE TO DB
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO quiz_results (username, subject, score, total_questions) VALUES (%s, %s, %s, %s)", 
                        (session['username'], "SAT Mixed", score, total_qs))
            conn.commit()
            cur.close()
            conn.close()

        # Clear session quiz data
        session.pop('quiz_math_active', None)
        session.pop('quiz_eng_active', None)

        return render_template("quiz-results.html", results=results, total_score=score, total_questions=total_qs)

    # --- GET REQUEST ---
    num_questions = 7 if duration == 30 else 12
    sel_math = random.sample(math_questions, min(len(math_questions), num_questions))
    sel_eng = random.sample(english_questions, min(len(english_questions), num_questions))
    
    # SAVE to session so we can grade them on POST
    session['quiz_math_active'] = sel_math
    session['quiz_eng_active'] = sel_eng

    return render_template("start-quiz.html", math_questions=sel_math, english_questions=sel_eng, duration=duration)

# (KEEP YOUR LOGIN/REGISTER/LOGOUT ROUTES HERE)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                session["username"] = username
                return redirect(url_for("dashboard"))
        flash("Invalid login credentials.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                conn.commit()
                return redirect(url_for("login"))
            except:
                flash("User already exists.")
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
