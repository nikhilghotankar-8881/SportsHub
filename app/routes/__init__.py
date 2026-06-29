from app.routes.main_routes import main
from app.routes.auth_routes import auth
from app.routes.product_routes import products_bp
from app.routes.cart_routes import cart_bp
from app.routes.checkout_routes import checkout_bp
from app.routes.order_routes import orders_bp
from app.routes.admin_routes import admin_bp

__all__ = ["main", "auth", "products_bp", "cart_bp", "checkout_bp", "orders_bp", "admin_bp"]
