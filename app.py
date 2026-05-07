from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "dsmarket"

# DATABASE CONNECTION
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# USERS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    balance INTEGER DEFAULT 0
)
""")

# REQUESTS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    type TEXT,
    amount INTEGER,
    status TEXT,
    number TEXT
)
""")

conn.commit()

# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")

# REGISTER
@app.route("/register", methods=["POST"])
def register():

    username = request.form["username"]
    password = request.form["password"]

    c.execute(
        "INSERT INTO users(username,password,balance) VALUES(?,?,?)",
        (username,password,0)
    )

    conn.commit()

    return redirect("/")

# LOGIN
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    )

    user = c.fetchone()

    if user:

        session["username"] = username

        return redirect("/dashboard")

    return "Wrong login details"

# USER DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/")

    username = session["username"]

    c.execute(
        "SELECT balance FROM users WHERE username=?",
        (username,)
    )

    balance = c.fetchone()[0]

    c.execute(
        "SELECT type,amount,status FROM requests WHERE username=?",
        (username,)
    )

    history = c.fetchall()

    return render_template(
        "dashboard.html",
        balance=balance,
        history=history
    )

# DEPOSIT
@app.route("/deposit", methods=["POST"])
def deposit():

    if "username" not in session:
        return redirect("/")

    amount = request.form["amount"]

    c.execute(
        """
        INSERT INTO requests(username,type,amount,status,number)
        VALUES(?,?,?,?,?)
        """,
        (
            session["username"],
            "Deposit",
            amount,
            "Pending",
            ""
        )
    )

    conn.commit()

    return redirect("/dashboard")

# WITHDRAW
@app.route("/withdraw", methods=["POST"])
def withdraw():

    if "username" not in session:
        return redirect("/")

    amount = request.form["amount"]
    number = request.form["number"]

    c.execute(
        """
        INSERT INTO requests(username,type,amount,status,number)
        VALUES(?,?,?,?,?)
        """,
        (
            session["username"],
            "Withdraw",
            amount,
            "Pending",
            number
        )
    )

    conn.commit()

    return redirect("/dashboard")

# ADMIN DASHBOARD
@app.route("/admin")
def admin():

    c.execute(
        "SELECT * FROM requests WHERE status='Pending'"
    )

    requests_data = c.fetchall()

    return render_template(
        "admin.html",
        requests=requests_data
    )

# APPROVE REQUEST
@app.route("/approve/<int:id>")
def approve(id):

    c.execute(
        "SELECT * FROM requests WHERE id=?",
        (id,)
    )

    req = c.fetchone()

    username = req[1]
    req_type = req[2]
    amount = req[3]

    # APPROVE DEPOSIT
    if req_type == "Deposit":

        c.execute(
            "UPDATE users SET balance = balance + ? WHERE username=?",
            (amount,username)
        )

    # APPROVE WITHDRAWAL
    elif req_type == "Withdraw":

        c.execute(
            "UPDATE users SET balance = balance - ? WHERE username=?",
            (amount,username)
        )

    # UPDATE STATUS
    c.execute(
        "UPDATE requests SET status='Approved' WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect("/admin")

# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# RUN APP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)