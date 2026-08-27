from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

from app.models.company import Company


class CompanySettingsForm(FlaskForm):
    tax_rate = DecimalField(
        _l("Tax rate (%)"), places=2, validators=[DataRequired(), NumberRange(min=0, max=100)]
    )
    tax_enabled_default = BooleanField(_l("Include tax by default on new sales"))
    product_short_name_enabled = BooleanField(
        _l("Ask for a short name when creating a product")
    )
    product_size_enabled = BooleanField(
        _l("Ask for size (ml) when creating a product")
    )
    product_sku_enabled = BooleanField(
        _l("Ask for a SKU when creating a product")
    )
    language = SelectField(
        _l("Language"),
        choices=[(Company.LANGUAGE_ES, "Español"), (Company.LANGUAGE_EN, "English")],
        validators=[DataRequired()],
    )
    submit = SubmitField(_l("Save settings"))


class CustomerSegmentForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=60)])
    is_active = BooleanField(_l("Active"), default=True)
    submit = SubmitField(_l("Save segment"))
