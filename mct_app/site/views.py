from typing import Callable

from datetime import datetime
from flask import g
from flask import Blueprint, render_template
import werkzeug.exceptions 

from mct_app.site.links import SOICAL_MEDIA_LINKS

site = Blueprint('site', __name__)


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
def base_template_data_processor() -> dict[str, Callable[[str | None], str]]:

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
    return render_template('news.html')

@site.route('/articles')
def articles():
    return render_template('articles.html')

@site.route('/textbook')
def textbook():
    return render_template('textbook.html')

@site.route('/questions')
def questions():
    return render_template('questions.html')

@site.route('/consultation')
def consultation():
    return render_template('consultation.html')

@site.route('/contacts')
def contacts():
    return render_template('contacts.html')
