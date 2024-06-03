from datetime import datetime
import os
import uuid
from flask import Blueprint, render_template, request, send_from_directory, session, redirect, url_for, flash
import werkzeug.exceptions
from mct_app import db

from mct_app.site.models import Article, ArticleCard, News, TextbookChapter, TextbookParagraph
from sqlalchemy import select
from flask_ckeditor import upload_success, upload_fail
from flask_ckeditor import CKEditor

from config import IMAGE_BASE_PATH, IMAGE_REL_PATHS, SOICAL_MEDIA_LINKS, basedir
from mct_app.utils import get_articles_by_months, get_textbook_chapters_paragraphs
from mct_app import csrf


NEWS_PER_PAGE = 3
ARTICLES_PER_PAGE = 2

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
    articles_by_month_list = db.session.query(
        ArticleCard.last_update,
        ArticleCard.article_id,
        ArticleCard.title).order_by(ArticleCard.last_update.desc()).all()
    articles_by_month = get_articles_by_months(articles_by_month_list)

    return {
        'links': SOICAL_MEDIA_LINKS,
        'current_year': datetime.now().year,
        'articles_by_month': articles_by_month
    }


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
    return render_template(
        'articles.html',
        articles=articles.items,
        next_url=next_url, prev_url=prev_url,
        pages_amount=pages_amount, active_page=active_page,
        current_site=current_site)

@site.route('/articles/<article_id>')
def article(article_id):
    article = Article.query.filter_by(id=article_id).first()
    return render_template('article.html', article=article)

@site.route('/textbook')
def textbook():
    flash('textbook', 'active_links')
    query = select(TextbookChapter.name, TextbookParagraph.name).join_from(TextbookParagraph, TextbookChapter)
    textbook_data = db.session.execute(query).all()
    textbook_items = get_textbook_chapters_paragraphs(textbook_data)
    print(textbook_items)
    return render_template('textbook.html', textbook_items=textbook_items)

@site.route('/textbook/<paragraph>')
def textbook_paragraph(paragraph):
    paragraph = TextbookParagraph.query.filter_by(name=paragraph).first_or_404()
    return render_template('paragraph.html', paragraph=paragraph)

@site.route('/questions')
def questions():
    flash('questions', 'active_links')
    return render_template('questions.html')

@site.route('/consultation')
def consultation():
    flash('consultation', 'active_links')
    return render_template('consultation.html')

@site.route('/contacts')
def contacts():
    flash('contacts', 'active_links')
    return render_template('contacts.html')