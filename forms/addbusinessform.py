import datetime

from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class AddBusinessForm(FlaskForm):
    title = StringField("Описание", validators=[DataRequired()])
    priority = SelectField("Значимость", choices=[(1, 'Наименьшая'), (2, 'Средняя'), (3, 'Наибольшая')])
    category = SelectField('Категория')
    start_date = DateTimeLocalField("Дата начала", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeLocalField("Дата окончания", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Добавить')