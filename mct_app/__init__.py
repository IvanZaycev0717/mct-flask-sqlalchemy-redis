from flask import Flask
from mct_app.site.views import site

def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename['APP_SETTINGS'])
    app.register_blueprint(site)

    return app