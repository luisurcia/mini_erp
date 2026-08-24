from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class CompanySettingsForm(FlaskForm):
    tax_rate = DecimalField(
        "Tax rate (%)", places=2, validators=[DataRequired(), NumberRange(min=0, max=100)]
    )
    tax_enabled_default = BooleanField("Include tax by default on new sales")
    submit = SubmitField("Save settings")
