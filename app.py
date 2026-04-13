from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import bcrypt

# 🔥 IMPORT RAG
from rag import ragsimple

app = Flask(__name__)
CORS(app)

# =========================
# 🔗 DB CONNECTION
# =========================
conn = psycopg2.connect(
    dbname="rag_app",
    user="samanthraj",
    password="dopamine",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()


# =========================
# 🟢 HOME
# =========================
@app.route("/")
def home():
    return "Backend running!"


# =========================
# 🟢 REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return {"error": "Missing fields"}, 400

        # 🔥 FIX: store as string
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed)
        )
        conn.commit()

        return {"message": "User registered"}

    except Exception as e:
        print("REGISTER ERROR:", e)
        conn.rollback()
        return {"error": "Server error"}, 500


# =========================
# 🟢 LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json

        email = data.get("email")
        password = data.get("password")

        cursor.execute(
            "SELECT id, username, password FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return {"error": "User not found"}, 404

        user_id, username, hashed = user

        # 🔥 FIX: convert DB string → bytes
        if not bcrypt.checkpw(password.encode(), hashed.encode()):
            return {"error": "Wrong password"}, 401

        return {
            "user_id": user_id,
            "username": username
        }

    except Exception as e:
        print("LOGIN ERROR:", e)
        return {"error": "Server error"}, 500


# =========================
# 🟢 CHAT (RAG)
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json

        user_id = data.get("user_id")
        message = data.get("message")

        if not user_id or not message:
            return {"error": "Missing data"}, 400

        # 🔥 RAG CALL
        answer = ragsimple(message)

        cursor.execute(
            "INSERT INTO chats (user_id, question, answer) VALUES (%s, %s, %s)",
            (user_id, message, answer)
        )
        conn.commit()

        return {"reply": answer}

    except Exception as e:
        print("CHAT ERROR:", e)
        return {"error": "Server error"}, 500


# =========================
# 🟢 HISTORY
# =========================
@app.route("/history/<int:user_id>", methods=["GET"])
def history(user_id):
    try:
        cursor.execute(
            "SELECT question, answer FROM chats WHERE user_id=%s ORDER BY id ASC",
            (user_id,)
        )

        rows = cursor.fetchall()

        messages = []
        for q, a in rows:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "bot", "content": a})

        return jsonify(messages)

    except Exception as e:
        print("HISTORY ERROR:", e)
        return {"error": "Server error"}, 500


# =========================
# 🟢 CLEAR CHAT
# =========================
@app.route("/clear", methods=["DELETE"])
def clear():
    try:
        data = request.json
        user_id = data.get("user_id")

        cursor.execute(
            "DELETE FROM chats WHERE user_id=%s",
            (user_id,)
        )
        conn.commit()

        return {"message": "Chat cleared"}

    except Exception as e:
        print("CLEAR ERROR:", e)
        return {"error": "Server error"}, 500


# =========================
# ▶️ RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)