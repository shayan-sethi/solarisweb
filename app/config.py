from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SOLARIS_SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'solaris.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get(
        "SOLARIS_UPLOAD_FOLDER", str(BASE_DIR / "static" / "uploads")
    )
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ENABLE_HTMX = False
    BABEL_DEFAULT_LOCALE = "en"
    BABEL_DEFAULT_TIMEZONE = "UTC"
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # Keep for backward compatibility
    BABEL_TRANSLATION_DIRECTORIES = str(BASE_DIR / "translations")
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    LANGUAGES = {
        "en": "English",
        "hi": "हिंदी",
        "mr": "मराठी",
        "ta": "தமிழ்",
        "te": "తెలుగు",
        "bn": "বাংলা",
        "gu": "ગુજરાતી",
    }


