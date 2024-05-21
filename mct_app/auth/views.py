import os
from datetime import datetime
from flask import Blueprint, jsonify, render_template, redirect, session, url_for, flash, request
import requests
from mct_app.auth.models import User, UserSession, db, UserRole, Role, SocialAccount
from mct_app.auth.forms import RegistrationForm, LoginForm, ResetPasswordForm, RequestResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import select, update
from urllib.parse import urlsplit
from flask import abort
from config import Is, SocialPlatform
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from config import basedir
from http import HTTPStatus
from mct_app.email import send_email


auth = Blueprint('auth', __name__)

SOCIAL_AUTH_VK_OAUTH2_KEY = '51920174'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'cqUJVoTNym6Os5pQWfDJ'
SOCIAL_AUTH_VK_REDIRECT = 'https://localhost/vk-callback'

OK_CLIENT_ID = '512002593594'
OK_CLIENT_SECRET = '0AF67F589594B24F2F41BDE6'
OK_PUBLIC_KEY = 'CLDEJMLGDIHBABABA'
OK_REDIRECT_URI = 'https://localhost/ok-callback'

YA_CLIENT_ID = '50e26776ec814fe6a520f6d98659f8f1'
YA_CLIENT_SECRET = '2e2cfc985cbe4afe93fafcc8d8f408db'
YA_REDIRECT_URI = 'https://localhost/yandex-callback'

GOOGLE_CLIENT_ID = '904059633989-0hasb3m586f1u6u0tcnumm249itt9a4k.apps.googleusercontent.com'

client_secrets_file = os.path.join(basedir, 'client_secret.json')

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://localhost/google-callback"
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
    correct_name: str = user.username
    if correct_name.endswith(')'):
        for platform in SocialPlatform:
            correct_name = correct_name.replace(platform, '')
    return render_template('profile/profile.html', user=user, correct_name=correct_name)

@auth.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect('/')

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect('/')
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.has_social_account:
                flash(f'Войдите через {user.social_account.platform}', 'send-reset-password')
                return redirect(url_for('auth.login'))
            else:
                token = user.generate_password_reset_token()
                reset_link = url_for('auth.reset_password', token=token, _external=True)
                send_email(
                    user.email,
                    'Сброс пароля',
                    'forms/email/reset_password',
                    user=user,
                    reset_link=reset_link,
                    next=request.args.get('next'))
        flash(f'Сброс пароля был отправлен на почту {form.email.data}', 'send-reset-password')
        return redirect(url_for('auth.login'))
    return render_template('forms/reset_password_request.html', form=form)
            
@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect('/')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('Проверьте правильность введенного адреса электронной почты', 'reset-pass-error')
            return redirect(url_for('auth.reset_password_request'))
        if user.reset_password(token, form.new_password.data):
            flash(f'Пароль обновлён для пользователя с email: {user.email}', 'send-reset-password')
            return redirect(url_for('auth.login'))
        else:
            flash(f'Неверная ссылка на обновление пароля', 'send-reset-password')
            return redirect(url_for('auth.login'))
    return render_template('forms/reset_password.html', form=form)

        

@auth.route("/google-login")
def google_login():
    authorization_url, state = flow.authorization_url()
    return redirect(authorization_url)

@auth.route("/google-callback")
def google_callback():
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

    registration_result = social_registration(username, email, SocialPlatform.GOOGLE)

    if not registration_result:
        abort(500)

    return redirect(url_for('auth.profile', username=registration_result.username))

@auth.route('/vk-login')
def vk_login():
    return redirect(fr'https://oauth.vk.com/authorize?client_id={SOCIAL_AUTH_VK_OAUTH2_KEY}&scope=messages;email&redirect_uri={SOCIAL_AUTH_VK_REDIRECT}&response_type=code')

@auth.route('/vk-callback')
def vk_callback():
    code = request.args.get('code')
    response = requests.get('https://oauth.vk.com/access_token', params={
        'client_id': SOCIAL_AUTH_VK_OAUTH2_KEY,
        'client_secret': SOCIAL_AUTH_VK_OAUTH2_SECRET,
        'redirect_uri': SOCIAL_AUTH_VK_REDIRECT,
        'code': code,
    })

    if response.status_code == HTTPStatus.OK:
        data = response.json()
        access_token = data['access_token']
        user_id = data['user_id']

        user_info_response = requests.get('https://api.vk.com/method/users.get', params={
            'access_token': access_token,
            'user_ids': user_id,
            'v': '5.199',
        })
        if user_info_response.status_code == HTTPStatus.OK:
            user_info = user_info_response.json()['response'][0]
            user_data = {
                'id': user_info['id'],
                'first_name': user_info.get('first_name'),
                'last_name': user_info.get('last_name'),
            }
            username = f'{user_data['first_name']} {user_data['last_name']}'
            email = os.environ['SOCIAL_EMAIL']
            registration_result = social_registration(username, email, SocialPlatform.VK)

            if not registration_result:
                abort(500)

            return redirect(url_for('auth.profile', username=registration_result.username))
    else:
        abort(500)

@auth.route('/ok-login')
def ok_login():
    return redirect(f'https://connect.ok.ru/oauth/authorize?client_id={OK_CLIENT_ID}&scope=VALUABLE_ACCESS;GET_EMAIL&response_type=token&redirect_uri={OK_REDIRECT_URI}')

@auth.route('/ok-callback')
def ok_callback():
    access_token = request.args.get('access_token')
    session_secret_key = request.args.get('session_secret_key')
    if access_token and session_secret_key and 'null' not in access_token and 'null' not in session_secret_key:
        url = 'https://api.ok.ru/fb.do'
        params = {
            'application_key': OK_PUBLIC_KEY,
            'method': 'users.getCurrentUser',
            'access_token': access_token,
            'sig': session_secret_key,
            'format': 'json'
        }

        ok_response = requests.get(url, params=params)
        if ok_response.status_code == HTTPStatus.OK:
            ok_user_data = ok_response.json()
            username = ok_user_data.get('name')
            email = ok_user_data.get('email')

            if not email:
                email = os.environ.get('SOCIAL_EMAIL')

            registration_result = social_registration(username, email, SocialPlatform.ODNOKLASSNIKI)

            if not registration_result:
                abort(500)

            return redirect(url_for('auth.profile', username=registration_result.username))
    else:
        return redirect('/ok-redirect')

@auth.route('/ok-redirect')
def ok_redirect():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile', username=current_user.username))
    return redirect('/')


@auth.route('/yandex-login')
def yandex_login():
    return redirect(f'https://oauth.yandex.ru/authorize?response_type=code&client_id={YA_CLIENT_ID}&redirect_uri={YA_REDIRECT_URI}')

@auth.route('/yandex-callback')
def yandex_callback():
    code = request.args.get('code')
    if code:
        token_url = f'https://oauth.yandex.ru/token'
        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': YA_CLIENT_ID,
            'client_secret': YA_CLIENT_SECRET
        }
        response = requests.post(token_url, data=token_params)
        data = response.json()
        if 'access_token' in data:
            user_info_url = 'https://login.yandex.ru/info'
            headers = {'Authorization': f'OAuth {data["access_token"]}'}
            user_info_response = requests.get(user_info_url, headers=headers)
            user_info = user_info_response.json()
            username = user_info['login']
            email = user_info['default_email']

            registration_result = social_registration(username, email, SocialPlatform.YANDEX)

            if not registration_result:
                abort(500)

            return redirect(url_for('auth.profile', username=registration_result.username))
    else:
        abort(500)

@auth.route('/telegram-callback')
def telegram_callback():
    username = request.args.get('username')
    if username:
        email = os.environ['SOCIAL_EMAIL']

        registration_result = social_registration(username, email, SocialPlatform.TELEGRAM)

        if not registration_result:
            abort(500)
        return redirect(url_for('auth.profile', username=registration_result.username))
    else:
        abort(500)



def social_registration(name, email, social_platform):
    if current_user.is_authenticated:
        return redirect('/')

    name += social_platform
    user = db.session.scalar(select(User).where(User.username==name))

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
        user_id = user.id
        new_social_account = SocialAccount(user_id=user_id, platform=social_platform)
        db.session.add(new_social_account)
        db.session.commit()
 
        # generate user role
        user_role = UserRole()
        user_role.role_id = Is.PATIENT
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()

        _create_user_session(user)
        login_user(user)
        _update_user_session(user)
        return user

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
    else:
        _create_user_session(user)
