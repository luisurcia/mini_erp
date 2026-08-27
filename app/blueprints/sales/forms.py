from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class SaleMetaForm(FlaskForm):
    """Holds the sale-level fields; line items are handled as dynamic rows
    in the template/JS and read from request.form directly in the route.

    No `status` field: a sale recorded here already happened, so it's
    always created as completed — never exposed as an input. No `notes`
    field either — it doesn't add value to Scoby's process, though the
    column stays on the model for compatibility.
    """

    customer_id = SelectField(_l("Customer"), coerce=int)
    sale_date = DateField(
        _l("Sale date"), validators=[DataRequired()], render_kw={"type": "date"}
    )
    include_tax = BooleanField(_l("Include tax (IVA)"))
    invoice_number = StringField(
        _l("Invoice number"), validators=[Optional(), Length(max=40)]
    )
    submit = SubmitField(_l("Record sale"))
