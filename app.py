import os
import sqlite3
import random
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "tajny-klic-123")

# --- 1. DATABÁZE (SQLite v perzistentním úložišti) ---
DB_PATH = "/data/quiz.db"

def init_db():
    # Pokud složka neexistuje (pro lokální testování), vytvoříme ji
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. DATA KVÍZU ---
ALL_QUESTIONS = [
    {"id": 1, "q": "Kolik srdcí má chobotnice?", "opts": ["Jedno", "Dvě", "Tři", "Čtyři"], "ans": 2},
    {"id": 2, "q": "Který savec má nejhustší srst?", "opts": ["Lední medvěd", "Vydra mořská", "Činčila", "Bobr"], "ans": 1},
    {"id": 3, "q": "Věda studující ptáky?", "opts": ["Entomologie", "Ornitologie", "Ichtyologie", "Herpetologie"], "ans": 1},
    {"id": 4, "q": "Nejvyšší krevní tlak má?", "opts": ["Žirafa", "Velryba", "Slon", "Gepard"], "ans": 0},
    {"id": 5, "q": "Létá pozpátku?", "opts": ["Rorýs", "Albatros", "Kolibřík", "Sokol"], "ans": 2},
    {"id": 6, "q": "Barva kůže ledního medvěda?", "opts": ["Bílá", "Růžová", "Černá", "Šedá"], "ans": 2},
    {"id": 7, "q": "Počet žaludků krávy?", "opts": ["1", "2", "3", "4"], "ans": 3},
    {"id": 8, "q": "Nejrychlejší mořský tvor?", "opts": ["Plachetník", "Žralok", "Kosatka", "Tuňák"], "ans": 0},
    {"id": 9, "q": "Březost slona afrického?", "opts": ["12 měsíců", "18 měsíců", "22 měsíců", "24 měsíců"], "ans": 2},
    {"id": 10, "q": "Nejsilnější jed na světě?", "opts": ["Kobra", "Mamba", "Taipan", "Chřestýš"], "ans": 2},
    {"id": 11, "q": "Který pták má největší rozpětí křídel?", "opts": ["Orel", "Kondor", "Albatros", "Pelikán"], "ans": 2},
    {"id": 12, "q": "Které zvíře neumí skákat?", "opts": ["Slon", "Hroch", "Nosorožec", "Všechna uvedená"], "ans": 0}
]

# --- 3. ROUTY ---

@app.route('/')
def index():
    random_questions = random.sample(ALL_QUESTIONS, 10)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    db_data = conn.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 10").fetchall()
    conn.close()
    
    hall_of_fame = [dict(row) for row in db_data]
    return render_template('index.html', questions=random_questions, leaderboard=hall_of_fame)

@app.route('/leaderboard')
def full_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    db_data = conn.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 50").fetchall()
    conn.close()
    
    hall_of_fame = [dict(row) for row in db_data]
    return render_template('leaderboard.html', leaderboard=hall_of_fame)

@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.json or {}
    user = data.get("user", "Anonym").strip() or "Anonym"
    score = int(data.get("score", 0))
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO leaderboard (name, score) VALUES (?, ?)", (user, score))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/ai', methods=['POST'])
def ai_comment():
    data = request.json or {}
    score = data.get("score", 0)
    user = data.get("user", "Hráč")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://kurim.ithope.eu/v1")

    payload = {
        "model": "gemma3:27b", 
        "messages": [
            {"role": "system", "content": "Jsi vtipný zoolog."},
            {"role": "user", "content": f"Hráč {user} získal {score}/10 v kvízu o zvířatech. Napiš jednu krátkou vtipnou větu v češtině."}
        ], 
        "stream": False
    }

    try:
        clean_url = f"{base_url.rstrip('/')}/chat/completions"
        res = requests.post(clean_url, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=8, verify=False)
        msg = res.json()['choices'][0]['message']['content'] if res.status_code == 200 else "Zvířata tleskají!"
        return jsonify({"ai_comment": msg})
    except:
        return jsonify({"ai_comment": "Zoolog má polední pauzu."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
