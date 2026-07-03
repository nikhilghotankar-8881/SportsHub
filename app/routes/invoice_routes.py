"""
app/routes/invoice_routes.py
Download PDF invoice for an order.
"""
from flask import Blueprint, send_file, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import io

from app.models import Order
from app.helpers.invoice_helper import generate_invoice_pdf

invoice_bp = Blueprint("invoice", __name__, url_prefix="/invoice")


@invoice_bp.route("/download/<int:order_id>")
@login_required
def download(order_id):
    """Generate and stream PDF invoice for the given order."""
    order = Order.query.get_or_404(order_id)

    # Security: only the owner or admin can download
    if order.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to download this invoice.", "danger")
        return redirect(url_for("main.index"))

    try:
        pdf_bytes = generate_invoice_pdf(order)
        buffer    = io.BytesIO(pdf_bytes)
        buffer.seek(0)

        filename = f"SportsHub_Invoice_{order.invoice_number}.pdf"
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as exc:
        current_app.logger.error(f"Invoice generation failed for order {order_id}: {exc}")
        flash("Could not generate invoice. Please try again later.", "danger")
        return redirect(url_for("orders.order_detail", order_id=order_id))
