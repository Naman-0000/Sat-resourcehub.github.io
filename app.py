from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
# Use a fixed key so Vercel doesn't log you out
app.secret_key = os.environ.get("SECRET_KEY", "sat_hub_permanent_key_2024")

# ==========================
# DATABASE CONFIG (NEON)
# ==========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        return None
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None

# ==========================
# FULL SAT QUESTION BANK (With IDs)
# ==========================
# We added 'id' to every question so the computer remembers which one you answered
math_questions = [
    {"id": "m1", "question": "Solve for x: 3x - 5 = 16", "options": ["7", "5", "3", "9"], "answer": "7"},
    {"id": "m2", "question": "If x² = 49, what are the values of x?", "options": ["7", "-7", "7 and -7", "0"], "answer": "7 and -7"},
    {"id": "m3", "question": "What is the slope of y = 4x + 2?", "options": ["4", "2", "-4", "0"], "answer": "4"},
    {"id": "m4", "question": "Simplify: (x + 2)(x - 2)", "options": ["x² - 4", "x² + 4", "x² - 2", "x² + 2"], "answer": "x² - 4"},
    {"id": "m5", "question": "What is 30% of 250?", "options": ["75", "60", "80", "90"], "answer": "75"},
    {"id": "m6", "question": "Solve for x: 2x + 9 = 21", "options": ["6", "5", "7", "8"], "answer": "6"},
    {"id": "m7", "question": "What is the value of 5² + 3?", "options": ["28", "25", "23", "30"], "answer": "28"},
    {"id": "m8", "question": "If 4x = 36, what is x?", "options": ["8", "9", "7", "6"], "answer": "9"},
    {"id": "m9", "question": "What is the median of 3, 7, 9, 11, 15?", "options": ["9", "7", "11", "10"], "answer": "9"},
    {"id": "m10", "question": "Factor: x² + 5x + 6", "options": ["(x+2)(x+3)", "(x+1)(x+6)", "(x+2)(x+2)", "(x+3)(x+3)"], "answer": "(x+2)(x+3)"},
    {"id": "m11", "question": "What is 15% of 200?", "options": ["25", "30", "35", "40"], "answer": "30"},
    {"id": "m12", "question": "If y = 3x and x = 4, what is y?", "options": ["12", "7", "9", "16"], "answer": "12"},
    {"id": "m13", "question": "Solve: 5(x - 2) = 20", "options": ["6", "4", "5", "8"], "answer": "6"},
    {"id": "m14", "question": "What is the slope of a horizontal line?", "options": ["0", "Undefined", "1", "-1"], "answer": "0"},
    {"id": "m15", "question": "Simplify: √64", "options": ["6", "7", "8", "9"], "answer": "8"},
]

english_questions = [
    {"id": "e1", "question": "Choose the correct sentence.", "options": ["She go to school.", "She goes to school.", "She going school.", "She gone school."], "answer": "She goes to school."},
    {"id": "e2", "question": "Synonym of 'meticulous'?", "options": ["Careless", "Precise", "Lazy", "Rough"], "answer": "Precise"},
    {"id": "e3", "question": "Fill blank: He ___ to the store yesterday.", "options": ["go", "went", "gone", "going"], "answer": "went"},
    {"id": "e4", "question": "Choose the correct sentence.", "options": ["They was late.", "They were late.", "They is late.", "They be late."], "answer": "They were late."},
    {"id": "e5", "question": "Synonym of 'abundant'?", "options": ["Scarce", "Plentiful", "Tiny", "Weak"], "answer": "Plentiful"},
    {"id": "e6", "question": "Fill in the blank: She has lived here ___ 2019.", "options": ["since", "for", "from", "by"], "answer": "since"},
    {"id": "e7", "question": "Antonym of 'optimistic'?", "options": ["Hopeful", "Cheerful", "Pessimistic", "Excited"], "answer": "Pessimistic"},
    {"id": "e8", "question": "Choose the correct word: Their / There / They're going home.", "options": ["Their", "There", "They're", "None"], "answer": "They're"},
    {"id": "e9", "question": "Fill blank: The book is ___ the table.", "options": ["on", "in", "at", "by"], "answer": "on"},
    {"id": "e10", "question": "Meaning of 'inevitable'?", "options": ["Avoidable", "Uncertain", "Certain to happen", "Rare"], "answer": "Certain to happen"},
    {"id": "e11", "question": "Choose the grammatically correct sentence.", "options": ["Me and him went.", "He and I went.", "Him and me went.", "I and he gone."], "answer": "He and I went."},
    {"id": "e12", "question": "Synonym of 'rapid'?", "options": ["Slow", "Fast", "Weak", "Heavy"], "answer": "Fast"},
    {"id": "e13", "question": "Fill blank: She is better ___ math than science.", "options": ["in", "at", "on", "with"], "answer": "at"},
]

# Combined lookup list
ALL_QUESTIONS = math_questions + english_questions

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
                quiz_results.append({
                    'subject': r[0],
                    'score': r[1],
                    'total_questions': r[2],
                    'timestamp': r[3]
                })
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching scores: {e}")
            
    return render_template("dashboard.html", quiz_results=quiz_results)

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

    if request.method == "POST":
        # GET THE IDs WE SAVED IN THE GET REQUEST
        shown_ids = session.get('shown_ids', [])
        results = []
        score = 0
        
        for q_id in shown_ids:
            # Find the original question in the bank by its ID
            q_data = next((q for q in ALL_QUESTIONS if q["id"] == q_id), None)
            if q_data:
                # In start-quiz.html, inputs must be named name="q_{{ q.id }}"
                user_ans = request.form.get(f"q_{q_id}")
                is_correct = (str(user_ans).strip() == str(q_data["answer"]).strip())
                if is_correct:
                    score += 1
                results.append({
                    "question": q_data["question"],
                    "user_answer": user_ans or "No Answer",
                    "correct_answer": q_data["answer"],
                    "is_correct": is_correct
                })

        # SAVE TO DB
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO quiz_results (username, subject, score, total_questions) VALUES (%s, %s, %s, %s)", 
                        (session['username'], "SAT Mixed", score, len(results)))
            conn.commit()
            cur.close()
            conn.close()

        session.pop('shown_ids', None) # Clear for next time
        return render_template("quiz-results.html", results=results, total_score=score, total_questions=len(results))

    # --- GET REQUEST (Load Quiz) ---
    num_questions = 7 if duration == 30 else 12
    sel_math = random.sample(math_questions, min(len(math_questions), num_questions))
    sel_eng = random.sample(english_questions, min(len(english_questions), num_questions))
    
    # Store the exact IDs shown to this user in the session
    session['shown_ids'] = [q['id'] for q in sel_math] + [q['id'] for q in sel_eng]

    return render_template("start-quiz.html", math_questions=sel_math, english_questions=sel_eng, duration=duration)

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
                flash("Account created! Please login.")
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
    app.run()
