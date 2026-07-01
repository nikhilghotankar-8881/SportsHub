from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

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

    from app.routes.auth_routes import auth
    from app.routes.main_routes import main
    from app.routes.product_routes import products_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.checkout_routes import checkout_bp
    from app.routes.order_routes import orders_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.wishlist_routes import wishlist_bp

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(wishlist_bp)

    from app import models  # noqa: F401

    # Flask-Login user loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
