from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app, jsonify
from flask_login import login_required, current_user
from app import csrf
import razorpay
from decimal import Decimal
from app import db
from app.models import Order, Payment, PaymentStatus, OrderStatus

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


def get_razorpay_client():
    key_id = current_app.config.get("RAZORPAY_KEY_ID")
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET")
    return razorpay.Client(auth=(key_id, key_secret))

@payment_bp.route("/verify", methods=["POST"])
@csrf.exempt
@login_required
def verify_payment():
    razorpay_payment_id = request.form.get("razorpay_payment_id")
    razorpay_order_id = request.form.get("razorpay_order_id")
    razorpay_signature = request.form.get("razorpay_signature")

    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        flash("Invalid payment details returned from Razorpay.", "danger")
        return redirect(url_for("cart.cart"))

    # Find the corresponding Order and Payment
    payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id, payment_status=PaymentStatus.PENDING.value).first()
    if not payment:
        flash("Order not found or payment already processed.", "danger")
        return redirect(url_for("cart.cart"))
    
    order = payment.order
    
    # Verify the signature
    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        payment.payment_status = PaymentStatus.FAILED.value
        db.session.commit()
        flash("Payment verification failed. The signature could not be verified.", "danger")
        return redirect(url_for("payment.payment_failed", order_id=order.id))

    # Signature is valid. Update payment and order
    payment.payment_status = PaymentStatus.PAID.value
    payment.razorpay_payment_id = razorpay_payment_id
    payment.payment_signature = razorpay_signature
    payment.payment_method = "Razorpay"
    
    order.status = OrderStatus.PLACED.value
    
    # Reduce stock for all items
    for item in order.order_items:
        product = item.product
        if product.stock >= item.quantity:
            product.stock -= item.quantity
        else:
            # Handle edge case where stock ran out during payment
            product.stock = 0

    # Clear user's cart
    for cart_item in current_user.cart_items:
        db.session.delete(cart_item)

    # Increase coupon usage if applicable
    if order.coupon_code:
        from app.models import Coupon
        coupon = Coupon.query.filter_by(code=order.coupon_code).first()
        if coupon:
            coupon.used_count += 1

    db.session.commit()

    # Clear coupon session data
    from flask import session
    session.pop("coupon_code", None)
    session.pop("coupon_discount", None)

    # Send confirmation email (graceful fallback)
    try:
        from app.helpers.email_helper import send_order_confirmation_email, send_payment_success_email
        send_order_confirmation_email(order.user, order)
        send_payment_success_email(order.user, order, payment)
    except Exception:
        pass

    flash("Payment successful! Your order has been placed.", "success")
    return redirect(url_for("checkout.order_confirmation", order_id=order.id))


@payment_bp.route("/failed/<int:order_id>")
@login_required
def payment_failed(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("main.index"))
    
    return render_template("payment_failed.html", order=order)
