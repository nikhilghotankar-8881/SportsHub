from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import Order

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

@orders_bp.route("/")
@login_required
def order_history():
    """List all orders for the current user, newest first."""
    orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template(
        "orders.html",
        title="My Orders – SportsHub",
        orders=orders,
    )

@orders_bp.route("/<int:order_id>")
@login_required
def order_detail(order_id):
    """Detailed view of a single order."""
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash("Order not found.", "danger")
        return redirect(url_for("orders.order_history"))

    return render_template(
        "order_detail.html",
        title=f"Order #{order.id} – SportsHub",
        order=order,
    )
