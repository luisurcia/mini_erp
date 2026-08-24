from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProductForm(FlaskForm):
    flavor_id = SelectField(_l("Flavor"), coerce=int, validators=[DataRequired()])
    name = StringField(_l("Product name"), validators=[DataRequired()])
    short_name = StringField(
        _l("Short name"), validators=[Optional(), Length(max=3)]
    )
    sku = StringField(_l("SKU"), validators=[DataRequired()])
    size_ml = IntegerField(
        _l("Size (ml)"), default=355, validators=[DataRequired(), NumberRange(min=1)]
    )
    unit_price = DecimalField(
        _l("Unit price"), places=2, validators=[DataRequired(), NumberRange(min=0)]
    )
    initial_qty = IntegerField(
        _l("Initial stock"), default=0, validators=[Optional(), NumberRange(min=0)]
    )
    reorder_level = IntegerField(
        _l("Reorder level"), default=10, validators=[DataRequired(), NumberRange(min=0)]
    )
    is_active = BooleanField(_l("Active"), default=True)
    submit = SubmitField(_l("Save product"))


class RestockForm(FlaskForm):
    quantity = IntegerField(
        _l("Quantity to add"), validators=[DataRequired(), NumberRange(min=1)]
    )
    note = TextAreaField(_l("Note"), validators=[Optional()])
    submit = SubmitField(_l("Restock"))
