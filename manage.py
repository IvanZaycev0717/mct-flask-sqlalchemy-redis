from mct_app import create_app, db
from flask_migrate import Migrate
from config import CSV_FILE_PATHS
from mct_app.auth.models import Role, User, UserRole
from mct_app.site.models import Image, News, Article, TextbookParagraph
import locale


locale.setlocale(locale.LC_ALL, ('ru_RU', 'UTF-8'))
app, celery = create_app()
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return {'app': app, 'db': db,
            'general_setup': general_setup,
            'recreate_db': recreate_db,
            'User': User,
            'Image': Image,
            'news': News,
            'article': Article,
            'textbook': TextbookParagraph}

def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


def general_setup():
    Role.insert_roles(CSV_FILE_PATHS.get('roles'))
    User.create_admin()
    UserRole.create_admin_role()


if __name__ == '__main__':
    general_setup()
    app.run(host='0.0.0.0', port=443, ssl_context='adhoc')