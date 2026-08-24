from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class CustomerForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=120)])
    email = StringField(_l("Email"), validators=[Optional(), Email(), Length(max=120)])
    phone = StringField(_l("Phone"), validators=[Optional(), Length(max=40)])
    instagram_handle = StringField(
        _l("Instagram handle"), validators=[Optional(), Length(max=80)]
    )
    notes = TextAreaField(_l("Notes"), validators=[Optional()])
    submit = SubmitField(_l("Save customer"))
