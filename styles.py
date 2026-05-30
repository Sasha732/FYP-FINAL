"""
Global CSS — supports both dark and light mode themes.
"""

import streamlit as st


def inject_css(dark_mode: bool = True):
    if dark_mode:
        bg = "linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%)"
        card_bg = "rgba(255,255,255,0.05)"
        card_border = "rgba(255,255,255,0.1)"
        input_bg = "rgba(255,255,255,0.92)"
        input_color = "#111111"
        input_border = "rgba(255,255,255,0.15)"
        label_color = "rgba(255,255,255,0.75)"
        text_color = "#ffffff"
        subtext_color = "rgba(255,255,255,0.5)"
        divider_color = "rgba(255,255,255,0.35)"
        divider_border = "rgba(255,255,255,0.12)"
        google_btn_bg = "rgba(255,255,255,0.1)"
        google_btn_hover = "rgba(255,255,255,0.18)"
        google_btn_border = "rgba(255,255,255,0.15)"
        google_btn_color = "#fff"
        tab_list_bg = "rgba(255,255,255,0.05)"
        tab_color = "rgba(255,255,255,0.6)"
        tab_selected_bg = "rgba(108,99,255,0.4)"
        dash_card_bg = "rgba(255,255,255,0.05)"
        dash_card_border = "rgba(255,255,255,0.1)"
        checkbox_color = "rgba(255,255,255,0.7)"
        hr_color = "rgba(255,255,255,0.15)"
        otp_hint_bg = "rgba(108,99,255,0.15)"
        otp_hint_border = "rgba(108,99,255,0.35)"
        otp_hint_color = "#c4bfff"
        secondary_btn_bg = "rgba(255,255,255,0.07)"
        secondary_btn_border = "rgba(255,255,255,0.15)"
    else:
        bg = "linear-gradient(135deg, #e8eaf6 0%, #f3f4f6 50%, #e0f2fe 100%)"
        card_bg = "rgba(255,255,255,0.85)"
        card_border = "rgba(0,0,0,0.08)"
        input_bg = "#ffffff"
        input_color = "#111111"
        input_border = "rgba(0,0,0,0.2)"
        label_color = "#374151"
        text_color = "#111827"
        subtext_color = "#6b7280"
        divider_color = "#9ca3af"
        divider_border = "rgba(0,0,0,0.1)"
        google_btn_bg = "rgba(0,0,0,0.05)"
        google_btn_hover = "rgba(0,0,0,0.1)"
        google_btn_border = "rgba(0,0,0,0.15)"
        google_btn_color = "#111"
        tab_list_bg = "rgba(0,0,0,0.05)"
        tab_color = "#4b5563"
        tab_selected_bg = "rgba(108,99,255,0.2)"
        dash_card_bg = "rgba(255,255,255,0.7)"
        dash_card_border = "rgba(0,0,0,0.08)"
        checkbox_color = "#374151"
        hr_color = "rgba(0,0,0,0.1)"
        otp_hint_bg = "rgba(108,99,255,0.08)"
        otp_hint_border = "rgba(108,99,255,0.25)"
        otp_hint_color = "#4f46e5"
        secondary_btn_bg = "rgba(0,0,0,0.05)"
        secondary_btn_border = "rgba(0,0,0,0.15)"

    st.markdown(f"""
    <style>
    html, body, [class*="css"] {{
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}

    .stApp {{
        background: {bg};
        min-height: 100vh;
    }}

    .auth-card {{
        background: {card_bg};
        backdrop-filter: blur(20px);
        border: 1px solid {card_border};
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin: 2rem auto;
        max-width: 460px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    }}

    .brand-logo {{ text-align: center; margin-bottom: 1.5rem; }}
    .brand-logo h1 {{
        font-size: 2.2rem; font-weight: 800;
        background: linear-gradient(135deg, #6C63FF, #48CAE4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }}
    .brand-logo p {{ color: {subtext_color}; font-size: 0.9rem; margin-top: 0.25rem; }}

    .stTextInput > div > div > input,
    .stTextInput > div > div > input:focus {{
        background: {input_bg} !important;
        border: 1px solid {input_border} !important;
        border-radius: 10px !important;
        color: {input_color} !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.95rem !important;
        transition: border 0.2s;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 2px rgba(108,99,255,0.25) !important;
    }}
    .stTextInput label {{ color: {label_color} !important; font-size: 0.85rem !important; }}

    .stButton > button {{
        width: 100%;
        background: linear-gradient(135deg, #6C63FF, #48CAE4) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.65rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        cursor: pointer;
        transition: opacity 0.2s, transform 0.1s;
    }}
    .stButton > button:hover {{ opacity: 0.9; transform: translateY(-1px); }}
    .stButton > button[kind="secondary"] {{
        background: {secondary_btn_bg} !important;
        border: 1px solid {secondary_btn_border} !important;
        color: {text_color} !important;
    }}

    .divider {{
        display: flex; align-items: center; gap: 0.75rem;
        margin: 1.25rem 0; color: {divider_color}; font-size: 0.85rem;
    }}
    .divider::before, .divider::after {{
        content: ''; flex: 1;
        border-top: 1px solid {divider_border};
    }}

    .google-btn {{
        display: flex; align-items: center; justify-content: center; gap: 0.6rem;
        background: {google_btn_bg};
        border: 1px solid {google_btn_border};
        border-radius: 10px; padding: 0.6rem;
        color: {google_btn_color}; font-size: 0.95rem; font-weight: 500;
        cursor: pointer; width: 100%; transition: background 0.2s;
    }}
    .google-btn:hover {{ background: {google_btn_hover}; }}

    .strength-bar {{
        height: 4px; border-radius: 2px;
        transition: width 0.3s, background 0.3s; margin-top: 4px;
    }}

    .stAlert {{ border-radius: 10px !important; }}

    .stCheckbox label {{ color: {checkbox_color} !important; font-size: 0.88rem !important; }}

    .stTabs [data-baseweb="tab-list"] {{
        background: {tab_list_bg} !important;
        border-radius: 12px !important; padding: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {tab_color} !important; border-radius: 8px !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {tab_selected_bg} !important; color: {text_color} !important;
    }}

    .dash-card {{
        background: {dash_card_bg};
        border: 1px solid {dash_card_border};
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
    }}
    .dash-card h3 {{ color: {text_color}; margin: 0 0 0.5rem; }}
    .dash-card p  {{ color: {subtext_color}; margin: 0; }}

    .avatar {{
        width: 64px; height: 64px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.6rem; font-weight: 700; color: #fff; margin: 0 auto 1rem;
    }}

    .otp-hint {{
        background: {otp_hint_bg};
        border: 1px solid {otp_hint_border};
        border-radius: 10px; padding: 0.75rem 1rem;
        color: {otp_hint_color}; font-size: 0.88rem; margin: 0.75rem 0;
    }}

    hr {{ border-color: {hr_color} !important; }}
    p, span, div {{ color: {text_color}; }}

    footer {{ display: none !important; }}
    #MainMenu {{ display: none !important; }}
    header  {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)