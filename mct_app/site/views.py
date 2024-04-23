from flask import Blueprint, render_template

site = Blueprint('site', __name__)

@site.route('/')
@site.route('/home')
def home():
    return render_template('home.html')
