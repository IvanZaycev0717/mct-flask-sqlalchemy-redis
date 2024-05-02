from flask import Blueprint, render_template, session, redirect, url_for, flash
from mct_app.auth.models import User, db
from mct_app.auth.forms import RegistrationForm, LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash('Вы успешно зарегистрировались на сайте')
        print('Успешно')
        return redirect('account')
    if form.errors:
        print(form.username.errors)
        flash('Вы НЕ зарегистрировались на сайте')
    return render_template('forms/registration.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Вы успешно зашли на сайт')
        return redirect('account')
    return render_template('forms/login.html', form=form)

@auth.route('/account')
def account():
    return render_template('account.html')