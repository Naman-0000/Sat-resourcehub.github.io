from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
# Vercel needs a static secret key to keep sessions alive across serverless spins
app.secret_key = os.environ.get("SECRET_KEY", "sat_hub_permanent_key_2024")

# ==========================
# DATABASE CONFIG
# ==========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        # Neon.tech requires sslmode=require for external connections
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except:
        return None

# ==========================
# QUESTION BANKS
# ==========================
# [KEEP YOUR ENTIRE math_questions = [...] LIST HERE]
# [KEEP YOUR ENTIRE english_questions = [...] LIST HERE]

# ==========================
# CORE ROUTES
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
            cur.execute("""
                SELECT subject, score, total_questions, timestamp 
                FROM quiz_results 
                WHERE username=%s 
                ORDER BY timestamp DESC
            """, (session['username'],))
            rows = cur.fetchall()
            for r in rows:
                quiz_results.append({
                    'subject': r[0], 'score': r[1],
                    'total_questions': r[2], 'timestamp': r[3]
                })
            cur.close()
            conn.close()
        except:
            pass
    return render_template("dashboard.html", quiz_results=quiz_results)

# ==========================
# THE REPAIRED QUIZ LOGIC
# ==========================

@app.route("/start-quiz/<int:duration>", methods=["GET", "POST"])
def start_quiz(duration):
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # 1. Pull correct answers from session (Only strings to keep cookie < 4KB)
        math_answers = session.get('m_ans', [])
        eng_answers = session.get('e_ans', [])
        
        results = []
        score = 0
        
        # 2. Grade Math
        for i, correct_val in enumerate(math_answers, start=1):
            user_val = request.form.get(f"math_{i}")
            is_correct = (str(user_val).strip() == str(correct_val).strip())
            if is_correct: score += 1
            results.append({
                "category": "Math",
                "user_answer": user_val, 
                "correct_answer": correct_val, 
                "is_correct": is_correct
            })

        # 3. Grade English
        for i, correct_val in enumerate(eng_answers, start=1):
            user_val = request.form.get(f"eng_{i}")
            is_correct = (str(user_val).strip() == str(correct_val).strip())
            if is_correct: score += 1
            results.append({
                "category": "English",
                "user_answer": user_val, 
                "correct_answer": correct_val, 
                "is_correct": is_correct
            })

        # 4. Save to Neon
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO quiz_results (username, subject, score, total_questions) 
                VALUES (%s, %s, %s, %s)
            """, (session['username'], "SAT Mixed", score, len(results)))
            conn.commit()
            cur.close()
            conn.close()

        return render_template("quiz-results.html", results=results, total_score=score, total_questions=len(results))

    # GET REQUEST: Generate Quiz
    num = 7 if duration == 30 else 12
    sel_math = random.sample(math_questions, min(len(math_questions), num))
    sel_eng = random.sample(english_questions, min(len(english_questions), num))
    
    # Store ONLY answers in session to prevent 500 Internal Error (Cookie overflow)
    session['m_ans'] = [q['answer'] for q in sel_math]
    session['e_ans'] = [q['answer'] for q in sel_eng]

    # Shuffle options locally for this specific view
    # This won't affect the 'answer' stored in session
    for q in sel_math + sel_eng:
        random.shuffle(q['options'])

    return render_template("start-quiz.html", math_questions=sel_math, english_questions=sel_eng, duration=duration)

# ==========================
# AUTHENTICATION
# ==========================

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
        flash("Invalid login credentials.")
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
            except Exception as e:
                flash("Username already exists.")
            finally:
                cur.close()
                conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# Static Pages
@app.route("/math")
def math(): return render_template("math.html")

@app.route("/english")
def english(): return render_template("english.html")

@app.route("/quiz-options")
def quiz_options(): return render_template("quiz-options.html")

if __name__ == "__main__":
    app.run()
