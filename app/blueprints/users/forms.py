from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional

from app.models.user import User


class UserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    role = SelectField(
        "Role",
        choices=[(role, role.capitalize()) for role in User.ROLES],
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Password", validators=[Optional(), Length(min=8)]
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Save user")
