"""Reusable UI widgets and styling components for the dark fintech Streamlit interface."""

import streamlit as st


def apply_custom_css() -> None:
    """Inject polished dark fintech CSS styling with emerald accents."""
    st.markdown(
        """
        <style>
        /* Base typography & containers */
        .main {
            background-color: #0d1117;
            color: #f0f6fc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }

        /* Metric card container */
        .fintech-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            transition: border-color 0.2s ease-in-out;
        }
        .fintech-card:hover {
            border-color: #10b981;
        }

        /* Accent badge */
        .emerald-badge {
            background-color: rgba(16, 185, 129, 0.15);
            color: #10b981;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }

        /* Placeholder badge */
        .roadmap-badge {
            background-color: rgba(100, 116, 139, 0.2);
            color: #94a3b8;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }

        /* Page header title */
        .page-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #f0f6fc;
            margin-bottom: 0.25rem;
        }
        .page-subtitle {
            font-size: 0.95rem;
            color: #8b949e;
            margin-bottom: 1.5rem;
        }

        /* Form button */
        div.stButton > button:first-child {
            background-color: #10b981;
            color: #ffffff;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1.25rem;
            transition: background-color 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #059669;
            color: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str, badge_text: str = "Phase 1 Foundation") -> None:
    """Render a standardized page title banner with metadata badge."""
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="page-title">{title}</div>
                <div class="page-subtitle">{subtitle}</div>
            </div>
            <div>
                <span class="emerald-badge">{badge_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_phase_placeholder(
    feature_name: str,
    target_phase: str,
    description: str,
) -> None:
    """Render a clean placeholder indicating the scheduled development phase."""
    st.markdown(
        f"""
        <div class="fintech-card" style="border-left: 4px solid #3b82f6; margin-top: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <h4 style="margin: 0; color: #f0f6fc;">{feature_name}</h4>
                <span class="roadmap-badge">Scheduled: {target_phase}</span>
            </div>
            <p style="color: #8b949e; margin: 0; font-size: 0.95rem;">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
