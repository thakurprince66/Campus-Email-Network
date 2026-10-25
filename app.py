
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, url_for
from database import init_db, get_db
from network_monitor import get_network_status, get_services, get_logs, add_log
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Please configure it in your .env file."
    )

# Initialize database
init_db()


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()

        conn.close()

        if user:
            session["username"] = username
            session["email"] = user["email"]
            session["department"] = user["department"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("login"))

    network = get_network_status()
    services = get_services()
    logs = get_logs()

    return render_template(
        "dashboard.html",
        username=session["username"],
        email=session["email"],
        department=session["department"],
        network=network,
        services=services,
        logs=logs
    )


@app.route("/inbox")
def inbox():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    emails = conn.execute("""
        SELECT * FROM emails
        WHERE receiver = ?
        ORDER BY timestamp DESC
    """, (session["email"],)).fetchall()

    conn.close()

    return render_template(
        "inbox.html",
        emails=emails
    )


@app.route("/sent")
def sent():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    emails = conn.execute("""
        SELECT * FROM emails
        WHERE sender = ?
        ORDER BY timestamp DESC
    """, (session["email"],)).fetchall()

    conn.close()

    return render_template(
        "sent.html",
        emails=emails
    )


@app.route("/compose", methods=["GET", "POST"])
def compose():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        receiver = request.form["receiver"]
        subject = request.form["subject"]
        message = request.form["message"]

        conn = get_db()

        # Check whether receiver exists
        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ?
        """, (receiver,)).fetchone()

        if not user:
            conn.close()

            return render_template(
                "compose.html",
                error="Receiver email does not exist."
            )

        conn.execute("""
            INSERT INTO emails
            (sender, receiver, subject, message)
            VALUES (?, ?, ?, ?)
        """, (
            session["email"],
            receiver,
            subject,
            message
        ))

        conn.commit()
        conn.close()

        add_log(
            f"Email sent from {session['email']} to {receiver}"
        )

        return redirect(url_for("sent"))
    return render_template("compose.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)