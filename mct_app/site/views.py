from datetime import datetime
import os
import uuid
from flask import Blueprint, abort, jsonify, render_template, request, send_from_directory, session, redirect, url_for, flash
import werkzeug.exceptions
from mct_app import db

from mct_app.site.forms import QuestionForm
from mct_app.site.models import Article, ArticleCard, News, TextbookChapter, TextbookParagraph
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from flask_ckeditor import upload_success, upload_fail
from flask_ckeditor import CKEditor
import requests
from flask_login import current_user

from config import IMAGE_BASE_PATH, IMAGE_REL_PATHS, SOICAL_MEDIA_LINKS, basedir
from mct_app.utils import get_articles_by_months, get_textbook_chapters_paragraphs
from mct_app import csrf
from mct_app.auth.models import Question, Answer, User



GOOGLE_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
NEWS_PER_PAGE = 3
ARTICLES_PER_PAGE = 2
QUESTIONS_PER_PAGE = 6


site = Blueprint('site', __name__)

@site.app_errorhandler(werkzeug.exceptions.Unauthorized)
def page_not_found(e):
    return render_template('errors/401.html'), 401

@site.app_errorhandler(werkzeug.exceptions.NotFound)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@site.app_errorhandler(werkzeug.exceptions.Forbidden)
def access_denied(e):
    return render_template('errors/403.html'), 403

@site.app_errorhandler(werkzeug.exceptions.InternalServerError)
def server_error(e):
    return render_template('errors/500.html'), 500


@site.app_context_processor
def base_template_data_processor() -> dict[str, str]:
    return {
        'links': SOICAL_MEDIA_LINKS,
        'current_year': datetime.now().year,
    }


def create_articles_list():
    articles_by_month_list = db.session.query(
        ArticleCard.last_update,
        ArticleCard.article_id,
        ArticleCard.title).order_by(ArticleCard.last_update.desc()).all()
    articles_by_month = get_articles_by_months(articles_by_month_list)
    return articles_by_month


@site.route('/')
@site.route('/home')
def home():
    return render_template('home.html')

@site.route('/news')
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

@site.route('/articles/<article_id>')
def article(article_id):
    articles_by_month = create_articles_list()
    article = Article.query.filter_by(id=article_id).first()
    return render_template('article.html', article=article, articles_by_month=articles_by_month)

@site.route('/textbook')
def textbook():
    flash('textbook', 'active_links')
    query = select(TextbookChapter.name, TextbookParagraph.name).join_from(TextbookParagraph, TextbookChapter).order_by(TextbookChapter.name, TextbookParagraph.name)
    textbook_data = db.session.execute(query).all()
    textbook_items = get_textbook_chapters_paragraphs(textbook_data)
    return render_template('textbook.html', textbook_items=textbook_items)

@site.route('/textbook/<paragraph>')
def textbook_paragraph(paragraph):
    paragraph = TextbookParagraph.query.filter_by(name=paragraph).first_or_404()
    paragraphs = TextbookParagraph.query.order_by(TextbookParagraph.name).all()
    current_index = next((index for index, par in enumerate(paragraphs) if par == paragraph), None)
    prev_index = current_index - 1 if current_index > 0 else None
    next_index = current_index + 1 if current_index < len(paragraphs) - 1 else None
    return render_template('paragraph.html', paragraph=paragraph,  paragraphs=paragraphs, prev_index=prev_index, next_index=next_index)

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
    return render_template('question.html', question=question)

@site.route('/consultation')
def consultation():
    flash('consultation', 'active_links')
    return render_template('consultation.html')

@site.route('/contacts')
def contacts():
    flash('contacts', 'active_links')
    return render_template('contacts.html')