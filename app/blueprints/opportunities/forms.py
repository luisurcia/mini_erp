from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional

from app.models.opportunity import Opportunity


class OpportunityForm(FlaskForm):
    customer_id = SelectField("Customer", coerce=int, validators=[DataRequired()])
    product_id = SelectField("Product interested in", coerce=int, validators=[DataRequired()])
    quantity_requested = IntegerField(
        "Quantity requested", default=1, validators=[DataRequired(), NumberRange(min=1)]
    )
    source = SelectField(
        "Source",
        choices=[
            (Opportunity.SOURCE_INSTAGRAM, "Instagram DM"),
            (Opportunity.SOURCE_WEBSITE, "Website"),
            (Opportunity.SOURCE_REFERRAL, "Referral"),
            (Opportunity.SOURCE_OTHER, "Other"),
        ],
    )
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save request")


class StageForm(FlaskForm):
    stage = SelectField(
        "Stage",
        choices=[
            (Opportunity.STAGE_NEW, "New"),
            (Opportunity.STAGE_CONTACTED, "Contacted"),
            (Opportunity.STAGE_QUOTED, "Quoted"),
            (Opportunity.STAGE_LOST, "Lost"),
        ],
    )
    submit = SubmitField("Update stage")
