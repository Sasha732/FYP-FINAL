"""
page_views/forgot_password.py

Password reset flow — unchanged architecture.
Step 1: Enter email → Send OTP
Step 2: Enter OTP + new password (inline, same page)
"""

import streamlit as st
from auth import (
    validate_email,
    validate_password_strength,
    send_login_otp,
    verify_login_otp,
    reset_password,
)
from database import get_user_by_email


def show_forgot_password(navigate):
    for k, v in {
        "fp_otp_sent": False,
        "fp_email":    "",
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    st.markdown("""
    <div class="brand-logo">
        <h1>🔐 AuthFlow</h1>
        <p>Reset your password</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.fp_otp_sent:
        email = st.text_input("Registered Email", placeholder="you@example.com", key="fp_email_input")

        if st.button("Send OTP", key="fp_send_otp"):
            email = email.strip()
            ok, msg = validate_email(email)
            if not ok:
                st.error(msg)
            elif not get_user_by_email(email):
                st.error("No account found with that email.")
            else:
                _, ok, err = send_login_otp(email)
                if not ok:
                    st.error(f"Could not send OTP: {err}")
                else:
                    st.session_state.fp_otp_sent = True
                    st.session_state.fp_email    = email
                    st.rerun()
    else:
        email = st.session_state.fp_email
        st.markdown(
            f'<div class="otp-hint">📧 A code was sent to <strong>{email}</strong>.</div>',
            unsafe_allow_html=True,
        )

        otp_code     = st.text_input("Enter OTP",        placeholder="• • • • • •", max_chars=6, key="fp_otp")
        new_password = st.text_input("New Password",     placeholder="New password",  type="password", key="fp_new_pw")
        confirm_pw   = st.text_input("Confirm Password", placeholder="Repeat it",     type="password", key="fp_confirm_pw")

        if st.button("Reset Password", key="fp_reset"):
            if not otp_code.strip():
                st.error("Please enter the OTP.")
            elif not verify_login_otp(email, otp_code.strip()):
                st.error("Invalid or expired OTP.")
            elif new_password != confirm_pw:
                st.error("Passwords do not match.")
            else:
                ok, msg = reset_password(email, new_password)
                if ok:
                    st.success(msg)
                    st.session_state.fp_otp_sent = False
                    st.session_state.fp_email    = ""
                    import time; time.sleep(1)
                    navigate("signin")
                else:
                    st.error(msg)

        if st.button("← Back", key="fp_back"):
            st.session_state.fp_otp_sent = False
            st.session_state.fp_email    = ""
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Sign In", key="fp_to_signin"):
        navigate("signin")

    st.markdown('</div>', unsafe_allow_html=True)