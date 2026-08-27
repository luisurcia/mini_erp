from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


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


class TransferForm(FlaskForm):
    product_id = SelectField(_l("Product"), coerce=int, validators=[DataRequired()])
    from_warehouse_id = SelectField(_l("From warehouse"), coerce=int, validators=[DataRequired()])
    to_warehouse_id = SelectField(_l("To warehouse"), coerce=int, validators=[DataRequired()])
    quantity = IntegerField(_l("Quantity"), validators=[DataRequired(), NumberRange(min=1)])
    note = TextAreaField(_l("Note"), validators=[Optional()])
    submit = SubmitField(_l("Transfer"))

    def validate_to_warehouse_id(self, field):
        if self.from_warehouse_id.data == field.data:
            raise ValidationError(_l("Source and destination warehouse must be different."))
