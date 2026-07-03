"""
app/routes/order_routes.py
Customer order history, detail view, tracking, and cancellation.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Order, OrderStatusHistory

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

# Statuses the customer can cancel from
CANCELLABLE_STATUSES = {"placed", "confirmed", "pending", "processing"}


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
    """Detailed view of a single order with tracking timeline."""
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash("Order not found.", "danger")
        return redirect(url_for("orders.order_history"))

    # Build timeline from status history
    history = order.status_history.order_by(OrderStatusHistory.changed_at.asc()).all()

    # Tracking pipeline (for the visual stepper)
    tracking_steps = [
        ("placed",           "Order Placed",       "bi-bag-plus"),
        ("confirmed",        "Confirmed",           "bi-check-circle"),
        ("packed",           "Packed",              "bi-box-seam"),
        ("shipped",          "Shipped",             "bi-truck"),
        ("out_for_delivery", "Out for Delivery",    "bi-bicycle"),
        ("delivered",        "Delivered",           "bi-bag-check"),
    ]

    status_order = [s[0] for s in tracking_steps]
    current_idx  = status_order.index(order.status) if order.status in status_order else -1
    is_cancelled = order.status == "cancelled"

    return render_template(
        "order_detail.html",
        title=f"Order #{order.id} – SportsHub",
        order=order,
        history=history,
        tracking_steps=tracking_steps,
        current_idx=current_idx,
        is_cancelled=is_cancelled,
        can_cancel=order.status in CANCELLABLE_STATUSES,
    )


@orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    """Customer can cancel an order if it's still in an early status."""
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash("Order not found.", "danger")
        return redirect(url_for("orders.order_history"))

    if order.status not in CANCELLABLE_STATUSES:
        flash("This order cannot be cancelled at this stage.", "warning")
        return redirect(url_for("orders.order_detail", order_id=order_id))

    # Restore stock
    for item in order.order_items:
        item.product.stock += item.quantity

    order.status = "cancelled"
    history = OrderStatusHistory(
        order_id = order.id,
        status   = "cancelled",
        note     = "Cancelled by customer.",
    )
    db.session.add(history)
    db.session.commit()

    flash(f"Order #{order.id} has been cancelled. Stock restored.", "info")
    return redirect(url_for("orders.order_history"))
