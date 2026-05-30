"""
page_views/dashboard.py — unchanged from original architecture.
"""

import streamlit as st
from database import delete_remember_token


def show_dashboard(navigate):
    username   = st.session_state.get("username",  "User")
    full_name  = st.session_state.get("full_name", "User")
    email      = st.session_state.get("email",     "")
    user_id    = st.session_state.get("user_id")
    avatar_col = "#6C63FF"

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="brand-logo">
        <div class="avatar" style="background:{avatar_col};">
            {full_name[0].upper() if full_name else "U"}
        </div>
        <h1 style="font-size:1.5rem;">Welcome, {full_name}!</h1>
        <p>@{username} · {email}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="dash-card">
        <h3>🎉 You're signed in</h3>
        <p>Your session is active. This is your dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", key="signout"):
        if user_id:
            try:
                delete_remember_token(user_id)
            except Exception:
                pass
        for key in ["authenticated", "user_id", "username", "email", "full_name",
                    "remember_me", "signin_otp_sent", "signin_email",
                    "signup_otp_sent", "signup_form_data"]:
            if key in st.session_state:
                del st.session_state[key]
        navigate("signin")

    st.markdown('</div>', unsafe_allow_html=True)