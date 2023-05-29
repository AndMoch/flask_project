from flask_wtf import FlaskForm
from wtforms import EmailField, SubmitField
from wtforms.validators import DataRequired, Length


class ResetPasswordForm(FlaskForm):
    email = EmailField('Почта, на которую придёт письмо с ссылкой для сброса', validators=[DataRequired(),
                                                                                           Length(max=74)])
    submit = SubmitField('Отправить')