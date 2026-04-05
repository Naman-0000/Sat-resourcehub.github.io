from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
# Permanent key for session persistence on Vercel
app.secret_key = os.environ.get("SECRET_KEY", "sat_hub_2026_secure_key")

# ==========================
# DATABASE CONFIG
# ==========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        # Crucial for Neon: sslmode is required
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# ==========================
# FULL QUESTION BANK
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
    {"question": "What is the area of a circle with radius 3? (Use π ≈ 3.14)", "options": ["28.26", "18.84", "9.42", "31.4"], "answer": "28.26"},
    {"question": "Solve for y: y/4 + 2 = 10", "options": ["32", "24", "48", "36"], "answer": "32"}
]

english_questions = [
    {"question": "Choose the correct sentence.", "options": ["She go to school.", "She goes to school.", "She going school.", "She gone school."], "answer": "She goes to school."},
    {"question": "Synonym of 'meticulous'?", "options": ["Careless", "Precise", "Lazy", "Rough"], "answer": "Precise"},
    {"question": "Fill blank: He ___ to the store yesterday.", "options": ["go", "went", "gone", "going"], "answer": "went"},
    {"question": "Antonym of 'optimistic'?", "options": ["Hopeful", "Cheerful", "Pessimistic", "Excited"], "answer": "Pessimistic"},
    {"question": "Which word is a verb?", "options": ["Quickly", "Run", "Beautiful", "Apple"], "answer": "Run"},
    {"question": "Correct the punctuation: 'Its raining outside.'", "options": ["It's raining outside.", "Its' raining outside.", "Its raining outside!", "No change."], "answer": "It's raining outside."},
    {"question": "Identify the conjunction: 'I like tea and coffee.'", "options": ["like", "tea", "and", "coffee"], "answer": "and"},
    {"question": "Synonym of 'ubiquitous'?", "options": ["Rare", "Everywhere", "Hidden", "Small"], "answer": "Everywhere"}
]

# ==========================
# MAIN ROUTES
# ==========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/math")
def math():
    return render_template("math.html")

@app.route("/english")
def english():
    return render_template("english.html")

@app.route("/quiz-options")
def quiz_options():
    return render_template("quiz-options.html")

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
        except Exception as e:
            print(f"Error fetching results: {e}")
            
    return render_template("dashboard.html", quiz_results=quiz_results)

# ==========================
# QUIZ CORE LOGIC
# ==========================

@app.route("/start-quiz/<int:duration>", methods=["GET", "POST"])
def start_quiz(duration):
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Pull correct answers stored in session (keeps cookie size small)
        math_answers = session.get('m_ans', [])
        eng_answers = session.get('e_ans', [])
        
        results = []
        score = 0
        
        # Grade Math
        for i, correct_val in enumerate(math_answers, start=1):
            user_val = request.form.get(f"math_{i}")
            is_correct = (str(user_val).strip() == str(correct_val).strip())
            if is_correct: score += 1
            results.append({"category": "Math", "user_answer": user_val, "correct_answer": correct_val, "is_correct": is_correct})

        # Grade English
        for i, correct_val in enumerate(eng_answers, start=1):
            user_val = request.form.get(f"eng_{i}")
            is_correct = (str(user_val).strip() == str(correct_val).strip())
            if is_correct: score += 1
            results.append({"category": "English", "user_answer": user_val, "correct_answer": correct_val, "is_correct": is_correct})

        # Save to Database
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

    # GET REQUEST Logic
    num = 7 if duration == 30 else 12
    sel_math = random.sample(math_questions, min(len(math_questions), num))
    sel_eng = random.sample(english_questions, min(len(english_questions), num))
    
    # Store ONLY answers in session to prevent "500 Internal Server Error" (Cookie Overflow)
    session['m_ans'] = [q['answer'] for q in sel_math]
    session['e_ans'] = [q['answer'] for q in sel_eng]

    # Shuffle for the view
    for q in sel_math + sel_eng:
        random.shuffle(q['options'])

    return render_template("start-quiz.html", math_questions=sel_math, english_questions=sel_eng, duration=duration)

# ==========================
# AUTHENTICATION
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
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
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (u, p))
                conn.commit()
                flash("Registration successful! Please login.")
                return redirect(url_for("login"))
            except Exception:
                flash("Username already exists.")
            finally:
                cur.close()
                conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
