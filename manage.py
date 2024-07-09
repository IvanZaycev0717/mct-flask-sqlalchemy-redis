from typing import Any

from flask_migrate import Migrate

from mct_app import create_app, db
from config import CSV_FILE_PATHS
from mct_app.auth.models import Role, User, UserRole
from mct_app.site.models import Article, Image, News, TextbookParagraph


app = create_app()
celery = app.extensions['celery']
app.app_context().push()
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context() -> dict[str, Any]:
    """Make access to Flask from terminal."""
    return {'app': app, 'db': db,
            'general_setup': general_setup,
            'recreate_db': recreate_db,
            'User': User,
            'Image': Image,
            'news': News,
            'article': Article,
            'textbook': TextbookParagraph}


def recreate_db() -> None:
    """Recreates all the tables in database."""
    db.drop_all()
    db.create_all()
    db.session.commit()


def recreate_search_indexes() -> None:
    """Recreate indexes of textbook paragraphs in Elasticsearch."""
    TextbookParagraph.reindex()


def general_setup() -> None:
    """Generate roles and admin."""
    Role.insert_roles(CSV_FILE_PATHS.get('roles'))
    User.create_admin()
    UserRole.create_admin_role()


if __name__ == '__main__':
    general_setup()
    app.run(host='0.0.0.0', port=443, ssl_context='adhoc')
