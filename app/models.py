from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal
import enum


# ── Enums ────────────────────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    PLACED          = "placed"
    CONFIRMED       = "confirmed"
    PACKED          = "packed"
    SHIPPED         = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED       = "delivered"
    CANCELLED       = "cancelled"
    # Legacy aliases kept for backward compatibility
    PENDING         = "pending"
    PROCESSING      = "processing"


class CouponType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED      = "fixed"


# ── Models ───────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin      = db.Column(db.Boolean, nullable=False, default=False)
    created_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    cart_items = db.relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    orders = db.relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Order.created_at.desc()",
    )
    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    reviews = db.relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Product(db.Model):

    __tablename__ = "products"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    price        = db.Column(db.Numeric(10, 2), nullable=False)
    stock        = db.Column(db.Integer, nullable=False, default=0)
    image        = db.Column(db.String(300), nullable=True)
    category     = db.Column(db.String(100), nullable=True)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    created_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    cart_items = db.relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    order_items = db.relationship(
        "OrderItem",
        back_populates="product",
        lazy="dynamic",
    )
    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    reviews = db.relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Product {self.name}>"

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock <= 0

    @property
    def formatted_price(self):
        return f"₹{self.price:,.2f}"

    @property
    def average_rating(self):
        avg = db.session.query(db.func.avg(Review.rating)).filter(
            Review.product_id == self.id
        ).scalar()
        return round(float(avg), 1) if avg else 0.0

    @property
    def effective_price(self):
        """Calculate the lowest price after applying active flash sales and promotions."""
        best_price = float(self.price)
        
        # 1. Check Flash Sales
        from datetime import datetime
        flash_sales = FlashSale.query.filter_by(product_id=self.id).all()
        for fs in flash_sales:
            if fs.is_active():
                discounted = float(self.price) - fs.calculate_discount(self.price)
                if discounted < best_price:
                    best_price = discounted

        # 2. Check Product-Specific Promotions
        product_promos = Promotion.query.join(PromotionProduct).filter(
            PromotionProduct.product_id == self.id,
            Promotion.is_active == True,
            Promotion.start_date <= datetime.utcnow(),
            Promotion.end_date >= datetime.utcnow()
        ).all()
        for promo in product_promos:
            if promo.usage_limit is None or promo.used_count < promo.usage_limit:
                discounted = float(self.price) - promo.calculate_discount(self.price)
                if discounted < best_price:
                    best_price = discounted

        # 3. Check Category-Specific Promotions
        if self.category:
            cat_promos = Promotion.query.join(PromotionCategory).filter(
                PromotionCategory.category == self.category,
                Promotion.is_active == True,
                Promotion.start_date <= datetime.utcnow(),
                Promotion.end_date >= datetime.utcnow()
            ).all()
            for promo in cat_promos:
                if promo.usage_limit is None or promo.used_count < promo.usage_limit:
                    discounted = float(self.price) - promo.calculate_discount(self.price)
                    if discounted < best_price:
                        best_price = discounted

        return max(0.0, round(best_price, 2))

    @property
    def formatted_effective_price(self):
        return f"₹{self.effective_price:,.2f}"

    @property
    def total_reviews(self):
        return self.reviews.count()

    @property
    def inventory_value(self):
        return float(self.price) * self.stock


class CartItem(db.Model):

    __tablename__ = "cart_items"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"),    nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False, default=1)

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )

    user    = db.relationship("User",    back_populates="cart_items")
    product = db.relationship("Product", back_populates="cart_items")

    @property
    def subtotal(self):
        return Decimal(str(self.product.effective_price)) * self.quantity

    @property
    def formatted_subtotal(self):
        return f"₹{self.subtotal:,.2f}"

    def __repr__(self):
        return f"<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>"


class Order(db.Model):
    """One order per checkout — snapshot of cart at purchase time."""

    __tablename__ = "orders"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status           = db.Column(
                           db.String(30),
                           nullable=False,
                           default=OrderStatus.PLACED.value,
                       )
    total_amount     = db.Column(db.Numeric(12, 2), nullable=False)
    discount_amount  = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    coupon_code      = db.Column(db.String(50), nullable=True)
    gst_amount       = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    # Shipping details captured at checkout
    shipping_name    = db.Column(db.String(150), nullable=False)
    shipping_address = db.Column(db.String(300), nullable=False)
    shipping_city    = db.Column(db.String(100), nullable=False)
    shipping_phone   = db.Column(db.String(20),  nullable=False)
    created_at       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)

    # Relationships
    user        = db.relationship("User",      back_populates="orders")
    order_items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="select",
    )
    status_history = db.relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="OrderStatusHistory.changed_at.asc()",
    )

    @property
    def subtotal_amount(self):
        return sum(item.line_total for item in self.order_items)

    @property
    def formatted_total(self):
        return f"₹{self.total_amount:,.2f}"

    @property
    def formatted_discount(self):
        return f"₹{self.discount_amount:,.2f}"

    @property
    def invoice_number(self):
        return f"SH-INV-{self.id:06d}"

    @property
    def status_badge(self):
        """Return (css_class, icon) tuple for the status badge."""
        MAP = {
            "placed":           ("secondary", "bi-clock-history"),
            "confirmed":        ("info",      "bi-check-circle"),
            "packed":           ("warning",   "bi-box-seam"),
            "shipped":          ("primary",   "bi-truck"),
            "out_for_delivery": ("warning",   "bi-bicycle"),
            "delivered":        ("success",   "bi-bag-check"),
            "cancelled":        ("danger",    "bi-x-circle"),
            # Legacy
            "pending":          ("warning",   "bi-clock"),
            "processing":       ("info",      "bi-arrow-repeat"),
        }
        return MAP.get(self.status, ("secondary", "bi-question-circle"))

    @property
    def status_label(self):
        labels = {
            "placed":           "Placed",
            "confirmed":        "Confirmed",
            "packed":           "Packed",
            "shipped":          "Shipped",
            "out_for_delivery": "Out for Delivery",
            "delivered":        "Delivered",
            "cancelled":        "Cancelled",
            "pending":          "Pending",
            "processing":       "Processing",
        }
        return labels.get(self.status, self.status.title())

    def __repr__(self):
        return f"<Order #{self.id} user={self.user_id} status={self.status}>"


class OrderStatusHistory(db.Model):
    """Tracks each status change for order tracking timeline."""

    __tablename__ = "order_status_history"

    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    status     = db.Column(db.String(30), nullable=False)
    note       = db.Column(db.String(300), nullable=True)
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    order = db.relationship("Order", back_populates="status_history")

    @property
    def status_label(self):
        labels = {
            "placed":           "Order Placed",
            "confirmed":        "Order Confirmed",
            "packed":           "Order Packed",
            "shipped":          "Shipped",
            "out_for_delivery": "Out for Delivery",
            "delivered":        "Delivered",
            "cancelled":        "Cancelled",
            "pending":          "Pending",
            "processing":       "Processing",
        }
        return labels.get(self.status, self.status.title())

    def __repr__(self):
        return f"<OrderStatusHistory order={self.order_id} status={self.status}>"


class OrderItem(db.Model):
    """One row per product line in an Order — price is frozen at order time."""

    __tablename__ = "order_items"

    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey("orders.id"),   nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)   # price snapshot

    # Relationships
    order   = db.relationship("Order",   back_populates="order_items")
    product = db.relationship("Product", back_populates="order_items")

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def formatted_line_total(self):
        return f"₹{self.line_total:,.2f}"

    @property
    def formatted_unit_price(self):
        return f"₹{self.unit_price:,.2f}"

    def __repr__(self):
        return f"<OrderItem order={self.order_id} product={self.product_id} qty={self.quantity}>"


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"),    nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )

    user    = db.relationship("User",    back_populates="wishlist_items")
    product = db.relationship("Product", back_populates="wishlist_items")

    def __repr__(self):
        return f"<Wishlist user={self.user_id} product={self.product_id}>"


class Review(db.Model):
    __tablename__ = "reviews"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id  = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    rating      = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
    )

    user    = db.relationship("User",    back_populates="reviews")
    product = db.relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review user={self.user_id} product={self.product_id} rating={self.rating}>"


# ── Phase 13 Models ──────────────────────────────────────────────────────────

class Coupon(db.Model):
    """Discount coupon model supporting percentage and fixed discounts."""
    
    __tablename__ = "coupons"
    
    id                = db.Column(db.Integer, primary_key=True)
    code              = db.Column(db.String(50), unique=True, nullable=False)
    description       = db.Column(db.String(200), nullable=True)
    coupon_type       = db.Column(db.String(20), nullable=False, default=CouponType.PERCENTAGE.value)
    discount_value    = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_purchase  = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    max_discount      = db.Column(db.Numeric(10, 2), nullable=True)   # cap for percentage coupons
    usage_limit       = db.Column(db.Integer, nullable=True)          # None = unlimited
    used_count        = db.Column(db.Integer, nullable=False, default=0)
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    expires_at        = db.Column(db.DateTime, nullable=True)
    created_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def is_valid(self, cart_total):
        """Check if coupon is valid for the given cart total."""
        from datetime import datetime as dt
        if not self.is_active:
            return False, "This coupon is inactive."
        if self.expires_at and self.expires_at < dt.utcnow():
            return False, "This coupon has expired."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "This coupon usage limit has been reached."
        if Decimal(str(cart_total)) < Decimal(str(self.minimum_purchase)):
            return False, f"Minimum purchase of ₹{self.minimum_purchase:,.2f} required."
        return True, "Valid"

    def calculate_discount(self, cart_total):
        """Calculate discount amount for given cart total."""
        cart_total_dec = Decimal(str(cart_total))
        if self.coupon_type == CouponType.PERCENTAGE.value:
            discount = cart_total_dec * Decimal(str(self.discount_value)) / Decimal("100")
            if self.max_discount:
                discount = min(discount, Decimal(str(self.max_discount)))
        else:
            discount = min(Decimal(str(self.discount_value)), cart_total_dec)
        return discount.quantize(Decimal("0.01"))

    @property
    def is_expired(self):
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return False

    @property
    def type_label(self):
        return "Percentage" if self.coupon_type == CouponType.PERCENTAGE.value else "Fixed Amount"

    @property
    def discount_display(self):
        if self.coupon_type == CouponType.PERCENTAGE.value:
            return f"{self.discount_value}%"
        return f"₹{self.discount_value:,.2f}"

    def __repr__(self):
        return f"<Coupon {self.code} {self.discount_display}>"

# ── Phase 14 Models ──────────────────────────────────────────────────────────

class Promotion(db.Model):
    """Promotion model representing a discount campaign that can apply to
    specific products, categories, or the entire cart. Supports percentage
    or fixed amount discounts with start/end dates and usage limits."""

    __tablename__ = "promotions"

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(150), nullable=False)
    description       = db.Column(db.Text, nullable=True)
    promo_type        = db.Column(db.String(20), nullable=False)  # "percentage" or "fixed"
    discount_value    = db.Column(db.Numeric(10, 2), nullable=False)
    max_discount      = db.Column(db.Numeric(10, 2), nullable=True)  # for percentage type
    start_date        = db.Column(db.DateTime, nullable=False)
    end_date          = db.Column(db.DateTime, nullable=False)
    usage_limit       = db.Column(db.Integer, nullable=True)  # None = unlimited
    used_count        = db.Column(db.Integer, nullable=False, default=0)
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    created_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # relationships for specific targets
    products   = db.relationship('PromotionProduct', back_populates='promotion', cascade='all, delete-orphan', lazy='dynamic')
    categories = db.relationship('PromotionCategory', back_populates='promotion', cascade='all, delete-orphan', lazy='dynamic')

    def is_current(self):
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date

    def is_valid(self, cart_total):
        if not self.is_current():
            return False, "Promotion is not active."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "Promotion usage limit reached."
        return True, "Valid"

    def calculate_discount(self, applicable_total):
        if self.promo_type == 'percentage':
            discount = float(applicable_total) * float(self.discount_value) / 100
            if self.max_discount:
                discount = min(discount, float(self.max_discount))
        else:
            discount = min(float(self.discount_value), float(applicable_total))
        return round(discount, 2)

    def __repr__(self):
        return f"<Promotion {self.name} {self.promo_type} {self.discount_value}>"

class PromotionProduct(db.Model):
    """Association table linking a promotion to specific products."""
    __tablename__ = "promotion_products"
    id          = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    product_id   = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    promotion = db.relationship('Promotion', back_populates='products')
    product   = db.relationship('Product')

    __table_args__ = (db.UniqueConstraint('promotion_id', 'product_id', name='uq_promo_product'),)

    def __repr__(self):
        return f"<PromotionProduct promo={self.promotion_id} product={self.product_id}>"

class PromotionCategory(db.Model):
    """Association table linking a promotion to product categories."""
    __tablename__ = "promotion_categories"
    id          = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    category    = db.Column(db.String(100), nullable=False)

    promotion = db.relationship('Promotion', back_populates='categories')

    __table_args__ = (db.UniqueConstraint('promotion_id', 'category', name='uq_promo_category'),)

    def __repr__(self):
        return f"<PromotionCategory promo={self.promotion_id} category={self.category}>"

class FlashSale(db.Model):
    """Flash sale model for limited‑time, high‑discount offers on specific products."""
    __tablename__ = "flash_sales"

    id          = db.Column(db.Integer, primary_key=True)
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)  # percentage discount for flash sale
    start_time  = db.Column(db.DateTime, nullable=False)
    end_time    = db.Column(db.DateTime, nullable=False)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    product = db.relationship('Product')

    def is_active(self):
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time

    def calculate_discount(self, price):
        discount = float(price) * float(self.discount_value) / 100
        return round(discount, 2)

    def __repr__(self):
        return f"<FlashSale product={self.product_id} {self.discount_value}%>"


class Contact(db.Model):
    """Customer contact / support message."""

    __tablename__ = "contacts"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    subject    = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Contact {self.email} '{self.subject}'>"