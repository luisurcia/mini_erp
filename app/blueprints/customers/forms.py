from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.models.customer_segment import CustomerSegment


class CustomerForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=120)])
    rut = StringField(_l("RUT"), validators=[DataRequired(), Length(max=20)])
    segment_id = SelectField(_l("Segment"), coerce=int, validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[Optional(), Email(), Length(max=120)])
    phone = StringField(_l("Phone"), validators=[Optional(), Length(max=40)])
    shipping_address = TextAreaField(_l("Shipping address"), validators=[Optional()])
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
        self.segment_id.choices = [(segment.id, segment.name) for segment in segments]
