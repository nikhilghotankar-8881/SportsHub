"""
seed_db.py
Database initialization and seeding script for SportsHub.
Used for local development and cloud PostgreSQL deployments (Neon / Supabase / Render / Vercel).
Run with: python seed_db.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Ensure app can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app import create_app, db
from app.models import User, Product, Coupon, Promotion, FlashSale, Review, CouponType

app = create_app()

def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed():
    with app.app_context():
        print("🔧 Creating database tables if they do not exist...")
        db.create_all()

        # ── 1. Seed Users ────────────────────────────────────────────────────────
        print("👤 Checking default users...")
        admin = User.query.filter_by(email="admin@sportshub.com").first()
        if not admin:
            admin = User(
                name="SportsHub Admin",
                email="admin@sportshub.com",
                is_admin=True,
            )
            admin.set_password("Admin@12345")
            db.session.add(admin)
            print("   ✅ Created admin: admin@sportshub.com / Admin@12345")
        else:
            print("   ℹ️ Admin account already exists.")

        demo_user = User.query.filter_by(email="athlete@sportshub.com").first()
        if not demo_user:
            demo_user = User(
                name="Alex Johnson",
                email="athlete@sportshub.com",
                is_admin=False,
            )
            demo_user.set_password("User@12345")
            db.session.add(demo_user)
            print("   ✅ Created demo user: athlete@sportshub.com / User@12345")

        db.session.commit()

        # ── 2. Seed Products ─────────────────────────────────────────────────────
        print("📦 Checking products...")
        sample_products = [
            {
                "name": "FIFA Pro Match Football (Size 5)",
                "category": "Football",
                "price": Decimal("1499.00"),
                "stock": 35,
                "low_stock_threshold": 5,
                "image": "https://images.unsplash.com/photo-1575361204480-aadea25e6e68?w=800&q=80",
                "description": "FIFA Quality Pro certified match ball. Thermal bonding technology ensures a seamless surface for a more predictable trajectory, better touch, and minimal water uptake.",
            },
            {
                "name": "Nike Mercurial Vapor Elite Cleats",
                "category": "Football",
                "price": Decimal("6499.00"),
                "stock": 14,
                "low_stock_threshold": 4,
                "image": "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=800&q=80",
                "description": "Engineered for speed, featuring a 3/4-length Zoom Air unit underfoot and grippy Vaporposite+ upper for exceptional touch at high speeds.",
            },
            {
                "name": "SS Vintage Kashmir Willow Cricket Bat",
                "category": "Cricket",
                "price": Decimal("3899.00"),
                "stock": 20,
                "low_stock_threshold": 4,
                "image": "https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=800&q=80",
                "description": "Handcrafted premium grade Kashmir Willow with huge edges and balanced pickup. Comes with full padded protective bat cover.",
            },
            {
                "name": "Kookaburra Turf White Leather Cricket Ball",
                "category": "Cricket",
                "price": Decimal("899.00"),
                "stock": 60,
                "low_stock_threshold": 10,
                "image": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800&q=80",
                "description": "Four-piece construction using first-grade alum tanned steakhide leather. Specially formulated finish for optimal seam visibility and swing.",
            },
            {
                "name": "Spalding NBA Official Composite Basketball",
                "category": "Basketball",
                "price": Decimal("2499.00"),
                "stock": 28,
                "low_stock_threshold": 5,
                "image": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800&q=80",
                "description": "Designed for indoor and outdoor play. Premium composite leather cover provides superior grip and moisture management.",
            },
            {
                "name": "Yonex Nanoray 10F Badminton Racket",
                "category": "Badminton",
                "price": Decimal("2199.00"),
                "stock": 18,
                "low_stock_threshold": 3,
                "image": "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=800&q=80",
                "description": "Lightweight head-light racket with TFA CAP technology for rapid swing speed and quick repulsion. Ideal for fast-paced doubles rallies.",
            },
            {
                "name": "Yonex Mavis 350 Nylon Shuttlecocks (Pack of 6)",
                "category": "Badminton",
                "price": Decimal("649.00"),
                "stock": 80,
                "low_stock_threshold": 15,
                "image": "https://images.unsplash.com/photo-1613918108466-292b78a8ef95?w=800&q=80",
                "description": "The gold standard of nylon shuttles. Engineered for precision flight trajectory and lasting durability across all court conditions.",
            },
            {
                "name": "Ultra-Responsive Carbon Running Shoes X5",
                "category": "Running",
                "price": Decimal("7999.00"),
                "stock": 12,
                "low_stock_threshold": 3,
                "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80",
                "description": "Full-length carbon fiber propulsion plate with responsive dual-density foam midsole. Reduces fatigue on marathons and daily tempo runs.",
            },
            {
                "name": "Hydration Running Vest & Water Flasks",
                "category": "Running",
                "price": Decimal("1899.00"),
                "stock": 25,
                "low_stock_threshold": 5,
                "image": "https://images.unsplash.com/photo-1594882645126-14020914d58d?w=800&q=80",
                "description": "Ultralight breathable mesh running vest with two 500ml BPA-free soft flasks, zippered smartphone pocket, and reflective safety bands.",
            },
            {
                "name": "Hex Rubber Dumbbells Set (2x 10kg)",
                "category": "Fitness",
                "price": Decimal("3299.00"),
                "stock": 16,
                "low_stock_threshold": 4,
                "image": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800&q=80",
                "description": "Heavy-duty cast iron heads encased in virgin rubber to protect flooring and minimize noise. Ergonomic chrome knurled steel handle.",
            },
            {
                "name": "High-Density Eco Yoga & Exercise Mat (6mm)",
                "category": "Fitness",
                "price": Decimal("999.00"),
                "stock": 45,
                "low_stock_threshold": 8,
                "image": "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=800&q=80",
                "description": "Non-slip textured TPE yoga mat with alignment guides. Excellent joint cushioning, moisture-resistant, and easy to clean.",
            },
            {
                "name": "Wilson Pro Staff Precision Tennis Racket",
                "category": "Tennis",
                "price": Decimal("5499.00"),
                "stock": 11,
                "low_stock_threshold": 3,
                "image": "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?w=800&q=80",
                "description": "Graphite composite frame delivering pinpoint precision and feel. Midplus head size offers an ideal balance of power and control.",
            },
        ]

        for p_data in sample_products:
            existing = Product.query.filter_by(name=p_data["name"]).first()
            if not existing:
                prod = Product(**p_data)
                db.session.add(prod)
                print(f"   ✅ Added product: {p_data['name']}")

        db.session.commit()

        # ── 3. Seed Coupons ──────────────────────────────────────────────────────
        print("🎟️ Checking coupons...")
        sample_coupons = [
            {
                "code": "WELCOME10",
                "description": "10% off on your first order",
                "coupon_type": CouponType.PERCENTAGE.value,
                "discount_value": Decimal("10.00"),
                "minimum_purchase": Decimal("499.00"),
                "max_discount": Decimal("500.00"),
                "usage_limit": None,
                "is_active": True,
                "expires_at": _utc_now() + timedelta(days=90),
            },
            {
                "code": "SPORT500",
                "description": "Flat ₹500 off on orders above ₹2,500",
                "coupon_type": CouponType.FIXED.value,
                "discount_value": Decimal("500.00"),
                "minimum_purchase": Decimal("2500.00"),
                "max_discount": None,
                "usage_limit": 500,
                "is_active": True,
                "expires_at": _utc_now() + timedelta(days=60),
            },
            {
                "code": "FITNESS20",
                "description": "20% off on gym & fitness equipment",
                "coupon_type": CouponType.PERCENTAGE.value,
                "discount_value": Decimal("20.00"),
                "minimum_purchase": Decimal("999.00"),
                "max_discount": Decimal("1000.00"),
                "usage_limit": 200,
                "is_active": True,
                "expires_at": _utc_now() + timedelta(days=45),
            },
        ]

        for c_data in sample_coupons:
            existing = Coupon.query.filter_by(code=c_data["code"]).first()
            if not existing:
                coupon = Coupon(**c_data)
                db.session.add(coupon)
                print(f"   ✅ Added coupon: {c_data['code']}")

        db.session.commit()

        # ── 4. Seed Active Flash Sale ─────────────────────────────────────────────
        print("⚡ Checking flash sales...")
        active_fs = FlashSale.query.filter(
            FlashSale.end_time >= _utc_now()
        ).first()
        if not active_fs:
            first_product = Product.query.first()
            if first_product:
                fs = FlashSale(
                    product_id=first_product.id,
                    discount_value=Decimal("25.00"),
                    start_time=_utc_now() - timedelta(hours=2),
                    end_time=_utc_now() + timedelta(hours=36),
                )
                db.session.add(fs)
                print(f"   ✅ Created active 25% Flash Sale on '{first_product.name}' (ends in 36h)")

        db.session.commit()

        # ── 5. Seed Reviews ──────────────────────────────────────────────────────
        print("⭐ Checking customer reviews...")
        if Review.query.count() == 0 and demo_user:
            products = Product.query.limit(4).all()
            reviews_data = [
                (products[0].id, 5, "Outstanding build quality! The grip and bounce are top-tier. Worth every rupee."),
                (products[1].id, 5, "Super lightweight and blazing fast on the field. Fits true to size."),
                (products[2].id, 4, "Excellent willow punch and balance. Knocked it in and played two league games — superb!"),
            ]
            for pid, rating, text in reviews_data:
                rev = Review(
                    user_id=demo_user.id,
                    product_id=pid,
                    rating=rating,
                    review_text=text,
                    created_at=_utc_now() - timedelta(days=2),
                )
                db.session.add(rev)
                print(f"   ✅ Added sample review for product ID {pid}")

            db.session.commit()

        print("\n✨ Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
