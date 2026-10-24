from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from decimal import Decimal

from app import db
from app.models import Product, CartItem, Promotion
from datetime import datetime

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


def _get_cart_items():
    """Return all CartItems for the current user, newest first."""
    return (
        current_user.cart_items
        .join(Product)
        .order_by(Product.name)
        .all()
    )


def _cart_total(items):
    """Sum of subtotals across all cart items."""
    return sum(item.subtotal for item in items)


@cart_bp.route("/")
@login_required
def cart():
    """Display the current user's cart."""
    items = _get_cart_items()
    total = _cart_total(items)
    item_count = sum(i.quantity for i in items)
    
    # Active general cart promotions
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
            promo_disc = Decimal(str(promo.calculate_discount(total)))
            if promo_disc > best_cart_promo_discount:
                best_cart_promo_discount = promo_disc

    free_shipping_threshold = Decimal("999.00")
    free_shipping_needed = max(Decimal("0"), free_shipping_threshold - total)
    free_shipping_pct = min(100, int((float(total) / float(free_shipping_threshold)) * 100)) if total > 0 else 0
                
    return render_template(
        "cart.html",
        title="My Shopping Cart – SportsHub",
        items=items,
        total=total,
        item_count=item_count,
        cart_promo_discount=best_cart_promo_discount,
        free_shipping_needed=free_shipping_needed,
        free_shipping_pct=free_shipping_pct,
    )


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    """Add a product to the cart, or increase quantity if already present."""
    product = Product.query.get_or_404(product_id)

    if not product.in_stock:
        flash(f"Sorry, '{product.name}' is out of stock.", "warning")
        return redirect(request.referrer or url_for("products.products"))

    try:
        qty = int(request.form.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1
    if qty < 1:
        qty = 1

    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
    ).first()

    if existing:
        new_qty = existing.quantity + qty
        if new_qty > product.stock:
            new_qty = product.stock
            flash(
                f"Only {product.stock} unit(s) of '{product.name}' available. Quantity adjusted.",
                "warning",
            )
        existing.quantity = new_qty
        db.session.commit()
        flash(f"'{product.name}' quantity updated in your cart.", "success")
    else:
        if qty > product.stock:
            qty = product.stock
        item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=qty,
        )
        db.session.add(item)
        db.session.commit()
        flash(f"'{product.name}' added to your cart!", "success")

    return redirect(request.referrer or url_for("cart.cart"))


@cart_bp.route("/update/<int:cart_item_id>", methods=["POST"])
@login_required
def update(cart_item_id):
    """Update quantity of a cart item with AJAX support."""
    item = CartItem.query.get_or_404(cart_item_id)

    if item.user_id != current_user.id:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": False, "message": "Unauthorized"}), 403
        flash("Action not allowed.", "danger")
        return redirect(url_for("cart.cart"))

    try:
        if request.is_json:
            qty = int(request.json.get("quantity", 1))
        else:
            qty = int(request.form.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    item_removed = False

    if qty < 1:
        db.session.delete(item)
        db.session.commit()
        item_removed = True
        msg = "Item removed from cart."
    elif qty > item.product.stock:
        item.quantity = item.product.stock
        db.session.commit()
        msg = f"Only {item.product.stock} units available in stock."
    else:
        item.quantity = qty
        db.session.commit()
        msg = f"Quantity updated to {qty}."

    items = _get_cart_items()
    new_total = _cart_total(items)
    new_count = sum(i.quantity for i in items)
    free_needed = max(0.0, 999.0 - float(new_total))
    free_pct = min(100, int((float(new_total) / 999.0) * 100)) if new_total > 0 else 0

    if is_ajax:
        return jsonify({
            "success": True,
            "message": msg,
            "item_removed": item_removed,
            "item_id": cart_item_id,
            "quantity": 0 if item_removed else item.quantity,
            "item_subtotal": 0 if item_removed else float(item.subtotal),
            "cart_total": float(new_total),
            "cart_count": new_count,
            "free_shipping_needed": free_needed,
            "free_shipping_pct": free_pct,
        })

    flash(msg, "info" if item_removed else "success")
    return redirect(url_for("cart.cart"))


@cart_bp.route("/remove/<int:cart_item_id>", methods=["POST"])
@login_required
def remove(cart_item_id):
    """Remove item from cart with AJAX support."""
    item = CartItem.query.get_or_404(cart_item_id)

    if item.user_id != current_user.id:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": False, "message": "Unauthorized"}), 403
        flash("Action not allowed.", "danger")
        return redirect(url_for("cart.cart"))

    product_name = item.product.name
    db.session.delete(item)
    db.session.commit()

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    if is_ajax:
        items = _get_cart_items()
        new_total = _cart_total(items)
        new_count = sum(i.quantity for i in items)
        return jsonify({
            "success": True,
            "message": f"'{product_name}' removed from your cart.",
            "item_id": cart_item_id,
            "cart_total": float(new_total),
            "cart_count": new_count,
            "free_shipping_needed": max(0.0, 999.0 - float(new_total)),
            "free_shipping_pct": min(100, int((float(new_total) / 999.0) * 100)) if new_total > 0 else 0,
        })

    flash(f"'{product_name}' removed from your cart.", "info")
    return redirect(url_for("cart.cart"))
