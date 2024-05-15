from collections.abc import Sequence
from typing import Any, Mapping
from flask_wtf import FlaskForm
import phonenumbers
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, Optional, EqualTo
from mct_app import db
from mct_app.auth.models import User
from sqlalchemy import select
from flask import request

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

    def validate_username(self, username):
        if '(' in request.form['username'] or ')' in request.form['username']:
            raise ValidationError('Символы "(" или ")" недоупстимы')
        user = db.session.scalar(select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Пользователь с таким именем уже существует')
    
    def validate_email(self, email):
        user = db.session.scalar(select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Такой адрес электронной почты уже существует')
    

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

class RequestResetPasswordForm(FlaskForm):
    email = EmailField('Адрес электронной почты', validators=[DataRequired(message='Требуется ввести адрес электронной почты'), Email(message='Неверно введён адрес электронной почты')])
    submit = SubmitField('Отправить письмо со сбросом пароля')

class ResetPasswordForm(FlaskForm):
    email = EmailField('Адрес электронной почты', validators=[DataRequired(message='Требуется ввести адрес электронной почты'), Email(message='Неверно введён адрес электронной почты')])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), EqualTo('repeat_password', 'Пароли должен совпадать')])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Сбросить пароль')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first() is None:
            raise ValidationError('Такого адреса электронной почты не существует')
