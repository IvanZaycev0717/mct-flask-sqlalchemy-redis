from mct_app import create_app, db
from flask_migrate import Migrate
from config import CSV_FILE_PATHS
from mct_app.auth.models import Role, Permission, RolePermission

app = create_app()
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {'app': app, 'db': db,
            'general_setup': general_setup,
            'recreate_db': recreate_db}

def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()

def general_setup():
    Role.insert_roles(CSV_FILE_PATHS.get('roles'))
    Permission.insert_permissions(CSV_FILE_PATHS.get('permissions'))
    RolePermission.insert_roles_permissions(CSV_FILE_PATHS.get('roles_permissions'))


if __name__ == '__main__':
    recreate_db()
    general_setup()
    app.run()