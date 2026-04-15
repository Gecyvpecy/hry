import os
import datetime
import random
import requests
import urllib3
from flask import Flask, request, jsonify, render_template

# --- 1. ZÁKLADNÍ NASTAVENÍ ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "tajny-klic-123")

# --- 2. VOLITELNÝ REDIS (S POJISTKOU) ---
# Pokusíme se importovat redis. Pokud v systému není, aplikace nespadne.
try:
    import redis
    redis_host = os.environ.get("REDIS_HOST", "cache")
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True, socket_connect_timeout=1)
    r.ping()
    print("Redis pripojen!")
except (ImportError, Exception):
    r = None
    print("Redis neni dostupny - jedeme v rezimu bez databaze.")

# --- 3. DATA KVÍZU ---
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

# --- 4. ROUTY ---

@app.route('/')
def index():
    try:
        random_questions = random.sample(ALL_QUESTIONS, 10)
        hall_of_fame = []
        if r:
            try:
                data = r.zrevrange("leaderboard", 0, 9, withscores=True)
                hall_of_fame = [{"name": name, "score": int(score)} for name, score in data]
            except:
                hall_of_fame = []
        
        return render_template('index.html', questions=random_questions, leaderboard=hall_of_fame)
    except Exception as e:
        return f"Chyba: {str(e)}", 500

@app.route('/submit', methods=['POST'])
def submit_score():
    if r:
        try:
            data = request.json or {}
            user = data.get("user", "Anonym").strip() or "Anonym"
            score = int(data.get("score", 0))
            r.zadd("leaderboard", {user: score})
        except:
            pass
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
