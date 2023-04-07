import datetime

from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class AddBusinessForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    priority = SelectField("Значимость", choices=[(1, 'Наименьшая'), (2, 'Средняя'), (3, 'Наибольшая')])
    start_date = DateTimeLocalField("Дата начала", format='%Y-%m-%dT%H:%M', validators=[DataRequired()],
                                    default=datetime.datetime.now())
    end_date = DateTimeLocalField("Дата окончания", format='%Y-%m-%dT%H:%M', validators=[DataRequired()],
                                  default=datetime.datetime.now())
    submit = SubmitField()