from datetime import datetime
import json
import os
import uuid
from flask import Blueprint, abort, jsonify, render_template, request, send_from_directory, session, redirect, url_for, flash
import kombu
import werkzeug.exceptions
from mct_app import db
from flask import g

from mct_app.site.forms import ConsultationForm, QuestionForm, AnswerForm, SearchForm
from mct_app.site.models import Article, ArticleCard, News, TextbookChapter, TextbookParagraph
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from flask_ckeditor import upload_success, upload_fail
from flask_ckeditor import CKEditor
import requests
from flask_login import current_user
from mct_app.email import send_email
from mct_app import csrf, cache

from config import IMAGE_BASE_PATH, IMAGE_REL_PATHS, SOICAL_MEDIA_LINKS, basedir
from mct_app.utils import get_articles_by_months
from mct_app import csrf
from mct_app.auth.models import Question, Answer, User, Consultation, UserStatistics
from flask import current_app



GOOGLE_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
NEWS_PER_PAGE = 5
ARTICLES_PER_PAGE = 5
QUESTIONS_PER_PAGE = 5
SEARCH_RESULTS_PER_PAGE = 5


site = Blueprint('site', __name__)

@site.app_errorhandler(werkzeug.exceptions.Unauthorized)
def page_not_found(e):
    current_app.logger.error(f"There is 401 {e}")
    return render_template('errors/401.html'), 401

@site.app_errorhandler(werkzeug.exceptions.NotFound)
def page_not_found(e):
    current_app.logger.error(f"There is 404 {e}")
    return render_template('errors/404.html'), 404

@site.app_errorhandler(werkzeug.exceptions.Forbidden)
def access_denied(e):
    current_app.logger.error(f"There is 403 {e}")
    return render_template('errors/403.html'), 403

@site.app_errorhandler(werkzeug.exceptions.InternalServerError)
def server_error(e):
    current_app.logger.error(f"There is 500 {e}")
    return render_template('errors/500.html'), 500

@site.before_app_request
def before_request():
    g.search_form = SearchForm()

@site.app_context_processor
def base_template_data_processor() -> dict[str, str]:
    return {
        'links': SOICAL_MEDIA_LINKS,
        'current_year': datetime.now().year,
    }

@cache.cached(timeout=60, key_prefix='articles_list')
def create_articles_list():
    articles_by_month_list = db.session.query(
        ArticleCard.last_update,
        ArticleCard.article_id,
        ArticleCard.title).order_by(ArticleCard.last_update.desc()).all()
    return get_articles_by_months(articles_by_month_list)

@site.route('/')
@site.route('/home')
@cache.cached(timeout=86400)
def home():
    return render_template('home.html')

@site.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('site.home'))
    page = request.args.get('page', 1, type=int)
    paragraphs, total = TextbookParagraph.search(
        g.search_form.q.data,
        page,
        SEARCH_RESULTS_PER_PAGE
    )
    next_url = url_for('site.search', q=g.search_form.q.data, page=page + 1) if total > page * SEARCH_RESULTS_PER_PAGE else None
    prev_url = url_for('site.search', q=g.search_form.q.data, page=page - 1) if page > 1 else None
    return render_template(
        'search_result.html',
        title='Результаты поиска',
        paragraphs=paragraphs,
        next_url=next_url,
        prev_url=prev_url
        )


@site.route('/news')
@cache.cached(timeout=300)
def news():
    flash('news', 'active_links')
    query = select(News).order_by(News.last_update.desc())
    page = request.args.get('page', 1, type=int)
    news = db.paginate(query, page=page, per_page=NEWS_PER_PAGE, error_out=False)
    pages_amount = news.pages
    active_page = news.page
    next_url = url_for('site.news', page=news.next_num) if news.has_next else None
    prev_url = url_for('site.news', page=news.prev_num) if news.has_prev else None
    current_site = 'site.news'
    return render_template('news.html', news=news.items, next_url=next_url, prev_url=prev_url, pages_amount=pages_amount, active_page=active_page, current_site=current_site)

@site.route('/articles')
@csrf.exempt
@cache.cached(timeout=300)
def articles():
    flash('articles', 'active_links')

    query = select(ArticleCard).order_by(ArticleCard.last_update.desc())
    page = request.args.get('page', 1, type=int)
    articles = db.paginate(query, page=page, per_page=ARTICLES_PER_PAGE, error_out=False)
    pages_amount = articles.pages
    active_page = articles.page
    next_url = url_for('site.articles', page=articles.next_num) if articles.has_next else None
    prev_url = url_for('site.articles', page=articles.prev_num) if articles.has_prev else None
    current_site = 'site.articles'
    articles_by_month = create_articles_list()
    return render_template(
        'articles.html',
        articles=articles.items,
        next_url=next_url, prev_url=prev_url,
        pages_amount=pages_amount, active_page=active_page,
        current_site=current_site,
        articles_by_month=articles_by_month)

@site.route('/articles/<article_id>', methods=['GET', 'POST'])
def article(article_id, has_read=False, statisticts_dict=None):
    if current_user.is_authenticated:
        statistics_instance = UserStatistics.query.filter_by(user_id=current_user.id).first()
        statisticts_dict = json.loads(statistics_instance.articles_statistics)
        has_read = statisticts_dict[article_id]
        if request.form.get('has_read'):
            has_read = not has_read
            statisticts_dict[article_id] = has_read
            statistics_instance.articles_statistics = json.dumps(statisticts_dict)
            db.session.commit()
    articles_by_month = create_articles_list()
    article = Article.query.filter_by(id=article_id).first()
    return render_template('article.html', article=article, articles_by_month=articles_by_month, has_read=has_read, statisticts_dict=statisticts_dict)



@site.route('/textbook')
@cache.cached(timeout=40)
def textbook(statisticts_dict=None):
    flash('textbook', 'active_links')
    textbook_data = TextbookChapter.query.all()
    if current_user.is_authenticated:
        statistics_instance = UserStatistics.query.filter_by(user_id=current_user.id).first()
        statisticts_dict = json.loads(statistics_instance.textbook_statistics)
    return render_template('textbook.html', textbook_data=textbook_data, statisticts_dict=statisticts_dict)

@site.route('/textbook/<paragraph>', methods=['GET', 'POST'])
def textbook_paragraph(paragraph, has_read=None):
    paragraph = TextbookParagraph.query.filter_by(name=paragraph).first_or_404()
    paragraphs = TextbookParagraph.query.order_by(TextbookParagraph.name).all()
    current_index = next((index for index, par in enumerate(paragraphs) if par == paragraph), None)
    prev_index = current_index - 1 if current_index > 0 else None
    next_index = current_index + 1 if current_index < len(paragraphs) - 1 else None
    if current_user.is_authenticated:
        statistics_instance = UserStatistics.query.filter_by(user_id=current_user.id).first()
        statisticts_dict = json.loads(statistics_instance.textbook_statistics)
        has_read = statisticts_dict[str(paragraph.id)]
        if request.form.get('has_read'):
            has_read = not has_read
            statisticts_dict[str(paragraph.id)] = has_read
            statistics_instance.textbook_statistics = json.dumps(statisticts_dict)
            db.session.commit()
    return render_template('paragraph.html', paragraph=paragraph,  paragraphs=paragraphs, prev_index=prev_index, next_index=next_index, has_read=has_read)

@site.route('/questions', methods=['GET', 'POST'])
def questions():
    flash('questions', 'active_links')
    site_key = os.environ.get('GOOGLE_RECAPTCHA_SITE_KEY')
    secret_key = os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY')
    form = QuestionForm()
    if form.validate_on_submit():
        secret_response = request.form['g-recaptcha-response']
        verify_response = requests.post(url=f'{GOOGLE_VERIFY_URL}?secret={secret_key}&response={secret_response}').json()
        if not verify_response['success'] or verify_response['score'] < 0.5:
            current_app.logger.warning("User can not pass reCaptcha")
            abort(401)
        question = Question(
            anon_name=form.anon_name.data,
            user_id=None if current_user.is_anonymous else current_user.id,
            body=form.body.data,
            date=datetime.now(),
            ip_address=request.remote_addr
        )
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('site.question', question_id=question.id))

    page = request.args.get('page', 1, type=int)
    query = select(Question).order_by(Question.date.desc())
    questions = db.paginate(query, page=page, per_page=QUESTIONS_PER_PAGE)
    pages_amount = questions.pages
    active_page = questions.page
    current_site = 'site.questions'
    next_url = url_for('site.questions', page=questions.next_num) if questions.has_next else None
    prev_url = url_for('site.questions', page=questions.prev_num) if questions.has_prev else None
    return render_template(
        'questions.html',
        form=form,
        site_key=site_key,
        current_site=current_site,
        questions=questions.items,
        next_url=next_url,
        prev_url=prev_url,
        pages_amount=pages_amount,
        active_page=active_page)

@site.route('/questions/<question_id>', methods=['GET', 'POST'])
def question(question_id):
    question = Question.query.filter_by(id=question_id).first()
    form = AnswerForm()
    if form.validate_on_submit():
        answer = Answer(
            user_id=current_user.id,
            question_id=question_id,
            body=form.body.data
        )
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('site.question', question_id=question_id))
    return render_template('question.html', form=form, question=question)

@site.route('/consultation', methods=['GET', 'POST'])
def consultation():
    flash('consultation', 'active_links')
    site_key = os.environ.get('GOOGLE_RECAPTCHA_SITE_KEY')
    secret_key = os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY')
    form = ConsultationForm()
    if form.validate_on_submit():
        date=datetime.now()
        secret_response = request.form['g-recaptcha-response']
        verify_response = requests.post(url=f'{GOOGLE_VERIFY_URL}?secret={secret_key}&response={secret_response}').json()
        if not verify_response['success'] or verify_response['score'] < 0.5:
            current_app.logger.warning("User can not pass reCaptcha")
            abort(401)
        consultation = Consultation(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            user_id=current_user.id if current_user.is_authenticated else None,
            date=date
        )
        db.session.add(consultation)
        db.session.commit()
        try:
            task = send_email.delay(
                os.environ.get('ADMIN_EMAIL'),
                'Запись на консультацию',
                'forms/email/consultation',
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                date=date,
                next=request.args.get('next'))
        except kombu.exceptions.OperationalError:
            current_app.logger.exception("Redis sever is disconnected")
        flash(f'Уважаемый {form.first_name.data} {form.last_name.data}! Вы успешно записались на консультацию. С Вами свяжутся в ближайшее время!', 'send-consultation-message')
        return redirect(url_for('site.home'), code=302)
    return render_template('consultation.html', form=form, site_key=site_key)

@site.route('/contacts')
@cache.cached(timeout=86400)
def contacts():
    flash('contacts', 'active_links')
    return render_template('contacts.html')

@site.route('/cookie-info')
@cache.cached(timeout=86400)
def cookie_info():
    return render_template('cookie-info.html')