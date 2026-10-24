from flask import Blueprint, render_template, abort, request
from app import db
from app.models import Product, Review
from app.forms import ReviewForm
from sqlalchemy import func

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
def products():
    """List all products with dynamic category filter, price filter, search, and sort."""
    category     = request.args.get("category", "").strip()
    search       = request.args.get("q", "").strip()
    sort         = request.args.get("sort", "newest").strip()
    min_price    = request.args.get("min_price", type=float)
    max_price    = request.args.get("max_price", type=float)
    in_stock     = request.args.get("in_stock", type=str)
    page         = request.args.get("page", 1, type=int)

    query = Product.query

    # Category filter
    if category:
        query = query.filter(Product.category.ilike(category))

    # Keyword search
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%"),
            )
        )

    # Price range filters
    if min_price is not None and min_price >= 0:
        query = query.filter(Product.price >= min_price)
    if max_price is not None and max_price > 0:
        query = query.filter(Product.price <= max_price)

    # In stock filter
    if in_stock in ("1", "true", "True", "on"):
        query = query.filter(Product.stock > 0)

    # Sorting
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())
        
    pagination = query.paginate(page=page, per_page=9, error_out=False)
    all_products = pagination.items

    # Dynamically query distinct categories from database
    distinct_categories = [
        c[0] for c in db.session.query(Product.category)
        .filter(Product.category.isnot(None))
        .distinct()
        .all()
        if c[0]
    ]
    all_categories = sorted(distinct_categories) if distinct_categories else [
        "Football", "Cricket", "Basketball", "Badminton", "Running", "Fitness", "Tennis"
    ]

    # Category counts
    cat_counts = dict(
        db.session.query(Product.category, func.count(Product.id))
        .filter(Product.category.isnot(None))
        .group_by(Product.category)
        .all()
    )

    return render_template(
        "products.html",
        title="Shop Sports Gear – SportsHub",
        products=all_products,
        pagination=pagination,
        categories=all_categories,
        cat_counts=cat_counts,
        active_category=category,
        search_query=search,
        current_sort=sort,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock in ("1", "true", "True", "on"),
    )


@products_bp.route("/<int:product_id>")
def product_detail(product_id):
    """Show a single product detail page with reviews and related products."""
    product = Product.query.get_or_404(product_id)

    # Fetch related products in the same category (max 4)
    related = (
        Product.query
        .filter(Product.category == product.category, Product.id != product.id)
        .limit(4)
        .all()
    )
    
    review_form = ReviewForm()
    reviews = product.reviews.order_by(Review.created_at.desc()).all()

    return render_template(
        "product_detail.html",
        title=f"{product.name} – SportsHub",
        product=product,
        related=related,
        review_form=review_form,
        reviews=reviews,
    )
