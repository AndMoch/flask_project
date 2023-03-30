from flask_wtf import FlaskForm
from wtforms import DateTimeField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class AddBusinessForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    priority = SelectField("Значимость", choices=[(1, 'Наименьшая'), (2, 'Средняя'), (3, 'Наибольшая')])
    start_date = DateTimeField("Дата начала", validators=[DataRequired()])
    end_date = DateTimeField("Дата окончания", validators=[DataRequired()])
    submit = SubmitField()