from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.models.customer_segment import CustomerSegment


def _optional_int(value):
    """Coerce a select value to int, or None for the empty placeholder
    option — so DataRequired fires when no segment is chosen (#77)."""
    return int(value) if value not in ("", None) else None


class CustomerForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=120)])
    nickname = StringField(_l("Nickname"), validators=[Optional(), Length(max=80)])
    # Only Name + Segment are required to create a customer (#74). RUT is
    # optional: not every customer is invoiced (a boleta needs no RUT) and it
    # can be filled in later.
    rut = StringField(_l("RUT"), validators=[Optional(), Length(max=20)])
    segment_id = SelectField(
        _l("Segment"), coerce=_optional_int, validators=[DataRequired()]
    )
    email = StringField(_l("Email"), validators=[Optional(), Email(), Length(max=120)])
    phone = StringField(_l("Phone"), validators=[Optional(), Length(max=40)])
    shipping_street = StringField(_l("Street"), validators=[Optional(), Length(max=120)])
    shipping_number = StringField(_l("Number"), validators=[Optional(), Length(max=20)])
    shipping_city = StringField(_l("City"), validators=[Optional(), Length(max=80)])
    shipping_commune = StringField(_l("Commune"), validators=[Optional(), Length(max=80)])
    shipping_region = StringField(_l("Region"), validators=[Optional(), Length(max=80)])
    instagram_handle = StringField(
        _l("Instagram handle"), validators=[Optional(), Length(max=80)]
    )
    notes = TextAreaField(_l("Notes"), validators=[Optional()])
    submit = SubmitField(_l("Save customer"))

    def __init__(self, *args, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        segments = list(
            CustomerSegment.query.filter_by(is_active=True).order_by(CustomerSegment.id).all()
        )
        # Keep the customer's current segment selectable even if it's since
        # been deactivated, so editing them doesn't silently reassign it.
        if customer is not None and customer.segment is not None:
            if not any(segment.id == customer.segment_id for segment in segments):
                segments.append(customer.segment)
        self.segment_id.choices = [("", _l("— Select a segment —"))] + [
            (segment.id, segment.name) for segment in segments
        ]
