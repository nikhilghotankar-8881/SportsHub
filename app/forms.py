from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from flask_login import current_user
from app.models import User


class RegisterForm(FlaskForm):

    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )

    submit = SubmitField("Create Account")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is already registered. Please log in.")


class LoginForm(FlaskForm):

    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    remember = BooleanField("Remember Me")

    submit = SubmitField("Sign In")


class EditProfileForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()]
    )

    submit = SubmitField("Save Changes")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("That email is already registered.")

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()]
    )

    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=6)]
    )

    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )

    submit = SubmitField("Update Password")

class PromotionForm(FlaskForm):
    name = StringField('Promotion Name', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    promo_type = SelectField('Type', choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], validators=[DataRequired()])
    discount_value = StringField('Discount Value', validators=[DataRequired()])
    max_discount = StringField('Max Discount (optional)')
    start_date = StringField('Start Date (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    end_date = StringField('End Date (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    usage_limit = StringField('Usage Limit (optional)')
    submit = SubmitField('Save Promotion')

class FlashSaleForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    discount_value = StringField('Discount %', validators=[DataRequired()])
    start_time = StringField('Start Time (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    end_time = StringField('End Time (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    submit = SubmitField('Create Flash Sale')

class ReviewForm(FlaskForm):
    rating = SelectField(
        "Rating",
        choices=[(5, '5 Stars'), (4, '4 Stars'), (3, '3 Stars'), (2, '2 Stars'), (1, '1 Star')],
        coerce=int,
        validators=[DataRequired()]
    )
    review_text = TextAreaField(
        "Review",
        validators=[DataRequired(), Length(min=10, max=1000, message="Review must be between 10 and 1000 characters.")]
    )
    submit = SubmitField("Submit Review")