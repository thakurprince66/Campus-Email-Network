import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, url_for
from database import init_db, get_db
from network_monitor import get_network_status, get_services, get_logs, add_log
from datetime import datetime
from werkzeug.security import check_password_hash

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
            WHERE username = ?
        """, (username,)).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
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

        receiver = request.form.get("receiver", "").strip().lower()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Validate required fields
        if not receiver or not subject or not message:
            return render_template(
                "compose.html",
                error="All fields are required.",
                receiver=receiver,
                subject=subject,
                message=message
            )

        # Basic email format validation
        if (
            "@" not in receiver
            or receiver.count("@") != 1
            or receiver.startswith("@")
            or receiver.endswith("@")
            or "." not in receiver.rsplit("@", 1)[1]
        ):
            return render_template(
                "compose.html",
                error="Please enter a valid recipient email address.",
                receiver=receiver,
                subject=subject,
                message=message
            )

        # Limit input sizes
        if len(receiver) > 254 or len(subject) > 200 or len(message) > 10000:
            return render_template(
                "compose.html",
                error="Input is too long. Subject: maximum 200 characters; message: maximum 10,000 characters.",
                receiver=receiver,
                subject=subject,
                message=message
            )

        conn = get_db()

        try:
            # Confirm that the recipient is a registered user
            user = conn.execute("""
                SELECT email FROM users
                WHERE lower(email) = ?
            """, (receiver,)).fetchone()

            if not user:
                return render_template(
                    "compose.html",
                    error="Recipient email does not exist.",
                    receiver=receiver,
                    subject=subject,
                    message=message
                )

            # Save the internal email
            conn.execute("""
                INSERT INTO emails
                (sender, receiver, subject, message)
                VALUES (?, ?, ?, ?)
            """, (
                session["email"],
                user["email"],
                subject,
                message
            ))

            conn.commit()

        except Exception:
            conn.rollback()
            app.logger.exception("Failed to send an internal email")

            return render_template(
                "compose.html",
                error="Unable to send the email right now. Please try again.",
                receiver=receiver,
                subject=subject,
                message=message
            )

        finally:
            conn.close()

        add_log(
            f"Email sent from {session['email']} to {user['email']}"
        )

        return redirect(url_for("sent"))

    return render_template("compose.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)