from flask import Blueprint, render_template, session, redirect, url_for
from mct_app.auth.models import User, db
from mct_app.auth.forms import LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session['phone'] = form.phone.data
        return redirect(url_for('site.home'))
    return render_template('forms/login.html', form=form)

