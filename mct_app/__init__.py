from flask import Flask
from mct_app.site.views import site

app = Flask(__name__)
app.register_blueprint(site)