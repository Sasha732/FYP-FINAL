"""
=====================================================
  Streamlit Authentication System - app.py
=====================================================
  MERGE CHANGE START
  Merges AuthFlow (OTP auth) with AI Object Detection System (YOLOv8).
  After successful Sign In, user goes directly to the detection dashboard.
  Sign Out lives in the detection page sidebar.
  MERGE CHANGE END
"""

import streamlit as st

# ── Page config (must be first Streamlit call) ──
# MERGE CHANGE START
# layout="wide" and initial_sidebar_state="expanded" required by the
# detection dashboard. Auth pages are kept narrow via .auth-card max-width CSS.
st.set_page_config(
    page_title="AI Object Detection System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
# MERGE CHANGE END

# ── Internal imports ─────────────────────────────
from database import init_db
from styles import inject_css
from page_views.signin import show_signin
from page_views.signup import show_signup
from page_views.forgot_password import show_forgot_password
# MERGE CHANGE START
from page_views.detection import show_detection
# MERGE CHANGE END

# ── Bootstrap DB ──────────────────────────────────
init_db()

# ── Session-state defaults ────────────────────────
for key, default in {
    "page":           "signin",
    "authenticated":  False,
    "user_id":        None,
    "username":       None,
    "email":          None,
    "full_name":      None,
    "remember_me":    False,
    "dark_mode":      True,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Router ────────────────────────────────────────
def navigate(page: str):
    st.session_state.page = page
    st.rerun()


page = st.session_state.page

# MERGE CHANGE START
# Theme toggle and AuthFlow CSS only injected on auth pages.
# The detection page manages its own CSS and sidebar.
_auth_pages = {"signin", "signup", "forgot_password"}
if page in _auth_pages:
    col_spacer, col_toggle = st.columns([6, 1])
    with col_toggle:
        icon = "☀️" if st.session_state.dark_mode else "🌙"
        if st.button(icon, key="theme_toggle", help="Toggle light/dark mode"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    inject_css(dark_mode=st.session_state.dark_mode)
# MERGE CHANGE END

if page == "signin":
    show_signin(navigate)
elif page == "signup":
    show_signup(navigate)
elif page == "forgot_password":
    show_forgot_password(navigate)
# MERGE CHANGE START
# "dashboard" route now goes directly to the detection page.
elif page in ("dashboard", "detection"):
    if not st.session_state.authenticated:
        st.warning("⚠️  Please sign in to access the system.")
        navigate("signin")
    else:
        show_detection(navigate)
# MERGE CHANGE END
else:
    navigate("signin")