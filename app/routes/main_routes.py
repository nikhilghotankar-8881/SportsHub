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
    return render_template("dashboard.html", title="Dashboard")
