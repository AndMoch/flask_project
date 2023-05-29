from flask_wtf import FlaskForm
from wtforms import RadioField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class SettingsForm(FlaskForm):
    usage_variants = RadioField("Типы взаимодействия", coerce=int,
                                 validators=[DataRequired()])
    email_checkbox = BooleanField("Включить уведомления по электронной почте")
    submit = SubmitField('Применить')