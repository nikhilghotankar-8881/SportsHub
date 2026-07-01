from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum


# ── Enums ────────────────────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    SHIPPED    = "shipped"
    DELIVERED  = "delivered"
    CANCELLED  = "cancelled"


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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Product(db.Model):

    __tablename__ = "products"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price       = db.Column(db.Numeric(10, 2), nullable=False)
    stock       = db.Column(db.Integer, nullable=False, default=0)
    image       = db.Column(db.String(300), nullable=True)
    category    = db.Column(db.String(100), nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

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

    def __repr__(self):
        return f"<Product {self.name}>"

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def formatted_price(self):
        return f"₹{self.price:,.2f}"


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
        return self.product.price * self.quantity

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
                           db.String(20),
                           nullable=False,
                           default=OrderStatus.PROCESSING.value,
                       )
    total_amount     = db.Column(db.Numeric(12, 2), nullable=False)
    # Shipping details captured at checkout
    shipping_name    = db.Column(db.String(150), nullable=False)
    shipping_address = db.Column(db.String(300), nullable=False)
    shipping_city    = db.Column(db.String(100), nullable=False)
    shipping_phone   = db.Column(db.String(20),  nullable=False)
    created_at       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user        = db.relationship("User",      back_populates="orders")
    order_items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def formatted_total(self):
        return f"₹{self.total_amount:,.2f}"

    @property
    def status_badge(self):
        """Return (css_class, icon) tuple for the status badge."""
        MAP = {
            "pending":    ("warning",  "bi-clock"),
            "processing": ("info",     "bi-arrow-repeat"),
            "shipped":    ("primary",  "bi-truck"),
            "delivered":  ("success",  "bi-bag-check"),
            "cancelled":  ("danger",   "bi-x-circle"),
        }
        return MAP.get(self.status, ("secondary", "bi-question-circle"))

    def __repr__(self):
        return f"<Order #{self.id} user={self.user_id} status={self.status}>"


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