"""
app/routes/inventory_routes.py
Placeholder — inventory management is handled inside admin_routes.
This file exists for blueprint registration completeness.
"""
from flask import Blueprint

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")
# All inventory routes are under /admin/inventory in admin_routes.py
