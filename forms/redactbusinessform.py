from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length


class RedactBusinessForm(FlaskForm):
    title = TextAreaField("Описание", validators=[DataRequired(), Length(max=255)])
    priority = SelectField("Значимость", choices=[(1, 'Наименьшая'), (2, 'Средняя'), (3, 'Наибольшая')])
    category = SelectField('Категория')
    end_date = DateTimeLocalField("Дата окончания", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Изменить')