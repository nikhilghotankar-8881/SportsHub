"""
app/routes/static_pages_routes.py
Static informational pages: FAQ and About Us.
"""
from flask import Blueprint, render_template

static_pages_bp = Blueprint("pages", __name__, url_prefix="/pages")


@static_pages_bp.route("/faq")
def faq():
    """FAQ page with Bootstrap accordion."""
    return render_template("faq.html", title="FAQ – SportsHub")


@static_pages_bp.route("/about")
def about():
    """About Us page with hero, mission, team, stats, and CTA."""
    return render_template("about.html", title="About Us – SportsHub")
