import sqlite3

conn = sqlite3.connect("memoboat.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS meeting_types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_id INTEGER NOT NULL,
        raw_notes TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (type_id) REFERENCES meeting_types(type_id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transcript_id INTEGER NOT NULL,
        summary TEXT NOT NULL,
        action_items TEXT NOT NULL,
        key_decisions TEXT NOT NULL,
        FOREIGN KEY (transcript_id) REFERENCES transcripts(transcript_id)
    )
""")

# pre-populate meeting types
cursor.executemany(
    "INSERT INTO meeting_types (type_name) VALUES (?)",
    [
        ("Kickoff",),
        ("Weekly Sync",),
        ("Budget Review",),
        ("Retrospective",),
        ("Planning",),
        ("Other",)
    ]
)

conn.commit()
conn.close()
print("Database created successfully!")