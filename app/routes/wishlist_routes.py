from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Wishlist
from sqlalchemy.exc import IntegrityError

wishlist_bp = Blueprint("wishlist", __name__, url_prefix="/wishlist")

@wishlist_bp.route("/")
@login_required
def view_wishlist():
    items = current_user.wishlist_items.all()
    return render_template("wishlist.html", items=items, title="My Wishlist – SportsHub")

@wishlist_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    product = Product.query.get_or_404(product_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        msg = f"'{product.name}' is already in your wishlist."
        if is_ajax:
            return jsonify({
                "success": True,
                "in_wishlist": True,
                "message": msg,
                "count": current_user.wishlist_items.count()
            })
        flash(msg, "info")
    else:
        new_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(new_item)
        try:
            db.session.commit()
            msg = f"'{product.name}' added to your wishlist!"
            if is_ajax:
                return jsonify({
                    "success": True,
                    "in_wishlist": True,
                    "message": msg,
                    "count": current_user.wishlist_items.count()
                })
            flash(msg, "success")
        except IntegrityError:
            db.session.rollback()
            if is_ajax:
                return jsonify({"success": False, "message": "Error updating wishlist."}), 500
            flash("Error updating wishlist.", "danger")
            
    return redirect(request.referrer or url_for('products.products'))

@wishlist_bp.route("/remove/<int:product_id>", methods=["POST"])
@login_required
def remove(product_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    
    msg = "Item removed from your wishlist."
    if is_ajax:
        return jsonify({
            "success": True,
            "in_wishlist": False,
            "message": msg,
            "count": current_user.wishlist_items.count()
        })
    
    flash(msg, "info")
    return redirect(request.referrer or url_for('wishlist.view_wishlist'))
