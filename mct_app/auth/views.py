from datetime import datetime
import hashlib
import hmac
from http import HTTPStatus
import json
import os
from urllib.parse import urlsplit
import uuid


from flask import (abort, Blueprint, current_app,
                   flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from google.oauth2 import id_token
import kombu
from pip._vendor import cachecontrol
import requests
from sqlalchemy import select


from config import basedir, Is, Mood, SocialPlatform
from mct_app import cache
from mct_app.auth.models import (db, DiaryRecommendation,
                                 SocialAccount, User,
                                 UserDiary, UserRole,
                                 UserSession, UserStatistics)
from mct_app.auth.forms import (LoginForm, NewDiaryForm,
                                RecommendationForm, RegistrationForm,
                                RequestResetPasswordForm, ResetPasswordForm)
from mct_app.email import send_email
from mct_app.site.models import Article, TextbookParagraph
from mct_app.utils import get_random_email, get_statistics_data


auth = Blueprint('auth', __name__)

BOT_TOKEN_HASH = hashlib.sha256(os.environ['BOT_TOKEN'].encode())
client_secrets_file = os.path.join(basedir, 'client_secret.json')

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'],
    redirect_uri='https://localhost/google-callback'
)


@auth.route('/registration', methods=['GET', 'POST'])
def registration():
    """Render registration page."""
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
        user_role.role_id = Is.PATIENT
        user.roles.append(user_role)

        db.session.add(user)
        db.session.commit()

        _create_user_statistics(user.id)
        _create_user_session(user)
        login_user(user)
        cache.clear()
        return redirect(url_for('auth.profile', username=user.username))
    return render_template('forms/registration.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Render login page."""
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        query = select(User).where(User.username == form.username.data)
        user = db.session.scalar(query)
        if user is None:
            flash(
                'Неверное имя пользователя или'
                ' такого пользователя не существует',
                'name-error')
            return redirect('login')
        if not user.verify_password(form.password.data):
            flash('Неверный пароль', 'pass-error')
            return redirect('login')
        login_user(user)
        _update_user_session(user)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('auth.profile', username=user.username)
        cache.clear()
        return redirect(url_for('auth.profile', username=user.username))
    return render_template('forms/login.html', form=form)


@auth.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    """Render profile page."""
    if current_user.username != request.view_args['username']:
        role_id = current_user.roles[0].role_id
        if role_id not in (Is.ADMIN, Is.DOCTOR):
            current_app.logger.exception(
                f'User {username} is not ADMIN and DOCTOR')
            abort(403)
    user = db.first_or_404(select(User).where(User.username == username))
    correct_name: str = user.username
    if correct_name.endswith(')'):
        for platform in SocialPlatform:
            correct_name = correct_name.replace(platform, '')
    return render_template('profile/profile.html',
                           user=user,
                           correct_name=correct_name)


@auth.route('/profile/<username>/statistics')
@login_required
def user_statistics(username):
    """Render user's statistics page."""
    articles = json.loads(current_user.user_statistics.articles_statistics)
    textbooks = json.loads(current_user.user_statistics.textbook_statistics)
    articles_percent = get_statistics_data(articles)
    textbooks_percent = get_statistics_data(textbooks)
    return render_template(
        'profile/statistics.html',
        articles_percent=articles_percent,
        textbooks_percent=textbooks_percent)


@auth.route('/profile/<username>/diary', methods=['GET', 'POST'])
@login_required
def user_diary(username):
    """Render user's diary page."""
    form = NewDiaryForm()
    if form.validate_on_submit():
        diary_record = UserDiary(
            date=datetime.now(),
            mood=Mood(form.mood.data).name,
            record=form.record.data,
            user_id=current_user.id
        )
        db.session.add(diary_record)
        db.session.commit()
        return redirect(
            url_for('auth.user_diary', username=current_user.username))
    page = request.args.get('page', 1, type=int)
    if current_user.is_admin() or current_user.is_doctor():
        query = select(
            UserDiary).filter_by(
                user_id=User.query.filter_by(
                    username=username).first().id).order_by(
                        UserDiary.date.desc())
    else:
        query = select(
            UserDiary).filter_by(
                user_id=current_user.id).order_by(UserDiary.date.desc())
    diary_records = db.paginate(query, page=page, per_page=5, error_out=False)
    pages_amount = diary_records.pages
    active_page = diary_records.page
    current_site = 'auth.user_diary'
    next_url = url_for(
        'auth.user_diary',
        username=current_user.username, page=diary_records.next_num) \
        if diary_records.has_next else None
    prev_url = url_for(
        'auth.user_diary',
        username=current_user.username, page=diary_records.prev_num) \
        if diary_records.has_prev else None
    
    data = {
        'form': form,
        'current_site': current_site,
        'diary_records': diary_records.items,
        'next_url': next_url,
        'prev_url': prev_url,
        'pages_amount': pages_amount,
        'active_page': active_page,
        'edit_mode': False,
        'diary_username': username}

    return render_template('profile/diary.html', data=data)


@auth.route('/profile/<username>/patient_list', methods=['GET'])
@login_required
def patient_list(username):
    """Render a list of diaries of patients."""
    patient_list = UserRole.query.filter_by(role_id=Is.PATIENT).all()
    links = [
        (url_for(
            'auth.user_diary', username=user_role.user.username),
            user_role.user.username) for user_role in patient_list]
    return render_template(
        'profile/patient_list.html',
        links=links,
        username=username)


@auth.route('/profile/<username>/diary/delete_<diary_id>',
            methods=['GET', 'DELETE'])
@login_required
def delete_diary_record(username, diary_id):
    """Delete chosen diary record."""
    diary = UserDiary.query.get_or_404(diary_id)
    db.session.delete(diary)
    db.session.commit()
    return redirect(url_for('auth.user_diary', username=username))


@auth.route('/profile/<username>/diary/edit_<diary_id>',
            methods=['GET', 'POST'])
@login_required
def edit_diary_record(username, diary_id):
    """Edit chosen diary record."""
    diary = UserDiary.query.get_or_404(diary_id)
    form = NewDiaryForm(obj=diary)
    if form.validate_on_submit():
        diary.mood = Mood(form.mood.data).name
        diary.record = form.record.data
        db.session.commit()
        return redirect(url_for('auth.user_diary', username=username))
    return render_template('profile/diary.html', form=form, edit_mode=True)


@auth.route('/profile/<username>/diary/recommend_<diary_id>',
            methods=['GET', 'POST'])
@login_required
def give_recommendation(username, diary_id):
    """Allow to write a recommendation on diary record."""
    diary = UserDiary.query.get_or_404(diary_id)
    form = RecommendationForm()
    if form.validate_on_submit():
        recommendation = DiaryRecommendation(
            recommendation=form.record.data,
            user_diary_id=diary.id,
            user_id=current_user.id
        )
        db.session.add(recommendation)
        db.session.commit()
        return redirect(url_for('auth.user_diary', username=username))
    return render_template('forms/recommendation.html', form=form, diary=diary)


@auth.route('/profile/<username>/diary/recommend_delete_<recommed_id>',
            methods=['GET', 'DELETE'])
@login_required
def delete_recommendation(username, recommed_id):
    """Delete chosen recommendation."""
    recommendation = DiaryRecommendation.query.get_or_404(recommed_id)
    db.session.delete(recommendation)
    db.session.commit()
    return redirect(url_for('auth.user_diary', username=username))


@auth.route('/logout')
def logout():
    """Sign out user."""
    logout_user()
    cache.clear()
    session.clear()
    return redirect('/')


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Send a request to reset password."""
    if not current_user.is_anonymous():
        return redirect('/')
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.has_social_account:
                flash(
                    f'Войдите через {user.social_account.platform}',
                    'send-reset-password')
                return redirect(url_for('auth.login'))
            else:
                token = user.generate_password_reset_token()
                reset_link = url_for(
                    'auth.reset_password',
                    token=token,
                    _external=True)
                try:
                    task = send_email.delay(
                        recipient=user.email,
                        subject='Сброс пароля',
                        template='forms/email/reset_password',
                        reset_link=reset_link,
                        next=request.args.get('next'))
                except kombu.exceptions.OperationalError:
                    current_app.logger.exception("Redis sever is disconnected")
        flash(
            f'Сброс пароля был отправлен на почту {form.email.data}',
            'send-reset-password')
        return redirect(url_for('auth.login'))
    return render_template('forms/reset_password_request.html', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Render reset password form."""
    if not current_user.is_anonymous():
        return redirect('/')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash(
                'Проверьте правильность введенного адреса электронной почты',
                'reset-pass-error')
            return redirect(url_for('auth.reset_password_request'))
        if user.reset_password(token, form.new_password.data):
            flash(
                f'Пароль обновлён для пользователя с email: {user.email}',
                'send-reset-password')
            return redirect(url_for('auth.login'))
        else:
            flash('Неверная ссылка на обновление пароля',
                  'send-reset-password')
            return redirect(url_for('auth.login'))
    return render_template('forms/reset_password.html', form=form)


@auth.route("/google-login")
def google_login():
    """Reginster or sign in by means of Google Account."""
    authorization_url, state = flow.authorization_url()
    return redirect(authorization_url)


@auth.route("/google-callback")
def google_callback():
    """Fetch a response from Google."""
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(
        session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=os.environ.get('GOOGLE_CLIENT_ID'),
        clock_skew_in_seconds=10
    )
    social_uid = str(id_info.get('sub'))
    username = id_info.get('name')
    email = id_info.get('email')

    if not email:
        email = get_random_email()

    registration_result = social_registration(
        name=username,
        email=email,
        social_platform=SocialPlatform.GOOGLE,
        uid=social_uid)

    if not registration_result:
        current_app.logger.exception("Goggle enter FAIL")
        abort(500)

    return redirect(
        url_for('auth.profile',
                username=registration_result.username))


@auth.route('/vk-login')
def vk_login():
    """Reginster or sign in by means of VK Account."""
    redirect_url = os.environ.get('VK_API_REQUEST')
    return redirect(redirect_url)


@auth.route('/vk-callback')
def vk_callback():
    """Fetch a response from VK."""
    code = request.args.get('code')
    response = requests.post('https://oauth.vk.com/access_token', params={
        'client_id': os.environ.get('SOCIAL_AUTH_VK_OAUTH2_KEY'),
        'client_secret': os.environ.get('SOCIAL_AUTH_VK_OAUTH2_SECRET'),
        'redirect_uri': os.environ.get('SOCIAL_AUTH_VK_REDIRECT'),
        'code': code,
    })

    if response.status_code == HTTPStatus.OK:
        data = response.json()
        access_token = data['access_token']
        user_id = data['user_id']

        user_info_response = requests.post(
            'https://api.vk.com/method/users.get',
            params={
                'access_token': access_token,
                'user_ids': user_id,
                'v': '5.199'})
        if user_info_response.status_code == HTTPStatus.OK:
            user_info = user_info_response.json()['response'][0]
            user_data = {
                'id': user_info.get('id'),
                'first_name': user_info.get('first_name'),
                'last_name': user_info.get('last_name'),
            }

            username = f'{user_data['first_name']} {user_data['last_name']}'
            email = get_random_email()
            social_uid = str(user_data['id'])

            registration_result = social_registration(
                name=username,
                email=email,
                social_platform=SocialPlatform.VK,
                uid=social_uid)

            if not registration_result:
                current_app.logger.exception('VK enter FAIL')
                abort(500)

            return redirect(
                url_for('auth.profile',
                        username=registration_result.username))
    else:
        current_app.logger.exception('VK response FAIL')
        abort(500)


@auth.route('/ok-login')
def ok_login():
    """Reginster or sign in by means of OK Account."""
    redicrect_url = os.environ.get('OK_API_REQUEST')
    return redirect(redicrect_url)


@auth.route('/ok-callback')
def ok_callback():
    """Fetch a response from Odnoklassniki."""
    access_token = request.args.get('access_token')
    session_secret_key = request.args.get('session_secret_key')
    if access_token and session_secret_key \
        and 'null' not in access_token \
            and 'null' not in session_secret_key:
        url = 'https://api.ok.ru/fb.do'
        params = {
            'application_key': os.environ.get('OK_PUBLIC_KEY'),
            'method': 'users.getCurrentUser',
            'access_token': access_token,
            'sig': session_secret_key,
            'format': 'json'
        }

        ok_response = requests.post(url, params=params)
        if ok_response.status_code == HTTPStatus.OK:
            ok_user_data = ok_response.json()

            username = ok_user_data.get('name')
            email = ok_user_data.get('email')
            social_uid = str(ok_user_data.get('uid'))

            if not email:
                email = get_random_email()

            registration_result = social_registration(
                name=username,
                email=email,
                social_platform=SocialPlatform.ODNOKLASSNIKI,
                uid=social_uid)

            if not registration_result:
                current_app.logger.exception('OK enter FAIL')
                abort(500)

            return redirect(
                url_for('auth.profile',
                        username=registration_result.username))
    return render_template('ok.html')


@auth.route('/ok-redirect')
def ok_redirect():
    """Redirect to OK enter."""
    return render_template('ok.html')


@auth.route('/yandex-login')
def yandex_login():
    """Reginster or sign in by means of Yandex Account."""
    redirect_url = os.environ.get('YANDEX_API_REQUEST')
    return redirect(redirect_url)


@auth.route('/yandex-callback')
def yandex_callback():
    """Fetch a response from Yandex."""
    code = request.args.get('code')
    if code:
        token_url = 'https://oauth.yandex.ru/token'
        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': os.environ.get('YA_CLIENT_ID'),
            'client_secret': os.environ.get('YA_CLIENT_SECRET')
        }
        response = requests.post(token_url, data=token_params)
        data = response.json()
        if 'access_token' in data:
            user_info_url = 'https://login.yandex.ru/info'
            headers = {'Authorization': f'OAuth {data['access_token']}'}
            user_info_response = requests.post(user_info_url, headers=headers)
            user_info = user_info_response.json()

            username = user_info.get('login')
            email = user_info.get('default_email')
            social_uid = str(user_info.get('id'))
            phone = user_info.get('default_phone').get('number')

            if not email:
                email = get_random_email()

            registration_result = social_registration(
                name=username,
                email=email,
                social_platform=SocialPlatform.YANDEX,
                uid=social_uid,
                phone=phone)

            if not registration_result:
                current_app.logger.exception('YANDEX enter FAIL')
                abort(500)

            return redirect(
                url_for('auth.profile',
                        username=registration_result.username))
    else:
        current_app.logger.exception(
            'YANDEX response FAIL')
        abort(500)


@auth.route('/telegram-callback')
def telegram_callback():
    """Reginster or sign in by means of Telegram Account."""

    username = request.args.get('username')
    social_uid = str(request.args.get('id'))
    email = get_random_email()

    if username:
        # check security
        query_hash = request.args.get('hash')
        params = request.args.items()
        data_check_string = '\n'.join(
            sorted(f'{x}={y}' for x, y in params if x not in ('hash', 'next')))
        computed_hash = hmac.new(
            BOT_TOKEN_HASH.digest(),
            data_check_string.encode(),
            'sha256').hexdigest()
        is_correct = hmac.compare_digest(computed_hash, query_hash)
        if not is_correct:
            current_app.logger.exception('Telegram HASH problem')
            abort(403)

        
        registration_result = social_registration(
            name=username,
            email=email,
            social_platform=SocialPlatform.TELEGRAM,
            uid=social_uid)

        if not registration_result:
            current_app.logger.exception('TELEGRAM response FAIL')
            abort(500)

        return redirect(url_for('auth.profile',
                                username=registration_result.username))
    else:
        current_app.logger.exception("Telegram response FAIL")
        abort(500)


def social_registration(name, email, social_platform, uid, phone=None):
    """Sign in via social platform."""
    if current_user.is_authenticated:
        return redirect('/')

    name += social_platform
    user = db.session.scalar(select(User).where(User.username == name))

    if user and user.has_social_account and user.social_uid == uid:
        login_user(user)
        _update_user_session(user)
        return user
    elif user and user.has_social_account and user.social_uid != uid:
        current_app.logger.error(
            'User needs to register via another social media')
        abort(451)
    else:
        user = User(
            username=name,
            password=str(uuid.uuid4()),
            email=email,
            has_social_account=True,
            phone=phone,
            social_uid=uid)
        db.session.add(user)
        db.session.commit()

        # generate social account information
        user_id = user.id
        new_social_account = SocialAccount(
            user_id=user_id,
            platform=social_platform)
        db.session.add(new_social_account)
        db.session.commit()

        # generate user role
        user_role = UserRole()
        user_role.role_id = Is.PATIENT
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()

        _create_user_statistics(user.id)
        _create_user_session(user)
        login_user(user)
        _update_user_session(user)
        return user


def _create_user_session(user):
    user_sessions = UserSession(ip_address=request.remote_addr,
                                last_activity=datetime.now(),
                                user_id=user.id,
                                attendance=1)
    db.session.add(user_sessions)
    db.session.commit()


def _update_user_session(user):
    query = select(UserSession).where(UserSession.user_id == user.id)
    user_session = db.session.scalar(query)
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


def _add_user_statistics():
    articles = {id[0]: False for id in db.session.query(Article.id).all()}
    textbooks = {
        id[0]: False for id in db.session.query(TextbookParagraph.id).all()}
    return articles, textbooks


def _create_user_statistics(user_id):
    article_stat, textbook_stat = _add_user_statistics()

    articles_statistics = json.dumps(article_stat)
    textbook_statistics = json.dumps(textbook_stat)

    statistics = UserStatistics(
        articles_statistics=articles_statistics,
        textbook_statistics=textbook_statistics,
        user_id=user_id
    )
    db.session.add(statistics)
    db.session.commit()
