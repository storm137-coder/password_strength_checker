# app.py
# Main Flask application file

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt
from datetime import datetime
import os
import pkgutil
import importlib.util

# Compatibility shim: Python 3.12+ removed `pkgutil.get_loader` which
# some dependencies (Flask/Werkzeug) still call. Provide a simple
# replacement using `importlib.util.find_spec` when missing.
if not hasattr(pkgutil, "get_loader"):
    def _compat_get_loader(name):
        spec = importlib.util.find_spec(name)
        return spec.loader if spec is not None else None

    setattr(pkgutil, "get_loader", _compat_get_loader)

app = Flask('app')

# Secret key for session security (change this in production)
app.secret_key = "super_secret_key_change_this"

def get_database_path():
    # Vercel's runtime only guarantees write access to /tmp.
    if os.environ.get("DATABASE_PATH"):
        return os.environ["DATABASE_PATH"]
    if os.environ.get("VERCEL"):
        return "/tmp/users.db"
    return os.path.join(os.path.dirname(__file__), "users.db")


DATABASE = get_database_path()

# -----------------------------
# Database helper function
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# -----------------------------
# Initialize database
# -----------------------------
def init_db():
    conn = None
    try:
        db_dir = os.path.dirname(DATABASE)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError:
        # If the SQLite file is corrupted, recreate it so registration works.
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()


    # Ensure the database exists whether the app is run locally or imported
    # by a serverless host such as Vercel.
    init_db()

# -----------------------------
# Home page
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Basic validation
        if not full_name or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        # Hash password with bcrypt
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """, (full_name, email, password_hash.decode("utf-8"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        except sqlite3.DatabaseError:
            # Recover from a malformed database and retry once.
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            if os.path.exists(DATABASE):
                os.remove(DATABASE)
            init_db()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            """, (full_name, email, password_hash.decode("utf-8"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")

# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            session["created_at"] = user["created_at"]
            flash("Login successful!", "success")
            return redirect(url_for("password_tool"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# -----------------------------
# Dashboard (protected)
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template("dashboard.html",
                           full_name=session["full_name"],
                           created_at=session["created_at"])

# -----------------------------
# User details table
# -----------------------------
@app.route("/users")
def users():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, email, password_hash, created_at
        FROM users
        ORDER BY id DESC
    """)
    users = cursor.fetchall()
    conn.close()

    return render_template("users.html", users=users)

# -----------------------------
# Password generator/checker page
# -----------------------------
@app.route("/password")
def password_tool():
    return render_template("password.html")

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)