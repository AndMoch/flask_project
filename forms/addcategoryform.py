from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class AddCategoryForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    submit = SubmitField('Назвать')