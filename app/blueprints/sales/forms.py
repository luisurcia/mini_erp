from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, TextAreaField, SubmitField
from wtforms.validators import Length, Optional


class SaleMetaForm(FlaskForm):
    """Holds the sale-level fields; line items are handled as dynamic rows
    in the template/JS and read from request.form directly in the route."""

    customer_id = SelectField(_l("Customer"), coerce=int)
    status = SelectField(_l("Status"))
    invoice_number = StringField(
        _l("Invoice number"), validators=[Optional(), Length(max=40)]
    )
    include_tax = BooleanField(_l("Include tax (IVA)"))
    notes = TextAreaField(_l("Notes"), validators=[Optional()])
    submit = SubmitField(_l("Record sale"))
