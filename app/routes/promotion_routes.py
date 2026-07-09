from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Promotion, PromotionProduct, PromotionCategory, Product
from app.forms import PromotionForm
from datetime import datetime
from decimal import Decimal

promotion_bp = Blueprint('promotion', __name__, url_prefix='/admin/promotions')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@promotion_bp.route('/')
@login_required
@admin_required
def list_promotions():
    promotions = Promotion.query.order_by(Promotion.start_date.desc()).all()
    return render_template('admin_promotions.html', promotions=promotions, title='Manage Promotions – SportsHub')

@promotion_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_promotion():
    form = PromotionForm()
    if form.validate_on_submit():
        try:
            start_dt = datetime.strptime(form.start_date.data, '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(form.end_date.data, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD HH:MM', 'danger')
            return redirect(url_for('promotion.add_promotion'))
        promo = Promotion(
            name=form.name.data,
            description=form.description.data,
            promo_type=form.promo_type.data,
            discount_value=Decimal(form.discount_value.data),
            max_discount=Decimal(form.max_discount.data) if form.max_discount.data else None,
            start_date=start_dt,
            end_date=end_dt,
            usage_limit=int(form.usage_limit.data) if form.usage_limit.data else None,
            is_active=True,
        )
        db.session.add(promo)
        db.session.commit()
        flash('Promotion created successfully.', 'success')
        return redirect(url_for('promotion.list_promotions'))
    return render_template('admin_promotion_form.html', form=form, title='Add Promotion – SportsHub')

@promotion_bp.route('/edit/<int:promo_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    form = PromotionForm(obj=promo)
    if form.validate_on_submit():
        try:
            promo.start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d %H:%M')
            promo.end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('promotion.edit_promotion', promo_id=promo_id))
        promo.name = form.name.data
        promo.description = form.description.data
        promo.promo_type = form.promo_type.data
        promo.discount_value = Decimal(form.discount_value.data)
        promo.max_discount = Decimal(form.max_discount.data) if form.max_discount.data else None
        promo.usage_limit = int(form.usage_limit.data) if form.usage_limit.data else None
        db.session.commit()
        flash('Promotion updated.', 'success')
        return redirect(url_for('promotion.list_promotions'))
    # pre‑fill date fields for display
    form.start_date.data = promo.start_date.strftime('%Y-%m-%d %H:%M')
    form.end_date.data = promo.end_date.strftime('%Y-%m-%d %H:%M')
    return render_template('admin_promotion_form.html', form=form, title='Edit Promotion – SportsHub')

@promotion_bp.route('/delete/<int:promo_id>', methods=['POST'])
@login_required
@admin_required
def delete_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    db.session.delete(promo)
    db.session.commit()
    flash('Promotion deleted.', 'success')
    return redirect(url_for('promotion.list_promotions'))

@promotion_bp.route('/reports')
@login_required
@admin_required
def promotion_reports():
    from sqlalchemy import func
    reports = db.session.query(
        Promotion.name,
        func.count(PromotionProduct.id).label('product_count'),
        func.count(PromotionCategory.id).label('category_count')
    ).outerjoin(PromotionProduct).outerjoin(PromotionCategory).group_by(Promotion.id).all()
    return render_template('admin_promotion_reports.html', reports=reports, title='Promotion Reports – SportsHub')
