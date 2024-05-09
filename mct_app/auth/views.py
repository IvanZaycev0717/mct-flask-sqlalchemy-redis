import os
from datetime import datetime
from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
import requests
from mct_app.auth.models import User, UserSession, db, UserRole, Role, SocialAccount
from mct_app.auth.forms import RegistrationForm, LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import select, update
from urllib.parse import urlsplit
from flask import abort
from config import Is
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from config import basedir


auth = Blueprint('auth', __name__)

SOCIAL_AUTH_VK_OAUTH2_KEY = '51920174'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'cqUJVoTNym6Os5pQWfDJ'
SOCIAL_AUTH_VK_REDIRECT = 'https://localhost/vk-callback'


GOOGLE_CLIENT_ID = '904059633989-0hasb3m586f1u6u0tcnumm249itt9a4k.apps.googleusercontent.com'

client_secrets_file = os.path.join(basedir, 'client_secret.json')

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://localhost/callback"
)


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


@auth.route("/google-login")
def google_login():
    authorization_url, state = flow.authorization_url()
    return redirect(authorization_url)

@auth.route('/vk-login')
def vk_login():
    return redirect(fr'https://oauth.vk.com/authorize?client_id={SOCIAL_AUTH_VK_OAUTH2_KEY}&redirect_uri={SOCIAL_AUTH_VK_REDIRECT}&response_type=code')

@auth.route('/vk-callback')
def vk_callback():
    code = request.args.get('code')
    # Запрос на обмен кода авторизации на токен доступа
    response = requests.get('https://oauth.vk.com/access_token', params={
        'client_id': SOCIAL_AUTH_VK_OAUTH2_KEY,
        'client_secret': SOCIAL_AUTH_VK_OAUTH2_SECRET,
        'redirect_uri': SOCIAL_AUTH_VK_REDIRECT,
        'code': code
    })

    if response.status_code == 200:
        data = response.json()
        access_token = data['access_token']
        user_id = data['user_id']

        # Запрос на получение информации о пользователе
        user_info_response = requests.get('https://api.vk.com/method/users.get', params={
            'access_token': access_token,
            'user_ids': user_id,
            'v': '5.131'  # Версия API
        })

        if user_info_response.status_code == 200:
            # Обработка информации о пользователе
            user_info = user_info_response.json()['response'][0]
            user_data = {
                'id': user_info['id'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
            }

            # Возвращаем информацию о пользователе в формате JSON
            print(user_data)
            return jsonify(user_data)
        else:
            return 'Failed to fetch user info from VK'
    else:
        abort(500)


@auth.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10
    )
    username = id_info.get("name")
    email = id_info.get("email")

    registration_result = google_registration(username, email)

    if registration_result:
        return redirect(url_for('auth.profile', username=registration_result.username))
    else:
        return jsonify({'error': 'Registration failed'}), 500


def google_registration(name, email):
    if current_user.is_authenticated:
        return redirect('/')

    name += '(Google)'
    user = db.session.scalar(select(User).where(User.username==name))

    # user exists and we login him/her
    if user and user.has_social_account:
        login_user(user)
        _update_user_session(user)
        return user
    elif user and not user.has_social_account:
        abort(500)
    else:
        user = User(
            username=name,
            password=os.environ['SOCIAL_USER_PASS'],
            email=email,
            has_social_account=True
            )
        db.session.add(user)
        db.session.commit()

        # generate social account information
        platform = 'Google'
        user_id=user.id
        new_social_account = SocialAccount(user_id=user_id, platform=platform)
        db.session.add(new_social_account)
        db.session.commit()
 
        # generate user role
        user_role = UserRole()
        user_role.role = db.session.query(Role).filter_by(name='Patient').first()
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()

        _create_user_session(user)
        login_user(user)
        _update_user_session(user)
        return user


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
        return redirect(url_for('auth.profile', username=user.username))
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