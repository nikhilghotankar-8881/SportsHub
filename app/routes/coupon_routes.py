"""
app/routes/coupon_routes.py
Handles coupon application via AJAX and admin CRUD for coupons.
"""
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify, session,
)
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from decimal import Decimal

from app import db
from app.models import Coupon, CartItem, CouponType

coupon_bp = Blueprint("coupon", __name__, url_prefix="/coupon")


# ── Admin guard ───────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated


# ── Customer: Apply Coupon (AJAX + form fallback) ─────────────────────────────

@coupon_bp.route("/apply", methods=["POST"])
@login_required
def apply_coupon():
    """Apply coupon code during checkout. Returns JSON for AJAX requests."""
    code = request.form.get("coupon_code", "").strip().upper()

    # Calculate cart total
    cart_items = current_user.cart_items.all()
    cart_total = sum(item.subtotal for item in cart_items)

    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        resp = {"success": False, "message": "Invalid coupon code."}
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(resp)
        flash(resp["message"], "danger")
        return redirect(url_for("checkout.checkout"))

    if session.get("coupon_code") == coupon.code:
        resp = {"success": False, "message": "Coupon is already applied."}
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(resp)
        flash(resp["message"], "info")
        return redirect(url_for("checkout.checkout"))

    valid, msg = coupon.is_valid(cart_total)
    if not valid:
        resp = {"success": False, "message": msg}
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(resp)
        flash(msg, "danger")
        return redirect(url_for("checkout.checkout"))

    discount = coupon.calculate_discount(cart_total)
    # Store in session for use at order placement
    session["coupon_code"]     = coupon.code
    session["coupon_discount"] = str(discount)

    resp = {
        "success":          True,
        "message":          f"Coupon '{code}' applied! You save ₹{discount:,.2f}",
        "discount":         float(discount),
        "coupon_code":      code,
        "cart_total":       float(cart_total),
        "payable":          max(0.0, float(cart_total) - float(discount)),
    }
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(resp)

    flash(resp["message"], "success")
    return redirect(url_for("checkout.checkout"))


@coupon_bp.route("/remove", methods=["POST"])
@login_required
def remove_coupon():
    """Remove applied coupon from session."""
    session.pop("coupon_code", None)
    session.pop("coupon_discount", None)
    flash("Coupon removed.", "info")
    return redirect(url_for("checkout.checkout"))


# ── Admin: Coupon CRUD ────────────────────────────────────────────────────────

@coupon_bp.route("/admin/list")
@login_required
@admin_required
def admin_list():
    """List all coupons."""
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template(
        "admin_coupons.html",
        title="Manage Coupons – SportsHub",
        coupons=coupons,
        coupon_types=CouponType,
        now=datetime.utcnow(),
    )


@coupon_bp.route("/admin/add", methods=["GET", "POST"])
@login_required
@admin_required
def admin_add():
    """Add a new coupon."""
    if request.method == "POST":
        code          = request.form.get("code", "").strip().upper()
        description   = request.form.get("description", "").strip()
        coupon_type   = request.form.get("coupon_type", CouponType.PERCENTAGE.value)
        discount_val  = request.form.get("discount_value", "0")
        min_purchase  = request.form.get("minimum_purchase", "0")
        max_discount  = request.form.get("max_discount", "")
        usage_limit   = request.form.get("usage_limit", "")
        is_active     = request.form.get("is_active") == "on"
        expires_at_str = request.form.get("expires_at", "")

        # Validate
        if not code:
            flash("Coupon code is required.", "danger")
            return redirect(url_for("coupon.admin_add"))
        if Coupon.query.filter_by(code=code).first():
            flash(f"Coupon code '{code}' already exists.", "danger")
            return redirect(url_for("coupon.admin_add"))

        try:
            discount_val = Decimal(discount_val)
            min_purchase = Decimal(min_purchase)
            max_discount_dec = Decimal(max_discount) if max_discount else None
        except ValueError:
            flash("Invalid numeric values.", "danger")
            return redirect(url_for("coupon.admin_add"))

        expires_at = None
        if expires_at_str:
            try:
                expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid expiry date format.", "danger")
                    return redirect(url_for("coupon.admin_add"))

        coupon = Coupon(
            code             = code,
            description      = description,
            coupon_type      = coupon_type,
            discount_value   = discount_val,
            minimum_purchase = min_purchase,
            max_discount     = max_discount_dec,
            usage_limit      = int(usage_limit) if usage_limit else None,
            is_active        = is_active,
            expires_at       = expires_at,
        )
        db.session.add(coupon)
        try:
            db.session.commit()
            flash(f"Coupon '{code}' created successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("A database error occurred. Could not create coupon.", "danger")
        return redirect(url_for("coupon.admin_list"))

    return render_template(
        "admin_coupon_form.html",
        title="Add Coupon – SportsHub",
        coupon=None,
        coupon_types=[CouponType.PERCENTAGE.value, CouponType.FIXED.value],
    )


@coupon_bp.route("/admin/edit/<int:coupon_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit(coupon_id):
    """Edit an existing coupon."""
    coupon = Coupon.query.get_or_404(coupon_id)

    if request.method == "POST":
        coupon.code           = request.form.get("code", "").strip().upper()
        coupon.description    = request.form.get("description", "").strip()
        coupon.coupon_type    = request.form.get("coupon_type", CouponType.PERCENTAGE.value)
        coupon.is_active      = request.form.get("is_active") == "on"

        try:
            coupon.discount_value   = Decimal(request.form.get("discount_value", 0))
            coupon.minimum_purchase = Decimal(request.form.get("minimum_purchase", 0))
            max_discount = request.form.get("max_discount", "")
            coupon.max_discount = Decimal(max_discount) if max_discount else None
        except ValueError:
            flash("Invalid numeric values.", "danger")
            return redirect(url_for("coupon.admin_edit", coupon_id=coupon_id))

        usage_limit = request.form.get("usage_limit", "")
        coupon.usage_limit = int(usage_limit) if usage_limit else None

        expires_at_str = request.form.get("expires_at", "")
        if expires_at_str:
            try:
                coupon.expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    coupon.expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid expiry date.", "danger")
                    return redirect(url_for("coupon.admin_edit", coupon_id=coupon_id))
        else:
            coupon.expires_at = None

        try:
            db.session.commit()
            flash(f"Coupon '{coupon.code}' updated.", "success")
        except Exception:
            db.session.rollback()
            flash("A database error occurred. Could not update coupon.", "danger")
            
        return redirect(url_for("coupon.admin_list"))

    return render_template(
        "admin_coupon_form.html",
        title="Edit Coupon – SportsHub",
        coupon=coupon,
        coupon_types=[CouponType.PERCENTAGE.value, CouponType.FIXED.value],
    )


@coupon_bp.route("/admin/delete/<int:coupon_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete(coupon_id):
    """Delete a coupon."""
    coupon = Coupon.query.get_or_404(coupon_id)
    code = coupon.code
    db.session.delete(coupon)
    try:
        db.session.commit()
        flash(f"Coupon '{code}' deleted.", "success")
    except Exception:
        db.session.rollback()
        flash("A database error occurred. Could not delete coupon.", "danger")
    return redirect(url_for("coupon.admin_list"))


@coupon_bp.route("/admin/toggle/<int:coupon_id>", methods=["POST"])
@login_required
@admin_required
def admin_toggle(coupon_id):
    """Toggle coupon active/inactive."""
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    try:
        db.session.commit()
        state = "activated" if coupon.is_active else "deactivated"
        flash(f"Coupon '{coupon.code}' {state}.", "success")
    except Exception:
        db.session.rollback()
        flash("A database error occurred. Could not toggle coupon.", "danger")
    return redirect(url_for("coupon.admin_list"))
