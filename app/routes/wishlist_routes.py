from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Product, Wishlist
from sqlalchemy.exc import IntegrityError

wishlist_bp = Blueprint("wishlist", __name__, url_prefix="/wishlist")

@wishlist_bp.route("/")
@login_required
def view_wishlist():
    items = current_user.wishlist_items.all()
    return render_template("wishlist.html", items=items)

@wishlist_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash(f"{product.name} is already in your wishlist.", "info")
    else:
        new_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(new_item)
        try:
            db.session.commit()
            flash(f"{product.name} added to your wishlist!", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Error adding item to wishlist.", "danger")
            
    return redirect(request.referrer or url_for('products.products'))

@wishlist_bp.route("/remove/<int:product_id>", methods=["POST"])
@login_required
def remove(product_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from your wishlist.", "info")
    return redirect(request.referrer or url_for('wishlist.view_wishlist'))
