from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Product, Review
from app.forms import ReviewForm

reviews_bp = Blueprint("reviews", __name__)

@reviews_bp.route("/product/<int:product_id>/review", methods=["POST"])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    
    # Check if user already reviewed
    existing_review = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_review:
        flash("You have already reviewed this product.", "warning")
        return redirect(url_for("products.product_detail", product_id=product.id))
        
    if form.validate_on_submit():
        review = Review(
            user_id=current_user.id,
            product_id=product.id,
            rating=form.rating.data,
            review_text=form.review_text.data
        )
        db.session.add(review)
        db.session.commit()
        flash("Your review has been submitted successfully!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", "danger")
                
    return redirect(url_for("products.product_detail", product_id=product.id))

@reviews_bp.route("/review/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id:
        flash("You can only edit your own reviews.", "danger")
        return redirect(url_for("products.product_detail", product_id=review.product_id))
        
    form = ReviewForm()
    if form.validate_on_submit():
        review.rating = form.rating.data
        review.review_text = form.review_text.data
        db.session.commit()
        flash("Your review has been updated.", "success")
        
        # Check where the user came from (my-reviews or product page)
        next_page = request.args.get("next")
        if next_page == "my_reviews":
            return redirect(url_for("reviews.my_reviews"))
        return redirect(url_for("products.product_detail", product_id=review.product_id))
        
    elif request.method == "GET":
        form.rating.data = review.rating
        form.review_text.data = review.review_text
        
    return render_template("edit_review.html", title="Edit Review", form=form, product=review.product)

@reviews_bp.route("/review/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to delete this review.", "danger")
        return redirect(url_for("products.product_detail", product_id=review.product_id))
        
    product_id = review.product_id
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted successfully.", "success")
    
    next_page = request.args.get("next")
    if next_page == "my_reviews":
        return redirect(url_for("reviews.my_reviews"))
    elif next_page == "admin":
        return redirect(url_for("admin.reviews"))
        
    return redirect(url_for("products.product_detail", product_id=product_id))

@reviews_bp.route("/my-reviews")
@login_required
def my_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    return render_template("my_reviews.html", title="My Reviews", reviews=reviews)
