"""
page_views/signup.py

Sign-up flow:
  1. User fills Full Name, Username, Email, Password, Confirm Password → "Send OTP"
  2. Passwords must match before OTP is sent.
  3. OTP field + 60-second countdown appear on the SAME page.
  4. After correct OTP: account created → session set → dashboard.
"""

import time
import random
import streamlit as st
from auth import (
    hash_password,
    validate_email,
    validate_username,
    validate_password_strength,
    password_strength_label,
    send_signup_verification,
    verify_signup_otp,
)
from database import create_user, get_user_by_email, update_last_login

OTP_LIFETIME = 60   # seconds shown in the UI countdown


def _random_avatar_color() -> str:
    colors = ["#6C63FF", "#48CAE4", "#F77F00", "#E63946", "#2DC653", "#FF6B9D"]
    return random.choice(colors)


def show_signup(navigate):
    # ── page-level session state ──────────────────────────────────────────────
    for k, v in {
        "signup_otp_sent":  False,
        "signup_form_data": {},
        "signup_otp_sent_at": 0.0,   # epoch timestamp of last OTP send
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    st.markdown("""
    <div class="brand-logo">
        <h1>🔐 AuthFlow</h1>
        <p>Create your account</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.signup_otp_sent:
        # ── Step 1: registration form ─────────────────────────────────────────
        full_name    = st.text_input("Full Name",         placeholder="Jane Doe",         key="su_full_name")
        username     = st.text_input("Username",          placeholder="jane_doe",          key="su_username")
        email        = st.text_input("Email",             placeholder="jane@example.com",  key="su_email")
        password     = st.text_input("Password",          placeholder="At least 8 chars…", key="su_password",  type="password")
        confirm_pass = st.text_input("Re-enter Password", placeholder="Repeat password",   key="su_confirm",   type="password")

        # Live password strength indicator
        if password:
            label, color = password_strength_label(password)
            score = sum([
                len(password) >= 8,
                bool(__import__("re").search(r"[A-Z]", password)),
                bool(__import__("re").search(r"[a-z]", password)),
                bool(__import__("re").search(r"\d", password)),
                bool(__import__("re").search(r"[!@#$%^&*(),.?\":{}|<>]", password)),
            ])
            bar_width = score * 20
            st.markdown(
                f'<div class="strength-bar" style="width:{bar_width}%;background:{color};"></div>'
                f'<span style="font-size:0.78rem;color:{color};">{label}</span>',
                unsafe_allow_html=True,
            )

        if st.button("Send OTP", key="signup_send_otp"):
            errors = []
            full_name    = full_name.strip()
            username     = username.strip()
            email        = email.strip()

            if not full_name:
                errors.append("Full name is required.")

            ok, msg = validate_username(username)
            if not ok:
                errors.append(msg)

            ok, msg = validate_email(email)
            if not ok:
                errors.append(msg)
            elif get_user_by_email(email):
                errors.append("Email is already registered.")

            ok, msg = validate_password_strength(password)
            if not ok:
                errors.append(msg)

            # ── Confirm password check ────────────────────────────────────────
            if not confirm_pass:
                errors.append("Please re-enter your password.")
            elif password != confirm_pass:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                _, ok, err = send_signup_verification(email)
                if not ok:
                    st.error(f"Could not send OTP: {err}")
                else:
                    st.session_state.signup_otp_sent    = True
                    st.session_state.signup_otp_sent_at = time.time()
                    st.session_state.signup_form_data   = {
                        "full_name": full_name,
                        "username":  username,
                        "email":     email,
                        "password":  password,
                    }
                    st.rerun()

    else:
        # ── Step 2: OTP verification + countdown ─────────────────────────────
        d     = st.session_state.signup_form_data
        email = d["email"]

        # Frozen account summary
        st.markdown(f"""
        <div class="dash-card" style="margin-bottom:1rem;">
            <p style="margin:0;font-size:0.85rem;opacity:.7;">Registering as</p>
            <p style="margin:0;font-weight:600;">{d['full_name']} &nbsp;·&nbsp; @{d['username']}</p>
            <p style="margin:0;font-size:0.85rem;opacity:.7;">{email}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f'<div class="otp-hint">📧 A 6-digit code was sent to <strong>{email}</strong>. '
            f'Check your inbox (and spam folder).</div>',
            unsafe_allow_html=True,
        )

        # ── Countdown calculation ─────────────────────────────────────────────
        elapsed  = time.time() - st.session_state.signup_otp_sent_at
        remaining = max(0, int(OTP_LIFETIME - elapsed))
        otp_expired = remaining == 0

        timer_placeholder = st.empty()

        if not otp_expired:
            timer_placeholder.markdown(
                f'<p style="font-size:0.88rem;color:#f59e0b;">⏱ OTP expires in <strong>{remaining} second{"s" if remaining != 1 else ""}</strong></p>',
                unsafe_allow_html=True,
            )
        else:
            timer_placeholder.markdown(
                '<p style="font-size:0.88rem;color:#ef4444;">⌛ OTP expired. Please request a new one.</p>',
                unsafe_allow_html=True,
            )

        otp_code = st.text_input(
            "Enter OTP",
            placeholder="• • • • • •",
            max_chars=6,
            key="signup_otp_input",
            disabled=otp_expired,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Verify & Create Account", key="signup_verify", disabled=otp_expired):
                if not otp_code.strip():
                    st.error("Please enter the OTP.")
                elif verify_signup_otp(email, otp_code.strip()):
                    ok, msg = create_user(
                        full_name     = d["full_name"],
                        username      = d["username"],
                        email         = email,
                        password_hash = hash_password(d["password"]),
                        avatar_color  = _random_avatar_color(),
                    )
                    if ok:
                        user = get_user_by_email(email)
                        update_last_login(user["id"])
                        st.session_state.authenticated    = True
                        st.session_state.user_id          = user["id"]
                        st.session_state.username         = user["username"]
                        st.session_state.email            = user["email"]
                        st.session_state.full_name        = user["full_name"]
                        st.session_state.signup_otp_sent  = False
                        st.session_state.signup_form_data = {}
                        navigate("detection")
                    else:
                        st.error(f"Account creation failed: {msg}")
                else:
                    st.error("Invalid or expired OTP. Please try again.")

        with col2:
            if st.button("Resend OTP", key="signup_resend"):
                _, ok, err = send_signup_verification(email)
                if not ok:
                    st.error(f"Could not resend OTP: {err}")
                else:
                    st.session_state.signup_otp_sent_at = time.time()
                    st.success("A new OTP has been sent.")
                    st.rerun()

        # ── Live tick: rerun every second while timer is running ──────────────
        if not otp_expired:
            time.sleep(1)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Start over", key="signup_back"):
            st.session_state.signup_otp_sent    = False
            st.session_state.signup_form_data   = {}
            st.session_state.signup_otp_sent_at = 0.0
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Already have an account? Sign In", key="to_signin"):
        navigate("signin")

    st.markdown('</div>', unsafe_allow_html=True)