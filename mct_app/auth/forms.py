from flask import current_app, request
from flask_wtf import FlaskForm
import phonenumbers
from sqlalchemy import select
from wtforms import (
    EmailField, PasswordField,
    SelectField, StringField,
    SubmitField, TextAreaField)
from wtforms.validators import (
    DataRequired,
    Email, EqualTo, Length,
    Optional, ValidationError)

from config import Mood
from mct_app import db
from mct_app.auth.models import User


class RegistrationForm(FlaskForm):
    """Class for registration on current site."""

    username = StringField(
        'Имя пользователя',
        render_kw={'placeholder': 'Придумайте имя пользователя'},
        validators=[DataRequired(message='Требуется ввести имя пользователя')])
    password = PasswordField(
        'Пароль',
        render_kw={'placeholder': 'Придумайте пароль'},
        validators=[DataRequired(message='Требуется ввести пароль')])
    email = EmailField(
        'Адрес электронной почты',
        render_kw={'placeholder': 'Введите адрес электронной почты'},
        validators=[
            DataRequired(message='Требуется ввести адрес электронной почты'),
            Email(message='Неверно введён адрес электронной почты')])
    phone = StringField(
        'Номер телефона',
        validators=[Optional()])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        """Validate username data.

        Username doesn't have unallowed symbols
        and that this username is unique.
        """
        if '(' in request.form['username'] or ')' in request.form['username']:
            raise ValidationError('Символы "(" или ")" недоупстимы')
        user = db.session.scalar(
            select(User).where(User.username == username.data))
        if user is not None:
            current_app.logger.warn(
                f'User does exist with name {username.data}')
            raise ValidationError('Пользователь с таким именем уже существует')

    def validate_email(self, email):
        """Validate whether email is unique."""
        user = db.session.scalar(select(User).where(User.email == email.data))
        if user is not None:
            current_app.logger.warn(f'Email does exist {email.data}')
            raise ValidationError(
                'Такой адрес электронной почты уже существует')

    def validate_phone(self, phone):
        """Validate whether phone is correct."""
        try:
            p = phonenumbers.parse(phone.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            current_app.logger.warn(f'Phone does exist {phone.data}')
            raise ValidationError('Неправильно введен номер телефона')


class LoginForm(FlaskForm):
    """Class for login user."""

    username = StringField(
        'Имя пользователя',
        render_kw={'placeholder': 'Введите имя пользователя'},
        validators=[DataRequired(message='Требуется ввести имя пользователя')])
    password = PasswordField(
        'Пароль',
        render_kw={'placeholder': 'Введите пароль'},
        validators=[DataRequired(message='Требуется ввести пароль')])
    submit = SubmitField('Войти')


class RequestResetPasswordForm(FlaskForm):
    """Class of reset password form before sending reset email."""

    email = EmailField(
        'Адрес электронной почты',
        validators=[
            DataRequired(message='Требуется ввести адрес электронной почты'),
            Email(message='Неверно введён адрес электронной почты')])
    submit = SubmitField('Отправить письмо со сбросом пароля')


class ResetPasswordForm(FlaskForm):
    """Class of reset password form after sending reset email."""

    email = EmailField(
        'Адрес электронной почты',
        validators=[
            DataRequired(message='Требуется ввести адрес электронной почты'),
            Email(message='Неверно введён адрес электронной почты')])
    new_password = PasswordField(
        'Новый пароль',
        validators=[
            DataRequired(),
            EqualTo('repeat_password', 'Пароли должен совпадать')])
    repeat_password = PasswordField(
        'Повторите пароль',
        validators=[DataRequired()])
    submit = SubmitField('Сбросить пароль')

    def validate_email(self, email):
        """Validate whether entered email exists."""
        if User.query.filter_by(email=email.data).first() is None:
            current_app.logger.warn(f'Email doesnt exist {email.data}')
            raise ValidationError(
                'Такого адреса электронной почты не существует')


class NewDiaryForm(FlaskForm):
    """Class for form of new note in the patient diary."""

    mood = SelectField(
        'Выберите настроение:',
        choices=[mood.value for mood in Mood])
    record = TextAreaField(
        'Запись в дневник',
        render_kw={'placeholder': 'Введите текст записи дневника'},
        validators=[
            DataRequired(message='Требуется ввести текст записи дневника'),
            Length(
                min=3,
                max=2000,
                message='Запись не должна быть меньше 3 символов и больше'
                        '2000 символов')])
    submit = SubmitField('Опубликовать')


class RecommendationForm(FlaskForm):
    """Class for from of recommendation by a doctor."""

    record = TextAreaField(
        'Дать рекомендацию',
        render_kw={'placeholder': 'Введите текст рекомендации'},
        validators=[DataRequired(
            message='Требуется ввести текст рекомендации'),
            Length(min=3, max=2000,
                   message='Запись не должна быть меньше 3 символов'
                           'и больше 2000 символов')])
    submit = SubmitField('дать рекомендацию')
