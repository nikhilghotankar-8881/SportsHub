import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or (_ for _ in ()).throw(
        ValueError("SECRET_KEY environment variable is not set. Set it in your .env file.")
    )

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'sportshub.db')}"
    )
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