from typing import Callable

from datetime import datetime
from flask import Blueprint, render_template
import werkzeug.exceptions 

from mct_app.site.links import SOICAL_MEDIA_LINKS

site = Blueprint('site', __name__)


@site.app_errorhandler(werkzeug.exceptions.NotFound)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@site.context_processor
def base_template_data_processor() -> dict[str, Callable[[str | None], str]]:
    def get_social_media_links(link: str) -> str:
        return SOICAL_MEDIA_LINKS[link]

    def get_current_year() -> str:
        return datetime.now().year

    return dict(links=get_social_media_links, current_year=get_current_year)

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
