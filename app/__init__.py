from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.login_message = "Please log in to access this page."


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_object("app.config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # ── Existing blueprints ──────────────────────────────────────────────────
    from app.routes.auth_routes import auth
    from app.routes.main_routes import main
    from app.routes.product_routes import products_bp
    from app.routes.promotion_routes import promotion_bp
    from app.routes.flashsale_routes import flashsale_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.checkout_routes import checkout_bp
    from app.routes.order_routes import orders_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.wishlist_routes import wishlist_bp
    from app.routes.review_routes import reviews_bp

    # ── Phase 13 blueprints ──────────────────────────────────────────────────
    from app.routes.coupon_routes import coupon_bp
    from app.routes.invoice_routes import invoice_bp
    from app.routes.inventory_routes import inventory_bp
    from app.routes.contact_routes import contact_bp
    from app.routes.static_pages_routes import static_pages_bp
    from app.routes.payment_routes import payment_bp

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(products_bp)
    app.register_blueprint(promotion_bp)
    app.register_blueprint(flashsale_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(coupon_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(static_pages_bp)
    app.register_blueprint(payment_bp)

    from app import models  # noqa: F401

    # Flask-Login user loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
