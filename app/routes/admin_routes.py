"""
app/routes/admin_routes.py
Full admin panel: dashboard analytics, product/user/order/coupon management,
order status updates, inventory management, contact messages.
"""
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify,
)
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
from decimal import Decimal

from app import db
from app.models import (
    User, Product, Order, OrderItem, OrderStatus,
    Review, Coupon, Contact, OrderStatusHistory,
)
from app.helpers.email_helper import send_order_delivered_email

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ── Admin guard ───────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated_function


# ── Sales Dashboard ───────────────────────────────────────────────────────────

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Admin dashboard with full analytics and charts."""
    now   = datetime.utcnow()
    today = now.date()

    # ── Core counts ───────────────────────────────────────────────
    total_users    = User.query.count()
    total_products = Product.query.count()
    total_orders   = Order.query.count()

    # ── Revenue calculations ──────────────────────────────────────
    non_cancelled = Order.query.filter(Order.status != "cancelled")

    total_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(Order.status != "cancelled").scalar() or 0

    today_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(
        Order.status != "cancelled",
        func.date(Order.created_at) == today,
    ).scalar() or 0

    # Monthly revenue (current month)
    first_of_month = today.replace(day=1)
    monthly_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(
        Order.status != "cancelled",
        Order.created_at >= first_of_month,
    ).scalar() or 0

    # ── Order status counts ───────────────────────────────────────
    pending_orders   = Order.query.filter(Order.status.in_(["placed", "pending"])).count()
    delivered_orders = Order.query.filter(Order.status == "delivered").count()
    cancelled_orders = Order.query.filter(Order.status == "cancelled").count()

    # ── Best-selling products ─────────────────────────────────────
    best_sellers = (
        db.session.query(
            Product,
            func.sum(OrderItem.quantity).label("total_sold"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != "cancelled")
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    # ── Top customers ─────────────────────────────────────────────
    top_customers = (
        db.session.query(
            User,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_spent"),
        )
        .join(Order, User.id == Order.user_id)
        .filter(Order.status != "cancelled")
        .group_by(User.id)
        .order_by(func.sum(Order.total_amount).desc())
        .limit(5)
        .all()
    )

    # ── Monthly revenue chart data (last 6 months) ────────────────
    monthly_labels = []
    monthly_data   = []
    for i in range(5, -1, -1):
        target = today - timedelta(days=i * 30)
        month_start = target.replace(day=1)
        if i == 0:
            month_end = today
        else:
            next_month  = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end   = next_month - timedelta(days=1)

        rev = db.session.query(
            func.sum(Order.total_amount)
        ).filter(
            Order.status != "cancelled",
            Order.created_at >= month_start,
            Order.created_at <= datetime.combine(month_end, datetime.max.time()),
        ).scalar() or 0

        monthly_labels.append(month_start.strftime("%b %Y"))
        monthly_data.append(float(rev))

    # ── Daily orders chart (last 7 days) ──────────────────────────
    daily_labels = []
    daily_data   = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Order.query.filter(
            func.date(Order.created_at) == day
        ).count()
        daily_labels.append(day.strftime("%d %b"))
        daily_data.append(count)

    # ── Low stock products ────────────────────────────────────────
    low_stock_products = Product.query.filter(
        Product.stock <= Product.low_stock_threshold,
        Product.stock > 0,
    ).count()
    out_of_stock_products = Product.query.filter(Product.stock <= 0).count()

    # ── Unread contact messages ───────────────────────────────────
    unread_contacts = Contact.query.filter_by(is_read=False).count()

    return render_template(
        "admin_dashboard.html",
        title="Admin Dashboard – SportsHub",
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        today_revenue=float(today_revenue),
        monthly_revenue=float(monthly_revenue),
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        best_sellers=best_sellers,
        top_customers=top_customers,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
        daily_labels=daily_labels,
        daily_data=daily_data,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        unread_contacts=unread_contacts,
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template(
        "admin_users.html",
        title="Manage Users – SportsHub",
        users=users_list,
    )


# ── Products ──────────────────────────────────────────────────────────────────

@admin_bp.route("/products")
@login_required
@admin_required
def products():
    products_list = Product.query.order_by(Product.created_at.desc()).all()
    return render_template(
        "admin_products.html",
        title="Manage Products – SportsHub",
        products=products_list,
    )


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def product_add():
    """Add a new product."""
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price_str   = request.form.get("price", "0")
        stock_str   = request.form.get("stock", "0")
        image       = request.form.get("image", "").strip()
        category    = request.form.get("category", "").strip()
        threshold   = request.form.get("low_stock_threshold", "5")

        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("admin.product_add"))
        try:
            price    = Decimal(price_str)
            stock    = int(stock_str)
            threshold = int(threshold)
        except (ValueError, Exception):
            flash("Invalid price or stock values.", "danger")
            return redirect(url_for("admin.product_add"))

        product = Product(
            name=name, description=description, price=price,
            stock=stock, image=image or None, category=category or None,
            low_stock_threshold=threshold,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"Product '{name}' added successfully.", "success")
        return redirect(url_for("admin.products"))

    categories = db.session.query(Product.category).filter(
        Product.category.isnot(None)
    ).distinct().all()
    categories = [c[0] for c in categories]
    return render_template(
        "admin_product_form.html",
        title="Add Product – SportsHub",
        product=None,
        categories=categories,
    )


@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def product_edit(product_id):
    """Edit an existing product."""
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name        = request.form.get("name", "").strip()
        product.description = request.form.get("description", "").strip()
        product.image       = request.form.get("image", "").strip() or None
        product.category    = request.form.get("category", "").strip() or None
        try:
            product.price               = Decimal(request.form.get("price", "0"))
            product.stock               = int(request.form.get("stock", "0"))
            product.low_stock_threshold = int(request.form.get("low_stock_threshold", "5"))
        except (ValueError, Exception):
            flash("Invalid price or stock values.", "danger")
            return redirect(url_for("admin.product_edit", product_id=product_id))

        db.session.commit()
        flash(f"Product '{product.name}' updated.", "success")
        return redirect(url_for("admin.products"))

    categories = db.session.query(Product.category).filter(
        Product.category.isnot(None)
    ).distinct().all()
    categories = [c[0] for c in categories]
    return render_template(
        "admin_product_form.html",
        title="Edit Product – SportsHub",
        product=product,
        categories=categories,
    )


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted.", "success")
    return redirect(url_for("admin.products"))


# ── Orders ────────────────────────────────────────────────────────────────────

@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    status_filter = request.args.get("status", "")
    q = Order.query
    if status_filter:
        q = q.filter(Order.status == status_filter)
    orders_list = q.order_by(Order.created_at.desc()).all()

    valid_statuses = [
        "placed", "confirmed", "packed", "shipped",
        "out_for_delivery", "delivered", "cancelled",
    ]
    return render_template(
        "admin_orders.html",
        title="Manage Orders – SportsHub",
        orders=orders_list,
        valid_statuses=valid_statuses,
        current_status=status_filter,
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def order_update_status(order_id):
    """Update the status of an order with tracking history."""
    order      = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "").strip()
    note       = request.form.get("note", "").strip()

    valid_statuses = [
        "placed", "confirmed", "packed", "shipped",
        "out_for_delivery", "delivered", "cancelled",
        "pending", "processing",
    ]
    if new_status not in valid_statuses:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.orders"))

    old_status   = order.status
    order.status = new_status

    # Restore stock on cancellation
    if new_status == "cancelled" and old_status != "cancelled":
        for item in order.order_items:
            item.product.stock += item.quantity

    # Record in history
    history = OrderStatusHistory(
        order_id = order.id,
        status   = new_status,
        note     = note or None,
    )
    db.session.add(history)
    db.session.commit()

    # Send delivery email
    if new_status == "delivered":
        try:
            send_order_delivered_email(order.user, order)
        except Exception:
            pass

    flash(f"Order #{order.id} updated to '{new_status}'.", "success")
    return redirect(url_for("admin.orders"))


# ── Reviews ───────────────────────────────────────────────────────────────────

@admin_bp.route("/reviews")
@login_required
@admin_required
def reviews():
    product_id = request.args.get("product_id")
    user_id    = request.args.get("user_id")

    query = Review.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    if user_id:
        query = query.filter_by(user_id=user_id)

    reviews  = query.order_by(Review.created_at.desc()).all()
    products = Product.query.order_by(Product.name).all()
    users    = User.query.order_by(User.name).all()

    return render_template(
        "admin_reviews.html",
        reviews=reviews,
        products=products,
        users=users,
        selected_product=int(product_id) if product_id else None,
        selected_user=int(user_id) if user_id else None,
    )


@admin_bp.route("/reviews/delete/<int:review_id>", methods=["POST"])
@login_required
@admin_required
def review_delete(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("admin.reviews"))


# ── Inventory ─────────────────────────────────────────────────────────────────

@admin_bp.route("/inventory")
@login_required
@admin_required
def inventory():
    """Inventory dashboard with stock levels."""
    filter_type = request.args.get("filter", "all")
    q = Product.query

    if filter_type == "low":
        q = q.filter(Product.stock <= Product.low_stock_threshold, Product.stock > 0)
    elif filter_type == "out":
        q = q.filter(Product.stock <= 0)

    products_list = q.order_by(Product.stock.asc()).all()

    total_products    = Product.query.count()
    total_inventory   = db.session.query(func.sum(Product.stock)).scalar() or 0
    inventory_value   = sum(p.inventory_value for p in Product.query.all())
    low_stock_count   = Product.query.filter(
        Product.stock <= Product.low_stock_threshold, Product.stock > 0
    ).count()
    out_of_stock_count = Product.query.filter(Product.stock <= 0).count()

    return render_template(
        "admin_inventory.html",
        title="Inventory Management – SportsHub",
        products=products_list,
        total_products=total_products,
        total_inventory=total_inventory,
        inventory_value=inventory_value,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        current_filter=filter_type,
    )


@admin_bp.route("/inventory/update/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def inventory_update(product_id):
    """Update stock for a single product."""
    product   = Product.query.get_or_404(product_id)
    new_stock = request.form.get("stock", "")
    threshold = request.form.get("low_stock_threshold", "")

    try:
        if new_stock != "":
            product.stock = int(new_stock)
        if threshold != "":
            product.low_stock_threshold = int(threshold)
    except ValueError:
        flash("Invalid stock value.", "danger")
        return redirect(url_for("admin.inventory"))

    db.session.commit()
    flash(f"Stock for '{product.name}' updated to {product.stock}.", "success")
    return redirect(url_for("admin.inventory"))


@admin_bp.route("/inventory/bulk-update", methods=["POST"])
@login_required
@admin_required
def inventory_bulk_update():
    """Bulk update stock for multiple products."""
    updated = 0
    for key, value in request.form.items():
        if key.startswith("stock_"):
            try:
                product_id = int(key.split("_")[1])
                new_stock  = int(value)
                product    = Product.query.get(product_id)
                if product and product.stock != new_stock:
                    product.stock = new_stock
                    updated += 1
            except (ValueError, IndexError):
                continue

    db.session.commit()
    flash(f"Bulk update complete. {updated} product(s) updated.", "success")
    return redirect(url_for("admin.inventory"))


# ── Contacts ──────────────────────────────────────────────────────────────────

@admin_bp.route("/contacts")
@login_required
@admin_required
def contacts():
    """List all contact messages."""
    filter_type = request.args.get("filter", "all")
    q = Contact.query

    if filter_type == "unread":
        q = q.filter_by(is_read=False)
    elif filter_type == "read":
        q = q.filter_by(is_read=True)

    contacts_list = q.order_by(Contact.created_at.desc()).all()
    unread_count  = Contact.query.filter_by(is_read=False).count()

    return render_template(
        "admin_contacts.html",
        title="Contact Messages – SportsHub",
        contacts=contacts_list,
        unread_count=unread_count,
        current_filter=filter_type,
    )


@admin_bp.route("/contacts/<int:contact_id>/read", methods=["POST"])
@login_required
@admin_required
def contact_mark_read(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.is_read = True
    db.session.commit()
    flash("Message marked as read.", "success")
    return redirect(url_for("admin.contacts"))


@admin_bp.route("/contacts/<int:contact_id>/delete", methods=["POST"])
@login_required
@admin_required
def contact_delete(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("admin.contacts"))


# ── Sales Analytics ───────────────────────────────────────────────────────────

@admin_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    """Detailed sales analytics page."""
    return redirect(url_for("admin.dashboard"))
