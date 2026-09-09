from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.forms import optional_int
from app.models.purchase_category import PurchaseCategory


class PurchaseForm(FlaskForm):
    """One plant-overhead expense. The correlative is assigned by the
    service, not entered here. See #93."""

    purchase_date = DateField(
        _l("Date"), validators=[DataRequired()], render_kw={"type": "date"}
    )
    item = StringField(_l("Item"), validators=[DataRequired(), Length(max=200)])
    supplier = StringField(_l("Supplier"), validators=[DataRequired(), Length(max=160)])
    # Optional (#110): a purchase left uncategorized is saved against the
    # "No definido" category by the service, not blocked.
    category_id = SelectField(
        _l("Category"), coerce=optional_int, validators=[Optional()]
    )
    invoice_number = StringField(
        _l("Invoice number"), validators=[Optional(), Length(max=60)]
    )
    amount = DecimalField(
        _l("Amount"), places=2, validators=[DataRequired(), NumberRange(min=0)]
    )
    includes_tax = BooleanField(_l("Amount includes tax (IVA)"))
    notes = StringField(_l("Notes"), validators=[Optional(), Length(max=255)])
    submit = SubmitField(_l("Save purchase"))

    def __init__(self, *args, purchase=None, **kwargs):
        super().__init__(*args, **kwargs)
        categories = list(
            PurchaseCategory.query.filter_by(is_active=True)
            .order_by(PurchaseCategory.name)
            .all()
        )
        # "No definido" always sits first and is the default choice.
        categories.sort(key=lambda c: (not c.is_fallback, c.name))
        # Keep an editing purchase's current category selectable even if
        # it's since been deactivated (mirrors CustomerForm).
        if purchase is not None and purchase.category is not None:
            if not any(c.id == purchase.category_id for c in categories):
                categories.append(purchase.category)
        self.category_id.choices = [(c.id, c.name) for c in categories]


class VoidPurchaseForm(FlaskForm):
    """CSRF wrapper for the void / restore buttons."""

    submit = SubmitField(_l("Void"))
