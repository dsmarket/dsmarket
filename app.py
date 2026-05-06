from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            balance REAL,
            plan TEXT,
            last_profit TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            time TEXT
        )
    ''')

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
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        return redirect('/dashboard')

    return "Invalid login"

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    wallet = c.fetchone()

    if wallet:
        balance = wallet[0]
    else:
        balance = 0

    # GET HISTORY FOR CHART
    c.execute("SELECT amount FROM history WHERE user_id=? ORDER BY id ASC", (user_id,))
    history = c.fetchall()

    conn.close()

    chart_data = [h[0] for h in history]

    return render_template("dashboard.html", balance=balance, chart_data=chart_data)

# ---------------- DEPOSIT ----------------
@app.route('/deposit', methods=['POST'])
def deposit():
    amount = float(request.form['amount'])
    user_id = session['user_id']
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    data = c.fetchone()

    if data:
        new_balance = data[0] + amount
        c.execute("UPDATE wallet SET balance=? WHERE user_id=?", (new_balance, user_id))
    else:
        new_balance = amount
        c.execute("INSERT INTO wallet (user_id, balance, plan, last_profit) VALUES (?, ?, NULL, NULL)", (user_id, amount))

    # SAVE HISTORY
    c.execute("INSERT INTO history (user_id, amount, time) VALUES (?, ?, ?)",
              (user_id, new_balance, now))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- WITHDRAW ----------------
@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount = float(request.form['amount'])
    user_id = session['user_id']
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,))
    data = c.fetchone()

    if data:
        new_balance = data[0] - amount
        c.execute("UPDATE wallet SET balance=? WHERE user_id=?", (new_balance, user_id))

        # SAVE HISTORY
        c.execute("INSERT INTO history (user_id, amount, time) VALUES (?, ?, ?)",
                  (user_id, new_balance, now))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)