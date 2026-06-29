from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from decimal import Decimal

from app import db
from app.models import Order, OrderItem, CartItem

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


# ── helpers ───────────────────────────────────────────────────────────────────

def _cart_items():
    return (
        current_user.cart_items
        .join(CartItem.product)
        .order_by("products_1.name")          # joined alias
        .all()
    )


def _cart_total(items):
    return sum(i.subtotal for i in items)


# ── routes ────────────────────────────────────────────────────────────────────

@checkout_bp.route("/", methods=["GET", "POST"])
@login_required
def checkout():
    """Show checkout form (GET) and place the order (POST)."""
    items = current_user.cart_items.all()

    if not items:
        flash("Your cart is empty. Add products before checking out.", "warning")
        return redirect(url_for("products.products"))

    total = _cart_total(items)

    if request.method == "POST":
        # ── Collect shipping fields ───────────────────────────
        name    = request.form.get("name",    "").strip()
        address = request.form.get("address", "").strip()
        city    = request.form.get("city",    "").strip()
        phone   = request.form.get("phone",   "").strip()

        # Simple server-side validation
        errors = []
        if not name:    errors.append("Full name is required.")
        if not address: errors.append("Delivery address is required.")
        if not city:    errors.append("City is required.")
        if not phone:   errors.append("Phone number is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "checkout.html",
                title="Checkout – SportsHub",
                items=items,
                total=total,
                form_data=request.form,
            )

        # ── Re-check stock before committing ─────────────────
        stock_errors = []
        for item in items:
            if item.quantity > item.product.stock:
                stock_errors.append(
                    f"'{item.product.name}' only has {item.product.stock} unit(s) left."
                )
        if stock_errors:
            for e in stock_errors:
                flash(e, "danger")
            return redirect(url_for("cart.cart"))

        # ── Create Order ──────────────────────────────────────
        order = Order(
            user_id          = current_user.id,
            status           = "processing",
            total_amount     = total,
            shipping_name    = name,
            shipping_address = address,
            shipping_city    = city,
            shipping_phone   = phone,
        )
        db.session.add(order)
        db.session.flush()          # get order.id before adding items

        # ── Create OrderItems + deduct stock ──────────────────
        for item in items:
            order_item = OrderItem(
                order_id   = order.id,
                product_id = item.product_id,
                quantity   = item.quantity,
                unit_price = item.product.price,   # price snapshot
            )
            db.session.add(order_item)
            item.product.stock -= item.quantity    # deduct stock

        # ── Clear cart ────────────────────────────────────────
        for item in items:
            db.session.delete(item)

        db.session.commit()

        flash(f"Order #{order.id} placed successfully! Thank you, {current_user.name}.", "success")
        return redirect(url_for("checkout.order_confirmation", order_id=order.id))

    return render_template(
        "checkout.html",
        title="Checkout – SportsHub",
        items=items,
        total=total,
        form_data={},
    )


@checkout_bp.route("/confirmation/<int:order_id>")
@login_required
def order_confirmation(order_id):
    """Order success page shown immediately after checkout."""
    order = Order.query.get_or_404(order_id)

    # Security: only the owner can view
    if order.user_id != current_user.id:
        flash("Order not found.", "danger")
        return redirect(url_for("main.index"))

    return render_template(
        "order_confirmation.html",
        title=f"Order #{order.id} Confirmed – SportsHub",
        order=order,
    )


