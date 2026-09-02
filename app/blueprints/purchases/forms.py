from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class PurchaseForm(FlaskForm):
    """One plant-overhead expense. The correlative is assigned by the
    service, not entered here. See #93."""

    purchase_date = DateField(
        _l("Date"), validators=[DataRequired()], render_kw={"type": "date"}
    )
    item = StringField(_l("Item"), validators=[DataRequired(), Length(max=200)])
    supplier = StringField(_l("Supplier"), validators=[DataRequired(), Length(max=160)])
    category = StringField(_l("Category"), validators=[Optional(), Length(max=80)])
    invoice_number = StringField(
        _l("Invoice number"), validators=[Optional(), Length(max=60)]
    )
    amount = DecimalField(
        _l("Amount"), places=2, validators=[DataRequired(), NumberRange(min=0)]
    )
    includes_tax = BooleanField(_l("Amount includes tax (IVA)"))
    notes = StringField(_l("Notes"), validators=[Optional(), Length(max=255)])
    submit = SubmitField(_l("Save purchase"))


class VoidPurchaseForm(FlaskForm):
    """CSRF wrapper for the void / restore buttons."""

    submit = SubmitField(_l("Void"))
