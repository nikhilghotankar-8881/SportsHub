"""
app/helpers/email_helper.py
Sends transactional emails via Flask-Mail.
Fails gracefully when SMTP is unavailable.
"""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)


def _send(subject: str, recipients: list, html_body: str) -> bool:
    """Core send function — swallows all SMTP errors so the app never crashes."""
    if not current_app.config.get("MAIL_USERNAME"):
        logger.info("[Email] MAIL_USERNAME not configured — skipping email.")
        return False
    try:
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
        logger.warning(f"[Email] Failed to send '{subject}': {exc}")
        return False


# ── Specific email senders ────────────────────────────────────────────────────

def send_registration_email(user):
    """Welcome email after registration."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">⚡ Welcome to SportsHub!</h1>
      </div>
      <div style="background:#f9f9f9;padding:30px;border-radius:0 0 8px 8px;">
        <h2 style="color:#333;">Hi {user.name}!</h2>
        <p style="color:#555;">Your account has been created successfully. Start exploring our premium sports gear!</p>
        <p style="color:#555;">Email: <strong>{user.email}</strong></p>
        <a href="#" style="background:#667eea;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;display:inline-block;margin-top:16px;">Shop Now</a>
        <p style="color:#999;font-size:12px;margin-top:24px;">© 2025 SportsHub. All rights reserved.</p>
      </div>
    </div>
    """
    return _send(
        subject="Welcome to SportsHub! 🎉",
        recipients=[user.email],
        html_body=html,
    )


def send_order_confirmation_email(user, order):
    """Order confirmation email after successful checkout."""
    items_html = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee;'>{item.product.name}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center;'>{item.quantity}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right;'>₹{item.unit_price:,.2f}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right;'>₹{item.line_total:,.2f}</td></tr>"
        for item in order.order_items
    )
    discount_row = (
        f"<tr><td colspan='3' style='text-align:right;padding:6px;color:green;'>Discount ({order.coupon_code})</td>"
        f"<td style='text-align:right;padding:6px;color:green;'>-₹{order.discount_amount:,.2f}</td></tr>"
        if order.discount_amount and float(order.discount_amount) > 0 else ""
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">Order Confirmed! ✅</h1>
      </div>
      <div style="background:#f9f9f9;padding:30px;border-radius:0 0 8px 8px;">
        <h2>Hi {user.name},</h2>
        <p>Your order <strong>#{order.id}</strong> has been placed successfully.</p>
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr style="background:#667eea;color:white;">
            <th style="padding:10px;text-align:left;">Product</th>
            <th style="padding:10px;text-align:center;">Qty</th>
            <th style="padding:10px;text-align:right;">Price</th>
            <th style="padding:10px;text-align:right;">Total</th>
          </tr></thead>
          <tbody>{items_html}</tbody>
          <tfoot>
            {discount_row}
            <tr><td colspan='3' style='text-align:right;padding:8px;font-weight:bold;'>Total</td>
            <td style='text-align:right;padding:8px;font-weight:bold;'>₹{order.total_amount:,.2f}</td></tr>
          </tfoot>
        </table>
        <p style="color:#555;margin-top:16px;">Shipping to: {order.shipping_name}, {order.shipping_address}, {order.shipping_city}</p>
        <p style="color:#999;font-size:12px;margin-top:24px;">© 2025 SportsHub. All rights reserved.</p>
      </div>
    </div>
    """
    return _send(
        subject=f"SportsHub – Order #{order.id} Confirmed!",
        recipients=[user.email],
        html_body=html,
    )


def send_password_change_email(user):
    """Security notification after password change."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:linear-gradient(135deg,#f093fb,#f5576c);padding:30px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">🔐 Password Changed</h1>
      </div>
      <div style="background:#f9f9f9;padding:30px;border-radius:0 0 8px 8px;">
        <h2>Hi {user.name},</h2>
        <p style="color:#555;">Your password was changed successfully. If you did not make this change, please contact our support immediately.</p>
        <p style="color:#555;">📧 {user.email}</p>
        <p style="color:#999;font-size:12px;margin-top:24px;">© 2025 SportsHub. All rights reserved.</p>
      </div>
    </div>
    """
    return _send(
        subject="SportsHub – Password Changed",
        recipients=[user.email],
        html_body=html,
    )


def send_order_delivered_email(user, order):
    """Notification when order is marked delivered."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:linear-gradient(135deg,#11998e,#38ef7d);padding:30px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">🎉 Order Delivered!</h1>
      </div>
      <div style="background:#f9f9f9;padding:30px;border-radius:0 0 8px 8px;">
        <h2>Hi {user.name},</h2>
        <p style="color:#555;">Great news! Your order <strong>#{order.id}</strong> has been delivered successfully.</p>
        <p style="color:#555;">We hope you love your sports gear! Don't forget to leave a review.</p>
        <p style="color:#999;font-size:12px;margin-top:24px;">© 2025 SportsHub. All rights reserved.</p>
      </div>
    </div>
    """
    return _send(
        subject=f"SportsHub – Order #{order.id} Delivered! 🎉",
        recipients=[user.email],
        html_body=html,
    )


def send_coupon_applied_email(user, order, coupon):
    """Notification when a coupon is applied during checkout."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <div style="background:linear-gradient(135deg,#f7971e,#ffd200);padding:30px;text-align:center;border-radius:8px 8px 0 0;">
        <h1 style="color:white;margin:0;">🏷️ Coupon Applied!</h1>
      </div>
      <div style="background:#f9f9f9;padding:30px;border-radius:0 0 8px 8px;">
        <h2>Hi {user.name},</h2>
        <p style="color:#555;">Your coupon <strong>{coupon.code}</strong> was applied to Order #{order.id}.</p>
        <p style="color:#555;">You saved <strong>₹{order.discount_amount:,.2f}</strong>!</p>
        <p style="color:#999;font-size:12px;margin-top:24px;">© 2025 SportsHub. All rights reserved.</p>
      </div>
    </div>
    """
    return _send(
        subject=f"SportsHub – Coupon Applied & You Saved ₹{order.discount_amount:,.2f}!",
        recipients=[user.email],
        html_body=html,
    )
