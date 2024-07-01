from flask import request
from flask_wtf import FlaskForm
from flask_wtf.form import _Auto
import phonenumbers
from wtforms import StringField, SubmitField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Optional, Length
from flask_login import current_user

from mct_app.utils import is_russian_name_correct
from flask import current_app



class QuestionForm(FlaskForm):
    anon_name = StringField(
        'Ваше имя',
        render_kw={"placeholder": "Введите ваше имя"},
        validators=[])
    body = TextAreaField(
        'Ваш вопрос',
        render_kw={"placeholder": "Введите текст вопроса"},
        validators=[DataRequired(message='Требуется ввести текст вопроса')])
    
    def validate_anon_name(self, anon_name):
        if not current_user.is_authenticated:
            if not self.anon_name.data:
                current_app.logger.error('User dont enter a name')
                raise ValidationError('Требуется ввести имя')
        return True


class AnswerForm(FlaskForm):
    body = TextAreaField(
        'Ваш ответ',
        render_kw={"placeholder": "Введите текст ответа"},
        validators=[DataRequired(message='Требуется ввести текст ответа')])
    submit = SubmitField('Ответить')

class ConsultationForm(FlaskForm):
    first_name = StringField(
        'Ваше имя',
        render_kw={"placeholder": "Введите ваше имя"},
        validators=[
            DataRequired('Необходимо ввести имя'),
            Length(
                min=2, max=25,
                message='Длина имени не может быть меньше 2 и больше 25 символов')])
    last_name = StringField(
        'Ваша фамилия',
        render_kw={"placeholder": "Введите вашу фамилию"},
        validators=[DataRequired('Необходимо ввести фамилию'), Length(
                min=2, max=25,
                message='Длина фамилии не может быть меньше 2 и больше 25 символов')])
    phone = StringField(
        'Номер телефона с WhatsUp/Telegram',
        validators=[DataRequired('Не был введен номер телефона')]
        )

    def validate_first_name(self, first_name):
        if not is_russian_name_correct(first_name.data):
            current_app.logger.error(f'First name is not valid {first_name}')
            raise ValidationError('Недопустимые символы в имени')
        return True

    def validate_last_name(self, last_name):
        if not is_russian_name_correct(last_name.data):
            current_app.logger.error(f'last name is not valid {last_name}')
            raise ValidationError('Недопустимые символы в фамилии')
        return True

    def validate_phone(self, phone):
        try:
            p = phonenumbers.parse(phone.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            current_app.logger.exception(f'Phone number is not valid {phone}')
            raise ValidationError('Неправильно введен номер телефона')
    
class SearchForm(FlaskForm):
    q = StringField('Что вас волнует', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)