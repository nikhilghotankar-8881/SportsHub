from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from decimal import Decimal

from app import db
from app.models import Product, CartItem

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


# ── helpers ──────────────────────────────────────────────────────────────────

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


# ── routes ────────────────────────────────────────────────────────────────────

@cart_bp.route("/")
@login_required
def cart():
    """Display the current user's cart."""
    items = _get_cart_items()
    total = _cart_total(items)
    item_count = sum(i.quantity for i in items)
    from datetime import datetime
    from app.models import Promotion
    
    cart_promos = Promotion.query.filter(
        Promotion.is_active == True,
        Promotion.start_date <= datetime.utcnow(),
        Promotion.end_date >= datetime.utcnow(),
        ~Promotion.products.any(),
        ~Promotion.categories.any()
    ).all()
    
    from decimal import Decimal
    best_cart_promo_discount = Decimal("0")
    for promo in cart_promos:
        if promo.usage_limit is None or promo.used_count < promo.usage_limit:
            promo_disc = Decimal(str(promo.calculate_discount(total)))
            if promo_disc > best_cart_promo_discount:
                best_cart_promo_discount = promo_disc
                
    return render_template(
        "cart.html",
        title="My Cart – SportsHub",
        items=items,
        total=total,
        item_count=item_count,
        cart_promo_discount=best_cart_promo_discount,
    )


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    """Add a product to the cart, or increase quantity if already present."""
    product = Product.query.get_or_404(product_id)

    if not product.in_stock:
        flash(f"Sorry, '{product.name}' is out of stock.", "warning")
        return redirect(request.referrer or url_for("products.products"))

    qty = int(request.form.get("quantity", 1))
    if qty < 1:
        qty = 1

    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
    ).first()

    if existing:
        new_qty = existing.quantity + qty
        # cap at available stock
        if new_qty > product.stock:
            new_qty = product.stock
            flash(
                f"Only {product.stock} unit(s) of '{product.name}' available. "
                "Quantity adjusted.",
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

    # Go back to where the user came from (product page / listing)
    return redirect(request.referrer or url_for("cart.cart"))


@cart_bp.route("/update/<int:cart_item_id>", methods=["POST"])
@login_required
def update(cart_item_id):
    """Update the quantity of a cart item."""
    item = CartItem.query.get_or_404(cart_item_id)

    # Security: only allow the owner to update
    if item.user_id != current_user.id:
        flash("Action not allowed.", "danger")
        return redirect(url_for("cart.cart"))

    try:
        qty = int(request.form.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1

    if qty < 1:
        # treat quantity=0 as a remove
        db.session.delete(item)
        db.session.commit()
        flash(f"'{item.product.name}' removed from your cart.", "info")
    elif qty > item.product.stock:
        item.quantity = item.product.stock
        db.session.commit()
        flash(
            f"Only {item.product.stock} unit(s) available. Quantity adjusted.",
            "warning",
        )
    else:
        item.quantity = qty
        db.session.commit()
        flash(f"'{item.product.name}' quantity updated.", "success")

    return redirect(url_for("cart.cart"))


@cart_bp.route("/remove/<int:cart_item_id>", methods=["POST"])
@login_required
def remove(cart_item_id):
    """Remove a single item from the cart."""
    item = CartItem.query.get_or_404(cart_item_id)

    # Security: only allow the owner to remove
    if item.user_id != current_user.id:
        flash("Action not allowed.", "danger")
        return redirect(url_for("cart.cart"))

    product_name = item.product.name
    db.session.delete(item)
    db.session.commit()
    flash(f"'{product_name}' removed from your cart.", "info")
    return redirect(url_for("cart.cart"))
