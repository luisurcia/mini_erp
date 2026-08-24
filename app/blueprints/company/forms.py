from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from app.models.company import Company


class CompanySettingsForm(FlaskForm):
    tax_rate = DecimalField(
        _l("Tax rate (%)"), places=2, validators=[DataRequired(), NumberRange(min=0, max=100)]
    )
    tax_enabled_default = BooleanField(_l("Include tax by default on new sales"))
    language = SelectField(
        _l("Language"),
        choices=[(Company.LANGUAGE_ES, "Español"), (Company.LANGUAGE_EN, "English")],
        validators=[DataRequired()],
    )
    submit = SubmitField(_l("Save settings"))
