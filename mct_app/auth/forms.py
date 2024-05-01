from flask_wtf import FlaskForm
import phonenumbers
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    email = EmailField('Адрес электронной почты', validators=[Email()])
    phone = StringField('Номер телефона', validators=[DataRequired()])
    submit = SubmitField('Войти')

    def validate_phone(self, phone):
        try:
            p = phonenumbers.parse(phone.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Неправильно введен номер телефона')
