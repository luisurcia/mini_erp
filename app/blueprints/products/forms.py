from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp


class ProductForm(FlaskForm):
    """The product master (catalog) only — stock lives in Inventory, per
    warehouse, not here. See #26."""

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
    # Required (#126): every product carries a colour, used in the
    # Dashboard charts and on the physical label. Native colour picker.
    color = StringField(
        _l("Color"),
        default="#9a968c",
        validators=[
            DataRequired(),
            Regexp(r"^#[0-9A-Fa-f]{6}$", message=_l("Enter a colour like #E0762E.")),
        ],
        render_kw={"type": "color"},
    )
    is_active = BooleanField(_l("Active"), default=True)
    submit = SubmitField(_l("Save product"))
