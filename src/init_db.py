# src/init_db.py
import sqlite3

DB_NAME = "fraud.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # users table: store user status
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        status TEXT DEFAULT 'normal'
    )
    """)

    # predictions table: store each transaction prediction
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
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

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def show_all():
    """View all records in the predictions and users tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("\n📊 Users Table:")
    for row in cursor.execute("SELECT * FROM users"):
        print(row)

    print("\n💾 Predictions Table (last 10):")
    for row in cursor.execute("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 10"):
        print(row)

    conn.close()


def clear_db():
    """Delete all rows from both tables safely."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM predictions")
    conn.commit()
    conn.close()
    print("🧹 All data cleared successfully!")


if __name__ == "__main__":
    print("Choose an action:")
    print("1️⃣  Initialize DB")
    print("2️⃣  Show data")
    print("3️⃣  Clear all data")
    choice = input("Enter choice (1/2/3): ")

    if choice == "1":
        init_db()
    elif choice == "2":
        show_all()
    elif choice == "3":
        clear_db()
    else:
        print("❌ Invalid choice.")
