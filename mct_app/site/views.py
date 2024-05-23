from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import werkzeug.exceptions
from mct_app import db

from mct_app.site.models import News
from sqlalchemy import select

from config import SOICAL_MEDIA_LINKS


NEWS_PER_PAGE = 3

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
    return render_template('news.html', news=news.items, next_url=next_url, prev_url=prev_url, pages_amount=pages_amount, active_page=active_page)

@site.route('/articles')
def articles():
    flash('articles', 'active_links')
    return render_template('articles.html')

@site.route('/textbook')
def textbook():
    flash('textbook', 'active_links')
    return render_template('textbook.html')

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
