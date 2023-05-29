from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length


class RegisterForm(FlaskForm):
    login = StringField("Логин", validators=[DataRequired(), Length(min=4, max=25)])
    email = EmailField("Почта", validators=[DataRequired(), Length(max=74)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8, max=20)])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired(), Length(min=8, max=20)])
    submit = SubmitField('Зарегистрироваться')