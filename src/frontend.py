import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import sqlite3

# ---------------- Configuration ----------------
API_URL = "http://127.0.0.1:8000"
DB_NAME = "fraud.db"

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide", initial_sidebar_state="expanded")

# ---------------- Bright Background Styling ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f0f4ff, #e3f2fd, #ffffff);
    font-family: 'Poppins', sans-serif;
    color: #222;
}
.card {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
}
.section-title {
    font-size: 20px;
    color: #0077cc;
    font-weight: 700;
    border-left: 4px solid #0077cc;
    padding-left: 8px;
    margin-bottom: 10px;
}
.stButton>button {
    background: linear-gradient(135deg, #0077cc, #00bcd4);
    border-radius: 10px;
    color: white;
    font-weight: 600;
    border: none;
    transition: 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
    background: linear-gradient(135deg, #00bcd4, #0077cc);
}
h1, h2, h3, h4 {
    color: #004d99;
}
.stSidebar {
    background: linear-gradient(180deg, #e3f2fd, #ffffff);
}
</style>
""", unsafe_allow_html=True)


# ---------------- Helper Functions ----------------
def call_predict(payload: dict, timeout=10):
    try:
        r = requests.post(f"{API_URL}/predict", json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def call_flag_user(user_id: str, timeout=10):
    try:
        r = requests.post(f"{API_URL}/flag_user/{user_id}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}

# ---------------- Sidebar Navigation ----------------
with st.sidebar:
    st.markdown("## 📊 Dashboard Navigation")
    page = st.radio("Go to:", ["Predict Single Transaction", "Predict from CSV", "Database Management"])
    st.markdown("---")
    st.markdown("📦 Database: fraud.db")

# ---------------- Common Header ----------------
st.markdown("""
<div style='text-align:center'>
    <h1 style='color:#FFD700; font-size:48px; margin:0'>🚨 FRAUD DETECTION SYSTEM</h1>
    <p style='color:#FF8C00; font-size:18px; margin:0'>🔍 Detect fraudulent transactions in real-time</p>
</div>
""", unsafe_allow_html=True)
st.markdown('---')

# ---------------- PAGE 1: Predict Single Transaction ----------------
if page == "Predict Single Transaction":
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("""
        <div class="card">
            <div class="section-title">📝 Predict Single Transaction</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("single_txn"):
            c1, c2, c3 = st.columns(3)
            with c1:
                user_id = st.text_input("👤 User ID", placeholder="Enter ID")
                txn_type = st.selectbox("💳 Transaction Type", ["PAYMENT","TRANSFER","CASH_OUT","DEBIT","CASH_IN"])
            with c2:
                amount = st.number_input("💰 Amount", min_value=0.0, format="%.2f")
                oldbalanceOrg = st.number_input("🏦 Old Balance (Orig)", min_value=0.0, format="%.2f")
            with c3:
                newbalanceOrig = st.number_input("🏦 New Balance (Orig)", min_value=0.0, format="%.2f")
                oldbalanceDest = st.number_input("🏧 Old Balance (Dest)", min_value=0.0, format="%.2f")
                newbalanceDest = st.number_input("🏧 New Balance (Dest)", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Predict Fraud")

        if submitted:
            payload = {
                "user_id": user_id or "NA",
                "type": txn_type,
                "amount": amount,
                "oldbalanceOrg": oldbalanceOrg,
                "newbalanceOrig": newbalanceOrig,
                "oldbalanceDest": oldbalanceDest,
                "newbalanceDest": newbalanceDest
            }
            with st.spinner("Predicting..."):
                result = call_predict(payload)
            if result.get("error"):
                st.error(result["error"])
            else:
                st.success("✅ Prediction received")
                st.json(result)

    # --- Flag User ---
    with col_right:
        st.markdown("""
        <div class="card">
            <div class="section-title">⚠ Flag a User as Fraud</div>
        </div>
        """, unsafe_allow_html=True)
        flag_user_id = st.text_input("Enter User ID to Flag", key="flag_user_1")
        if st.button("Flag User", key="flag_btn_1"):
            if not flag_user_id:
                st.warning("Enter a user ID to flag.")
            else:
                with st.spinner("Flagging user..."):
                    resp = call_flag_user(flag_user_id)
                if resp.get("error"):
                    st.error(resp["error"])
                else:
                    st.success(resp.get("message", "User flagged!"))

# ---------------- PAGE 2: Predict from CSV ----------------
elif page == "Predict from CSV":
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("""
        <div class="card">
            <div class="section-title">📂 Predict from CSV</div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df)
                if st.button("Predict CSV"):
                    preds = []
                    progress = st.progress(0)
                    for i, row in df.iterrows():
                        payload = {
                            "user_id": row["user_id"],
                            "type": row["type"],
                            "amount": float(row["amount"]),
                            "oldbalanceOrg": float(row["oldbalanceOrg"]),
                            "newbalanceOrig": float(row["newbalanceOrig"]),
                            "oldbalanceDest": float(row["oldbalanceDest"]),
                            "newbalanceDest": float(row["newbalanceDest"])
                        }
                        res = call_predict(payload)
                        preds.append(res.get("prediction", res))
                        progress.progress((i+1)/len(df))
                    df["prediction"] = preds
                    st.dataframe(df)
                    st.download_button("📥 Download Predictions CSV", df.to_csv(index=False).encode('utf-8'),
                                       "predictions.csv", "text/csv")
            except Exception as e:
                st.error(f"CSV Error: {e}")

    # --- Flag User ---
    with col_right:
        st.markdown("""
        <div class="card">
            <div class="section-title">⚠ Flag a User as Fraud</div>
        </div>
        """, unsafe_allow_html=True)
        flag_user_id = st.text_input("Enter User ID to Flag", key="flag_user_2")
        if st.button("Flag User", key="flag_btn_2"):
            if not flag_user_id:
                st.warning("Enter a user ID to flag.")
            else:
                with st.spinner("Flagging user..."):
                    resp = call_flag_user(flag_user_id)
                if resp.get("error"):
                    st.error(resp["error"])
                else:
                    st.success(resp.get("message", "User flagged!"))

# ---------------- PAGE 3: Database Management ----------------
elif page == "Database Management":
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("""
        <div class="card">
            <div class="section-title">🧰 Database Management</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧾 Show DB Data"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    users_df = pd.read_sql_query("SELECT * FROM users", conn)
                    preds_df = pd.read_sql_query("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 10", conn)
                    conn.close()
                    st.markdown("### 👥 Users Table")
                    st.dataframe(users_df if not users_df.empty else pd.DataFrame(columns=["user_id","status"]))
                    st.markdown("### 💳 Predictions Table (Last 10)")
                    st.dataframe(preds_df if not preds_df.empty else pd.DataFrame(columns=["id","user_id","type","amount"]))
                except Exception as e:
                    st.error(f"DB Error: {e}")
        with col2:
            if st.button("🧹 Clear Database"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute("DELETE FROM users")
                    cur.execute("DELETE FROM predictions")
                    conn.commit()
                    conn.close()
                    st.success("Database cleared successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Flag User ---
    with col_right:
        st.markdown("""
        <div class="card">
            <div class="section-title">⚠ Flag a User as Fraud</div>
        </div>
        """, unsafe_allow_html=True)
        flag_user_id = st.text_input("Enter User ID to Flag", key="flag_user_3")
        if st.button("Flag User", key="flag_btn_3"):
            if not flag_user_id:
                st.warning("Enter a user ID to flag.")
            else:
                with st.spinner("Flagging user..."):
                    resp = call_flag_user(flag_user_id)
                if resp.get("error"):
                    st.error(resp["error"])
                else:
                    st.success(resp.get("message", "User flagged!"))

# ---------------- Footer ----------------
st.markdown('---')
st.markdown("<div style='text-align:center; color:#555'>Made with ❤️ using Streamlit</div>", unsafe_allow_html=True)
