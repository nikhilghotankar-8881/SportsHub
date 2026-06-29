import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = "sportshub-secret-key"

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'sportshub.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False