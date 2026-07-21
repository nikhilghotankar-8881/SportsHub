"""
app/helpers/email_helper.py
Sends transactional emails via Flask-Mail using Jinja2 templates.
Fails gracefully when SMTP is unavailable.
"""
from flask import current_app, render_template
from flask_mail import Message
from app import mail
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def _send(subject: str, recipients: list, template_name: str, **context) -> bool:
    """Core send function — swallows all SMTP errors so the app never crashes."""
    if not current_app.config.get("MAIL_USERNAME"):
        logger.warning(f"[Email] MAIL_USERNAME not configured — skipping email '{subject}'.")
        return False
    try:
        html_body = render_template(f"emails/{template_name}", subject=subject, **context)
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
        )
        mail.send(msg)
        logger.info(f"[Email] Sent '{subject}' to {recipients}")
        return True
    except Exception as exc:
        logger.error(f"[Email] Failed to send '{subject}': {exc}")
        return False

# ── Specific email senders ────────────────────────────────────────────────────

def send_registration_email(user):
    """Welcome email after registration."""
    return _send(
        subject="Welcome to SportsHub! 🎉",
        recipients=[user.email],
        template_name="registration.html",
        user=user,
        header_text="Welcome Aboard"
    )

def send_password_change_email(user):
    """Security notification after password change."""
    return _send(
        subject="Security Alert: Password Changed",
        recipients=[user.email],
        template_name="password_changed.html",
        user=user,
        time_changed=datetime.now().strftime("%B %d, %Y %I:%M %p"),
        header_text="Security Notification"
    )

def send_order_confirmation_email(user, order):
    """Order confirmation email after successful Razorpay checkout."""
    return _send(
        subject=f"SportsHub – Order #{order.id} Confirmed! ✅",
        recipients=[user.email],
        template_name="order_confirmation.html",
        user=user,
        order=order,
        header_text="Order Confirmation"
    )

def send_cod_order_email(user, order):
    """Order confirmation email after successful COD checkout."""
    return _send(
        subject=f"SportsHub – Cash on Delivery Order #{order.id} Placed",
        recipients=[user.email],
        template_name="cod_order_confirmation.html",
        user=user,
        order=order,
        header_text="COD Order Received"
    )

def send_payment_success_email(user, order, payment):
    """Notification for successful Razorpay payment verification."""
    return _send(
        subject=f"SportsHub – Payment Successful for Order #{order.id}",
        recipients=[user.email],
        template_name="payment_success.html",
        user=user,
        order=order,
        payment=payment,
        header_text="Payment Success"
    )

def send_order_status_email(user, order, new_status):
    """Generic status update email (e.g. Placed, Confirmed, Packed)."""
    return _send(
        subject=f"SportsHub – Order #{order.id} Status: {new_status}",
        recipients=[user.email],
        template_name="order_status_update.html",
        user=user,
        order=order,
        new_status=new_status,
        header_text="Order Status Update"
    )

def send_order_shipped_email(user, order):
    """Notification when order is shipped."""
    return _send(
        subject=f"SportsHub – Order #{order.id} Shipped! 🚚",
        recipients=[user.email],
        template_name="order_shipped.html",
        user=user,
        order=order,
        header_text="Order Shipped"
    )

def send_order_delivered_email(user, order):
    """Notification when order is marked delivered."""
    return _send(
        subject=f"SportsHub – Order #{order.id} Delivered! 🎉",
        recipients=[user.email],
        template_name="order_delivered.html",
        user=user,
        order=order,
        header_text="Order Delivered"
    )

def send_order_cancelled_email(user, order):
    """Notification when order is cancelled."""
    return _send(
        subject=f"SportsHub – Order #{order.id} Cancelled",
        recipients=[user.email],
        template_name="order_cancelled.html",
        user=user,
        order=order,
        header_text="Order Cancelled"
    )

def send_contact_confirmation_email(contact_msg):
    """Confirmation email to user after submitting Contact Us form."""
    return _send(
        subject="SportsHub – We received your message",
        recipients=[contact_msg.email],
        template_name="contact_confirmation.html",
        contact=contact_msg,
        header_text="Message Received"
    )
