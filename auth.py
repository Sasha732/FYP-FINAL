"""
Authentication helpers — password hashing, validation, OTP generation, SMTP delivery.
"""

import re
import random
import string
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from passlib.context import CryptContext
from database import (
    get_user_by_email, get_user_by_username,
    save_otp, verify_otp, update_password, can_send_otp,
)
from config import SMTP_HOST, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD

# ── Password hashing context ──────────────────────────────────────────────────
pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── Input validation ──────────────────────────────────────────────────────────

def validate_email(email: str) -> tuple[bool, str]:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    if re.match(pattern, email):
        return True, ""
    return False, "Invalid email address format."


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(username) > 20:
        return False, "Username must be 20 characters or fewer."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username may only contain letters, digits, and underscores."
    return True, ""


def password_strength_label(password: str) -> tuple[str, str]:
    """Returns (label, colour) for a visual strength indicator."""
    checks = [
        len(password) >= 8,
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)),
    ]
    score = sum(checks)
    if score <= 2:
        return "Weak", "#ef4444"
    if score <= 3:
        return "Fair", "#f59e0b"
    if score == 4:
        return "Good", "#3b82f6"
    return "Strong", "#10b981"


# ── Auth flows ────────────────────────────────────────────────────────────────

def login_with_email(email: str, password: str):
    """Returns (user_dict | None, error_message)."""
    user = get_user_by_email(email)
    if not user:
        return None, "No account found with that email."
    if not verify_password(password, user["password_hash"]):
        return None, "Incorrect password."
    return user, ""


def login_with_username(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return None, "No account found with that username."
    if not verify_password(password, user["password_hash"]):
        return None, "Incorrect password."
    return user, ""


# ── SMTP email delivery ───────────────────────────────────────────────────────

def _send_email(to_email: str, subject: str, html_body: str) -> tuple[bool, str]:
    """
    Send an HTML email via Gmail SMTP (port 587, STARTTLS).
    Returns (success, error_message).
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        # Dev fallback: print to console when SMTP is not configured
        print(f"\n{'='*50}")
        print(f"  [DEV MODE — SMTP not configured]")
        print(f"  To: {to_email}")
        print(f"  Subject: {subject}")
        print(f"  Body preview: {html_body[:200]}")
        print(f"{'='*50}\n")
        return True, ""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return True, ""
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check your SMTP_EMAIL and SMTP_PASSWORD."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Failed to send email: {e}"


def _otp_email_html(otp: str, purpose: str = "verification") -> str:
    """Returns a simple branded HTML body for OTP emails."""
    return f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:480px;margin:auto;
                background:#1a1a2e;color:#fff;border-radius:16px;padding:2rem;">
        <h2 style="background:linear-gradient(135deg,#6C63FF,#48CAE4);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   margin-top:0;">AuthFlow 🔐</h2>
        <p style="color:rgba(255,255,255,0.8);">
            Your {purpose} code is:
        </p>
        <div style="font-size:2.2rem;font-weight:800;letter-spacing:0.35rem;
                    text-align:center;padding:1rem;
                    background:rgba(108,99,255,0.2);border-radius:12px;
                    border:1px solid rgba(108,99,255,0.4);margin:1rem 0;">
            {otp}
        </div>
        <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">
            This code expires in <strong>10 minutes</strong>.
            If you didn't request this, ignore this email.
        </p>
    </div>
    """


# ── OTP public API ────────────────────────────────────────────────────────────

def generate_and_send_otp(email: str) -> tuple[str, bool, str]:
    """
    Generates a 6-digit OTP, persists it, and sends it via SMTP.
    Returns (otp_code, success, error_message).
    Includes a 30-second cooldown to prevent duplicate sends from reruns.
    """
    if not can_send_otp(email, cooldown_seconds=30):
        # An OTP was already sent within the last 30 seconds — skip silently.
        # Return empty string so callers know no new OTP was generated.
        return "", True, ""

    otp = "".join(random.choices(string.digits, k=6))
    save_otp(email, otp, ttl_minutes=10)

    ok, err = _send_email(
        to_email  = email,
        subject   = "Your AuthFlow verification code",
        html_body = _otp_email_html(otp, "verification"),
    )
    # Always log to console as a dev safety net
    print(f"\n{'='*50}\n  📧  OTP for {email}: {otp}  (valid 10 min)\n{'='*50}\n")
    return otp, ok, err


def send_signup_verification(email: str) -> tuple[str, bool, str]:
    """Alias used by signup flow."""
    return generate_and_send_otp(email)


def send_login_otp(email: str) -> tuple[str, bool, str]:
    """Alias used by signin flow."""
    return generate_and_send_otp(email)


def verify_otp_code(email: str, code: str) -> bool:
    """Thin wrapper kept for backward compatibility."""
    return verify_otp(email, code)


# Aliased names referenced in page views
verify_signup_otp = verify_otp_code
verify_login_otp  = verify_otp_code


# ── Password reset ────────────────────────────────────────────────────────────

def reset_password(email: str, new_password: str) -> tuple[bool, str]:
    ok, msg = validate_password_strength(new_password)
    if not ok:
        return False, msg
    update_password(email, hash_password(new_password))
    return True, "Password updated successfully."


# ── Remember-me token ─────────────────────────────────────────────────────────

def generate_remember_token() -> str:
    return secrets.token_urlsafe(32)


# ── Google OAuth simulation ───────────────────────────────────────────────────
MOCK_GOOGLE_USER = {
    "email": "demo.google@gmail.com",
    "full_name": "Google Demo User",
    "username": "google_demo",
    "avatar_color": "#EA4335",
}