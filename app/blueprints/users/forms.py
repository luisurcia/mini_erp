from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional

from app.models.user import User

ROLE_LABELS = {
    User.ROLE_ADMIN: _l("Admin"),
    User.ROLE_EDITOR: _l("Editor"),
    User.ROLE_VIEWER: _l("Viewer"),
}


class UserForm(FlaskForm):
    username = StringField(
        _l("Username"), validators=[DataRequired(), Length(min=3, max=80)]
    )
    role = SelectField(
        _l("Role"),
        choices=[(role, ROLE_LABELS[role]) for role in User.ROLES],
        validators=[DataRequired()],
    )
    password = PasswordField(
        _l("Password"), validators=[Optional(), Length(min=8)]
    )
    confirm_password = PasswordField(
        _l("Confirm password"),
        validators=[EqualTo("password", message=_l("Passwords must match."))],
    )
    submit = SubmitField(_l("Save user"))
