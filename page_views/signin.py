"""
page_views/signin.py

Sign-in flow:
  1. User enters email or username → clicks "Send OTP"
  2. OTP is emailed via SMTP; OTP input + 60-second countdown appear on the SAME page
  3. User enters OTP → authenticated → redirected to dashboard

No password field. No separate OTP page.
"""

import time
import streamlit as st
from auth import (
    send_login_otp,
    verify_login_otp,
    validate_email,
)
from database import get_user_by_email, get_user_by_username, update_last_login

OTP_LIFETIME = 60   # seconds shown in the UI countdown


def _resolve_user(identifier: str):
    """Return (user_dict, email) whether identifier is an email or username."""
    ok, _ = validate_email(identifier)
    if ok:
        user = get_user_by_email(identifier)
        return user, identifier
    user = get_user_by_username(identifier)
    email = user["email"] if user else None
    return user, email


def show_signin(navigate):
    # ── session keys used on this page ───────────────────────────────────────
    for k, v in {
        "signin_otp_sent":    False,
        "signin_email":       "",
        "signin_identifier":  "",
        "signin_otp_sent_at": 0.0,   # epoch timestamp of last OTP send
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    st.markdown("""
    <div class="brand-logo">
        <h1>🔐 AuthFlow</h1>
        <p>Sign in with a one-time code — no password needed</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 1: identifier input ──────────────────────────────────────────────
    identifier = st.text_input(
        "Email or Username",
        value=st.session_state.signin_identifier,
        placeholder="you@example.com  or  your_username",
        key="signin_identifier_input",
    )

    if not st.session_state.signin_otp_sent:
        if st.button("Send OTP", key="signin_send_otp"):
            identifier = identifier.strip()
            if not identifier:
                st.error("Please enter your email or username.")
            else:
                user, email = _resolve_user(identifier)
                if not user:
                    st.error("No account found. Please check your email or username.")
                else:
                    _, ok, err = send_login_otp(email)
                    if not ok:
                        st.error(f"Could not send OTP: {err}")
                    else:
                        st.session_state.signin_otp_sent    = True
                        st.session_state.signin_otp_sent_at = time.time()
                        st.session_state.signin_email       = email
                        st.session_state.signin_identifier  = identifier
                        st.rerun()

    else:
        # ── Step 2: OTP input + countdown ────────────────────────────────────
        email = st.session_state.signin_email

        st.markdown(
            f'<div class="otp-hint">📧 A 6-digit code was sent to <strong>{email}</strong>. '
            f'Check your inbox (and spam folder).</div>',
            unsafe_allow_html=True,
        )

        # ── Countdown calculation ─────────────────────────────────────────────
        elapsed   = time.time() - st.session_state.signin_otp_sent_at
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
            key="signin_otp_input",
            disabled=otp_expired,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Verify & Sign In", key="signin_verify", disabled=otp_expired):
                if not otp_code.strip():
                    st.error("Please enter the OTP.")
                elif verify_login_otp(email, otp_code.strip()):
                    user, _ = _resolve_user(email)
                    if user:
                        update_last_login(user["id"])
                        st.session_state.authenticated      = True
                        st.session_state.user_id            = user["id"]
                        st.session_state.username           = user["username"]
                        st.session_state.email              = user["email"]
                        st.session_state.full_name          = user["full_name"]
                        st.session_state.signin_otp_sent    = False
                        st.session_state.signin_email       = ""
                        st.session_state.signin_identifier  = ""
                        st.session_state.signin_otp_sent_at = 0.0
                        navigate("detection")
                    else:
                        st.error("Account lookup failed. Please try again.")
                else:
                    st.error("Invalid or expired OTP. Please try again.")

        with col2:
            if st.button("Resend OTP", key="signin_resend"):
                _, ok, err = send_login_otp(email)
                if not ok:
                    st.error(f"Could not resend OTP: {err}")
                else:
                    st.session_state.signin_otp_sent_at = time.time()
                    st.success("A new OTP has been sent.")
                    st.rerun()

        # ── Live tick: rerun every second while timer is running ──────────────
        if not otp_expired:
            time.sleep(1)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Use a different email / username", key="signin_back"):
            st.session_state.signin_otp_sent    = False
            st.session_state.signin_email       = ""
            st.session_state.signin_identifier  = ""
            st.session_state.signin_otp_sent_at = 0.0
            st.rerun()

    # ── Footer links ──────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Create account", key="to_signup"):
            navigate("signup")
    with col_b:
        if st.button("Forgot password", key="to_forgot"):
            navigate("forgot_password")

    st.markdown('</div>', unsafe_allow_html=True)