import sqlite3
from datetime import datetime, timezone

# Connect to local database
conn = sqlite3.connect('/media/shashank/Data/Link to PDocuments/leetcode tracker/codestreak/codestreak.db')
cursor = conn.cursor()

# Find a user (e.g. Sumukh or any non-primary user)
cursor.execute("SELECT id, name, leetcode_username FROM users WHERE id != 1 LIMIT 1")
user = cursor.fetchone()

if not user:
    # If only 1 user exists, insert a test friend
    cursor.execute("INSERT INTO users (name, leetcode_username, email, hashed_password) VALUES ('Sumukh Shandilya', 'Sumukh_Shandilya', 'sumukh@example.com', 'pass')")
    conn.commit()
    user_id = cursor.lastrowid
    user_name = "Sumukh Shandilya"
    user_handle = "Sumukh_Shandilya"
else:
    user_id, user_name, user_handle = user

# Insert a fresh solve recorded right now!
now_iso = datetime.now(timezone.utc).isoformat()
title = "3Sum"
title_slug = "3sum"

cursor.execute(
    "INSERT INTO solves (user_id, title_slug, title, solved_at) VALUES (?, ?, ?, ?)",
    (user_id, title_slug, title, now_iso)
)
conn.commit()
conn.close()

print(f"Success! Inserted test solve: {user_name} (@{user_handle}) just solved '{title}' at {now_iso}")
