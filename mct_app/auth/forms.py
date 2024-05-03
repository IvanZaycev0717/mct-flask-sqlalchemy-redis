from flask_wtf import FlaskForm
import phonenumbers
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, Optional

class RegistrationForm(FlaskForm):
    username = StringField(
        'Имя пользователя',
        render_kw={"placeholder": "Придумайте имя пользователя"},
        validators=[DataRequired(message='Требуется ввести имя пользователя')]
        )
    password = PasswordField(
        'Пароль',
        render_kw={"placeholder": "Придумайте пароль"},
        validators=[DataRequired(message='Требуется ввести пароль')]
        )
    email = EmailField(
        'Адрес электронной почты',
        render_kw={"placeholder": "Введите адрес электронной почты"},
        validators=[DataRequired(message='Требуется ввести адрес электронной почты'),
                    Email(message='Неверно введён адрес электронной почты')]
                    )
    phone = StringField(
        'Номер телефона',
        validators=[Optional()]
        )
    submit = SubmitField('Зарегистрироваться')

    def validate_phone(self, phone):
        try:
            p = phonenumbers.parse(phone.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Неправильно введен номер телефона')

class LoginForm(FlaskForm):
    username = StringField(
        'Имя пользователя',
        render_kw={"placeholder": "Введите имя пользователя"},
        validators=[DataRequired(message='Требуется ввести имя пользователя')]
        )
    password = PasswordField(
        'Пароль',
        render_kw={"placeholder": "Введите пароль"},
        validators=[DataRequired(message='Требуется ввести пароль')]
        )
    submit = SubmitField('Войти')
