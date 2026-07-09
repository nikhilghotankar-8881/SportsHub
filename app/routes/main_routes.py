"""
app/routes/main_routes.py
Home, dashboard, profile edit, change password.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms import EditProfileForm, ChangePasswordForm
from app import db

main = Blueprint("main", __name__)

from app.models import Product, FlashSale, Promotion
from datetime import datetime

@main.route("/")
@main.route("/home")
def index():
    featured_products = Product.query.limit(4).all()
    latest_arrivals   = Product.query.order_by(Product.created_at.desc()).limit(4).all()
    
    # Homepage Promotions
    now = datetime.utcnow()
    active_flash_sales = FlashSale.query.filter(
        FlashSale.start_time <= now,
        FlashSale.end_time >= now
    ).all()
    
    active_promotions = Promotion.query.filter(
        Promotion.is_active == True,
        Promotion.start_date <= now,
        Promotion.end_date >= now
    ).all()

    return render_template(
        "index.html",
        title="SportsHub - Home",
        featured_products=featured_products,
        latest_arrivals=latest_arrivals,
        active_flash_sales=active_flash_sales,
        active_promotions=active_promotions,
    )


@main.route("/dashboard")
@login_required
def dashboard():
    total_orders       = current_user.orders.count()
    total_wishlist_items = current_user.wishlist_items.count()
    total_cart_items   = sum(item.quantity for item in current_user.cart_items.all())
    total_reviews      = current_user.reviews.count()
    recent_orders      = current_user.orders.limit(5).all()

    return render_template(
        "dashboard.html",
        title="Dashboard",
        total_orders=total_orders,
        total_wishlist_items=total_wishlist_items,
        total_cart_items=total_cart_items,
        total_reviews=total_reviews,
        recent_orders=recent_orders,
    )


@main.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name  = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your profile has been updated successfully.", "success")
        return redirect(url_for("main.dashboard"))
    elif request.method == "GET":
        form.name.data  = current_user.name
        form.email.data = current_user.email
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@main.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()

            # Send password change email (graceful fallback)
            try:
                from app.helpers.email_helper import send_password_change_email
                send_password_change_email(current_user)
            except Exception:
                pass

            flash("Your password has been updated successfully.", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Incorrect current password.", "danger")
    return render_template("change_password.html", title="Change Password", form=form)
