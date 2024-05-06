from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from mct_app.auth.models import User, UserSession, db, UserRole, Role
from mct_app.auth.forms import RegistrationForm, LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import select, update
from urllib.parse import urlsplit
from flask import abort
from config import Is

auth = Blueprint('auth', __name__)

@auth.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect('/')
    form = RegistrationForm()
    if form.validate_on_submit():

        # Add current user to database
        user = User(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data)
        if form.phone.data:
            user.phone = form.phone.data
        user_role = UserRole()
        user_role.role = db.session.query(Role).filter_by(name='Patient').first()
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()

        _create_user_session(user)
        login_user(user)
        # Success message
        flash('Вы успешно зарегистрировались на сайте')
        return redirect(url_for('auth.profile', username=user.username))
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
        _update_user_session(user)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('auth.profile', username=user.username)
        return redirect(next_page)
    return render_template('forms/login.html', form=form)


@auth.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    if current_user.username != request.view_args['username']:
        role_id = current_user.roles[0].role_id
        if role_id not in (Is.ADMIN, Is.DOCTOR):
            abort(403)
    user = db.first_or_404(select(User).where(User.username==username))
    return render_template('profile/profile.html', user=user)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect('/')

def _create_user_session(user):
    user_sessions = UserSession(
            ip_address=request.remote_addr,
            last_activity=datetime.now(),
            user_id=user.id,
            attendance=1
        )
    db.session.add(user_sessions)
    db.session.commit()

def _update_user_session(user):
    user_session = db.session.scalar(select(UserSession).where(UserSession.user_id==user.id))
    if user_session:
        user_session.ip_address = request.remote_addr
        user_session.last_activity = datetime.now()
        if not user_session.attendance:
            user_session.attendance = 1
        else:
            user_session.attendance += 1
        db.session.commit()