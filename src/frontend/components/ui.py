"""Reusable UI widgets and styling components for the dark fintech Streamlit interface."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from src.core.money import format_currency

# Design system color tokens
PALETTE = {
    "bg": "#0B1120",
    "surface": "#151E30",
    "surface_elevated": "#1D2940",
    "accent": "#38BDF8",
    "positive": "#22C55E",
    "negative": "#F87171",
    "warning": "#F59E0B",
    "text": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "border": "#334155",
}


def format_money(value: Decimal | str | int | float, currency: str = "INR") -> str:
    """Format monetary decimal to display string using exact currency symbols.

    Enforces:
    - INR defaults to '₹'.
    - USD renders accurately as '$'.
    - Other ISO currencies render with their code prefix.
    - Floating-point representations are strictly avoided.
    """
    clean_curr = (currency or "INR").strip().upper()
    if clean_curr == "INR":
        symbol = "₹"
    elif clean_curr == "USD":
        symbol = "$"
    elif clean_curr == "EUR":
        symbol = "€"
    elif clean_curr == "GBP":
        symbol = "£"
    else:
        symbol = f"{clean_curr} "

    return format_currency(value, currency_symbol=symbol)


def apply_custom_css() -> None:
    """Inject polished dark fintech CSS styling matching the design system specifications."""
    st.markdown(
        f"""
        <style>
        /* Base typography & container background */
        .stApp {{
            background-color: {PALETTE["bg"]};
            color: {PALETTE["text"]};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Sidebar styling */
        section[data-testid="stSidebar"] {{
            background-color: {PALETTE["surface"]};
            border-right: 1px solid {PALETTE["border"]};
        }}

        /* Fintech Cards */
        .fintech-card {{
            background-color: {PALETTE["surface"]};
            border: 1px solid {PALETTE["border"]};
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: border-color 0.2s ease-in-out, transform 0.1s ease;
        }}
        .fintech-card:hover {{
            border-color: {PALETTE["accent"]};
        }}

        .fintech-card-elevated {{
            background-color: {PALETTE["surface_elevated"]};
            border: 1px solid {PALETTE["border"]};
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.4);
        }}

        /* Badges */
        .badge {{
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }}
        .badge-accent {{
            background-color: rgba(56, 189, 248, 0.15);
            color: {PALETTE["accent"]};
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .badge-positive {{
            background-color: rgba(34, 197, 94, 0.15);
            color: {PALETTE["positive"]};
            border: 1px solid rgba(34, 197, 94, 0.3);
        }}
        .badge-negative {{
            background-color: rgba(248, 113, 113, 0.15);
            color: {PALETTE["negative"]};
            border: 1px solid rgba(248, 113, 113, 0.3);
        }}
        .badge-warning {{
            background-color: rgba(245, 158, 11, 0.15);
            color: {PALETTE["warning"]};
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        .badge-secondary {{
            background-color: rgba(148, 163, 184, 0.15);
            color: {PALETTE["text_secondary"]};
            border: 1px solid rgba(148, 163, 184, 0.3);
        }}

        /* Page header */
        .page-title {{
            font-size: 1.85rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin-bottom: 0.25rem;
            letter-spacing: -0.025em;
        }}
        .page-subtitle {{
            font-size: 0.95rem;
            color: {PALETTE["text_secondary"]};
            margin-bottom: 1.5rem;
        }}

        /* Primary action button styling */
        div.stButton > button:first-child {{
            background-color: {PALETTE["accent"]};
            color: #0F172A;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1.25rem;
            transition: all 0.2s ease;
        }}
        div.stButton > button:first-child:hover {{
            background-color: #7dd3fc;
            color: #0F172A;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
        }}

        /* Secondary button override */
        div.stButton > button[kind="secondary"] {{
            background-color: {PALETTE["surface_elevated"]};
            color: {PALETTE["text"]};
            border: 1px solid {PALETTE["border"]};
        }}

        /* Streamlit metric overrides */
        div[data-testid="stMetricValue"] {{
            color: {PALETTE["text"]} !important;
            font-weight: 700 !important;
        }}
        div[data-testid="stMetricLabel"] {{
            color: {PALETTE["text_secondary"]} !important;
            font-weight: 500 !important;
        }}

        /* Streamlit form input styling */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > div,
        .stDateInput > div > div > input {{
            background-color: {PALETTE["surface_elevated"]} !important;
            color: {PALETTE["text"]} !important;
            border-color: {PALETTE["border"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(
    title: str, subtitle: str, badge_text: str | None = None, badge_type: str = "accent"
) -> None:
    """Render a standardized page title banner with optional status badge."""
    badge_html = ""
    if badge_text:
        badge_html = f'<div><span class="badge badge-{badge_type}">{badge_text}</span></div>'

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div>
                <div class="page-title">{title}</div>
                <div class="page-subtitle">{subtitle}</div>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, badge_type: str = "accent") -> str:
    """Return HTML snippet for an inline status badge."""
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def render_empty_state(title: str, message: str, icon: str = "📭") -> None:
    """Render a clean placeholder when a data collection is empty."""
    st.markdown(
        f"""
        <div class="fintech-card" style="text-align: center; padding: 2.5rem 1.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">{icon}</div>
            <h4 style="margin: 0 0 0.5rem 0; color: {PALETTE["text"]};">{title}</h4>
            <p style="margin: 0; color: {PALETTE["text_secondary"]}; font-size: 0.95rem;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
