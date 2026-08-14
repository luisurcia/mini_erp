from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import Optional


class SaleMetaForm(FlaskForm):
    """Holds the sale-level fields; line items are handled as dynamic rows
    in the template/JS and read from request.form directly in the route."""

    customer_id = SelectField("Customer", coerce=int)
    status = SelectField("Status")
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Record sale")
