
from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import json
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

api_key = os.getenv("OPENAI_API_KEY")

# Database
def get_db():
    conn = sqlite3.connect("memoboat.db")
    conn.row_factory = sqlite3.Row
    return conn

# Routes

@app.route("/")
def index():
    conn = get_db()
    meeting_types = conn.execute("SELECT type_id, type_name FROM meeting_types").fetchall()
    conn.close()
    return render_template("index.html", meeting_types=meeting_types)

@app.route("/memos")
def memos_page():
    conn = get_db()
    rows = conn.execute("""
        SELECT t.transcript_id, t.timestamp, s.summary, mt.type_name
        FROM transcripts t
        JOIN summaries s ON t.transcript_id = s.transcript_id
        JOIN meeting_types mt ON t.type_id = mt.type_id
        ORDER BY t.transcript_id DESC
    """).fetchall()
    conn.close()

    memos = []
    for row in rows:
        memos.append({
            "id":        row["transcript_id"],
            "timestamp": row["timestamp"],
            "title":     row["summary"].split(".")[0].strip(),
            "type_name": row["type_name"]
        })

    return render_template("memos.html", memos=memos)

@app.route("/memo/<int:memo_id>")
def view_memo(memo_id):
    conn = get_db()
    row = conn.execute("""
        SELECT t.transcript_id, t.timestamp, s.summary, s.action_items, s.key_decisions, mt.type_name
        FROM transcripts t
        JOIN summaries s ON t.transcript_id = s.transcript_id
        JOIN meeting_types mt ON t.type_id = mt.type_id
        WHERE t.transcript_id = ?
    """, (memo_id,)).fetchone()
    conn.close()

    if row is None:
        return "Memo not found", 404

    memo = {
        "id":           row["transcript_id"],
        "timestamp":    row["timestamp"],
        "title":        row["summary"].split(".")[0].strip(),
        "summary":      row["summary"],
        "action_items": json.loads(row["action_items"]),
        "key_decisions":json.loads(row["key_decisions"]),
        "type_name":    row["type_name"]
    }

    return render_template("memo.html", memo=memo)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/generate", methods=["POST"])
def generate():
    data      = request.json
    notes     = data.get("notes", "")
    type_id   = data.get("type_id", 1)
    timestamp = datetime.now().strftime("%B %d, %Y %I:%M %p")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        },
        json={
            "model": "gpt-4.1",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that turns raw meeting notes into structured memos. "
                        "Respond ONLY with a valid JSON object. No extra text, no markdown fences. "
                        "The JSON must have exactly three keys: "
                        "\"summary\" (one clear paragraph), "
                        "\"action_items\" (array of strings, each an actionable task), "
                        "\"key_decisions\" (array of strings, each a decision that was made)."
                    )
                },
                {
                    "role": "user",
                    "content": "Here are the raw meeting notes:\n\n" + notes
                }
            ],
            "max_tokens": 800
        }
    )

    result = response.json()
    memo   = json.loads(result["choices"][0]["message"]["content"])

    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO transcripts (type_id, raw_notes, timestamp) VALUES (?, ?, ?)",
        (type_id, notes, timestamp)
    )
    transcript_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO summaries (transcript_id, summary, action_items, key_decisions) VALUES (?, ?, ?, ?)",
        (transcript_id, memo["summary"], json.dumps(memo["action_items"]), json.dumps(memo["key_decisions"]))
    )

    conn.commit()
    conn.close()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)