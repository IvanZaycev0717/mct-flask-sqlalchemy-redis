import os
from mct_app.auth.models import User


def test_admin_was_created(app):
    with app.app_context():
        admin = User.query.first()
        assert admin is not None, 'Админ не бьл создан'
        assert admin.username == os.environ.get("ADMIN_NAME"), 'Имя админа не соответсвует'
        assert admin.email == os.environ.get("ADMIN_EMAIL"), 'Почта админа не соответсвует'

