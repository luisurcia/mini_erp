from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class RestockForm(FlaskForm):
    quantity = IntegerField(
        _l("Quantity to add"), default=0, validators=[Optional(), NumberRange(min=0)]
    )
    reorder_level = IntegerField(
        _l("Reorder level"), default=10, validators=[DataRequired(), NumberRange(min=0)]
    )
    note = TextAreaField(_l("Note"), validators=[Optional()])
    submit = SubmitField(_l("Save"))


class WarehouseForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=80)])
    is_active = BooleanField(_l("Active"), default=True)
    submit = SubmitField(_l("Save warehouse"))
