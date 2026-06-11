# app.py
# Main Flask application file

from flask import Flask, render_template, redirect, url_for
import sqlite3
from datetime import datetime
import os
import pkgutil
import importlib.util
from werkzeug.security import generate_password_hash

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
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if os.environ.get("VERCEL") or not os.access(project_dir, os.W_OK):
        return "/tmp/users.db"
    return os.path.join(project_dir, "users.db")

# -----------------------------
# Database helper function
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def hash_password(password):
    # Use Werkzeug's pure-Python hashing for deployment portability.
    return generate_password_hash(password)


# -----------------------------
# Initialize database
# -----------------------------
def init_db():
    conn = None
    try:
        database_path = get_database_path()
        db_dir = os.path.dirname(database_path)
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
        database_path = get_database_path()
        if os.path.exists(database_path):
            os.remove(database_path)
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
    return redirect(url_for("password_tool"))

# -----------------------------
# Password generator/checker page
# -----------------------------
@app.route("/password")
def password_tool():
    return render_template("password.html")

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)