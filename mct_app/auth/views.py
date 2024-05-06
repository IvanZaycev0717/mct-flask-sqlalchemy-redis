from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from mct_app.auth.models import User, UserSession, db, UserRole, Role
from mct_app.auth.forms import RegistrationForm, LoginForm
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

auth = Blueprint('auth', __name__)

@auth.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect('/')
    form = RegistrationForm()
    if form.validate_on_submit():
        # Add current session of this user
        user_session = UserSession(ip_address=request.remote_addr, last_activity=datetime.now())
        db.session.add(user_session)
        db.session.commit()

        # Add current user to database
        user = User(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data,
            session_id=user_session.id
            )
        if form.phone.data:
            user.phone = form.phone.data
        user_role = UserRole()
        user_role.role = db.session.query(Role).filter_by(name='Patient').first()
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()

        # Success message
        flash('Вы успешно зарегистрировались на сайте')
        return redirect('account')
    return render_template('forms/registration.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.username == form.username.data))
        if user is None:
            flash('Неверное имя пользователя или такого пользователя не существует', 'name-error')
            return redirect('login')
        if not user.verify_password(form.password.data):
            flash('Неверный пароль', 'pass-error')
            return redirect('login')
        login_user(user)
        flash('Вы успешно зашли на сайт')
        return redirect('account')
    return render_template('forms/login.html', form=form)

@auth.route('/account')
def account():
    return render_template('account.html')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect('/')