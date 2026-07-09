import datetime
from decimal import Decimal
from app.models import Promotion, PromotionProduct, PromotionCategory, FlashSale, Product
from app import db

def get_active_flash_sale(product_id):
    """Return active flash sale for given product if any."""
    now = datetime.datetime.utcnow()
    flash = FlashSale.query.filter(
        FlashSale.product_id == product_id,
        FlashSale.start_time <= now,
        FlashSale.end_time >= now
    ).first()
    return flash

def get_applicable_promotions(cart_items):
    """Return list of active promotions applicable to the cart.
    Each promotion is represented as a tuple (promotion, applicable_total).
    """
    now = datetime.datetime.utcnow()
    promotions = Promotion.query.filter(
        Promotion.is_active == True,
        Promotion.start_date <= now,
        Promotion.end_date >= now
    ).all()
    results = []
    for promo in promotions:
        # Determine which items the promotion applies to
        product_ids = [pp.product_id for pp in promo.products]
        categories = [pc.category for pc in promo.categories]
        applicable_total = Decimal('0')
        for item in cart_items:
            if product_ids and item.product_id in product_ids:
                applicable_total += item.subtotal
            elif categories and item.product.category in categories:
                applicable_total += item.subtotal
            elif not product_ids and not categories:
                # Promotion applies to whole cart
                applicable_total += item.subtotal
        if applicable_total > 0:
            results.append((promo, applicable_total))
    return results

def calculate_best_promotion_discount(cart_items):
    """Calculate the best promotion discount for the cart.
    Returns (discount_amount, promotion) where promotion may be None.
    """
    applicable = get_applicable_promotions(cart_items)
    best_discount = Decimal('0')
    best_promo = None
    for promo, total in applicable:
        discount = Decimal(promo.calculate_discount(total))
        if discount > best_discount:
            best_discount = discount
            best_promo = promo
    return best_discount, best_promo

def calculate_flash_sale_discount(cart_items):
    """Calculate total flash sale discount for cart items.
    Returns total discount amount.
    """
    total = Decimal('0')
    for item in cart_items:
        flash = get_active_flash_sale(item.product_id)
        if flash:
            discount = Decimal(flash.calculate_discount(item.product.price)) * item.quantity
            total += discount
    return total

def calculate_cart_discount(cart_items, coupon=None):
    """Calculate total discount for cart, considering flash sales, promotions, and optional coupon.
    Returns tuple (total_discount, description) where description is a string summary.
    """
    subtotal = sum(item.subtotal for item in cart_items)
    # Flash sale discount first
    flash_discount = calculate_flash_sale_discount(cart_items)
    subtotal_after_flash = subtotal - float(flash_discount)
    # Promotion discount on remaining subtotal
    promo_discount, promo = calculate_best_promotion_discount(cart_items)
    subtotal_after_promo = subtotal_after_flash - float(promo_discount)
    # Coupon discount on remaining subtotal
    coupon_discount = Decimal('0')
    if coupon:
        valid, _ = coupon.is_valid(subtotal_after_promo)
        if valid:
            coupon_discount = Decimal(coupon.calculate_discount(subtotal_after_promo))
    total_discount = flash_discount + promo_discount + coupon_discount
    parts = []
    if flash_discount:
        parts.append(f"Flash Sale: ₹{flash_discount:.2f}")
    if promo_discount:
        parts.append(f"Promotion ({promo.name}): ₹{promo_discount:.2f}")
    if coupon_discount:
        parts.append(f"Coupon ({coupon.code}): ₹{coupon_discount:.2f}")
    description = ", ".join(parts) if parts else "No discounts"
    return Decimal(total_discount), description
