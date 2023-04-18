import datetime

from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, SubmitField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired

from data.categories import Category
from data import db_session


class AddBusinessForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    priority = SelectField("Значимость", choices=[(1, 'Наименьшая'), (2, 'Средняя'), (3, 'Наибольшая')])
    db_session.global_init("db/todo_list.db")
    db_sess = db_session.create_session()
    categories = [(None, "Без категории")]
    for category in db_sess.query(Category).all():
        tup = category.id, category.title
        categories.append(tup)
    category = SelectField('Категория', choices=categories)
    start_date = DateTimeLocalField("Дата начала", format='%Y-%m-%dT%H:%M', validators=[DataRequired()],
                                    default=datetime.datetime.now())
    end_date = DateTimeLocalField("Дата окончания", format='%Y-%m-%dT%H:%M', validators=[DataRequired()],
                                  default=datetime.datetime.now())
    submit = SubmitField()