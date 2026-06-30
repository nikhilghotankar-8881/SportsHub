from flask import Blueprint, render_template, abort, request
from app.models import Product

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
def products():
    """List all products with optional category filter."""
    category = request.args.get("category", "").strip()
    search   = request.args.get("q", "").strip()
    sort     = request.args.get("sort", "newest").strip()
    page     = request.args.get("page", 1, type=int)

    query = Product.query

    if category:
        query = query.filter(Product.category.ilike(category))

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())
        
    pagination = query.paginate(page=page, per_page=8, error_out=False)
    all_products = pagination.items

    # Define hardcoded category list for filter sidebar
    all_categories = ["Cricket", "Football", "Basketball", "Gym", "Accessories"]

    return render_template(
        "products.html",
        title="Shop – SportsHub",
        products=all_products,
        pagination=pagination,
        categories=all_categories,
        active_category=category,
        search_query=search,
        current_sort=sort,
    )


@products_bp.route("/<int:product_id>")
def product_detail(product_id):
    """Show a single product detail page."""
    product = Product.query.get_or_404(product_id)

    # Fetch related products in the same category (max 4)
    related = (
        Product.query
        .filter(Product.category == product.category, Product.id != product.id)
        .limit(4)
        .all()
    )

    return render_template(
        "product_detail.html",
        title=f"{product.name} – SportsHub",
        product=product,
        related=related,
    )
