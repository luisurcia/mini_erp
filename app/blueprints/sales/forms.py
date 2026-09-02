from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class PaymentForm(FlaskForm):
    """Records that a sale has been paid: a transfer/reference number
    (required — the client wants proof of payment attached) and the date
    it was received. See #51."""

    payment_reference = StringField(
        _l("Transfer / reference number"),
        validators=[DataRequired(), Length(max=80)],
    )
    paid_at = DateField(
        _l("Payment date"), validators=[DataRequired()], render_kw={"type": "date"}
    )
    submit = SubmitField(_l("Register payment"))


class RevertPaymentForm(FlaskForm):
    """Bare form so the admin-only 'revert payment' button is CSRF-protected."""

    submit = SubmitField(_l("Revert payment"))


class SaleMetaForm(FlaskForm):
    """Holds the sale-level fields; line items are handled as dynamic rows
    in the template/JS and read from request.form directly in the route.

    No `status` field: a sale recorded here already happened, so it's
    always created as completed — never exposed as an input. No `notes`
    field either — it's not part of the sale-entry flow, though the
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
