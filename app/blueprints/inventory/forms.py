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
from wtforms.validators import DataRequired, NumberRange, Optional


class ProductForm(FlaskForm):
    flavor_id = SelectField("Flavor", coerce=int, validators=[DataRequired()])
    name = StringField("Product name", validators=[DataRequired()])
    sku = StringField("SKU", validators=[DataRequired()])
    size_ml = IntegerField("Size (ml)", default=355, validators=[DataRequired(), NumberRange(min=1)])
    unit_price = DecimalField("Unit price", places=2, validators=[DataRequired(), NumberRange(min=0)])
    initial_qty = IntegerField(
        "Initial stock", default=0, validators=[Optional(), NumberRange(min=0)]
    )
    reorder_level = IntegerField(
        "Reorder level", default=10, validators=[DataRequired(), NumberRange(min=0)]
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save product")


class RestockForm(FlaskForm):
    quantity = IntegerField("Quantity to add", validators=[DataRequired(), NumberRange(min=1)])
    note = TextAreaField("Note", validators=[Optional()])
    submit = SubmitField("Restock")
