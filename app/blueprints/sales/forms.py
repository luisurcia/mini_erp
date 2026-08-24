from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, TextAreaField, SubmitField
from wtforms.validators import Length, Optional


class SaleMetaForm(FlaskForm):
    """Holds the sale-level fields; line items are handled as dynamic rows
    in the template/JS and read from request.form directly in the route."""

    customer_id = SelectField("Customer", coerce=int)
    status = SelectField("Status")
    invoice_number = StringField(
        "Invoice number", validators=[Optional(), Length(max=40)]
    )
    include_tax = BooleanField("Include tax (IVA)")
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Record sale")
