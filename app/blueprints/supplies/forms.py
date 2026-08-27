from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class SupplyForm(FlaskForm):
    """The supply master (catalog) only — stock lives per warehouse,
    managed from the stock/restock screens, not here."""

    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=120)])
    unit = StringField(_l("Unit"), validators=[DataRequired(), Length(max=40)])
    unit_price = DecimalField(
        _l("Unit price"), places=2, validators=[DataRequired(), NumberRange(min=0)]
    )
    is_active = BooleanField(_l("Active"), default=True)
    submit = SubmitField(_l("Save supply"))
