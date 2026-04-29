from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import requests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["APP_NAME"] = "HeadlineXHub"
app.secret_key = "secret123"  # In production, use a complex random string
API_KEY = "f64d0276546b4698b8d09359cc4be936"

def create_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        conn.commit()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        # We only query by username now to check the hashed password safely
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect(url_for("news"))
        else:
            return "Invalid username or password"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            return "Fields cannot be empty"

        # Hash the password before storing it
        hashed_pw = generate_password_hash(password)

        try:
            with sqlite3.connect("users.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_pw)
                )
                conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists"

    return render_template("register.html")

@app.route("/news")
def news():
    if "user" not in session:
        return redirect(url_for("login"))
    
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}"
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return f"Error fetching news: {data.get('message', 'Unknown error')}"

        articles = data.get("articles", [])
        return render_template("news.html", articles=articles)
    except Exception as e:
        return f"Something went wrong: {str(e)}"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    create_db()
    app.run(debug=True)