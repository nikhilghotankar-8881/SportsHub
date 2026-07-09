from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import FlashSale, Product
from app.forms import FlashSaleForm
from datetime import datetime
from decimal import Decimal

flashsale_bp = Blueprint('flashsale', __name__, url_prefix='/admin/flashsales')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@flashsale_bp.route('/')
@login_required
@admin_required
def list_flashsales():
    flashsales = FlashSale.query.order_by(FlashSale.start_time.desc()).all()
    return render_template('admin_flashsales.html', flashsales=flashsales, title='Manage Flash Sales – SportsHub')

@flashsale_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_flashsale():
    form = FlashSaleForm()
    # Populate product choices
    form.product_id.choices = [(p.id, p.name) for p in Product.query.order_by(Product.name).all()]
    if form.validate_on_submit():
        try:
            start_dt = datetime.strptime(form.start_time.data, '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(form.end_time.data, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date/time format. Use YYYY-MM-DD HH:MM', 'danger')
            return redirect(url_for('flashsale.add_flashsale'))
        flashsale = FlashSale(
            product_id=form.product_id.data,
            discount_value=Decimal(form.discount_value.data),
            start_time=start_dt,
            end_time=end_dt,
        )
        db.session.add(flashsale)
        db.session.commit()
        flash('Flash sale created successfully.', 'success')
        return redirect(url_for('flashsale.list_flashsales'))
    return render_template('admin_flashsale_form.html', form=form, title='Add Flash Sale – SportsHub')

@flashsale_bp.route('/edit/<int:fs_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_flashsale(fs_id):
    flashsale = FlashSale.query.get_or_404(fs_id)
    form = FlashSaleForm(obj=flashsale)
    form.product_id.choices = [(p.id, p.name) for p in Product.query.order_by(Product.name).all()]
    if form.validate_on_submit():
        try:
            flashsale.start_time = datetime.strptime(form.start_time.data, '%Y-%m-%d %H:%M')
            flashsale.end_time = datetime.strptime(form.end_time.data, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date/time format.', 'danger')
            return redirect(url_for('flashsale.edit_flashsale', fs_id=fs_id))
        flashsale.product_id = form.product_id.data
        flashsale.discount_value = Decimal(form.discount_value.data)
        db.session.commit()
        flash('Flash sale updated.', 'success')
        return redirect(url_for('flashsale.list_flashsales'))
    # pre-fill dates
    form.start_time.data = flashsale.start_time.strftime('%Y-%m-%d %H:%M')
    form.end_time.data = flashsale.end_time.strftime('%Y-%m-%d %H:%M')
    return render_template('admin_flashsale_form.html', form=form, title='Edit Flash Sale – SportsHub')

@flashsale_bp.route('/delete/<int:fs_id>', methods=['POST'])
@login_required
@admin_required
def delete_flashsale(fs_id):
    flashsale = FlashSale.query.get_or_404(fs_id)
    db.session.delete(flashsale)
    db.session.commit()
    flash('Flash sale deleted.', 'success')
    return redirect(url_for('flashsale.list_flashsales'))
