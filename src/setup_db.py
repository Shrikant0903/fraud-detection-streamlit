# setup_db.py
import sqlite3

conn = sqlite3.connect("fraud.db")
cursor = conn.cursor()

# Drop old table if exists (⚠ careful, this will remove old data)
cursor.execute("DROP TABLE IF EXISTS predictions")

# Create correct predictions table
cursor.execute("""
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    type TEXT,
    amount REAL,
    oldbalanceOrg REAL,
    newbalanceOrig REAL,
    oldbalanceDest REAL,
    newbalanceDest REAL,
    score REAL,
    status TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Create users table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    status TEXT
)
""")

conn.commit()
conn.close()

print("✅ Database setup complete!")
