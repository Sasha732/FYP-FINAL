"""
Database layer — SQLite via Python's built-in sqlite3.
Handles all DB init and CRUD for users and OTPs.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "auth.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login    DATETIME,
            avatar_color  TEXT    DEFAULT '#6C63FF'
        );

        CREATE TABLE IF NOT EXISTS otp_store (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL,
            otp_code   TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            used       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS remember_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            token      TEXT    UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL
        );
    """)
    # Migration: add created_at to otp_store for existing DBs that predate this column
    existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(otp_store)").fetchall()]
    if "created_at" not in existing_cols:
        cur.execute("ALTER TABLE otp_store ADD COLUMN created_at DATETIME")

    conn.commit()
    conn.close()


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(full_name, username, email, password_hash, avatar_color="#6C63FF"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (full_name, username, email, password_hash, avatar_color) VALUES (?,?,?,?,?)",
            (full_name, username.lower(), email.lower(), password_hash, avatar_color),
        )
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        return False, "Email already registered."
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username.lower(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_last_login(user_id):
    conn = get_connection()
    conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_password(email, new_hash):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, email.lower()))
    conn.commit()
    conn.close()


# ── OTP helpers ───────────────────────────────────────────────────────────────

def can_send_otp(email, cooldown_seconds=30) -> bool:
    """
    Returns False if an OTP was already sent for this email within
    the last `cooldown_seconds`. Prevents duplicate sends from
    Streamlit reruns hitting the button handler twice.
    """
    conn = get_connection()
    row = conn.execute(
        """SELECT id FROM otp_store
           WHERE email=? AND used=0
           AND created_at > datetime('now', ?)
           ORDER BY id DESC LIMIT 1""",
        (email.lower(), f"-{cooldown_seconds} seconds"),
    ).fetchone()
    conn.close()
    return row is None


def save_otp(email, otp_code, ttl_minutes=10):
    """
    Invalidates any existing unused OTPs for this email, then saves
    the new one. Uses created_at so the cooldown guard works correctly.
    """
    conn = get_connection()
    # Invalidate previous unused OTPs (don't hard-delete — keeps audit trail)
    conn.execute(
        "UPDATE otp_store SET used=1 WHERE email=? AND used=0",
        (email.lower(),),
    )
    conn.execute(
        """INSERT INTO otp_store (email, otp_code, expires_at, created_at)
           VALUES (?, ?, datetime('now', ?), datetime('now'))""",
        (email.lower(), otp_code, f"+{ttl_minutes} minutes"),
    )
    conn.commit()
    conn.close()


def verify_otp(email, otp_code):
    conn = get_connection()
    row = conn.execute(
        """SELECT id FROM otp_store
           WHERE email=? AND otp_code=? AND used=0
           AND expires_at > datetime('now')""",
        (email.lower(), otp_code),
    ).fetchone()
    if row:
        conn.execute("UPDATE otp_store SET used=1 WHERE id=?", (row["id"],))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# ── Remember-me tokens ────────────────────────────────────────────────────────

def save_remember_token(user_id, token, days=30):
    conn = get_connection()
    conn.execute("DELETE FROM remember_tokens WHERE user_id=?", (user_id,))
    conn.execute(
        "INSERT INTO remember_tokens (user_id, token, expires_at) VALUES (?,?,datetime('now',?))",
        (user_id, token, f"+{days} days"),
    )
    conn.commit()
    conn.close()


def get_user_by_token(token):
    conn = get_connection()
    row = conn.execute(
        """SELECT u.* FROM users u
           JOIN remember_tokens t ON u.id=t.user_id
           WHERE t.token=? AND t.expires_at > datetime('now')""",
        (token,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_remember_token(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM remember_tokens WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()