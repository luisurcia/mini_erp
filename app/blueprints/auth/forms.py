from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from app.models.company import Company


class LoginForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    submit = SubmitField(_l("Log in"))


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_l("Current password"), validators=[DataRequired()])
    new_password = PasswordField(
        _l("New password"), validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField(
        _l("Confirm new password"),
        validators=[
            DataRequired(),
            EqualTo("new_password", message=_l("Passwords must match.")),
        ],
    )
    submit = SubmitField(_l("Change password"))


class ChangeLanguageForm(FlaskForm):
    language = SelectField(
        _l("Language"),
        choices=list(Company.LANGUAGE_LABELS.items()),
        validators=[DataRequired()],
    )
    submit = SubmitField(_l("Save"))
