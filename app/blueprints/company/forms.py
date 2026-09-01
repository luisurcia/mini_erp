from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange

from app.models.company import Company


class CompanySettingsForm(FlaskForm):
    name = StringField(
        _l("Company name"), validators=[DataRequired(), Length(max=120)]
    )
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
    product_flavor_enabled = BooleanField(
        _l("Ask for a flavor when creating a product")
    )
    product_price_enabled = BooleanField(
        _l("Ask for a unit price when creating a product")
    )
    language = SelectField(
        _l("Language"),
        choices=list(Company.LANGUAGE_LABELS.items()),
        validators=[DataRequired()],
    )
    currency_code = StringField(
        _l("Currency code"),
        validators=[DataRequired(), Length(min=3, max=3)],
        filters=[lambda value: value.upper() if value else value],
        description=_l("ISO code, e.g. CLP, USD, EUR."),
    )
    currency_symbol = StringField(
        _l("Currency symbol"), validators=[DataRequired(), Length(max=8)]
    )
    currency_decimals = IntegerField(
        _l("Decimal places shown for amounts"),
        validators=[InputRequired(), NumberRange(min=0, max=4)],
        description=_l("Chilean pesos (CLP) use 0 — no decimals anywhere in the app."),
    )
    submit = SubmitField(_l("Save settings"))


class CustomerSegmentForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=60)])
    is_active = BooleanField(_l("Active"), default=True)
    submit = SubmitField(_l("Save segment"))
