"""
app/routes/checkout_routes.py
Handles checkout flow with coupon support, GST, stock management.
"""
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session,
)
from flask_login import login_required, current_user
from decimal import Decimal

from app import db
from app.models import Order, OrderItem, CartItem, Coupon, OrderStatusHistory, Promotion, PromotionCategory, PromotionProduct
from app.helpers.email_helper import (
    send_order_confirmation_email, send_coupon_applied_email
)

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")

GST_RATE = Decimal("18")   # 18% – also in config but available as constant


# ── helpers ───────────────────────────────────────────────────────────────────

def _cart_items():
    return (
        current_user.cart_items
        .join(CartItem.product)
        .order_by("products_1.name")
        .all()
    )


def _cart_total(items):
    return sum(i.subtotal for i in items)


def _get_session_coupon():
    """Return (coupon_code, discount_amount) from session or (None, 0)."""
    code     = session.get("coupon_code")
    discount = Decimal(str(session.get("coupon_discount", 0)))
    return code, discount


# ── routes ────────────────────────────────────────────────────────────────────

@checkout_bp.route("/", methods=["GET", "POST"])
@login_required
def checkout():
    """Show checkout form (GET) and place the order (POST)."""
    items = current_user.cart_items.all()

    if not items:
        flash("Your cart is empty. Add products before checking out.", "warning")
        return redirect(url_for("products.products"))

    subtotal = _cart_total(items)
    coupon_code, discount = _get_session_coupon()

    # Validate session coupon still applies (cart may have changed)
    if coupon_code:
        coupon_obj = Coupon.query.filter_by(code=coupon_code).first()
        if coupon_obj:
            valid, _ = coupon_obj.is_valid(subtotal)
            if not valid:
                session.pop("coupon_code", None)
                session.pop("coupon_discount", None)
                coupon_code, discount = None, Decimal("0")
        else:
            session.pop("coupon_code", None)
            session.pop("coupon_discount", None)
            coupon_code, discount = None, Decimal("0")

    # Check for active cart-level promotions (no products or categories attached)
    from datetime import datetime
    cart_promos = Promotion.query.filter(
        Promotion.is_active == True,
        Promotion.start_date <= datetime.utcnow(),
        Promotion.end_date >= datetime.utcnow(),
        ~Promotion.products.any(),
        ~Promotion.categories.any()
    ).all()

    best_cart_promo_discount = Decimal("0")
    for promo in cart_promos:
        if promo.usage_limit is None or promo.used_count < promo.usage_limit:
            promo_disc = Decimal(str(promo.calculate_discount(subtotal)))
            if promo_disc > best_cart_promo_discount:
                best_cart_promo_discount = promo_disc

    total_discount = discount + best_cart_promo_discount
    taxable_amount = subtotal - total_discount
    if taxable_amount < Decimal("0"):
        taxable_amount = Decimal("0")
        total_discount = subtotal

    gst_amount     = (taxable_amount * GST_RATE / 100).quantize(Decimal("0.01"))
    total          = taxable_amount + gst_amount

    if request.method == "POST":
        # ── Collect shipping fields ───────────────────────────
        name    = request.form.get("name",    "").strip()
        address = request.form.get("address", "").strip()
        city    = request.form.get("city",    "").strip()
        phone   = request.form.get("phone",   "").strip()

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
                subtotal=subtotal,
                discount=discount,
                gst_amount=gst_amount,
                total=total,
                coupon_code=coupon_code,
                form_data=request.form,
            )

        # ── Re-check stock ────────────────────────────────────
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
        try:
            order = Order(
                user_id          = current_user.id,
                status           = "placed",
                total_amount     = total,
                discount_amount  = total_discount,
                coupon_code      = coupon_code,
                gst_amount       = gst_amount,
                shipping_name    = name,
                shipping_address = address,
                shipping_city    = city,
                shipping_phone   = phone,
            )
            db.session.add(order)
            db.session.flush()  # get order.id

            # ── Create OrderItems + deduct stock ──────────────────
            for item in items:
                order_item = OrderItem(
                    order_id   = order.id,
                    product_id = item.product_id,
                    quantity   = item.quantity,
                    unit_price = Decimal(str(item.product.effective_price)),
                )
                db.session.add(order_item)
                item.product.stock -= item.quantity

            # ── Initial status history entry ──────────────────────
            history = OrderStatusHistory(
                order_id = order.id,
                status   = "placed",
                note     = "Order placed successfully.",
            )
            db.session.add(history)

            # ── Increment coupon usage ────────────────────────────
            coupon_obj = None
            if coupon_code:
                coupon_obj = Coupon.query.filter_by(code=coupon_code).first()
                if coupon_obj:
                    coupon_obj.used_count += 1

            # ── Clear cart ────────────────────────────────────────
            for item in items:
                db.session.delete(item)

            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("An error occurred while placing your order. Please try again.", "danger")
            return redirect(url_for("checkout.checkout"))

        # ── Clear coupon session ──────────────────────────────
        session.pop("coupon_code", None)
        session.pop("coupon_discount", None)

        # ── Send emails (graceful fallback) ───────────────────
        try:
            send_order_confirmation_email(current_user, order)
            if coupon_obj and float(discount) > 0:
                send_coupon_applied_email(current_user, order, coupon_obj)
        except Exception:
            pass

        flash(
            f"Order #{order.id} placed successfully! Thank you, {current_user.name}.",
            "success",
        )
        return redirect(url_for("checkout.order_confirmation", order_id=order.id))

    return render_template(
        "checkout.html",
        title="Checkout – SportsHub",
        items=items,
        subtotal=subtotal,
        discount=discount,
        gst_amount=gst_amount,
        total=total,
        coupon_code=coupon_code,
        form_data={},
    )


@checkout_bp.route("/confirmation/<int:order_id>")
@login_required
def order_confirmation(order_id):
    """Order success page shown immediately after checkout."""
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash("Order not found.", "danger")
        return redirect(url_for("main.index"))

    return render_template(
        "order_confirmation.html",
        title=f"Order #{order.id} Confirmed – SportsHub",
        order=order,
    )
