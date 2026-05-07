from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dsmarket_secret"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            balance REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            type TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = generate_password_hash(request.form['password'])

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = c.lastrowid
        c.execute("INSERT INTO wallet (user_id, balance) VALUES (?, ?)", (user_id, 0))
        conn.commit()
    except:
        conn.close()
        return "User already exists"

    conn.close()
    return redirect('/')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()

    conn.close()

    if user and check_password_hash(user[2], password):
        session['user_id'] = user[0]
        session['username'] = user[1]
        return redirect('/dashboard')

    return "Invalid login"

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE user_id=?", (session['user_id'],))
    data = c.fetchone()

    balance = data[0] if data else 0

    c.execute("""
        SELECT type, amount, status
        FROM requests
        WHERE user_id=?
        ORDER BY id DESC
    """, (session['user_id'],))

    history = c.fetchall()

    conn.close()

    return render_template("dashboard.html", balance=balance, history=history)

# ---------------- DEPOSIT REQUEST ----------------
@app.route('/deposit', methods=['POST'])
def deposit():
    amount = float(request.form['amount'])

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO requests (user_id, username, type, amount)
        VALUES (?, ?, ?, ?)
    """, (session['user_id'], session['username'], 'deposit', amount))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- WITHDRAW REQUEST ----------------
@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount = float(request.form['amount'])

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO requests (user_id, username, type, amount)
        VALUES (?, ?, ?, ?)
    """, (session['user_id'], session['username'], 'withdraw', amount))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
def admin():
    if session.get("username") != "admin":
        return redirect('/')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM requests WHERE status='pending'")
    requests_data = c.fetchall()

    conn.close()

    return render_template("admin.html", requests=requests_data)

# ---------------- APPROVE ----------------
@app.route('/approve/<int:req_id>')
def approve(req_id):
    if session.get("username") != "admin":
        return redirect('/')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM requests WHERE id=?", (req_id,))
    req = c.fetchone()

    if req:
        user_id = req[1]
        req_type = req[3]
        amount = req[4]

        c.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
        wallet = c.fetchone()

        balance = wallet[0]

        if req_type == "deposit":
            new_balance = balance + amount
        else:
            new_balance = balance - amount

        c.execute("UPDATE wallet SET balance=? WHERE user_id=?", (new_balance, user_id))
        c.execute("UPDATE requests SET status='approved' WHERE id=?", (req_id,))

        conn.commit()

    conn.close()
    return redirect('/admin')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)