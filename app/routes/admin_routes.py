from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

from app import db
from app.models import User, Product, Order, OrderStatus

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing overall statistics."""
    
    # Calculate stats
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    
    # Calculate total revenue
    orders = Order.query.filter(Order.status != "cancelled").all()
    total_revenue = sum(order.total_amount for order in orders)
    
    return render_template(
        "admin_dashboard.html",
        title="Admin Dashboard – SportsHub",
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue
    )

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """List all registered users."""
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template(
        "admin_users.html",
        title="Manage Users – SportsHub",
        users=users_list
    )

@admin_bp.route("/products")
@login_required
@admin_required
def products():
    """List all products for admin management."""
    products_list = Product.query.order_by(Product.created_at.desc()).all()
    return render_template(
        "admin_products.html",
        title="Manage Products – SportsHub",
        products=products_list
    )

@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def product_add():
    """Add a new product."""
    flash("Add product feature coming soon.", "info")
    return redirect(url_for("admin.products"))

@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def product_edit(product_id):
    """Edit an existing product."""
    flash("Edit product feature coming soon.", "info")
    return redirect(url_for("admin.products"))

@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def product_delete(product_id):
    """Delete a product."""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted successfully.", "success")
    return redirect(url_for("admin.products"))

@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    """List all orders for admin management."""
    orders_list = Order.query.order_by(Order.created_at.desc()).all()
    return render_template(
        "admin_orders.html",
        title="Manage Orders – SportsHub",
        orders=orders_list
    )

@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def order_update_status(order_id):
    """Update the status of an order."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    
    valid_statuses = [s.value for s in OrderStatus]
    
    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.id} status updated to {new_status.title()}.", "success")
    else:
        flash("Invalid status provided.", "danger")
        
    return redirect(url_for("admin.orders"))
