from flask import Blueprint, render_template
from flask_login import login_required, current_user

main = Blueprint("main", __name__)


from app.models import Product

@main.route("/")
@main.route("/home")
def index():
    featured_products = Product.query.limit(4).all()
    latest_arrivals = Product.query.order_by(Product.created_at.desc()).limit(4).all()
    return render_template(
        "index.html", 
        title="SportsHub - Home", 
        featured_products=featured_products, 
        latest_arrivals=latest_arrivals
    )


@main.route("/dashboard")
@login_required
def dashboard():
    total_orders = current_user.orders.count()
    total_wishlist_items = current_user.wishlist_items.count()
    total_cart_items = sum(item.quantity for item in current_user.cart_items.all())
    recent_orders = current_user.orders.limit(5).all()
    
    return render_template(
        "dashboard.html",
        title="Dashboard",
        total_orders=total_orders,
        total_wishlist_items=total_wishlist_items,
        total_cart_items=total_cart_items,
        recent_orders=recent_orders
    )
