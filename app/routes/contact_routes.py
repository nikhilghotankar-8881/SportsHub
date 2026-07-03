"""
app/routes/contact_routes.py
Public contact form submission and admin message management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Contact

contact_bp = Blueprint("contact", __name__, url_prefix="/contact")


@contact_bp.route("/", methods=["GET", "POST"])
def contact():
    """Contact Us page with form."""
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        errors = []
        if not name:    errors.append("Name is required.")
        if not email:   errors.append("Email is required.")
        if not subject: errors.append("Subject is required.")
        if not message: errors.append("Message is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "contact.html",
                title="Contact Us – SportsHub",
                form_data=request.form,
            )

        contact_msg = Contact(
            name=name, email=email, subject=subject, message=message
        )
        db.session.add(contact_msg)
        db.session.commit()

        flash("Thank you! Your message has been sent. We'll get back to you shortly.", "success")
        return redirect(url_for("contact.contact"))

    return render_template(
        "contact.html",
        title="Contact Us – SportsHub",
        form_data={},
    )
