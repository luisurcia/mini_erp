from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional

from app.models.opportunity import Opportunity


class OpportunityForm(FlaskForm):
    customer_id = SelectField(_l("Customer"), coerce=int, validators=[DataRequired()])
    product_id = SelectField(
        _l("Product interested in"), coerce=int, validators=[DataRequired()]
    )
    quantity_requested = IntegerField(
        _l("Quantity requested"), default=1, validators=[DataRequired(), NumberRange(min=1)]
    )
    source = SelectField(
        _l("Source"),
        choices=[
            (Opportunity.SOURCE_INSTAGRAM, _l("Instagram DM")),
            (Opportunity.SOURCE_WEBSITE, _l("Website")),
            (Opportunity.SOURCE_REFERRAL, _l("Referral")),
            (Opportunity.SOURCE_OTHER, _l("Other")),
        ],
    )
    notes = TextAreaField(_l("Notes"), validators=[Optional()])
    submit = SubmitField(_l("Save request"))


class StageForm(FlaskForm):
    stage = SelectField(
        _l("Stage"),
        choices=[
            (Opportunity.STAGE_NEW, _l("New")),
            (Opportunity.STAGE_CONTACTED, _l("Contacted")),
            (Opportunity.STAGE_QUOTED, _l("Quoted")),
            (Opportunity.STAGE_LOST, _l("Lost")),
        ],
    )
    submit = SubmitField(_l("Update stage"))
