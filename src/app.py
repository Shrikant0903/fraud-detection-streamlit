# src/app.py
import sqlite3
import pickle
from fastapi import FastAPI
from pydantic import BaseModel

# Load model
import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "..", "Models", "fraud_model.pkl")

model = joblib.load(model_path)

app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "Fraud Prediction API is running!"}


# Transaction schema
class Transaction(BaseModel):
    user_id: str
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

# DB connection
def get_db():
    return sqlite3.connect("fraud.db")

# ----------------- Predict -----------------
@app.post("/predict")
def predict(transaction: Transaction):
    conn = get_db()
    cursor = conn.cursor()

    # Check if user is flagged
    cursor.execute("SELECT status FROM users WHERE user_id=?", (transaction.user_id,))
    user_status = cursor.fetchone()
    if user_status and "fraud" in user_status[0]:
        result = {"prediction": "fraud", "warning": f"⚠ User {transaction.user_id} flagged as fraud."}
        cursor.execute("""INSERT INTO predictions (user_id, type, amount, oldbalanceOrg, newbalanceOrig,
                          oldbalanceDest, newbalanceDest, score, status)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (transaction.user_id, transaction.type, transaction.amount,
                        transaction.oldbalanceOrg, transaction.newbalanceOrig,
                        transaction.oldbalanceDest, transaction.newbalanceDest,
                        1.0, "fraud (auto)"))
        conn.commit()
        conn.close()
        return result

    # Prepare features
    type_map = {"PAYMENT": 0, "TRANSFER": 1, "CASH_OUT": 2, "DEBIT": 3, "CASH_IN": 4}
    features = [[type_map.get(transaction.type.upper(), 0),
                 transaction.amount, transaction.oldbalanceOrg,
                 transaction.newbalanceOrig, transaction.oldbalanceDest,
                 transaction.newbalanceDest]]

    score = model.predict(features)[0]
    status = "fraud" if score == 1 else "safe"

    # Save to DB
    cursor.execute("""INSERT INTO predictions (user_id, type, amount, oldbalanceOrg, newbalanceOrig,
                      oldbalanceDest, newbalanceDest, score, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (transaction.user_id, transaction.type, transaction.amount,
                    transaction.oldbalanceOrg, transaction.newbalanceOrig,
                    transaction.oldbalanceDest, transaction.newbalanceDest,
                    float(score), status))
    conn.commit()
    conn.close()

    return {"prediction": status}

# ----------------- Flag User -----------------
@app.post("/flag_user/{user_id}")
def flag_user(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, status) VALUES (?, 'fraud')", (user_id,))
    conn.commit()
    conn.close()
    return {"message": f"🚨 User {user_id} flagged as fraud."}

# ----------------- Flag Transaction -----------------
@app.post("/flag_transaction/{transaction_id}")
def flag_transaction(transaction_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE predictions SET status='fraud (flagged_by_user)', score=1.0 WHERE id=?", (transaction_id,))
    conn.commit()
    conn.close()
    return {"message": f"⚠ Transaction {transaction_id} flagged as fraud by user."}

# ----------------- Last 10 Transactions -----------------
@app.get("/get_last10/{user_id}")
def get_last10(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, type, amount, oldbalanceOrg, newbalanceOrig,
                      oldbalanceDest, newbalanceDest, score, status, timestamp
                      FROM predictions WHERE user_id=?
                      ORDER BY id DESC LIMIT 10""", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    # warnings if flagged
    warnings = [f"⚠ Transaction {r[0]} was flagged as fraud by user." for r in rows if "flagged_by_user" in str(r[8])]
    return {"last_10_transactions": rows, "warnings": warnings}
