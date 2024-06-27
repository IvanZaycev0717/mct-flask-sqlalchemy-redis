import os
from mct_app.auth.models import User


def test_admin_was_created(app, admin):
    with app.app_context():
        user = User.query.first()
        assert user is not None, 'Админ не бьл создан'
        assert user.username == admin._username, 'Имя админа не соответсвует'
        assert user.email == admin._email, 'Почта админа не соответсвует'

