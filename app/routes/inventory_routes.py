"""
app/routes/inventory_routes.py
Placeholder — inventory management is handled inside admin_routes.
This file exists for blueprint registration completeness.
"""
from flask import Blueprint, redirect, url_for
from flask_login import login_required

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("")
@inventory_bp.route("/")
@login_required
def redirect_to_admin_inventory():
    return redirect(url_for("admin.inventory"))

