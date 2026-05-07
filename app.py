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
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL
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

    conn.close()

    balance = data[0] if data else 0

    return render_template("dashboard.html", balance=balance)

# ---------------- DEPOSIT ----------------
@app.route('/deposit', methods=['POST'])
def deposit():
    amount = float(request.form['amount'])
    user_id = session['user_id']

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    data = c.fetchone()

    if data:
        new_balance = data[0] + amount
        c.execute("UPDATE wallet SET balance=? WHERE user_id=?", (new_balance, user_id))
        c.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, 'deposit', ?)", (user_id, amount))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- WITHDRAW ----------------
@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount = float(request.form['amount'])
    user_id = session['user_id']

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    data = c.fetchone()

    if data:
        new_balance = data[0] - amount
        c.execute("UPDATE wallet SET balance=? WHERE user_id=?", (new_balance, user_id))
        c.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, 'withdraw', ?)", (user_id, amount))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- TRANSACTIONS ----------------
@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT type, amount FROM transactions WHERE user_id=?", (session['user_id'],))
    data = c.fetchall()

    conn.close()

    return render_template("transactions.html", data=data)

# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if session.get("username") != "admin":
        return redirect('/')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT users.id, users.username, COALESCE(wallet.balance, 0)
        FROM users
        LEFT JOIN wallet ON users.id = wallet.user_id
    """)

    users = c.fetchall()
    conn.close()

    return render_template("admin.html", users=users)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- PWA FILES ----------------
@app.route('/manifest.json')
def manifest():
    return send_from_directory(
        '.',
        'manifest.json',
        mimetype='application/json'
    )

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(
        '.',
        'service-worker.js',
        mimetype='application/javascript'
    )

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
