from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class AddCategoryForm(FlaskForm):
    title = TextAreaField("Название", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Назвать')