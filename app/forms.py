from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
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