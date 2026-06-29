"""
End-to-end flow test:
  Register -> Login -> Products -> Add to Cart -> Cart

Runs against the real SQLite database using Flask's test client.
CSRF is disabled for the test session via WTF_CSRF_ENABLED=False.
"""
import uuid
from app import create_app, db
from app.models import User, Product, CartItem

# ── Create app with CSRF disabled for testing ────────────────────────────────
app = create_app()
app.config["WTF_CSRF_ENABLED"] = False

SEP = "─" * 52


def run():
    with app.test_client() as client:
        with app.app_context():

            # ════════════════════════════════════════════════
            # STEP 1 — REGISTER
            # ════════════════════════════════════════════════
            email = f"flow_{uuid.uuid4().hex[:8]}@test.com"
            pwd   = "securepass99"

            r = client.post("/auth/register", data={
                "name":             "Flow Tester",
                "email":            email,
                "password":         pwd,
                "confirm_password": pwd,
            }, follow_redirects=False)

            assert r.status_code == 302, \
                f"REGISTER failed — expected 302, got {r.status_code}"
            print(f"[1] REGISTER   ✓   {email}")

            # ════════════════════════════════════════════════
            # STEP 2 — LOGIN
            # ════════════════════════════════════════════════
            r = client.post("/auth/login", data={
                "email":    email,
                "password": pwd,
                "remember": False,
            }, follow_redirects=False)

            assert r.status_code == 302, \
                f"LOGIN failed — expected 302, got {r.status_code}"
            print(f"[2] LOGIN      ✓   redirected to {r.headers.get('Location')}")

            # ════════════════════════════════════════════════
            # STEP 3 — OPEN PRODUCTS PAGE
            # ════════════════════════════════════════════════
            r = client.get("/products/")
            assert r.status_code == 200, \
                f"PRODUCTS failed — expected 200, got {r.status_code}"

            html = r.data.decode()
            product_count = Product.query.count()
            assert product_count > 0, "No products in DB — seed them first"
            print(f"[3] PRODUCTS   ✓   HTTP 200  ({product_count} products in DB)")

            # ════════════════════════════════════════════════
            # STEP 4 — ADD PRODUCT TO CART
            # ════════════════════════════════════════════════
            product = Product.query.filter(Product.stock > 0).first()
            assert product, "No in-stock product found"

            r = client.post(
                f"/cart/add/{product.id}",
                data={"quantity": "2"},
                follow_redirects=False,
            )
            assert r.status_code == 302, \
                f"ADD TO CART failed — expected 302, got {r.status_code}"
            print(f'[4] ADD CART   ✓   "{product.name}" x2  @ {product.formatted_price}')

            # ════════════════════════════════════════════════
            # STEP 5 — OPEN CART
            # ════════════════════════════════════════════════
            r = client.get("/cart/")
            assert r.status_code == 200, \
                f"CART PAGE failed — expected 200, got {r.status_code}"

            html = r.data.decode()
            assert product.name in html, \
                f"'{product.name}' not found in cart page HTML"
            print(f"[5] CART       ✓   HTTP 200  product visible in table")

            # ════════════════════════════════════════════════
            # DB VERIFICATION
            # ════════════════════════════════════════════════
            user       = User.query.filter_by(email=email).first()
            cart_items = CartItem.query.filter_by(user_id=user.id).all()

            print()
            print(SEP)
            print("  DB Verification")
            print(SEP)
            print(f"  User       : {user.name} <{user.email}>")
            print(f"  Cart rows  : {len(cart_items)}")
            for ci in cart_items:
                print(f"  └─ {ci.product.name:<30} x{ci.quantity}  {ci.formatted_subtotal}")
            print(SEP)

            # ════════════════════════════════════════════════
            # CLEANUP — remove test user + cart items
            # ════════════════════════════════════════════════
            for ci in cart_items:
                db.session.delete(ci)
            db.session.delete(user)
            db.session.commit()
            print("  Cleanup    : test user & cart items removed")
            print()
            print("  ALL 5 STEPS PASSED ✓")
            print(SEP)


if __name__ == "__main__":
    run()
