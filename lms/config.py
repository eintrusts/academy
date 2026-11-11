"""Branding and runtime configuration.

Secrets are read from Streamlit secrets (``.streamlit/secrets.toml`` or the
Streamlit Cloud secrets UI) first, then from environment variables.
"""
import os

BRAND_NAME = "EinTrust Academy"
COMPANY_NAME = "EinTrust"
COMPANY_WEBSITE = "https://www.eintrusts.com"
LOGO_URL = "https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true"
TAGLINE = "Practical sustainability, ESG and climate training from EinTrust consultants."

CATEGORIES = [
    "ESG Fundamentals",
    "Carbon Accounting",
    "Sustainability Reporting",
    "Climate Strategy & Net Zero",
    "Sustainable Supply Chain",
    "Energy & Resource Efficiency",
    "Other",
]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
MODULE_TYPES = ["Article", "Video", "PDF", "Link", "Quiz", "Other"]
DEFAULT_PASS_MARK = 70


def get_secret(name, default=None):
    """Return a secret from st.secrets, falling back to the environment."""
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets.toml, or running outside Streamlit
        pass
    return os.environ.get(name, default)


def db_path():
    return os.environ.get("ACADEMY_DB_PATH") or get_secret("ACADEMY_DB_PATH") or "academy.db"


def app_url():
    """Public URL of the deployed app, used in certificates and payment callbacks."""
    return (get_secret("APP_URL") or "").rstrip("/")
