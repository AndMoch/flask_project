from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class SetNewPasswordForm(FlaskForm):
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8, max=20)])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired(), Length(min=8, max=20)])
    submit = SubmitField('Отправить')