import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "campus_email.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Demo users
    users = [
        ("alice", "1234", "alice@college.com", "CSE"),
        ("bob", "1234", "bob@college.com", "AI"),
        ("charls", "1234", "charls@college.com", "ADMIN"),
        ("david", "1234", "david@college.com", "CSE"),
        ("jason","1234","jason@college.com","CSE"),
        ("prince","1234","prince@college.com","ADMIN")
    ]

    for user in users:
        try:
            conn.execute("""
                INSERT INTO users
                (username, password, email, department)
                VALUES (?, ?, ?, ?)
            """, user)
        except sqlite3.IntegrityError:
            pass

        # Migrate existing plaintext passwords to secure hashes
    existing_users = conn.execute(
        "SELECT id, password FROM users"
    ).fetchall()

    for user in existing_users:
        password = user["password"]

        # Skip passwords that are already hashed
        if not password.startswith(("scrypt:", "pbkdf2:")):
            hashed_password = generate_password_hash(password)

            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed_password, user["id"])
            )

    conn.commit()
    conn.close()