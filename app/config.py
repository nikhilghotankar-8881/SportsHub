import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _get_database_uri():
    """
    Returns the correct database URI:
    - Production (Render): reads DATABASE_URL from environment.
      Render provides a 'postgres://' URL; SQLAlchemy 2.x requires 'postgresql://'.
    - Local development: falls back to SQLite.
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Render (and some older providers) issue postgres:// URLs.
        # SQLAlchemy 2.x requires postgresql:// — fix it here.
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    # Local development — use SQLite
    return f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'sportshub.db')}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or (_ for _ in ()).throw(
        ValueError("SECRET_KEY environment variable is not set. Set it in your .env file.")
    )

    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "nikhilghotankar@gmail.com"
    )

    # Razorpay
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

    # Business Settings
    GST_RATE = float(os.environ.get("GST_RATE", "18"))
    FREE_DELIVERY_ABOVE = float(os.environ.get("FREE_DELIVERY_ABOVE", "999"))
    DELIVERY_CHARGE = float(os.environ.get("DELIVERY_CHARGE", "49"))
    COMPANY_NAME = "SportsHub"
    COMPANY_ADDRESS = "Chhatrapati Sambhajinagar, Maharashtra, India"
    COMPANY_PHONE = "+91 9823268881"
    COMPANY_EMAIL = "nikhilghotankar@gmail.com"
    COMPANY_WEBSITE = "https://github.com/nikhilghotankar-8881/SportsHub"
    COMPANY_GST = "27AABCS1234Z1Z5"